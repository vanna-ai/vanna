import uuid

import marqo
import pandas as pd

from ..base import VannaBase


class Marqo_VectorStore(VannaBase):
    def __init__(self, config=None):
        VannaBase.__init__(self, config=config)

        if config is not None and "marqo_url" in config:
            marqo_url = config["marqo_url"]
        else:
            marqo_url = "http://localhost:8882"

        if config is not None and "marqo_model" in config:
            marqo_model = config["marqo_model"]
        else:
            marqo_model = "hf/all_datasets_v4_MiniLM-L6"

        self.mq = marqo.Client(url=marqo_url)

        for index in ["vanna-sql", "vanna-ddl", "vanna-doc"]:
            try:
                self.mq.create_index(index, model=marqo_model)
            except Exception as e:
                print(e)
                print(f"Marqo index {index} already exists")
                pass

    def generate_embedding(self, data: str, **kwargs) -> list[float]:
        # Marqo doesn't need to generate embeddings
        pass

    def add_question_sql(self, question: str, sql: str, **kwargs) -> str:
        id = str(uuid.uuid4()) + "-sql"
        question_sql_dict = {
            "question": question,
            "sql": sql,
            "_id": id,
        }

        self.mq.index("vanna-sql").add_documents(
            [question_sql_dict],
            tensor_fields=["question", "sql"],
        )

        return id

    def add_ddl(self, ddl: str, **kwargs) -> str:
        id = str(uuid.uuid4()) + "-ddl"
        ddl_dict = {
            "ddl": ddl,
            "_id": id,
        }

        self.mq.index("vanna-ddl").add_documents(
            [ddl_dict],
            tensor_fields=["ddl"],
        )
        return id

    def add_documentation(self, documentation: str, **kwargs) -> str:
        id = str(uuid.uuid4()) + "-doc"
        doc_dict = {
            "doc": documentation,
            "_id": id,
        }

        self.mq.index("vanna-doc").add_documents(
            [doc_dict],
            tensor_fields=["doc"],
        )
        return id

    def get_training_data(self, **kwargs) -> pd.DataFrame:
        data = []

        for hit in self.mq.index("vanna-doc").search("", limit=1000)["hits"]:
            data.append(
                {
                    "id": hit["_id"],
                    "training_data_type": "documentation",
                    "question": "",
                    "content": hit["doc"],
                }
            )

        for hit in self.mq.index("vanna-ddl").search("", limit=1000)["hits"]:
            data.append(
                {
                    "id": hit["_id"],
                    "training_data_type": "ddl",
                    "question": "",
                    "content": hit["ddl"],
                }
            )

        for hit in self.mq.index("vanna-sql").search("", limit=1000)["hits"]:
            data.append(
                {
                    "id": hit["_id"],
                    "training_data_type": "sql",
                    "question": hit["question"],
                    "content": hit["sql"],
                }
            )

        df = pd.DataFrame(data)

        return df

    def remove_training_data(self, id: str, **kwargs) -> bool:
        if id.endswith("-sql"):
            self.mq.index("vanna-sql").delete_documents(ids=[id])
            return True
        elif id.endswith("-ddl"):
            self.mq.index("vanna-ddl").delete_documents(ids=[id])
            return True
        elif id.endswith("-doc"):
            self.mq.index("vanna-doc").delete_documents(ids=[id])
            return True
        else:
            return False

    # Static method to extract the documents from the results of a query
    @staticmethod
    def _extract_documents(data) -> list:
        # Check if 'hits' key is in the dictionary and if it's a list
        if "hits" in data and isinstance(data["hits"], list):
            # Iterate over each item in 'hits'

            if len(data["hits"]) == 0:
                return []

            # If there is a "doc" key, return the value of that key
            if "doc" in data["hits"][0]:
                return [hit["doc"] for hit in data["hits"]]

            # If there is a "ddl" key, return the value of that key
            if "ddl" in data["hits"][0]:
                return [hit["ddl"] for hit in data["hits"]]

            # Otherwise return the entire hit
            return [
                {key: value for key, value in hit.items() if not key.startswith("_")}
                for hit in data["hits"]
            ]
        else:
            # Return an empty list if 'hits' is not found or not a list
            return []

    def get_similar_question_sql(self, question: str, **kwargs) -> list:
        return Marqo_VectorStore._extract_documents(
            self.mq.index("vanna-sql").search(question)
        )

    def get_related_ddl(self, question: str, **kwargs) -> list:
        return Marqo_VectorStore._extract_documents(
            self.mq.index("vanna-ddl").search(question)
        )

    def get_related_documentation(self, question: str, **kwargs) -> list:
        return Marqo_VectorStore._extract_documents(
            self.mq.index("vanna-doc").search(question)
        )
