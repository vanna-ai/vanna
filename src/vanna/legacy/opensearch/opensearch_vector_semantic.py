import json

import pandas as pd
from langchain_community.vectorstores import OpenSearchVectorSearch

from ..base import VannaBase
from ..utils import deterministic_uuid


class OpenSearch_Semantic_VectorStore(VannaBase):
  def __init__(self, config=None):
    VannaBase.__init__(self, config=config)
    if config is None:
      config = {}

    if "embedding_function" in config:
      self.embedding_function = config.get("embedding_function")
    else:
      from langchain_huggingface import HuggingFaceEmbeddings
      self.embedding_function = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

    self.n_results_sql = config.get("n_results_sql", config.get("n_results", 10))
    self.n_results_documentation = config.get("n_results_documentation", config.get("n_results", 10))
    self.n_results_ddl = config.get("n_results_ddl", config.get("n_results", 10))

    self.document_index = config.get("es_document_index", "vanna_document_index")
    self.ddl_index = config.get("es_ddl_index", "vanna_ddl_index")
    self.question_sql_index = config.get("es_question_sql_index", "vanna_questions_sql_index")

    self.log(f"OpenSearch_Semantic_VectorStore initialized with document_index: {self.document_index}, ddl_index: {self.ddl_index}, question_sql_index: {self.question_sql_index}")

    es_urls = config.get("es_urls", "https://localhost:9200")
    ssl = config.get("es_ssl", True)
    verify_certs = config.get("es_verify_certs", True)

    if "es_user" in config:
      auth = (config["es_user"], config["es_password"])
    else:
      auth = None

    headers = config.get("es_headers", None)
    timeout = config.get("es_timeout", 60)
    max_retries = config.get("es_max_retries", 10)

    common_args = {
        "opensearch_url": es_urls,
        "embedding_function": self.embedding_function,
        "engine": "faiss",
        "http_auth": auth,
        "use_ssl": ssl,
        "verify_certs": verify_certs,
        "timeout": timeout,
        "max_retries": max_retries,
        "retry_on_timeout": True,
        "headers": headers,
    }

    self.documentation_store = OpenSearchVectorSearch(index_name=self.document_index, **common_args)
    self.ddl_store = OpenSearchVectorSearch(index_name=self.ddl_index, **common_args)
    self.sql_store = OpenSearchVectorSearch(index_name=self.question_sql_index, **common_args)

  def add_ddl(self, ddl: str, **kwargs) -> str:
    _id = deterministic_uuid(ddl) + "-ddl"
    self.ddl_store.add_texts(texts=[ddl], ids=[_id], **kwargs)
    return _id

  def add_documentation(self, documentation: str, **kwargs) -> str:
    _id = deterministic_uuid(documentation) + "-doc"
    self.documentation_store.add_texts(texts=[documentation], ids=[_id], **kwargs)
    return _id

  def add_question_sql(self, question: str, sql: str, **kwargs) -> str:
    question_sql_json = json.dumps(
      {
        "question": question,
        "sql": sql,
      },
      ensure_ascii=False,
    )

    _id = deterministic_uuid(question_sql_json) + "-sql"
    self.sql_store.add_texts(texts=[question_sql_json], ids=[_id], **kwargs)
    return _id

  def get_related_ddl(self, question: str, **kwargs) -> list:
    documents = self.ddl_store.similarity_search(query=question, k=self.n_results_ddl)
    return [document.page_content for document in documents]

  def get_related_documentation(self, question: str, **kwargs) -> list:
    documents = self.documentation_store.similarity_search(query=question, k=self.n_results_documentation)
    return [document.page_content for document in documents]

  def get_similar_question_sql(self, question: str, **kwargs) -> list:
    documents = self.sql_store.similarity_search(query=question, k=self.n_results_sql)
    return [json.loads(document.page_content) for document in documents]

  def get_training_data(self, **kwargs) -> pd.DataFrame:
    data = []
    query = {
      "query": {
        "match_all": {}
      }
    }

    indices = [
      {"index": self.document_index, "type": "documentation"},
      {"index": self.question_sql_index, "type": "sql"},
      {"index": self.ddl_index, "type": "ddl"},
    ]

    # Use documentation_store.client consistently for search on all indices
    opensearch_client = self.documentation_store.client

    for index_info in indices:
      index_name = index_info["index"]
      training_data_type = index_info["type"]
      scroll = '1m'  # keep scroll context for 1 minute
      response = opensearch_client.search(
        index=index_name,
        ignore_unavailable=True,
        body=query,
        scroll=scroll,
        size=1000
      )

      scroll_id = response.get('_scroll_id')

      while scroll_id:
        hits = response['hits']['hits']
        if not hits:
          break  # No more hits, exit loop

        for hit in hits:
          source = hit['_source']
          if training_data_type == "sql":
            try:
              doc_dict = json.loads(source['text'])
              content = doc_dict.get("sql")
              question = doc_dict.get("question")
            except json.JSONDecodeError as e:
              self.log(f"Skipping row with custom_id {hit['_id']} due to JSON parsing error: {e}","Error")
              continue
          else:  # documentation or ddl
            content = source['text']
            question = None

          data.append({
            "id": hit["_id"],
            "training_data_type": training_data_type,
            "question": question,
            "content": content,
          })

        # Get next batch of results, using documentation_store.client.scroll
        response = opensearch_client.scroll(scroll_id=scroll_id, scroll=scroll)
        scroll_id = response.get('_scroll_id')

    return pd.DataFrame(data)

  def remove_training_data(self, id: str, **kwargs) -> bool:
    try:
      if id.endswith("-sql"):
        return self.sql_store.delete(ids=[id], **kwargs)
      elif id.endswith("-ddl"):
        return self.ddl_store.delete(ids=[id], **kwargs)
      elif id.endswith("-doc"):
        return self.documentation_store.delete(ids=[id], **kwargs)
      else:
        return False
    except Exception as e:
      self.log(f"Error deleting training dataError deleting training data: {e}", "Error")
      return False

  def generate_embedding(self, data: str, **kwargs) -> list[float]:
    pass
