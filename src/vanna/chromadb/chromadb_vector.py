import json
import uuid
from abc import abstractmethod

import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
import pandas as pd

from ..base import VannaBase

default_ef = embedding_functions.DefaultEmbeddingFunction()


class ChromaDB_VectorStore(VannaBase):
    def __init__(self, config=None):
        VannaBase.__init__(self, config=config)

        if config is not None and "path" in config:
            path = config["path"]
        else:
            path = "."

        self.chroma_client = chromadb.PersistentClient(
            path=path, settings=Settings(anonymized_telemetry=False)
        )
        self.documentation_collection = self.chroma_client.get_or_create_collection(
            name="documentation", embedding_function=default_ef
        )
        self.ddl_collection = self.chroma_client.get_or_create_collection(
            name="ddl", embedding_function=default_ef
        )
        self.sql_collection = self.chroma_client.get_or_create_collection(
            name="sql", embedding_function=default_ef
        )

    def generate_embedding(self, data: str, **kwargs) -> list[float]:
        embedding = default_ef([data])
        if len(embedding) == 1:
            return embedding[0]
        return embedding

    def add_question_sql(self, question: str, sql: str, **kwargs) -> str:
        question_sql_json = json.dumps(
            {
                "question": question,
                "sql": sql,
            }
        )
        id = str(uuid.uuid4())+"-sql"
        self.sql_collection.add(
            documents=question_sql_json,
            embeddings=self.generate_embedding(question_sql_json),
            ids=id,
        )

        return id

    def add_ddl(self, ddl: str, **kwargs) -> str:
        id = str(uuid.uuid4())+"-ddl"
        self.ddl_collection.add(
            documents=ddl,
            embeddings=self.generate_embedding(ddl),
            ids=id,
        )
        return id

    def add_documentation(self, doc: str, **kwargs) -> str:
        id = str(uuid.uuid4())+"-doc"
        self.documentation_collection.add(
            documents=doc,
            embeddings=self.generate_embedding(doc),
            ids=id,
        )
        return id

    def get_training_data(self, **kwargs) -> pd.DataFrame:
        sql_data = self.sql_collection.get()

        df = pd.DataFrame()

        if sql_data is not None:
            # Extract the documents and ids
            documents = [json.loads(doc) for doc in sql_data['documents']]
            ids = sql_data['ids']

            # Create a DataFrame
            df_sql = pd.DataFrame({
                'id': ids,
                'question': [doc['question'] for doc in documents],
                'content': [doc['sql'] for doc in documents]
            })

            df_sql["training_data_type"] = "sql"

            df = pd.concat([df, df_sql])

        ddl_data = self.ddl_collection.get()

        if ddl_data is not None:
            # Extract the documents and ids
            documents = [doc for doc in ddl_data['documents']]
            ids = ddl_data['ids']

            # Create a DataFrame
            df_ddl = pd.DataFrame({
                'id': ids,
                'question': [None for doc in documents],
                'content': [doc for doc in documents]
            })

            df_ddl["training_data_type"] = "ddl"

            df = pd.concat([df, df_ddl])

        doc_data = self.documentation_collection.get()

        if doc_data is not None:
            # Extract the documents and ids
            documents = [doc for doc in doc_data['documents']]
            ids = doc_data['ids']

            # Create a DataFrame
            df_doc = pd.DataFrame({
                'id': ids,
                'question': [None for doc in documents],
                'content': [doc for doc in documents]
            })

            df_doc["training_data_type"] = "documentation"

            df = pd.concat([df, df_doc])

        return df

    def remove_training_data(self, id: str, **kwargs) -> bool:
        if id.endswith("-sql"):
            self.sql_collection.delete(ids=id)
            return True
        elif id.endswith("-ddl"):
            self.ddl_collection.delete(ids=id)
            return True
        elif id.endswith("-doc"):
            self.documentation_collection.delete(ids=id)
            return True
        else:
            return False

    # Static method to extract the documents from the results of a query
    @staticmethod
    def _extract_documents(query_results) -> list:
        if query_results is None:
            return []

        if "documents" in query_results:
            documents = query_results["documents"]

            if len(documents) == 1 and isinstance(documents[0], list):
                try:
                    documents = [json.loads(doc) for doc in documents[0]]
                except Exception as e:
                    return documents[0]

            return documents

    def get_similar_question_sql(self, question: str, **kwargs) -> list:
        return ChromaDB_VectorStore._extract_documents(
            self.sql_collection.query(
                query_texts=[question],
            )
        )

    def get_related_ddl(self, question: str, **kwargs) -> list:
        return ChromaDB_VectorStore._extract_documents(
            self.ddl_collection.query(
                query_texts=[question],
            )
        )

    def get_related_documentation(self, question: str, **kwargs) -> list:
        return ChromaDB_VectorStore._extract_documents(
            self.documentation_collection.query(
                query_texts=[question],
            )
        )
