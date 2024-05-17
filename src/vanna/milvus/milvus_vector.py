import uuid
import random
import json
from abc import ABC
import pandas as pd
from langchain_community.embeddings.xinference import XinferenceEmbeddings
from ..base import VannaBase
from langchain_community.vectorstores.milvus import Milvus
from langchain_core.documents import Document
from pymilvus import MilvusClient, DataType

ip = #Milvus server ip
port = #Milvus server port
client = MilvusClient("http://ip:port")


class Milvus_VectorStore(VannaBase):
    def __init__(self, config=None):
        VannaBase.__init__(self, config=config)

        if config is not None and "url" in config:
            milvus_model_url = config["url"]
        else:
            milvus_model_ip = #Embedding model ip
            milvus_model_port = #Embedding model port
            milvus_model_url = "http://milvus_model_ip:milvus_model_port"

        if config is not None and "milvus_model" in config:
            milvus_model = config["milvus_model"]
        else:
            milvus_model = "bge-large-zh-v1.5-yto"

        self.xinference_embeddings = XinferenceEmbeddings(
            server_url=milvus_model_url,
            model_uid=milvus_model
        )

    def create_sql_collection(self, name: str, **kwargs):
        has = client.has_collection(collection_name=name)
        # print(has)
        if not has:
            vannasql_schema = MilvusClient.create_schema(
                auto_id=True,
                enable_dynamic_field=False,
            )
            vannasql_schema.add_field(field_name="id", datatype=DataType.VARCHAR, max_length=65535)
            vannasql_schema.add_field(field_name="text", datatype=DataType.VARCHAR, max_length=65535)
            vannasql_schema.add_field(field_name="sql", datatype=DataType.VARCHAR, max_length=65535)
            vannasql_schema.add_field(field_name="my_id", datatype=DataType.INT64, is_primary=True)
            vannasql_schema.add_field(field_name="my_vector", datatype=DataType.FLOAT_VECTOR, dim=1024)

            vannasql_index_params = client.prepare_index_params()
            vannasql_index_params.add_index(
                field_name="my_vector",
                index_name="my_vector",
                index_type="IVF_FLAT",
                metric_type="L2",
                params={"nlist": 1024}
            )
            client.create_collection(
                collection_name=name,
                schema=vannasql_schema,
                index_params=vannasql_index_params,
                consistency_level="Strong"
            )
        else:
            pass

    def create_ddl_collection(self, name: str, **kwargs):
        has = client.has_collection(collection_name=name)
        # print(has)
        if not has:
            vannaddl_schema = MilvusClient.create_schema(
                auto_id=True,
                enable_dynamic_field=False,
            )
            vannaddl_schema.add_field(field_name="id", datatype=DataType.VARCHAR, max_length=65535)
            vannaddl_schema.add_field(field_name="ddl", datatype=DataType.VARCHAR, max_length=65535)
            vannaddl_schema.add_field(field_name="my_id", datatype=DataType.INT64, is_primary=True)
            vannaddl_schema.add_field(field_name="my_vector", datatype=DataType.FLOAT_VECTOR, dim=1024)

            vannaddl_index_params = client.prepare_index_params()
            vannaddl_index_params.add_index(
                field_name="my_vector",
                index_name="my_vector",
                index_type="IVF_FLAT",
                metric_type="L2",
                params={"nlist": 1024}
            )
            client.create_collection(
                collection_name=name,
                schema=vannaddl_schema,
                index_params=vannaddl_index_params,
                consistency_level="Strong"
            )
        else:
            pass

    def create_doc_collection(self, name: str, **kwargs):
        has = client.has_collection(collection_name=name)
        # print(has)
        if not has:
            vannadoc_schema = MilvusClient.create_schema(
                auto_id=True,
                enable_dynamic_field=False,
            )
            vannadoc_schema.add_field(field_name="id", datatype=DataType.VARCHAR, max_length=65535)
            vannadoc_schema.add_field(field_name="doc", datatype=DataType.VARCHAR, max_length=65535)
            vannadoc_schema.add_field(field_name="my_id", datatype=DataType.INT64, is_primary=True)
            vannadoc_schema.add_field(field_name="my_vector", datatype=DataType.FLOAT_VECTOR, dim=1024)

            vannadoc_index_params = client.prepare_index_params()
            vannadoc_index_params.add_index(
                field_name="my_vector",
                index_name="my_vector",
                index_type="IVF_FLAT",
                metric_type="L2",
                params={"nlist": 1024}
            )
            client.create_collection(
                collection_name=name,
                schema=vannadoc_schema,
                index_params=vannadoc_index_params,
                consistency_level="Strong"
            )
        else:
            pass

    def add_question_sql(self, question: str, sql: str, **kwargs) -> str:
        if len(question) == 0 or len(sql) == 0:
            raise Exception("pair of question and sql can not be null")
        self.create_sql_collection("vannasql")
        question_sql_json = json.dumps(
            {
                "question": question,
                "sql": sql,
            },
            ensure_ascii=False,
        )
        # a = random.randint(1,2**63-1)
        _id = str(uuid.uuid4()) + "-sql"
        embeddings = self.xinference_embeddings.embed_query(question)
        res = client.insert(
            collection_name="vannasql",
            data={
                'id': _id,
                'text': question,
                'sql': sql,
                # 'my_id':a,
                'my_vector': embeddings
            }
        )
        return _id

    def add_ddl(self, ddl: str, **kwargs) -> str:
        if len(ddl) == 0:
            raise Exception("ddl can not be null")
        self.create_ddl_collection("vannaddl")
        # b = random.randint(1,2**63-1)
        _id = str(uuid.uuid4()) + "-ddl"
        embeddings = self.xinference_embeddings.embed_query(ddl)
        res = client.insert(
            collection_name="vannaddl",
            data={
                'id': _id,
                'ddl': ddl,
                # 'my_id':b,
                'my_vector': embeddings
            }
        )
        return _id

    def add_documentation(self, documentation: str, **kwargs) -> str:
        if len(documentation) == 0:
            raise Exception("documentation can not be null")
        self.create_doc_collection("vannadoc")
        # c = random.randint(1,2**63-1)
        _id = str(uuid.uuid4()) + "-doc"
        embeddings = self.xinference_embeddings.embed_query(documentation)
        res = client.insert(
            collection_name="vannadoc",
            data={
                'id': _id,
                'doc': documentation,
                # 'my_id':c,
                'my_vector': embeddings
            }
        )
        return _id

    def get_training_data(self, **kwargs) -> pd.DataFrame:
        sql_data = client.query(
            collection_name="vannasql",
            filter="my_id > 0",
            output_fields=["*"],
        )
        df = pd.DataFrame()
        if sql_data is not None:
            df_sql = pd.DataFrame(
                {
                    "id": [doc["id"] for doc in sql_data],
                    "question": [doc["text"] for doc in sql_data],
                    "content": [doc["sql"] for doc in sql_data],
                }
            )
        df = pd.concat([df, df_sql])

        ddl_data = client.query(
            collection_name="vannaddl",
            filter="my_id > 0",
            output_fields=["*"],
        )

        if ddl_data is not None:
            df_ddl = pd.DataFrame(
                {
                    "id": [doc["id"] for doc in ddl_data],
                    "question": [None for doc in ddl_data],
                    "content": [doc["ddl"] for doc in ddl_data],
                }
            )
        df = pd.concat([df, df_ddl])

        doc_data = client.query(
            collection_name="vannadoc",
            filter="my_id > 0",
            output_fields=["*"],
        )

        if doc_data is not None:
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
        embeddings = [self.xinference_embeddings.embed_query(question)]
        res = client.search(
            collection_name="vannasql",
            anns_field="my_vector",
            data=embeddings,
            limit=10,
            filter='',
            output_fields=["text", "sql"],
            search_params=search_params
        )
        res = res[0]

        list_sql = []
        for doc in res:
            dict = {}
            dict["question"] = doc["entity"]["text"]
            dict["sql"] = doc["entity"]["sql"]
            #print(dict)
            list_sql.append(dict)
        return list_sql


    def get_related_ddl(self, question: str, **kwargs) -> list:
        search_params = {
            "metric_type": "L2",
            "params": {"nprobe": 128},
        }
        embeddings = [self.xinference_embeddings.embed_query(question)]
        res = client.search(
            collection_name="vannaddl",
            anns_field="my_vector",
            data=embeddings,
            limit=1,
            filter='',
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
        embeddings = [self.xinference_embeddings.embed_query(question)]
        res = client.search(
            collection_name="vannadoc",
            anns_field="my_vector",
            data=embeddings,
            limit=1,
            filter='',
            output_fields=["doc"],
            search_params=search_params
        )
        res = res[0]

        list_doc = []
        for doc in res:
            list_doc.append(doc["entity"]["doc"])
        return list_doc


    def remove_training_data(self, id: str, **kwargs) -> bool:
        pass
        # if id.endswith("-sql"):
        #     self.mq.index("vanna-sql").delete_documents(ids=[id])
        #     return True
        # elif id.endswith("-ddl"):
        #     self.mq.index("vanna-ddl").delete_documents(ids=[id])
        #     return True
        # elif id.endswith("-doc"):
        #     self.mq.index("vanna-doc").delete_documents(ids=[id])
        #     return True
        # else:
        #     return False
