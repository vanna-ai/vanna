import json
import uuid
from typing import List, Optional, Tuple

import oracledb
import pandas as pd
from chromadb.utils import embedding_functions

from ..base import VannaBase

default_ef = embedding_functions.DefaultEmbeddingFunction()


class Oracle_VectorStore(VannaBase):
  def __init__(self, config=None):
    VannaBase.__init__(self, config=config)

    if config is not None:
      self.embedding_function = config.get(
        "embedding_function",
        default_ef
      )
      self.pre_delete_collection = config.get("pre_delete_collection",
                                              False)
      self.cmetadata = config.get("cmetadata", {"created_by": "oracle"})
    else:
      self.embedding_function = default_ef
      self.pre_delete_collection = False
      self.cmetadata = {"created_by": "oracle"}

    self.oracle_conn = oracledb.connect(dsn=config.get("dsn"))
    self.oracle_conn.call_timeout = 30000
    self.documentation_collection = "documentation"
    self.ddl_collection = "ddl"
    self.sql_collection = "sql"
    self.n_results = config.get("n_results", 10)
    self.n_results_ddl = config.get("n_results_ddl", self.n_results)
    self.n_results_sql = config.get("n_results_sql", self.n_results)
    self.n_results_documentation = config.get("n_results_documentation",
                                              self.n_results)
    self.create_tables_if_not_exists()
    self.create_collections_if_not_exists(self.documentation_collection)
    self.create_collections_if_not_exists(self.ddl_collection)
    self.create_collections_if_not_exists(self.sql_collection)

  def generate_embedding(self, data: str, **kwargs) -> List[float]:
    embeddings = self.embedding_function([data])
    if len(embeddings) == 1:
      return list(embeddings[0].astype(float))
    return list(embeddings.astype(float))

  def add_question_sql(self, question: str, sql: str, **kwargs) -> str:
    cmetadata = self.cmetadata.copy()
    collection = self.get_collection(self.sql_collection)
    question_sql_json = json.dumps(
      {
        "question": question,
        "sql": sql,
      },
      ensure_ascii=False,
    )
    id = str(uuid.uuid4())
    embeddings = self.generate_embedding(question)
    custom_id = id + "-sql"

    cursor = self.oracle_conn.cursor()
    cursor.setinputsizes(None, oracledb.DB_TYPE_VECTOR)
    cursor.execute(
      """
          INSERT INTO oracle_embedding (
              collection_id,
              embedding,
              document,
              cmetadata,
              custom_id,
              uuid
          ) VALUES (
              :1,
              TO_VECTOR(:2),
              :3,
              :4,
              :5,
              :6
          )
      """, [
        collection["uuid"],
        embeddings,
        question_sql_json,
        json.dumps(cmetadata),
        custom_id,
        id
      ]
    )

    self.oracle_conn.commit()
    cursor.close()
    return id

  def add_ddl(self, ddl: str, **kwargs) -> str:
    collection = self.get_collection(self.ddl_collection)
    question_ddl_json = json.dumps(
      {
        "question": None,
        "ddl": ddl,
      },
      ensure_ascii=False,
    )
    id = str(uuid.uuid4())
    custom_id = id + "-ddl"
    cursor = self.oracle_conn.cursor()
    cursor.setinputsizes(None, oracledb.DB_TYPE_VECTOR)
    cursor.execute(
      """
      INSERT INTO oracle_embedding (
          collection_id,
          embedding,
          document,
          cmetadata,
          custom_id,
          uuid
      ) VALUES (
          :1,
          TO_VECTOR(:2),
          :3,
          :4,
          :5,
          :6
      )
      """, [
        collection["uuid"],
        self.generate_embedding(ddl),
        question_ddl_json,
        json.dumps(self.cmetadata),
        custom_id,
        id
      ]
    )
    self.oracle_conn.commit()
    cursor.close()
    return id

  def add_documentation(self, documentation: str, **kwargs) -> str:
    collection = self.get_collection(self.documentation_collection)
    question_documentation_json = json.dumps(
      {
        "question": None,
        "documentation": documentation,
      },
      ensure_ascii=False,
    )
    id = str(uuid.uuid4())
    custom_id = id + "-doc"
    cursor = self.oracle_conn.cursor()
    cursor.setinputsizes(None, oracledb.DB_TYPE_VECTOR)
    cursor.execute(
      """
      INSERT INTO oracle_embedding (
          collection_id,
          embedding,
          document,
          cmetadata,
          custom_id,
          uuid
      ) VALUES (
          :1,
          TO_VECTOR(:2),
          :3,
          :4,
          :5,
          :6
      )
      """, [
        collection["uuid"],
        self.generate_embedding(documentation),
        question_documentation_json,
        json.dumps(self.cmetadata),
        custom_id,
        id
      ]
    )
    self.oracle_conn.commit()
    cursor.close()
    return id

  def get_training_data(self, **kwargs) -> pd.DataFrame:
    df = pd.DataFrame()

    cursor = self.oracle_conn.cursor()
    sql_collection = self.get_collection(self.sql_collection)
    cursor.execute(
      """
                    SELECT
                        document,
                        uuid
                    FROM oracle_embedding
                    WHERE
                        collection_id = :1
                  """, [
        sql_collection["uuid"]
      ]
    )
    sql_data = cursor.fetchall()

    if sql_data is not None:
      # Extract the documents and ids
      documents = [row_data[0] for row_data in sql_data]
      ids = [row_data[1] for row_data in sql_data]

      # Create a DataFrame
      df_sql = pd.DataFrame(
        {
          "id": ids,
          "question": [
            json.loads(doc)["question"] if isinstance(doc,
                                                      str) else
            doc[
              "question"] for doc in documents],
          "content": [
            json.loads(doc)["sql"] if isinstance(doc, str) else
            doc["sql"] for
            doc in documents],
        }
      )
      df_sql["training_data_type"] = "sql"
      df = pd.concat([df, df_sql])

    ddl_collection = self.get_collection(self.ddl_collection)
    cursor.execute(
      """
          SELECT
              document,
              uuid
          FROM oracle_embedding
          WHERE
              collection_id = :1
      """, [ddl_collection["uuid"]])
    ddl_data = cursor.fetchall()

    if ddl_data is not None:
      # Extract the documents and ids
      documents = [row_data[0] for row_data in ddl_data]
      ids = [row_data[1] for row_data in ddl_data]

      # Create a DataFrame
      df_ddl = pd.DataFrame(
        {
          "id": ids,
          "question": [None for _ in documents],
          "content": [
            json.loads(doc)["ddl"] if isinstance(doc, str) else
            doc["ddl"] for
            doc in documents],
        }
      )
      df_ddl["training_data_type"] = "ddl"
      df = pd.concat([df, df_ddl])

    doc_collection = self.get_collection(self.documentation_collection)
    cursor.execute(
      """
          SELECT
              document,
              uuid
          FROM oracle_embedding
          WHERE
              collection_id = :1
      """, [doc_collection["uuid"]])
    doc_data = cursor.fetchall()

    if doc_data is not None:
      # Extract the documents and ids
      documents = [row_data[0] for row_data in doc_data]
      ids = [row_data[1] for row_data in doc_data]

      # Create a DataFrame
      df_doc = pd.DataFrame(
        {
          "id": ids,
          "question": [None for _ in documents],
          "content": [
            json.loads(doc)["documentation"] if isinstance(doc,
                                                           str) else
            doc[
              "documentation"] for
            doc in documents],
        }
      )
      df_doc["training_data_type"] = "documentation"
      df = pd.concat([df, df_doc])

    self.oracle_conn.commit()
    cursor.close()
    return df

  def remove_training_data(self, id: str, **kwargs) -> bool:
    cursor = self.oracle_conn.cursor()
    cursor.execute(
      """
          DELETE
          FROM
              oracle_embedding
          WHERE
          uuid  = :1
      """, [id])

    self.oracle_conn.commit()
    cursor.close()
    return True

  def update_training_data(self, id: str, train_type: str, question: str,
                           **kwargs) -> bool:
    print(f"{train_type=}")
    update_content = kwargs["content"]
    if train_type == 'sql':
      update_json = json.dumps(
        {
          "question": question,
          "sql": update_content,
        }
      )
    elif train_type == 'ddl':
      update_json = json.dumps(
        {
          "question": None,
          "ddl": update_content,
        }
      )
    elif train_type == 'documentation':
      update_json = json.dumps(
        {
          "question": None,
          "documentation": update_content,
        }
      )
    else:
      update_json = json.dumps(
        {
          "question": question,
          "sql": update_content,
        }
      )
    cursor = self.oracle_conn.cursor()
    cursor.setinputsizes(oracledb.DB_TYPE_VECTOR, oracledb.DB_TYPE_JSON)
    cursor.execute(
      """
                  UPDATE
                      oracle_embedding
                  SET
                      embedding = TO_VECTOR(:1),
                      document = JSON_MERGEPATCH(document, :2)
                  WHERE
                  uuid  = :3
                  """, [
        self.generate_embedding(update_content),
        update_json,
        id
      ]
    )

    self.oracle_conn.commit()
    cursor.close()
    return True

  @staticmethod
  def _extract_documents(query_results) -> list:
    """
    Static method to extract the documents from the results of a query.

    Args:
        query_results (pd.DataFrame): The dataframe to use.

    Returns:
        List[str] or None: The extracted documents, or an empty list or single document if an error occurred.
    """
    if query_results is None or len(query_results) == 0:
      return []

    documents = [
      json.loads(row_data[0]) if isinstance(row_data[0], str) else
      row_data[0]
      for row_data in query_results]

    return documents

  def get_similar_question_sql(self, question: str, **kwargs) -> list:
    embeddings = self.generate_embedding(question)
    collection = self.get_collection(self.sql_collection)
    cursor = self.oracle_conn.cursor()
    cursor.setinputsizes(None, oracledb.DB_TYPE_VECTOR,
                         oracledb.DB_TYPE_VECTOR)
    cursor.execute(
      """
      SELECT document
      FROM oracle_embedding
      WHERE collection_id = :1
      ORDER BY VECTOR_DISTANCE(embedding, TO_VECTOR(:2), COSINE)
      FETCH FIRST :3 ROWS ONLY
      """, [
        collection["uuid"],
        embeddings,
        self.n_results_sql
      ]
    )
    results = cursor.fetchall()
    cursor.close()
    return self._extract_documents(results)

  def get_related_ddl(self, question: str, **kwargs) -> list:
    collection = self.get_collection(self.ddl_collection)
    cursor = self.oracle_conn.cursor()
    cursor.setinputsizes(None, oracledb.DB_TYPE_VECTOR)
    cursor.execute(
      """
          SELECT
              document
          FROM oracle_embedding
          WHERE
              collection_id = :1
          ORDER BY VECTOR_DISTANCE(embedding, TO_VECTOR(:2), COSINE)
          FETCH FIRST :top_k ROWS ONLY
      """, [
        collection["uuid"],
        self.generate_embedding(question),
        100
      ]
    )
    results = cursor.fetchall()

    self.oracle_conn.commit()
    cursor.close()
    return Oracle_VectorStore._extract_documents(results)

  def search_tables_metadata(self,
                             engine: str = None,
                             catalog: str = None,
                             schema: str = None,
                             table_name: str = None,
                             ddl: str = None,
                             size: int = 10,
                             **kwargs) -> list:
    pass

  def get_related_documentation(self, question: str, **kwargs) -> list:
    collection = self.get_collection(self.documentation_collection)
    cursor = self.oracle_conn.cursor()
    cursor.setinputsizes(None, oracledb.DB_TYPE_VECTOR)
    cursor.execute(
      """
          SELECT
              document
          FROM oracle_embedding
          WHERE
              collection_id = :1
          ORDER BY VECTOR_DISTANCE(embedding, TO_VECTOR(:2), DOT)
          FETCH FIRST :top_k ROWS ONLY
      """, [
        collection["uuid"],
        self.generate_embedding(question),
        100
      ]
    )
    results = cursor.fetchall()

    self.oracle_conn.commit()
    cursor.close()

    return Oracle_VectorStore._extract_documents(results)

  def create_tables_if_not_exists(self) -> None:
    cursor = self.oracle_conn.cursor()
    cursor.execute(
      """
          CREATE TABLE IF NOT EXISTS oracle_collection (
              name      VARCHAR2(200) NOT NULL,
              cmetadata json NOT NULL,
              uuid      VARCHAR2(200) NOT NULL,
              CONSTRAINT oc_key_uuid PRIMARY KEY ( uuid )
          )
      """
    )

    cursor.execute(
      """
          CREATE TABLE IF NOT EXISTS oracle_embedding (
              collection_id VARCHAR2(200) NOT NULL,
              embedding     vector NOT NULL,
              document      json NOT NULL,
              cmetadata     json NOT NULL,
              custom_id     VARCHAR2(200) NOT NULL,
              uuid          VARCHAR2(200) NOT NULL,
              CONSTRAINT oe_key_uuid PRIMARY KEY ( uuid )
          )
      """
    )

    self.oracle_conn.commit()
    cursor.close()

  def create_collections_if_not_exists(
    self,
    name: str,
    cmetadata: Optional[dict] = None,
  ) -> Tuple[dict, bool]:
    """
    Get or create a collection.
    Returns [Collection, bool] where the bool is True if the collection was created.
    """
    if self.pre_delete_collection:
      self.delete_collection(name)
    created = False
    collection = self.get_collection(name)
    if collection:
      return collection, created

    cmetadata = json.dumps(
      self.cmetadata) if cmetadata is None else json.dumps(cmetadata)
    collection_id = str(uuid.uuid4())
    cursor = self.oracle_conn.cursor()
    cursor.execute(
      """
          INSERT INTO oracle_collection(name, cmetadata, uuid)
          VALUES (:1, :2, :3)
      """, [
        name,
        cmetadata,
        str(collection_id)
      ]
    )

    self.oracle_conn.commit()
    cursor.close()

    collection = {"name": name, "cmetadata": cmetadata,
                  "uuid": collection_id}
    created = True
    return collection, created

  def get_collection(self, name) -> Optional[dict]:
    return self.get_by_name(name)

  def get_by_name(self, name: str) -> Optional[dict]:
    cursor = self.oracle_conn.cursor()
    cursor.execute(
      """
          SELECT
              name,
              cmetadata,
              uuid
          FROM
              oracle_collection
          WHERE
              name = :1
          FETCH FIRST 1 ROWS ONLY
      """, [name])

    for row in cursor:
      return {"name": row[0], "cmetadata": row[1], "uuid": row[2]}

    return  # type: ignore

  def delete_collection(self, name) -> None:
    collection = self.get_collection(name)
    if not collection:
      return

    cursor = self.oracle_conn.cursor()
    cursor.execute(
      """
          DELETE
          FROM
              oracle_embedding
          WHERE
          collection_id = ( SELECT uuid FROM oracle_collection WHERE name = :1 )
      """, [name])
    cursor.execute(
      """
          DELETE
          FROM
              oracle_collection
          WHERE
              name = :1
      """, [name])

    self.oracle_conn.commit()
    cursor.close()
