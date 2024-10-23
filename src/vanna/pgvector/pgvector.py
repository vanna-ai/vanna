import ast
import json
import logging
import uuid

import pandas as pd
from langchain_core.documents import Document
from langchain_postgres.vectorstores import PGVector
from sqlalchemy import create_engine, text

from .. import ValidationError
from ..base import VannaBase
from ..types import TrainingPlan, TrainingPlanItem


class PG_VectorStore(VannaBase):
    def __init__(self, config=None):
        if not config or "connection_string" not in config:
            raise ValueError(
                "A valid 'config' dictionary with a 'connection_string' is required.")

        VannaBase.__init__(self, config=config)

        if config and "connection_string" in config:
            self.connection_string = config.get("connection_string")
            self.n_results = config.get("n_results", 10)

        if config and "embedding_function" in config:
            self.embedding_function = config.get("embedding_function")
        else:
            from langchain_huggingface import HuggingFaceEmbeddings
            self.embedding_function = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

        self.sql_collection = PGVector(
            embeddings=self.embedding_function,
            collection_name="sql",
            connection=self.connection_string,
        )
        self.ddl_collection = PGVector(
            embeddings=self.embedding_function,
            collection_name="ddl",
            connection=self.connection_string,
        )
        self.documentation_collection = PGVector(
            embeddings=self.embedding_function,
            collection_name="documentation",
            connection=self.connection_string,
        )

    def add_question_sql(self, question: str, sql: str, **kwargs) -> str:
        question_sql_json = json.dumps(
            {
                "question": question,
                "sql": sql,
            },
            ensure_ascii=False,
        )
        id = str(uuid.uuid4()) + "-sql"
        createdat = kwargs.get("createdat")
        doc = Document(
            page_content=question_sql_json,
            metadata={"id": id, "createdat": createdat},
        )
        self.sql_collection.add_documents([doc], ids=[doc.metadata["id"]])

        return id

    def add_ddl(self, ddl: str, **kwargs) -> str:
        _id = str(uuid.uuid4()) + "-ddl"
        doc = Document(
            page_content=ddl,
            metadata={"id": _id},
        )
        self.ddl_collection.add_documents([doc], ids=[doc.metadata["id"]])
        return _id

    def add_documentation(self, documentation: str, **kwargs) -> str:
        _id = str(uuid.uuid4()) + "-doc"
        doc = Document(
            page_content=documentation,
            metadata={"id": _id},
        )
        self.documentation_collection.add_documents([doc], ids=[doc.metadata["id"]])
        return _id

    def get_collection(self, collection_name):
        match collection_name:
            case "sql":
                return self.sql_collection
            case "ddl":
                return self.ddl_collection
            case "documentation":
                return self.documentation_collection
            case _:
                raise ValueError("Specified collection does not exist.")

    def get_similar_question_sql(self, question: str) -> list:
        documents = self.sql_collection.similarity_search(query=question, k=self.n_results)
        return [ast.literal_eval(document.page_content) for document in documents]

    def get_related_ddl(self, question: str, **kwargs) -> list:
        documents = self.ddl_collection.similarity_search(query=question, k=self.n_results)
        return [document.page_content for document in documents]

    def get_related_documentation(self, question: str, **kwargs) -> list:
        documents = self.documentation_collection.similarity_search(query=question, k=self.n_results)
        return [document.page_content for document in documents]

    def train(
        self,
        question: str | None = None,
        sql: str | None = None,
        ddl: str | None = None,
        documentation: str | None = None,
        plan: TrainingPlan | None = None,
        createdat: str | None = None,
    ):
        if question and not sql:
            raise ValidationError("Please provide a SQL query.")

        if documentation:
            logging.info(f"Adding documentation: {documentation}")
            return self.add_documentation(documentation)

        if sql and question:
            return self.add_question_sql(question=question, sql=sql, createdat=createdat)

        if ddl:
            logging.info(f"Adding ddl: {ddl}")
            return self.add_ddl(ddl)

        if plan:
            for item in plan._plan:
                if item.item_type == TrainingPlanItem.ITEM_TYPE_DDL:
                    self.add_ddl(item.item_value)
                elif item.item_type == TrainingPlanItem.ITEM_TYPE_IS:
                    self.add_documentation(item.item_value)
                elif item.item_type == TrainingPlanItem.ITEM_TYPE_SQL and item.item_name:
                    self.add_question_sql(question=item.item_name, sql=item.item_value)

    def get_training_data(self, **kwargs) -> pd.DataFrame:
        # Establishing the connection
        engine = create_engine(self.connection_string)

        # Querying the 'langchain_pg_embedding' table
        query_embedding = "SELECT cmetadata, document FROM langchain_pg_embedding"
        df_embedding = pd.read_sql(query_embedding, engine)

        # List to accumulate the processed rows
        processed_rows = []

        # Process each row in the DataFrame
        for _, row in df_embedding.iterrows():
            custom_id = row["cmetadata"]["id"]
            document = row["document"]
            training_data_type = "documentation" if custom_id[-3:] == "doc" else custom_id[-3:]

            if training_data_type == "sql":
                # Convert the document string to a dictionary
                try:
                    doc_dict = ast.literal_eval(document)
                    question = doc_dict.get("question")
                    content = doc_dict.get("sql")
                except (ValueError, SyntaxError):
                    logging.info(f"Skipping row with custom_id {custom_id} due to parsing error.")
                    continue
            elif training_data_type in ["documentation", "ddl"]:
                question = None  # Default value for question
                content = document
            else:
                # If the suffix is not recognized, skip this row
                logging.info(f"Skipping row with custom_id {custom_id} due to unrecognized training data type.")
                continue

            # Append the processed data to the list
            processed_rows.append(
                {"id": custom_id, "question": question, "content": content, "training_data_type": training_data_type}
            )

        # Create a DataFrame from the list of processed rows
        df_processed = pd.DataFrame(processed_rows)

        return df_processed

    def remove_training_data(self, id: str, **kwargs) -> bool:
        # Create the database engine
        engine = create_engine(self.connection_string)

        # SQL DELETE statement
        delete_statement = text(
            """
            DELETE FROM langchain_pg_embedding
            WHERE cmetadata ->> 'id' = :id
        """
        )

        # Connect to the database and execute the delete statement
        with engine.connect() as connection:
            # Start a transaction
            with connection.begin() as transaction:
                try:
                    result = connection.execute(delete_statement, {"id": id})
                    # Commit the transaction if the delete was successful
                    transaction.commit()
                    # Check if any row was deleted and return True or False accordingly
                    return result.rowcount > 0
                except Exception as e:
                    # Rollback the transaction in case of error
                    logging.error(f"An error occurred: {e}")
                    transaction.rollback()
                    return False

    def remove_collection(self, collection_name: str) -> bool:
        engine = create_engine(self.connection_string)

        # Determine the suffix to look for based on the collection name
        suffix_map = {"ddl": "ddl", "sql": "sql", "documentation": "doc"}
        suffix = suffix_map.get(collection_name)

        if not suffix:
            logging.info("Invalid collection name. Choose from 'ddl', 'sql', or 'documentation'.")
            return False

        # SQL query to delete rows based on the condition
        query = text(
            f"""
            DELETE FROM langchain_pg_embedding
            WHERE cmetadata->>'id' LIKE '%{suffix}'
        """
        )

        # Execute the deletion within a transaction block
        with engine.connect() as connection:
            with connection.begin() as transaction:
                try:
                    result = connection.execute(query)
                    transaction.commit()  # Explicitly commit the transaction
                    if result.rowcount > 0:
                        logging.info(
                            f"Deleted {result.rowcount} rows from "
                            f"langchain_pg_embedding where collection is {collection_name}."
                        )
                        return True
                    else:
                        logging.info(f"No rows deleted for collection {collection_name}.")
                        return False
                except Exception as e:
                    logging.error(f"An error occurred: {e}")
                    transaction.rollback()  # Rollback in case of error
                    return False

    def generate_embedding(self, *args, **kwargs):
        pass
