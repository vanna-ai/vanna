import base64
import uuid
from typing import List

import pandas as pd
from opensearchpy import OpenSearch

from ..base import VannaBase


class OpenSearch_VectorStore(VannaBase):
  def __init__(self, config=None):
    VannaBase.__init__(self, config=config)
    document_index = "vanna_document_index"
    ddl_index = "vanna_ddl_index"
    question_sql_index = "vanna_questions_sql_index"
    if config is not None and "es_document_index" in config:
      document_index = config["es_document_index"]
    if config is not None and "es_ddl_index" in config:
      ddl_index = config["es_ddl_index"]
    if config is not None and "es_question_sql_index" in config:
      question_sql_index = config["es_question_sql_index"]

    self.document_index = document_index
    self.ddl_index = ddl_index
    self.question_sql_index = question_sql_index
    print("OpenSearch_VectorStore initialized with document_index: ",
          document_index, " ddl_index: ", ddl_index, " question_sql_index: ",
          question_sql_index)

    document_index_settings = {
      "settings": {
        "index": {
          "number_of_shards": 6,
          "number_of_replicas": 2
        }
      },
      "mappings": {
        "properties": {
          "question": {
            "type": "text",
          },
          "doc": {
            "type": "text",
          }
        }
      }
    }

    ddl_index_settings = {
      "settings": {
        "index": {
          "number_of_shards": 6,
          "number_of_replicas": 2
        }
      },
      "mappings": {
        "properties": {
          "ddl": {
            "type": "text",
          },
          "doc": {
            "type": "text",
          }
        }
      }
    }

    question_sql_index_settings = {
      "settings": {
        "index": {
          "number_of_shards": 6,
          "number_of_replicas": 2
        }
      },
      "mappings": {
        "properties": {
          "question": {
            "type": "text",
          },
          "sql": {
            "type": "text",
          }
        }
      }
    }

    if config is not None and "es_document_index_settings" in config:
      document_index_settings = config["es_document_index_settings"]
    if config is not None and "es_ddl_index_settings" in config:
      ddl_index_settings = config["es_ddl_index_settings"]
    if config is not None and "es_question_sql_index_settings" in config:
      question_sql_index_settings = config["es_question_sql_index_settings"]

    self.document_index_settings = document_index_settings
    self.ddl_index_settings = ddl_index_settings
    self.question_sql_index_settings = question_sql_index_settings

    es_urls = None
    if config is not None and "es_urls" in config:
      es_urls = config["es_urls"]

    # Host and port
    if config is not None and "es_host" in config:
      host = config["es_host"]
    else:
      host = "localhost"

    if config is not None and "es_port" in config:
      port = config["es_port"]
    else:
      port = 9200

    if config is not None and "es_ssl" in config:
      ssl = config["es_ssl"]
    else:
      ssl = False

    if config is not None and "es_verify_certs" in config:
      verify_certs = config["es_verify_certs"]
    else:
      verify_certs = False

    # Authentication
    if config is not None and "es_user" in config:
      auth = (config["es_user"], config["es_password"])
    else:
      # Default to admin:admin
      auth = None

    headers = None
    # base64 authentication
    if config is not None and "es_encoded_base64" in config and "es_user" in config and "es_password" in config:
      if config["es_encoded_base64"]:
        encoded_credentials = base64.b64encode(
          (config["es_user"] + ":" + config["es_password"]).encode("utf-8")
        ).decode("utf-8")
        headers = {
          'Authorization': 'Basic ' + encoded_credentials
        }
        # remove auth from config
        auth = None

    # custom headers
    if config is not None and "es_headers" in config:
      headers = config["es_headers"]

    if config is not None and "es_timeout" in config:
      timeout = config["es_timeout"]
    else:
      timeout = 60

    if config is not None and "es_max_retries" in config:
      max_retries = config["es_max_retries"]
    else:
      max_retries = 10

    if config is not None and "es_http_compress" in config:
      es_http_compress = config["es_http_compress"]
    else:
      es_http_compress = False

    print("OpenSearch_VectorStore initialized with es_urls: ", es_urls,
          " host: ", host, " port: ", port, " ssl: ", ssl, " verify_certs: ",
          verify_certs, " timeout: ", timeout, " max_retries: ", max_retries)
    if es_urls is not None:
      # Initialize the OpenSearch client by passing a list of URLs
      self.client = OpenSearch(
        hosts=[es_urls],
        http_compress=es_http_compress,
        use_ssl=ssl,
        verify_certs=verify_certs,
        timeout=timeout,
        max_retries=max_retries,
        retry_on_timeout=True,
        http_auth=auth,
        headers=headers
      )
    else:
      # Initialize the OpenSearch client by passing a host and port
      self.client = OpenSearch(
        hosts=[{'host': host, 'port': port}],
        http_compress=es_http_compress,
        use_ssl=ssl,
        verify_certs=verify_certs,
        timeout=timeout,
        max_retries=max_retries,
        retry_on_timeout=True,
        http_auth=auth,
        headers=headers
      )

      print("OpenSearch_VectorStore initialized with client over ")

    # 执行一个简单的查询来检查连接
    try:
      print('Connected to OpenSearch cluster:')
      info = self.client.info()
      print('OpenSearch cluster info:', info)
    except Exception as e:
      print('Error connecting to OpenSearch cluster:', e)

    # Create the indices if they don't exist
    self.create_index_if_not_exists(self.document_index,
                                    self.document_index_settings)
    self.create_index_if_not_exists(self.ddl_index, self.ddl_index_settings)
    self.create_index_if_not_exists(self.question_sql_index,
                                    self.question_sql_index_settings)

  def create_index(self):
    for index in [self.document_index, self.ddl_index,
                  self.question_sql_index]:
      try:
        self.client.indices.create(index)
      except Exception as e:
        print("Error creating index: ", e)
        print(f"opensearch index {index} already exists")
        pass

  def create_index_if_not_exists(self, index_name: str,
                                 index_settings: dict) -> bool:
    try:
      if not self.client.indices.exists(index_name):
        print(f"Index {index_name} does not exist. Creating...")
        self.client.indices.create(index=index_name, body=index_settings)
        return True
      else:
        print(f"Index {index_name} already exists.")
        return False
    except Exception as e:
      print(f"Error creating index: {index_name} ", e)
      return False

  def add_ddl(self, ddl: str, **kwargs) -> str:
    # Assuming that you have a DDL index in your OpenSearch
    id = str(uuid.uuid4()) + "-ddl"
    ddl_dict = {
      "ddl": ddl
    }
    response = self.client.index(index=self.ddl_index, body=ddl_dict, id=id,
                                 **kwargs)
    return response['_id']

  def add_documentation(self, doc: str, **kwargs) -> str:
    # Assuming you have a documentation index in your OpenSearch
    id = str(uuid.uuid4()) + "-doc"
    doc_dict = {
      "doc": doc
    }
    response = self.client.index(index=self.document_index, id=id,
                                 body=doc_dict, **kwargs)
    return response['_id']

  def add_question_sql(self, question: str, sql: str, **kwargs) -> str:
    # Assuming you have a Questions and SQL index in your OpenSearch
    id = str(uuid.uuid4()) + "-sql"
    question_sql_dict = {
      "question": question,
      "sql": sql
    }
    response = self.client.index(index=self.question_sql_index,
                                 body=question_sql_dict, id=id,
                                 **kwargs)
    return response['_id']

  def get_related_ddl(self, question: str, **kwargs) -> List[str]:
    # Assume you have some vector search mechanism associated with your data
    query = {
      "query": {
        "match": {
          "ddl": question
        }
      }
    }
    print(query)
    response = self.client.search(index=self.ddl_index, body=query,
                                  **kwargs)
    return [hit['_source']['ddl'] for hit in response['hits']['hits']]

  def get_related_documentation(self, question: str, **kwargs) -> List[str]:
    query = {
      "query": {
        "match": {
          "doc": question
        }
      }
    }
    print(query)
    response = self.client.search(index=self.document_index,
                                  body=query,
                                  **kwargs)
    return [hit['_source']['doc'] for hit in response['hits']['hits']]

  def get_similar_question_sql(self, question: str, **kwargs) -> List[str]:
    query = {
      "query": {
        "match": {
          "question": question
        }
      }
    }
    print(query)
    response = self.client.search(index=self.question_sql_index,
                                  body=query,
                                  **kwargs)
    return [(hit['_source']['question'], hit['_source']['sql']) for hit in
            response['hits']['hits']]

  def get_training_data(self, **kwargs) -> pd.DataFrame:
    # This will be a simple example pulling all data from an index
    # WARNING: Do not use this approach in production for large indices!
    data = []
    response = self.client.search(
      index=self.document_index,
      body={"query": {"match_all": {}}},
      size=1000
    )
    print(query)
    # records = [hit['_source'] for hit in response['hits']['hits']]
    for hit in response['hits']['hits']:
      data.append(
        {
          "id": hit["_id"],
          "training_data_type": "documentation",
          "question": "",
          "content": hit["_source"]['doc'],
        }
      )

    response = self.client.search(
      index=self.question_sql_index,
      body={"query": {"match_all": {}}},
      size=1000
    )
    # records = [hit['_source'] for hit in response['hits']['hits']]
    for hit in response['hits']['hits']:
      data.append(
        {
          "id": hit["_id"],
          "training_data_type": "sql",
          "question": hit.get("_source", {}).get("question", ""),
          "content": hit.get("_source", {}).get("sql", ""),
        }
      )

    response = self.client.search(
      index=self.ddl_index,
      body={"query": {"match_all": {}}},
      size=1000
    )
    # records = [hit['_source'] for hit in response['hits']['hits']]
    for hit in response['hits']['hits']:
      data.append(
        {
          "id": hit["_id"],
          "training_data_type": "ddl",
          "question": "",
          "content": hit["_source"]['ddl'],
        }
      )

    return pd.DataFrame(data)

  def remove_training_data(self, id: str, **kwargs) -> bool:
    try:
      if id.endswith("-sql"):
        self.client.delete(index=self.question_sql_index, id=id)
        return True
      elif id.endswith("-ddl"):
        self.client.delete(index=self.ddl_index, id=id, **kwargs)
        return True
      elif id.endswith("-doc"):
        self.client.delete(index=self.document_index, id=id, **kwargs)
        return True
      else:
        return False
    except Exception as e:
      print("Error deleting training dataError deleting training data: ", e)
      return False

  def generate_embedding(self, data: str, **kwargs) -> list[float]:
    # opensearch doesn't need to generate embeddings
    pass

# OpenSearch_VectorStore.__init__(self, config={'es_urls':
# "https://opensearch-node.test.com:9200", 'es_encoded_base64': True, 'es_user':
# "admin", 'es_password': "admin", 'es_verify_certs': True})


# OpenSearch_VectorStore.__init__(self, config={'es_host':
# "https://opensearch-node.test.com", 'es_port': 9200, 'es_user': "admin",
# 'es_password': "admin", 'es_verify_certs': True})
