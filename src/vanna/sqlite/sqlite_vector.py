import json
import os
import sqlite3
from typing import List

import numpy as np
import pandas as pd
from fastembed import TextEmbedding

from ..base import VannaBase
from ..utils import deterministic_uuid


def cosine_similarity(a, b):
    a = np.array(a)
    b = np.array(b)
    dot_product = np.dot(a, b)
    magnitude_a = np.linalg.norm(a)
    magnitude_b = np.linalg.norm(b)
    if magnitude_a == 0 or magnitude_b == 0:
        return 0.0
    return dot_product / (magnitude_a * magnitude_b)


def sqlite_information_schema(database_path):
    conn = sqlite3.connect(database_path)
    tables = pd.read_sql_query(
        "SELECT name FROM sqlite_master WHERE type='table';", conn
    )
    schema_info = []
    for table in tables["name"]:
        table_info = pd.read_sql_query(f"PRAGMA table_info({table});", conn)
        for row in table_info.itertuples():
            schema_info.append(
                {
                    "table_catalog": "main",  # SQLite does not have catalogs, using a placeholder
                    "table_schema": "main",  # SQLite does not have schemas, using a placeholder
                    "table_name": table,
                    "column_name": row.name,
                    "ordinal_position": row.cid + 1,
                    "column_default": row.dflt_value,
                    "is_nullable": not row.notnull,
                    "data_type": row.type,
                    "identity_generation": None,  # Placeholder as SQLite does not have this
                    "identity_start": None,  # Placeholder as SQLite does not have this
                    "identity_increment": None,  # Placeholder as SQLite does not have this
                    "identity_maximum": None,  # Placeholder as SQLite does not have this
                    "identity_minimum": None,  # Placeholder as SQLite does not have this
                    "identity_cycle": None,  # Placeholder as SQLite does not have this
                    "is_generated": None,  # Placeholder as SQLite does not have this
                    "generation_expression": None,  # Placeholder as SQLite does not have this
                    "is_updatable": None,  # Placeholder as SQLite does not have this
                    "COLUMN_COMMENT": None,  # Placeholder for comments
                }
            )
    conn.close()
    return pd.DataFrame(schema_info)


class SQLite_VectorStore(VannaBase):
    def __init__(self, config=None):
        super().__init__(config=config)
        if config is None:
            config = {}

        path = config.get("path", ".")
        database_name = config.get("database_name", "vanna.sqlite")
        self.database_path = os.path.join(path, database_name)
        self.n_results_sql = config.get("n_results_sql", config.get("n_results", 10))
        self.n_results_documentation = config.get(
            "n_results_documentation", config.get("n_results", 10)
        )
        self.n_results_ddl = config.get("n_results_ddl", config.get("n_results", 10))
        self.model_name = self.config.get("model_name", "BAAI/bge-small-en-v1.5")
        self.embedding_model = TextEmbedding(model_name=self.model_name)

        conn = sqlite3.connect(self.database_path)
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS embeddings (
                id TEXT,
                text TEXT,
                model TEXT,
                vec BLOB
            );
        """
        )
        conn.close()

    def generate_embedding(self, data: str) -> List[float]:
        embeddings = list(self.embedding_model.embed([data]))
        return embeddings[0]

    def write_embedding_to_table(self, text, id, embedding):
        con = sqlite3.connect(self.database_path)
        embedding_array = np.array(embedding, dtype=np.float32).tobytes()
        con.execute(
            "INSERT INTO embeddings (id, text, model, vec) VALUES (?, ?, ?, ?)",
            (id, text, self.model_name, embedding_array),
        )
        con.commit()
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
        con = sqlite3.connect(self.database_path)
        sql_data = pd.read_sql_query("SELECT * FROM embeddings", con)
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
        con = sqlite3.connect(self.database_path)
        con.execute("DELETE FROM embeddings WHERE id = ?", (id,))
        con.commit()
        con.close()
        return True

    def remove_collection(self, collection_name: str) -> bool:
        suffix = {"sql": "%-sql", "ddl": "%-ddl", "documentation": "%-doc"}.get(
            collection_name, None
        )
        if suffix:
            con = sqlite3.connect(self.database_path)
            con.execute("DELETE FROM embeddings WHERE id LIKE ?", (suffix,))
            con.commit()
            con.close()
            return True
        return False

    def query_similar_embeddings(self, query_text: str, top_n: int) -> pd.DataFrame:
        query_embedding = self.generate_embedding(query_text)

        con = sqlite3.connect(self.database_path)
        embeddings_data = pd.read_sql_query("SELECT id, text, vec FROM embeddings", con)
        con.close()

        embeddings_data["vec"] = embeddings_data["vec"].apply(
            lambda x: np.frombuffer(x, dtype=np.float32)
        )
        embeddings_data["similarity_score"] = embeddings_data["vec"].apply(
            lambda vec: cosine_similarity(query_embedding, vec)
        )

        sorted_results = embeddings_data.sort_values(
            by="similarity_score", ascending=False
        ).head(top_n)
        return sorted_results[["text", "similarity_score"]]

    def get_similar_question_sql(self, question: str) -> list:
        results = self.query_similar_embeddings(question, self.n_results_sql)
        similar_questions = []
        for doc in results["text"]:
            try:
                if self._is_json(doc):
                    parsed_doc = json.loads(doc)
                    similar_questions.append(
                        {"question": parsed_doc["question"], "sql": parsed_doc["sql"]}
                    )
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON: {e} - Document: {doc}")
                continue
        return similar_questions

    def get_related_ddl(self, question: str) -> list:
        results = self.query_similar_embeddings(question, self.n_results_ddl)
        related_ddls = []
        for doc in results["text"]:
            related_ddls.append(doc)
        return related_ddls

    def get_related_documentation(self, question: str) -> list:
        results = self.query_similar_embeddings(question, self.n_results_documentation)
        related_docs = []
        for doc in results["text"]:
            related_docs.append(doc)
        return related_docs

    def _is_json(self, text: str) -> bool:
        try:
            json.loads(text)
        except ValueError:
            return False
        return True
