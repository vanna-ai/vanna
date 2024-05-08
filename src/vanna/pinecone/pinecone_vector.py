import json
from typing import List

from pinecone import Pinecone, PodSpec, ServerlessSpec
import pandas as pd
from ..base import VannaBase
from ..utils import deterministic_uuid

from fastembed import TextEmbedding


class PineconeDB_VectorStore(VannaBase):
    """
    Vectorstore using PineconeDB

    Args:
        config (dict): Configuration dictionary. Defaults to {}. You must provide either a Pinecone Client or an API key in the config.
            - client (Pinecone, optional): Pinecone client. Defaults to None.
            - api_key (str, optional): Pinecone API key. Defaults to None.
            - n_results (int, optional): Number of results to return. Defaults to 10.
            - dimensions (int, optional): Dimensions of the embeddings. Defaults to 384 which coresponds to the dimensions of BAAI/bge-small-en-v1.5.
            - fastembed_model (str, optional): Fastembed model to use. Defaults to "BAAI/bge-small-en-v1.5".
            - documentation_namespace (str, optional): Namespace for documentation. Defaults to "documentation".
            - distance_metric (str, optional): Distance metric to use. Defaults to "cosine".
            - ddl_namespace (str, optional): Namespace for DDL. Defaults to "ddl".
            - sql_namespace (str, optional): Namespace for SQL. Defaults to "sql".
            - index_name (str, optional): Name of the index. Defaults to "vanna-index".
            - metadata_config (dict, optional): Metadata configuration if using a pinecone pod. Defaults to {}.
            - server_type (str, optional): Type of Pinecone server to use. Defaults to "serverless". Options are "serverless" or "pod".
            - podspec (PodSpec, optional): PodSpec configuration if using a pinecone pod. Defaults to PodSpec(environment="us-west-2", pod_type="p1.x1", metadata_config=self.metadata_config).
            - serverless_spec (ServerlessSpec, optional): ServerlessSpec configuration if using a pinecone serverless index. Defaults to ServerlessSpec(cloud="aws", region="us-west-2").
    Raises:
        ValueError: If config is None, api_key is not provided OR client is not provided, client is not an instance of Pinecone, or server_type is not "serverless" or "pod".
    """

    def __init__(self, config=None):
        VannaBase.__init__(self, config=config)
        if config is None:
            raise ValueError(
                "config is required, pass either a Pinecone client or an API key in the config."
            )
        client = config.get("client")
        api_key = config.get("api_key")
        if not api_key and not client:
            raise ValueError(
                "api_key is required in config or pass a configured client"
            )
        if not client and api_key:
            self._client = Pinecone(api_key=api_key)
        elif not isinstance(client, Pinecone):
            raise ValueError("client must be an instance of Pinecone")
        else:
            self._client = client

        self.n_results = config.get("n_results", 10)
        self.dimensions = config.get("dimensions", 384)
        self.fastembed_model = config.get("fastembed_model", "BAAI/bge-small-en-v1.5")
        self.documentation_namespace = config.get(
            "documentation_namespace", "documentation"
        )
        self.distance_metric = config.get("distance_metric", "cosine")
        self.ddl_namespace = config.get("ddl_namespace", "ddl")
        self.sql_namespace = config.get("sql_namespace", "sql")
        self.index_name = config.get("index_name", "vanna-index")
        self.metadata_config = config.get("metadata_config", {})
        self.server_type = config.get("server_type", "serverless")
        if self.server_type not in ["serverless", "pod"]:
            raise ValueError("server_type must be either 'serverless' or 'pod'")
        self.podspec = config.get(
            "podspec",
            PodSpec(
                environment="us-west-2",
                pod_type="p1.x1",
                metadata_config=self.metadata_config,
            ),
        )
        self.serverless_spec = config.get(
            "serverless_spec", ServerlessSpec(cloud="aws", region="us-west-2")
        )
        self._setup_index()

    def _set_index_host(self, host: str) -> None:
        self.Index = self._client.Index(host=host)

    def _setup_index(self) -> None:
        existing_indexes = self._get_indexes()
        if self.index_name not in existing_indexes and self.server_type == "serverless":
            self._client.create_index(
                name=self.index_name,
                dimension=self.dimensions,
                metric=self.distance_metric,
                spec=self.serverless_spec,
            )
            pinecone_index_host = self._client.describe_index(self.index_name)["host"]
            self._set_index_host(pinecone_index_host)
        elif self.index_name not in existing_indexes and self.server_type == "pod":
            self._client.create_index(
                name=self.index_name,
                dimension=self.dimensions,
                metric=self.distance_metric,
                spec=self.podspec,
            )
            pinecone_index_host = self._client.describe_index(self.index_name)["host"]
            self._set_index_host(pinecone_index_host)
        else:
            pinecone_index_host = self._client.describe_index(self.index_name)["host"]
            self._set_index_host(pinecone_index_host)

    def _get_indexes(self) -> list:
        return [index["name"] for index in self._client.list_indexes()]

    def _check_if_embedding_exists(self, id: str, namespace: str) -> bool:
        fetch_response = self.Index.fetch(ids=[id], namespace=namespace)
        if fetch_response["vectors"] == {}:
            return False
        return True

    def add_ddl(self, ddl: str, **kwargs) -> str:
        id = deterministic_uuid(ddl) + "-ddl"
        if self._check_if_embedding_exists(id=id, namespace=self.ddl_namespace):
            print(f"DDL with id: {id} already exists in the index. Skipping...")
            return id
        self.Index.upsert(
            vectors=[(id, self.generate_embedding(ddl), {"ddl": ddl})],
            namespace=self.ddl_namespace,
        )
        return id

    def add_documentation(self, doc: str, **kwargs) -> str:
        id = deterministic_uuid(doc) + "-doc"

        if self._check_if_embedding_exists(
            id=id, namespace=self.documentation_namespace
        ):
            print(
                f"Documentation with id: {id} already exists in the index. Skipping..."
            )
            return id
        self.Index.upsert(
            vectors=[(id, self.generate_embedding(doc), {"documentation": doc})],
            namespace=self.documentation_namespace,
        )
        return id

    def add_question_sql(self, question: str, sql: str, **kwargs) -> str:
        question_sql_json = json.dumps(
            {
                "question": question,
                "sql": sql,
            },
            ensure_ascii=False,
        )
        id = deterministic_uuid(question_sql_json) + "-sql"
        if self._check_if_embedding_exists(id=id, namespace=self.sql_namespace):
            print(
                f"Question-SQL with id: {id} already exists in the index. Skipping..."
            )
            return id
        self.Index.upsert(
            vectors=[
                (
                    id,
                    self.generate_embedding(question_sql_json),
                    {"sql": question_sql_json},
                )
            ],
            namespace=self.sql_namespace,
        )
        return id

    def get_related_ddl(self, question: str, **kwargs) -> list:
        res = self.Index.query(
            namespace=self.ddl_namespace,
            vector=self.generate_embedding(question),
            top_k=self.n_results,
            include_values=True,
            include_metadata=True,
        )
        return [match["metadata"]["ddl"] for match in res["matches"]] if res else []

    def get_related_documentation(self, question: str, **kwargs) -> list:
        res = self.Index.query(
            namespace=self.documentation_namespace,
            vector=self.generate_embedding(question),
            top_k=self.n_results,
            include_values=True,
            include_metadata=True,
        )
        return (
            [match["metadata"]["documentation"] for match in res["matches"]]
            if res
            else []
        )

    def get_similar_question_sql(self, question: str, **kwargs) -> list:
        res = self.Index.query(
            namespace=self.sql_namespace,
            vector=self.generate_embedding(question),
            top_k=self.n_results,
            include_values=True,
            include_metadata=True,
        )
        return (
            [
                {
                    key: value
                    for key, value in json.loads(match["metadata"]["sql"]).items()
                }
                for match in res["matches"]
            ]
            if res
            else []
        )

    def get_training_data(self, **kwargs) -> pd.DataFrame:
        # Pinecone does not support getting all vectors in a namespace, so we have to query for the top_k vectors with a dummy vector
        df = pd.DataFrame()
        namespaces = {
            "sql": self.sql_namespace,
            "ddl": self.ddl_namespace,
            "documentation": self.documentation_namespace,
        }

        for data_type, namespace in namespaces.items():
            data = self.Index.query(
                top_k=10000,  # max results that pinecone allows
                namespace=namespace,
                include_values=True,
                include_metadata=True,
                vector=[0.0] * self.dimensions,
            )

            if data is not None:
                id_list = [match["id"] for match in data["matches"]]
                content_list = [
                    match["metadata"][data_type] for match in data["matches"]
                ]
                question_list = [
                    (
                        json.loads(match["metadata"][data_type])["question"]
                        if data_type == "sql"
                        else None
                    )
                    for match in data["matches"]
                ]

                df_data = pd.DataFrame(
                    {
                        "id": id_list,
                        "question": question_list,
                        "content": content_list,
                    }
                )
                df_data["training_data_type"] = data_type
                df = pd.concat([df, df_data])

        return df

    def remove_training_data(self, id: str, **kwargs) -> bool:
        if id.endswith("-sql"):
            self.Index.delete(ids=[id], namespace=self.sql_namespace)
            return True
        elif id.endswith("-ddl"):
            self.Index.delete(ids=[id], namespace=self.ddl_namespace)
            return True
        elif id.endswith("-doc"):
            self.Index.delete(ids=[id], namespace=self.documentation_namespace)
            return True
        else:
            return False

    def generate_embedding(self, data: str, **kwargs) -> List[float]:
        embedding_model = TextEmbedding(model_name=self.fastembed_model)
        embedding = next(embedding_model.embed(data))
        return embedding.tolist()
