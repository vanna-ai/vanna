import datetime
import os
import uuid
from typing import List, Optional
from vertexai.language_models import (
  TextEmbeddingInput,
  TextEmbeddingModel
)

import pandas as pd
from google.cloud import bigquery

from ..base import VannaBase


class BigQuery_VectorStore(VannaBase):
    def __init__(self, config: dict, **kwargs):
        self.config = config

        self.n_results_sql = config.get("n_results_sql", config.get("n_results", 10))
        self.n_results_documentation = config.get("n_results_documentation", config.get("n_results", 10))
        self.n_results_ddl = config.get("n_results_ddl", config.get("n_results", 10))

        if "api_key" in config or os.getenv("GOOGLE_API_KEY"):
            """
            If Google api_key is provided through config
            or set as an environment variable, assign it.
            """
            print("Configuring genai")
            self.type = "GEMINI"
            import google.generativeai as genai

            genai.configure(api_key=config["api_key"])

            self.genai = genai
        else:
            self.type = "VERTEX_AI"
            # Authenticate using VertexAI

        if self.config.get("project_id"):
            self.project_id = self.config.get("project_id")
        else:
            self.project_id = os.getenv("GOOGLE_CLOUD_PROJECT")

        if self.project_id is None:
            raise ValueError("Project ID is not set")

        self.conn = bigquery.Client(project=self.project_id)

        dataset_name = self.config.get('bigquery_dataset_name', 'vanna_managed')
        self.dataset_id = f"{self.project_id}.{dataset_name}"
        dataset = bigquery.Dataset(self.dataset_id)

        try:
            self.conn.get_dataset(self.dataset_id)  # Make an API request.
            print(f"Dataset {self.dataset_id} already exists")
        except Exception:
            # Dataset does not exist, create it
            dataset.location = "US"
            self.conn.create_dataset(dataset, timeout=30)  # Make an API request.
            print(f"Created dataset {self.dataset_id}")

        # Create a table called training_data in the dataset that contains the columns:
        # id, training_data_type, question, content, embedding, created_at

        self.table_id = f"{self.dataset_id}.training_data"
        schema = [
            bigquery.SchemaField("id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("training_data_type", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("question", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("content", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("embedding", "FLOAT64", mode="REPEATED"),
            bigquery.SchemaField("created_at", "TIMESTAMP", mode="REQUIRED"),
        ]

        table = bigquery.Table(self.table_id, schema=schema)

        try:
            self.conn.get_table(self.table_id)  # Make an API request.
            print(f"Table {self.table_id} already exists")
        except Exception:
            # Table does not exist, create it
            self.conn.create_table(table, timeout=30)  # Make an API request.
            print(f"Created table {self.table_id}")

        # Create VECTOR INDEX IF NOT EXISTS
        # TODO: This requires 5000 rows before it can be created
        # vector_index_query = f"""
        # CREATE VECTOR INDEX IF NOT EXISTS my_index
        # ON `{self.table_id}`(embedding)
        # OPTIONS(
        #     distance_type='COSINE',
        #     index_type='IVF',
        #     ivf_options='{{"num_lists": 1000}}'
        # )
        # """

        # try:
        #     self.conn.query(vector_index_query).result()  # Make an API request.
        #     print(f"Vector index on {self.table_id} created or already exists")
        # except Exception as e:
        #     print(f"Failed to create vector index: {e}")

    def store_training_data(self, training_data_type: str, question: str, content: str, embedding: List[float], **kwargs) -> str:
        id = str(uuid.uuid4())
        created_at = datetime.datetime.now()
        self.conn.insert_rows_json(self.table_id, [{
            "id": id,
            "training_data_type": training_data_type,
            "question": question,
            "content": content,
            "embedding": embedding,
            "created_at": created_at.isoformat()
        }])

        return id

    def fetch_similar_training_data(self, training_data_type: str, question: str, n_results, **kwargs) -> pd.DataFrame:
        question_embedding = self.generate_question_embedding(question)

        query = f"""
        SELECT
            base.id as id,
            base.question as question,
            base.training_data_type as training_data_type,
            base.content as content,
            distance
        FROM
            VECTOR_SEARCH(
                TABLE `{self.table_id}`,
                'embedding',
                (SELECT * FROM UNNEST([STRUCT({question_embedding})])),
                top_k => 5,
                distance_type => 'COSINE',
                options => '{{"use_brute_force":true}}'
            )
        WHERE
            base.training_data_type = '{training_data_type}'
        """

        results = self.conn.query(query).result().to_dataframe()
        return results

    def get_embeddings(self, data: str, task: str) -> List[float]:
        embeddings = None

        if self.type == "VERTEX_AI":
          input = [TextEmbeddingInput(data, task)]
          model = TextEmbeddingModel.from_pretrained("text-embedding-004")

          result = model.get_embeddings(input)

          if len(result) > 0:
              embeddings = result[0].values
        else:
          # Use Gemini Consumer API
          result = self.genai.embed_content(
            model="models/text-embedding-004",
            content=data,
            task_type=task)

          if 'embedding' in result:
            embeddings = result['embedding']

        return embeddings

    def generate_question_embedding(self, data: str, **kwargs) -> List[float]:
        result = self.get_embeddings(data, "RETRIEVAL_QUERY")

        if result != None:
            return result
        else:
            raise ValueError("No embeddings returned")

    def generate_storage_embedding(self, data: str, **kwargs) -> List[float]:
        result = self.get_embeddings(data, "RETRIEVAL_DOCUMENT")

        if result != None:
            return result
        else:
            raise ValueError("No embeddings returned")

        # task = "RETRIEVAL_DOCUMENT"
        # inputs = [TextEmbeddingInput(data, task)]
        # embeddings = self.vertex_embedding_model.get_embeddings(inputs)

        # if len(embeddings) == 0:
        #     raise ValueError("No embeddings returned")

        # return embeddings[0].values

        return result

    def generate_embedding(self, data: str, **kwargs) -> List[float]:
        return self.generate_storage_embedding(data, **kwargs)

    def get_similar_question_sql(self, question: str, **kwargs) -> list:
        df = self.fetch_similar_training_data(training_data_type="sql", question=question, n_results=self.n_results_sql)

        # Return a list of dictionaries with only question, sql fields. The content field needs to be renamed to sql
        return df.rename(columns={"content": "sql"})[["question", "sql"]].to_dict(orient="records")

    def get_related_ddl(self, question: str, **kwargs) -> list:
        df = self.fetch_similar_training_data(training_data_type="ddl", question=question, n_results=self.n_results_ddl)

        # Return a list of strings of the content
        return df["content"].tolist()

    def get_related_documentation(self, question: str, **kwargs) -> list:
        df = self.fetch_similar_training_data(training_data_type="documentation", question=question, n_results=self.n_results_documentation)

        # Return a list of strings of the content
        return df["content"].tolist()

    def add_question_sql(self, question: str, sql: str, **kwargs) -> str:
        doc = {
            "question": question,
            "sql": sql
        }

        embedding = self.generate_embedding(str(doc))

        return self.store_training_data(training_data_type="sql", question=question, content=sql, embedding=embedding)

    def add_ddl(self, ddl: str, **kwargs) -> str:
        embedding = self.generate_embedding(ddl)

        return self.store_training_data(training_data_type="ddl", question="", content=ddl, embedding=embedding)

    def add_documentation(self, documentation: str, **kwargs) -> str:
        embedding = self.generate_embedding(documentation)

        return self.store_training_data(training_data_type="documentation", question="", content=documentation, embedding=embedding)

    def get_training_data(self, **kwargs) -> pd.DataFrame:
        query = f"SELECT id, training_data_type, question, content FROM `{self.table_id}`"

        return self.conn.query(query).result().to_dataframe()

    def remove_training_data(self, id: str, **kwargs) -> bool:
        query = f"DELETE FROM `{self.table_id}` WHERE id = '{id}'"

        try:
            self.conn.query(query).result()
            return True

        except Exception as e:
            print(f"Failed to remove training data: {e}")
            return False
