import json

import pandas as pd
from fastembed import TextEmbedding
from hdbcli import dbapi

from vanna import TrainingPlan, TrainingPlanItem
from vanna.base import VannaBase
from vanna.utils import deterministic_uuid


class HANA_VectorStore(VannaBase):
    """
    Vectorstore implementation using SAP HANA - https://www.sap.com/products/hana.html

    Args:
        - config (dict, optional): Dictionary of `HANA_VectorStore config` options.
            - connection: A `hdbcli.dbapi.Connection` instance. Overrides other config options.
            - address: Database host address. Example: `"localhost"`.
            - port: Database port number. Example: `30015`.
            - user: Database username for authentication.
            - password: Database password for authentication.
            - encrypt: If `True` - use encrypted connection. Default: `True`.
            - sslValidateCertificate: If `True` - validate SSL certificates. Default: `False`.
            - connect_args: Additional connection arguments to pass to `hdbcli.dbapi.connect()`.
            - n_results: Number of results to return from similarity search. Defaults to 10.
            - fastembed_model: [Model](https://qdrant.github.io/fastembed/examples/Supported_Models/#supported-text-embedding-models) to use for `fastembed.TextEmbedding`.
                Defaults to `"BAAI/bge-small-en-v1.5"`.
            - ddl_table_name: Name of the table to store DDL. Defaults to `"ddl"`.
            - sql_table_name: Name of the table to store SQL. Defaults to `"sql"`.
            - documentation_table_name: Name of the table to store documentation. Defaults to `"documentation"`.

    Raises:
        TypeError: If config["connection"] is not a `hdbcli.dbapi.Connection` instance
    """

    def __init__(self, config=None):
        VannaBase.__init__(self, config=config)

        if config is None:
            raise ValueError("For HANA_VectorStore, config must be provided. ")

        connection = config.get("connection")
        if connection is None:
            self._connection = dbapi.connect(
                address=config.get("address"),
                port=config.get("port"),
                user=config.get("user"),
                password=config.get("password"),
                encrypt=True,
                sslValidateCertificate=False,
                **config.get("connect_args", {}),
            )
        elif not isinstance(connection, dbapi.Connection):
            raise TypeError(
                f"Expected connection to be of type {dbapi.Connection}, got {type(connection)}"
            )
        else:
            self._connection = connection

        self.n_results = config.get("n_results", 10)
        self.fastembed_model = config.get("fastembed_model", "BAAI/bge-small-en-v1.5")

        self._ddl_table_name = config.get("ddl_table_name", "ddl")
        self._sql_table_name = config.get("sql_table_name", "sql")
        self._documentation_table_name = config.get(
            "documentation_table_name", "documentation"
        )

        self._id_suffixes = {
            self._ddl_table_name: "ddl",
            self._documentation_table_name: "doc",
            self._sql_table_name: "sql",
        }

        for table_name in [
            self._ddl_table_name,
            self._sql_table_name,
            self._documentation_table_name,
        ]:
            if not self._table_exists(table_name):
                self._create_table(table_name)

    def _table_exists(self, table_name) -> bool:
        sql_str = (
            "SELECT COUNT(*) FROM SYS.TABLES WHERE SCHEMA_NAME = CURRENT_SCHEMA"
            " AND TABLE_NAME = ?"
        )
        try:
            cur = self._connection.cursor()
            cur.execute(sql_str, (table_name,))
            if cur.has_result_set():
                rows = cur.fetchall()
                if rows[0][0] == 1:
                    return True
        finally:
            cur.close()
        return False

    def _create_table(self, table_name):
        sql_str = (
            f'CREATE TABLE "{table_name}"('
            '"VEC_ID" VARCHAR(50), '
            '"VEC_TEXT" NCLOB, '
            '"VEC_META" NCLOB, '
            '"VEC_VECTOR" REAL_VECTOR '
            ");"
        )

        try:
            cur = self._connection.cursor()
            cur.execute(sql_str)
        finally:
            cur.close()

    def generate_embedding(self, data: str) -> list[float]:
        embedding_model = TextEmbedding(model_name=self.fastembed_model)
        embedding = next(embedding_model.embed(data))
        return embedding.tolist()

    def similarity_search(
        self, table_name: str, data: str, k: int = 10
    ) -> list[tuple[str, str, dict, float]]:
        result = []
        embedding = self.generate_embedding(data)
        embedding_as_str = "[" + ",".join(map(str, embedding)) + "]"

        sql_str = (
            f"SELECT TOP {k}"
            '  "VEC_ID", '
            '  "VEC_TEXT", '
            '  "VEC_META", '
            '  COSINE_SIMILARITY("VEC_VECTOR", TO_REAL_VECTOR (?)) AS CS '
            f'FROM "{table_name}"'
            "ORDER BY CS DESC;"
        )
        try:
            cur = self._connection.cursor()
            cur.execute(sql_str, (embedding_as_str,))
            if cur.has_result_set():
                if self.n_results is not None:
                    rows = cur.fetchmany(self.n_results)
                else:
                    rows = cur.fetchall()

                for row in rows:
                    row_id = row[0]
                    doc = row[1]
                    js = json.loads(row[2])
                    result.append((row_id, doc, js, row[3]))
        finally:
            cur.close()
        return result

    def _insert(self, table_name: str, sql_params: tuple):
        id = sql_params[0]
        sql_str = (
            f'UPSERT "{table_name}" '
            "VALUES (?, ?, ?, TO_REAL_VECTOR (?))"
            'WHERE VEC_ID = ?;'
        )
        try:
            cur = self._connection.cursor()
            cur.execute(sql_str, sql_params + (id,))
        finally:
            cur.close()

    def add_ddl(self, ddl: str, **kwargs) -> str:
        id = deterministic_uuid(ddl)
        embedding = self.generate_embedding(ddl)
        embedding_as_str = "[" + ",".join(map(str, embedding)) + "]"
        self._insert(self._ddl_table_name, (id, ddl, json.dumps({}), embedding_as_str))

    def add_documentation(self, doc: str, **kwargs) -> str:
        id = deterministic_uuid(doc)
        embedding = self.generate_embedding(doc)
        embedding_as_str = "[" + ",".join(map(str, embedding)) + "]"
        self._insert(
            self._documentation_table_name, (id, doc, json.dumps({}), embedding_as_str)
        )

    def add_question_sql(self, question: str, sql: str, **kwargs) -> str:
        question_answer = "Question: {0}\n\nSQL: {1}".format(question, sql)
        id = deterministic_uuid(question_answer)
        embedding = self.generate_embedding(question_answer)
        embedding_as_str = "[" + ",".join(map(str, embedding)) + "]"
        self._insert(
            self._sql_table_name,
            (
                id,
                question_answer,
                json.dumps({"question": question, "sql": sql}),
                embedding_as_str,
            ),
        )

    def get_related_ddl(self, question: str, **kwargs) -> list[str]:
        results = self.similarity_search(self._ddl_table_name, question)
        return [result[1] for result in results]

    def get_related_documentation(self, question: str, **kwargs) -> list[str]:
        results = self.similarity_search(self._documentation_table_name, question)
        return [result[1] for result in results]

    def get_similar_question_sql(self, question: str, **kwargs) -> list:
        results = self.similarity_search(self._sql_table_name, question)
        return [result[2] for result in results]

    def get_training_data(self, **kwargs) -> pd.DataFrame:
        df = pd.DataFrame()

        if sql_data := self._get_all_points(self._sql_table_name):
            question_list = [data[2]["question"] for data in sql_data]
            sql_list = [data[2]["sql"] for data in sql_data]
            id_list = [
                self._format_point_id(data[0], self._sql_table_name)
                for data in sql_data
            ]

            df_sql = pd.DataFrame(
                {
                    "id": id_list,
                    "question": question_list,
                    "content": sql_list,
                }
            )

            df_sql["training_data_type"] = "sql"

            df = pd.concat([df, df_sql])

        if ddl_data := self._get_all_points(self._ddl_table_name):
            ddl_list = [data[1] for data in ddl_data]
            id_list = [
                self._format_point_id(data[0], self._ddl_table_name)
                for data in ddl_data
            ]

            df_ddl = pd.DataFrame(
                {
                    "id": id_list,
                    "question": [None for _ in ddl_list],
                    "content": ddl_list,
                }
            )

            df_ddl["training_data_type"] = "ddl"

            df = pd.concat([df, df_ddl])

        if doc_data := self._get_all_points(self._documentation_table_name):
            document_list = [data[1] for data in doc_data]
            id_list = [
                self._format_point_id(data[0], self._documentation_table_name)
                for data in doc_data
            ]

            df_doc = pd.DataFrame(
                {
                    "id": id_list,
                    "question": [None for _ in document_list],
                    "content": document_list,
                }
            )

            df_doc["training_data_type"] = "documentation"

            df = pd.concat([df, df_doc])

        return df

    def _get_all_points(self, table_name: str) -> list[tuple[str, str, dict]]:
        result = []

        sql_str = f'SELECT "VEC_ID", "VEC_TEXT", "VEC_META" FROM "{table_name}"'
        try:
            cur = self._connection.cursor()
            cur.execute(sql_str)
            if cur.has_result_set():
                rows = cur.fetchall()
                for row in rows:
                    id = row[0]
                    doc = row[1]
                    js = json.loads(row[2])
                    result.append((id, doc, js))
        finally:
            cur.close()
        return result

    def remove_training_data(self, id: str, **kwargs) -> bool:
        try:
            id, collection_name = self._parse_point_id(id)
            sql_str = f'DELETE FROM "{collection_name}" WHERE "VEC_ID" = ?'

            cur = self._connection.cursor()
            cur.execute(sql_str, (id,))
            return True
        except ValueError:
            return False
        finally:
            cur.close()

    def _format_point_id(self, id: str, collection_name: str) -> str:
        return "{0}-{1}".format(id, self._id_suffixes[collection_name])

    def _parse_point_id(self, id: str) -> tuple[str, str]:
        id, curr_suffix = id.rsplit("-", 1)
        for collection_name, suffix in self._id_suffixes.items():
            if curr_suffix == suffix:
                return id, collection_name
        raise ValueError(f"Invalid id {id}")

    def get_training_plan_hana(self, df) -> TrainingPlan:
        columns = [
            "schema_name",
            "table_name",
            "column_name",
            "data_type_name",
            "comments",
        ]

        plan = TrainingPlan([])

        for schema in df["schema_name"].unique().tolist():
            for table in df["table_name"].unique().tolist():
                df_columns_filtered_to_table = df.query(
                    f"schema_name == '{schema}' and table_name == '{table}'"
                )
                doc = f"The following columns are in the {table} table in the {schema} schema:\n\n"
                doc += df_columns_filtered_to_table[columns].to_markdown()

                plan._plan.append(
                    TrainingPlanItem(
                        item_type=TrainingPlanItem.ITEM_TYPE_IS,
                        item_group=f"{schema}.{table}",
                        item_name=table,
                        item_value=doc,
                    )
                )

        return plan
