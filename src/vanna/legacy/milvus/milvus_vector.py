import uuid
from typing import List

import pandas as pd
from pymilvus import DataType, MilvusClient, model

from ..base import VannaBase

# Setting the URI as a local file, e.g.`./milvus.db`,
# is the most convenient method, as it automatically utilizes Milvus Lite
# to store all data in this file.
#
# If you have large scale of data such as more than a million docs, we
# recommend setting up a more performant Milvus server on docker or kubernetes.
# When using this setup, please use the server URI,
# e.g.`http://localhost:19530`, as your URI.

DEFAULT_MILVUS_URI = "./milvus.db"
# DEFAULT_MILVUS_URI = "http://localhost:19530"

MAX_LIMIT_SIZE = 10_000


class Milvus_VectorStore(VannaBase):
    """
    Vectorstore implementation using Milvus - https://milvus.io/docs/quickstart.md

    Args:
        - config (dict, optional): Dictionary of `Milvus_VectorStore config` options. Defaults to `None`.
            - milvus_client: A `pymilvus.MilvusClient` instance.
            - embedding_function:
                A `milvus_model.base.BaseEmbeddingFunction` instance. Defaults to `DefaultEmbeddingFunction()`.
                For more models, please refer to:
                https://milvus.io/docs/embeddings.md
    """
    def __init__(self, config=None):
        VannaBase.__init__(self, config=config)

        if "milvus_client" in config:
            self.milvus_client = config["milvus_client"]
        else:
            self.milvus_client = MilvusClient(uri=DEFAULT_MILVUS_URI)

        if "embedding_function" in config:
            self.embedding_function = config.get("embedding_function")
        else:
            self.embedding_function = model.DefaultEmbeddingFunction()
        self._embedding_dim = self.embedding_function.encode_documents(["foo"])[0].shape[0]
        self._create_collections()
        self.n_results = config.get("n_results", 10)

    def _create_collections(self):
        self._create_sql_collection("vannasql")
        self._create_ddl_collection("vannaddl")
        self._create_doc_collection("vannadoc")


    def generate_embedding(self, data: str, **kwargs) -> List[float]:
        return self.embedding_function.encode_documents(data).tolist()


    def _create_sql_collection(self, name: str):
        if not self.milvus_client.has_collection(collection_name=name):
            vannasql_schema = MilvusClient.create_schema(
                auto_id=False,
                enable_dynamic_field=False,
            )
            vannasql_schema.add_field(field_name="id", datatype=DataType.VARCHAR, max_length=65535, is_primary=True)
            vannasql_schema.add_field(field_name="text", datatype=DataType.VARCHAR, max_length=65535)
            vannasql_schema.add_field(field_name="sql", datatype=DataType.VARCHAR, max_length=65535)
            vannasql_schema.add_field(field_name="vector", datatype=DataType.FLOAT_VECTOR, dim=self._embedding_dim)

            vannasql_index_params = self.milvus_client.prepare_index_params()
            vannasql_index_params.add_index(
                field_name="vector",
                index_name="vector",
                index_type="AUTOINDEX",
                metric_type="L2",
            )
            self.milvus_client.create_collection(
                collection_name=name,
                schema=vannasql_schema,
                index_params=vannasql_index_params,
                consistency_level="Strong"
            )

    def _create_ddl_collection(self, name: str):
        if not self.milvus_client.has_collection(collection_name=name):
            vannaddl_schema = MilvusClient.create_schema(
                auto_id=False,
                enable_dynamic_field=False,
            )
            vannaddl_schema.add_field(field_name="id", datatype=DataType.VARCHAR, max_length=65535, is_primary=True)
            vannaddl_schema.add_field(field_name="ddl", datatype=DataType.VARCHAR, max_length=65535)
            vannaddl_schema.add_field(field_name="vector", datatype=DataType.FLOAT_VECTOR, dim=self._embedding_dim)

            vannaddl_index_params = self.milvus_client.prepare_index_params()
            vannaddl_index_params.add_index(
                field_name="vector",
                index_name="vector",
                index_type="AUTOINDEX",
                metric_type="L2",
            )
            self.milvus_client.create_collection(
                collection_name=name,
                schema=vannaddl_schema,
                index_params=vannaddl_index_params,
                consistency_level="Strong"
            )

    def _create_doc_collection(self, name: str):
        if not self.milvus_client.has_collection(collection_name=name):
            vannadoc_schema = MilvusClient.create_schema(
                auto_id=False,
                enable_dynamic_field=False,
            )
            vannadoc_schema.add_field(field_name="id", datatype=DataType.VARCHAR, max_length=65535, is_primary=True)
            vannadoc_schema.add_field(field_name="doc", datatype=DataType.VARCHAR, max_length=65535)
            vannadoc_schema.add_field(field_name="vector", datatype=DataType.FLOAT_VECTOR, dim=self._embedding_dim)

            vannadoc_index_params = self.milvus_client.prepare_index_params()
            vannadoc_index_params.add_index(
                field_name="vector",
                index_name="vector",
                index_type="AUTOINDEX",
                metric_type="L2",
            )
            self.milvus_client.create_collection(
                collection_name=name,
                schema=vannadoc_schema,
                index_params=vannadoc_index_params,
                consistency_level="Strong"
            )

    def add_question_sql(self, question: str, sql: str, **kwargs) -> str:
        if len(question) == 0 or len(sql) == 0:
            raise Exception("pair of question and sql can not be null")
        _id = str(uuid.uuid4()) + "-sql"
        embedding = self.embedding_function.encode_documents([question])[0]
        self.milvus_client.insert(
            collection_name="vannasql",
            data={
                "id": _id,
                "text": question,
                "sql": sql,
                "vector": embedding
            }
        )
        return _id

    def add_ddl(self, ddl: str, **kwargs) -> str:
        if len(ddl) == 0:
            raise Exception("ddl can not be null")
        _id = str(uuid.uuid4()) + "-ddl"
        embedding = self.embedding_function.encode_documents([ddl])[0]
        self.milvus_client.insert(
            collection_name="vannaddl",
            data={
                "id": _id,
                "ddl": ddl,
                "vector": embedding
            }
        )
        return _id

    def add_documentation(self, documentation: str, **kwargs) -> str:
        if len(documentation) == 0:
            raise Exception("documentation can not be null")
        _id = str(uuid.uuid4()) + "-doc"
        embedding = self.embedding_function.encode_documents([documentation])[0]
        self.milvus_client.insert(
            collection_name="vannadoc",
            data={
                "id": _id,
                "doc": documentation,
                "vector": embedding
            }
        )
        return _id

    def get_training_data(self, **kwargs) -> pd.DataFrame:
        sql_data = self.milvus_client.query(
            collection_name="vannasql",
            output_fields=["*"],
            limit=MAX_LIMIT_SIZE,
        )
        df = pd.DataFrame()
        df_sql = pd.DataFrame(
            {
                "id": [doc["id"] for doc in sql_data],
                "question": [doc["text"] for doc in sql_data],
                "content": [doc["sql"] for doc in sql_data],
            }
        )
        df = pd.concat([df, df_sql])

        ddl_data = self.milvus_client.query(
            collection_name="vannaddl",
            output_fields=["*"],
            limit=MAX_LIMIT_SIZE,
        )

        df_ddl = pd.DataFrame(
            {
                "id": [doc["id"] for doc in ddl_data],
                "question": [None for doc in ddl_data],
                "content": [doc["ddl"] for doc in ddl_data],
            }
        )
        df = pd.concat([df, df_ddl])

        doc_data = self.milvus_client.query(
            collection_name="vannadoc",
            output_fields=["*"],
            limit=MAX_LIMIT_SIZE,
        )

        df_doc = pd.DataFrame(
            {
                "id": [doc["id"] for doc in doc_data],
                "question": [None for doc in doc_data],
                "content": [doc["doc"] for doc in doc_data],
            }
        )
        df = pd.concat([df, df_doc])
        return df

    def get_similar_question_sql(self, question: str, **kwargs) -> list:
        search_params = {
            "metric_type": "L2",
            "params": {"nprobe": 128},
        }
        embeddings = self.embedding_function.encode_queries([question])
        res = self.milvus_client.search(
            collection_name="vannasql",
            anns_field="vector",
            data=embeddings,
            limit=self.n_results,
            output_fields=["text", "sql"],
            search_params=search_params
        )
        res = res[0]

        list_sql = []
        for doc in res:
            dict = {}
            dict["question"] = doc["entity"]["text"]
            dict["sql"] = doc["entity"]["sql"]
            list_sql.append(dict)
        return list_sql

    def get_related_ddl(self, question: str, **kwargs) -> list:
        search_params = {
            "metric_type": "L2",
            "params": {"nprobe": 128},
        }
        embeddings = self.embedding_function.encode_queries([question])
        res = self.milvus_client.search(
            collection_name="vannaddl",
            anns_field="vector",
            data=embeddings,
            limit=self.n_results,
            output_fields=["ddl"],
            search_params=search_params
        )
        res = res[0]

        list_ddl = []
        for doc in res:
            list_ddl.append(doc["entity"]["ddl"])
        return list_ddl

    def get_related_documentation(self, question: str, **kwargs) -> list:
        search_params = {
            "metric_type": "L2",
            "params": {"nprobe": 128},
        }
        embeddings = self.embedding_function.encode_queries([question])
        res = self.milvus_client.search(
            collection_name="vannadoc",
            anns_field="vector",
            data=embeddings,
            limit=self.n_results,
            output_fields=["doc"],
            search_params=search_params
        )
        res = res[0]

        list_doc = []
        for doc in res:
            list_doc.append(doc["entity"]["doc"])
        return list_doc

    def remove_training_data(self, id: str, **kwargs) -> bool:
        if id.endswith("-sql"):
            self.milvus_client.delete(collection_name="vannasql", ids=[id])
            return True
        elif id.endswith("-ddl"):
            self.milvus_client.delete(collection_name="vannaddl", ids=[id])
            return True
        elif id.endswith("-doc"):
            self.milvus_client.delete(collection_name="vannadoc", ids=[id])
            return True
        else:
            return False
