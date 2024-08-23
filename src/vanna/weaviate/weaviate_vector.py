import weaviate
import weaviate.classes as wvc
from fastembed import TextEmbedding

from vanna.base import VannaBase


class WeaviateDatabase(VannaBase):

    def __init__(self, config=None):
        """
        Initialize the VannaEnhanced class with the provided configuration.

        :param config: Dictionary containing configuration parameters.

        params:
        weaviate_url (str): Weaviate cluster URL while using weaviate cloud,
        weaviate_api_key (str): Weaviate API key while using weaviate cloud,
        weaviate_port (num): Weaviate port while using local weaviate,
        weaviate_grpc (num): Weaviate gRPC port while using local weaviate,
        fastembed_model (str): Fastembed model name for text embeddings. BAAI/bge-small-en-v1.5 by default.

        """
        super().__init__(config=config)

        if config is None:
            raise ValueError("config is required")

        self.n_results = config.get("n_results", 3)
        self.fastembed_model = config.get("fastembed_model", "BAAI/bge-small-en-v1.5")
        self.weaviate_api_key = config.get("weaviate_api_key")
        self.weaviate_url = config.get("weaviate_url")
        self.weaviate_port = config.get("weaviate_port")
        self.weaviate_grpc_port = config.get("weaviate_grpc", 50051)

        if not self.weaviate_api_key and not self.weaviate_port:
            raise ValueError("Add proper credentials to connect to weaviate")

        self.weaviate_client = self._initialize_weaviate_client()
        self.embeddings = TextEmbedding(model_name=self.fastembed_model)

        self.training_data_cluster = {
            "sql": "SQLTrainingDataEntry",
            "ddl": "DDLEntry",
            "doc": "DocumentationEntry"
        }

        self._create_collections_if_not_exist()

    def _create_collections_if_not_exist(self):
        properties_dict = {
            self.training_data_cluster['ddl']: [
                wvc.config.Property(name="description", data_type=wvc.config.DataType.TEXT),
            ],
            self.training_data_cluster['doc']: [
                wvc.config.Property(name="description", data_type=wvc.config.DataType.TEXT),
            ],
            self.training_data_cluster['sql']: [
                wvc.config.Property(name="sql", data_type=wvc.config.DataType.TEXT),
                wvc.config.Property(name="natural_language_question", data_type=wvc.config.DataType.TEXT),
            ]
        }

        for cluster, properties in properties_dict.items():
            if not self.weaviate_client.collections.exists(cluster):
                self.weaviate_client.collections.create(
                    name=cluster,
                    properties=properties
                )

    def _initialize_weaviate_client(self):
        if self.weaviate_api_key:
            return weaviate.connect_to_wcs(
                cluster_url=self.weaviate_url,
                auth_credentials=weaviate.auth.AuthApiKey(self.weaviate_api_key),
                additional_config=weaviate.config.AdditionalConfig(timeout=(10, 300)),
                skip_init_checks=True
            )
        else:
            return weaviate.connect_to_local(
                port=self.weaviate_port,
                grpc_port=self.weaviate_grpc_port,
                additional_config=weaviate.config.AdditionalConfig(timeout=(10, 300)),
                skip_init_checks=True
            )

    def generate_embedding(self, data: str, **kwargs):
            embedding_model = TextEmbedding(model_name=self.fastembed_model)
            embedding = next(embedding_model.embed(data))
            return embedding.tolist()


    def _insert_data(self, cluster_key: str, data_object: dict, vector: list) -> str:
        self.weaviate_client.connect()
        response = self.weaviate_client.collections.get(self.training_data_cluster[cluster_key]).data.insert(
            properties=data_object,
            vector=vector
        )
        self.weaviate_client.close()
        return response

    def add_ddl(self, ddl: str, **kwargs) -> str:
        data_object = {
            "description": ddl,
        }
        response = self._insert_data('ddl', data_object, self.generate_embedding(ddl))
        return f'{response}-ddl'

    def add_documentation(self, doc: str, **kwargs) -> str:
        data_object = {
            "description": doc,
        }
        response = self._insert_data('doc', data_object, self.generate_embedding(doc))
        return f'{response}-doc'

    def add_question_sql(self, question: str, sql: str, **kwargs) -> str:
        data_object = {
            "sql": sql,
            "natural_language_question": question,
        }
        response = self._insert_data('sql', data_object, self.generate_embedding(question))
        return f'{response}-sql'

    def _query_collection(self, cluster_key: str, vector_input: list, return_properties: list) -> list:
        self.weaviate_client.connect()
        collection = self.weaviate_client.collections.get(self.training_data_cluster[cluster_key])
        response = collection.query.near_vector(
            near_vector=vector_input,
            limit=self.n_results,
            return_properties=return_properties
        )
        response_list = [item.properties for item in response.objects]
        self.weaviate_client.close()
        return response_list

    def get_related_ddl(self, question: str, **kwargs) -> list:
        vector_input = self.generate_embedding(question)
        response_list = self._query_collection('ddl', vector_input, ["description"])
        return [item["description"] for item in response_list]

    def get_related_documentation(self, question: str, **kwargs) -> list:
        vector_input = self.generate_embedding(question)
        response_list = self._query_collection('doc', vector_input, ["description"])
        return [item["description"] for item in response_list]

    def get_similar_question_sql(self, question: str, **kwargs) -> list:
        vector_input = self.generate_embedding(question)
        response_list = self._query_collection('sql', vector_input, ["sql", "natural_language_question"])
        return [{"question": item["natural_language_question"], "sql": item["sql"]} for item in response_list]

    def get_training_data(self, **kwargs) -> list:
        self.weaviate_client.connect()
        combined_response_list = []
        for collection_name in self.training_data_cluster.values():
            if self.weaviate_client.collections.exists(collection_name):
                collection = self.weaviate_client.collections.get(collection_name)
                response_list = [item.properties for item in collection.iterator()]
                combined_response_list.extend(response_list)
        self.weaviate_client.close()
        return combined_response_list

    def remove_training_data(self, id: str, **kwargs) -> bool:
        self.weaviate_client.connect()
        success = False
        if id.endswith("-sql"):
            id = id.replace('-sql', '')
            success = self.weaviate_client.collections.get(self.training_data_cluster['sql']).data.delete_by_id(id)
        elif id.endswith("-ddl"):
            id = id.replace('-ddl', '')
            success = self.weaviate_client.collections.get(self.training_data_cluster['ddl']).data.delete_by_id(id)
        elif id.endswith("-doc"):
            id = id.replace('-doc', '')
            success = self.weaviate_client.collections.get(self.training_data_cluster['doc']).data.delete_by_id(id)
        self.weaviate_client.close()
        return success
