import json
import os
from typing import List

import duckdb
import numpy as np
import pandas as pd
from fastembed import TextEmbedding

from vanna.base import VannaBase
from vanna.utils import deterministic_uuid


class DuckDB_VectorStore(VannaBase):
    def __init__(self, config=None):
        super().__init__(config=config)
        if config is None:
            config = {}

        path = config.get("path", ".")
        database_name = config.get("database_name", "vanna.duckdb")
        self.database_path = os.path.join(path, database_name)
        self.n_results_sql = config.get("n_results_sql", config.get("n_results", 10))
        self.n_results_documentation = config.get(
            "n_results_documentation", config.get("n_results", 10)
        )
        self.n_results_ddl = config.get("n_results_ddl", config.get("n_results", 10))

        self.model_name = self.config.get("model_name", "BAAI/bge-small-en-v1.5")
        self.embedding_model = TextEmbedding(model_name=self.model_name)

        conn = duckdb.connect(database=self.database_path)
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS embeddings (
                id VARCHAR,
                text VARCHAR,
                model VARCHAR,
                vec FLOAT[384]
            );
        """
        )
        conn.close()

    def generate_embedding(self, data: str) -> List[float]:
        embeddings = list(self.embedding_model.embed([data]))
        return embeddings[0]

    def write_embedding_to_table(self, text, id, embedding):
        con = duckdb.connect(database=self.database_path)
        embedding_array = np.array(embedding, dtype=np.float32).tolist()
        con.execute(
            "INSERT INTO embeddings (id, text, model, vec) VALUES (?, ?, ?, ?)",
            [id, text, self.model_name, embedding_array],
        )
        con.close()

    def add_question_sql(self, question: str, sql: str) -> str:
        question_sql_json = json.dumps(
            {
                "question": question,
                "sql": sql,
            },
            ensure_ascii=False,
        )
        id = deterministic_uuid(question_sql_json) + "-sql"
        self.write_embedding_to_table(
            question_sql_json, id, self.generate_embedding(question_sql_json)
        )
        return id

    def add_ddl(self, ddl: str) -> str:
        id = deterministic_uuid(ddl) + "-ddl"
        self.write_embedding_to_table(ddl, id, self.generate_embedding(ddl))
        return id

    def add_documentation(self, documentation: str) -> str:
        id = deterministic_uuid(documentation) + "-doc"
        self.write_embedding_to_table(
            documentation, id, self.generate_embedding(documentation)
        )
        return id

    def get_training_data(self) -> pd.DataFrame:
        con = duckdb.connect(database=self.database_path)
        sql_data = con.execute("SELECT * FROM embeddings").fetchdf()
        con.close()

        df = pd.DataFrame()

        if not sql_data.empty:
            df_sql = sql_data[sql_data["id"].str.endswith("-sql")]
            df_sql = pd.DataFrame(
                {
                    "id": df_sql["id"],
                    "question": [json.loads(doc)["question"] for doc in df_sql["text"]],
                    "content": [json.loads(doc)["sql"] for doc in df_sql["text"]],
                    "training_data_type": "sql",
                }
            )
            df = pd.concat([df, df_sql])

            df_ddl = sql_data[sql_data["id"].str.endswith("-ddl")]
            df_ddl = pd.DataFrame(
                {
                    "id": df_ddl["id"],
                    "question": None,
                    "content": df_ddl["text"],
                    "training_data_type": "ddl",
                }
            )
            df = pd.concat([df, df_ddl])

            df_doc = sql_data[sql_data["id"].str.endswith("-doc")]
            df_doc = pd.DataFrame(
                {
                    "id": df_doc["id"],
                    "question": None,
                    "content": df_doc["text"],
                    "training_data_type": "documentation",
                }
            )
            df = pd.concat([df, df_doc])

        return df

    def remove_training_data(self, id: str) -> bool:
        con = duckdb.connect(database=self.database_path)
        con.execute("DELETE FROM embeddings WHERE id = ?", [id])
        con.close()
        return True

    def remove_collection(self, collection_name: str) -> bool:
        suffix = {"sql": "-sql", "ddl": "-ddl", "documentation": "-doc"}.get(
            collection_name, None
        )
        if suffix:
            con = duckdb.connect(database=self.database_path)
            con.execute("DELETE FROM embeddings WHERE id LIKE ?", ["%" + suffix])
            con.close()
            return True
        return False

    def query_similar_embeddings(self, query_text: str, top_n: int) -> pd.DataFrame:
        query_embedding = self.generate_embedding(query_text)
        query_embedding_array = np.array(query_embedding, dtype=np.float32).tolist()

        con = duckdb.connect(database=self.database_path)
        results = con.execute(
            """
            SELECT text, array_cosine_similarity(vec, ?::FLOAT[384]) AS similarity_score
            FROM embeddings
            ORDER BY similarity_score DESC
            LIMIT ?;
            """,
            [query_embedding_array, top_n],
        ).fetchdf()
        con.close()
        return results

    def get_similar_question_sql(self, question: str) -> list:
        results = self.query_similar_embeddings(question, self.n_results_sql)
        similar_questions = []
        for doc in results["text"]:
            try:
                parsed_doc = json.loads(doc)
                similar_questions.append(
                    {"question": parsed_doc["question"], "sql": parsed_doc["sql"]}
                )
            except json.JSONDecodeError as e:
                similar_questions.append(doc)
                continue
        return similar_questions

    def get_related_ddl(self, question: str) -> list:
        results = self.query_similar_embeddings(question, self.n_results_ddl)
        related_ddls = []
        for doc in results["text"]:
            try:
                related_ddls.append(json.loads(doc))
            except json.JSONDecodeError as e:
                related_ddls.append(doc)
                continue
        return related_ddls

    def get_related_documentation(self, question: str) -> list:
        results = self.query_similar_embeddings(question, self.n_results_documentation)
        related_docs = []
        for doc in results["text"]:
            try:
                related_docs.append(json.loads(doc))
            except json.JSONDecodeError as e:
                related_docs.append(doc)
                continue
        return related_docs
