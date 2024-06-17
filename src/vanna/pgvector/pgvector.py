import ast
import json
import uuid
from typing import List

import pandas as pd
from langchain.vectorstores.pgvector import PGVector
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.documents import Document
from pandas.core.api import DataFrame as DataFrame
from sqlalchemy import create_engine, text

from vanna.base.base import VannaBase


class PG_VectorStore(VannaBase):
    def __init__(self, config=None):
        if not config or "connection_string" not in config:
            raise ValueError(
                "A valid 'config' dictionary with a 'connection_string' is required.")

        VannaBase.__init__(self, config=config)

        self.connection_string = config["connection_string"]
        self.n_results = config.get("n_results", 10)
        self.embedding_function = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-l6-v2")
        self.ddl_vectorstore = PGVector(
            embedding_function=self.embedding_function,
            collection_name="ddl",
            connection_string=self.connection_string,
        )
        self.documentation_vectorstore = PGVector(
            embedding_function=self.embedding_function,
            collection_name="documentation",
            connection_string=self.connection_string,
        )
        self.sql_vectorstore = PGVector(
            embedding_function=self.embedding_function,
            collection_name="sql",
            connection_string=self.connection_string,
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
        doc = Document(
            page_content=question_sql_json,
            metadata={"id": id},
        )
        self.sql_vectorstore.add_documents([doc], ids=doc.metadata["id"])

        return id

    def add_ddl(self, ddl: str, **kwargs) -> str:
        id = str(uuid.uuid4()) + "-ddl"
        doc = Document(
            page_content=ddl,
            metadata={"id": id},
        )
        self.ddl_vectorstore.add_documents([doc], ids=doc.metadata["id"])
        return id

    def add_documentation(self, documentation: str, **kwargs) -> str:
        id = str(uuid.uuid4()) + "-doc"
        doc = Document(
            page_content=documentation,
            metadata={"id": id},
        )
        self.documentation_vectorstore.add_documents(
            [doc], ids=doc.metadata["id"])
        return id

    def get_similar_question_sql(self, question: str, **kwargs) -> list:
        result_list = []
        for document in self.sql_vectorstore.similarity_search(question, k=self.n_results):
            result_list.append(ast.literal_eval(document.page_content))
        return result_list

    def get_related_ddl(self, question: str, **kwargs) -> list:
        result_list = []
        for document in self.ddl_vectorstore.similarity_search(question, k=self.n_results):
            result_list.append(document.page_content)
        return result_list

    def get_related_documentation(self, question: str, **kwargs) -> list:
        result_list = []
        for document in self.documentation_vectorstore.similarity_search(question, k=self.n_results):
            result_list.append(document.page_content)
        return result_list

    def get_training_data(self, **kwargs) -> DataFrame:
        # Establishing the connection
        engine = create_engine(self.connection_string)

        # Querying the 'langchain_pg_embedding' table
        query_embedding = "SELECT cmetadata, document FROM langchain_pg_embedding"
        df_embedding = pd.read_sql(query_embedding, engine)

        # List to accumulate the processed rows
        processed_rows = []

        # Process each row in the DataFrame
        for _, row in df_embedding.iterrows():
            custom_id = row['cmetadata']['id']
            document = row['document']
            training_data_type = "documentation" if custom_id[-3:] == "doc" else custom_id[-3:]

            if training_data_type == 'sql':
                # Convert the document string to a dictionary
                try:
                    doc_dict = ast.literal_eval(document)
                    question = doc_dict.get('question')
                    content = doc_dict.get('sql')
                except (ValueError, SyntaxError):
                    print(
                        f"Skipping row with custom_id {custom_id} due to parsing error.")
                    continue
            elif training_data_type in ['documentation', 'ddl']:
                question = None  # Default value for question
                content = document
            else:
                # If the suffix is not recognized, skip this row
                print(
                    f"Skipping row with custom_id {custom_id} due to unrecognized training data type.")
                continue

            # Append the processed data to the list
            processed_rows.append({
                'id': custom_id,
                'question': question,
                'content': content,
                'training_data_type': training_data_type
            })

        # Create a DataFrame from the list of processed rows
        df_processed = pd.DataFrame(processed_rows)

        return df_processed

    def remove_training_data(self, id: str, **kwargs) -> bool:
        # Create the database engine
        engine = create_engine(self.connection_string)

        # SQL DELETE statement
        delete_statement = text("""
            DELETE FROM langchain_pg_embedding
            WHERE cmetadata ->> 'id' = :id
        """)

        # Connect to the database and execute the delete statement
        with engine.connect() as connection:
            # Start a transaction
            with connection.begin() as transaction:
                try:
                    result = connection.execute(
                        delete_statement, {'id': id})
                    # Commit the transaction if the delete was successful
                    transaction.commit()
                    # Check if any row was deleted and return True or False accordingly
                    return result.rowcount > 0
                except Exception as e:
                    # Rollback the transaction in case of error
                    print(f"An error occurred: {e}")
                    transaction.rollback()
                    return False

    def remove_collection(self, collection_name: str) -> bool:
        engine = create_engine(self.connection_string)

        # Determine the suffix to look for based on the collection name
        suffix_map = {'ddl': 'ddl', 'sql': 'sql', 'documentation': 'doc'}
        suffix = suffix_map.get(collection_name)

        if not suffix:
            print(
                "Invalid collection name. Choose from 'ddl', 'sql', or 'documentation'.")
            return False

        # SQL query to delete rows based on the condition
        query = text(f"""
            DELETE FROM langchain_pg_embedding
            WHERE cmetadata->>'id' LIKE '%{suffix}'
        """)

        # Execute the deletion within a transaction block
        with engine.connect() as connection:
            with connection.begin() as transaction:
                try:
                    result = connection.execute(query)
                    transaction.commit()  # Explicitly commit the transaction
                    if result.rowcount > 0:
                        print(
                            f"Deleted {result.rowcount} rows from langchain_pg_embedding where collection is {collection_name}.")
                        return True
                    else:
                        print(
                            f"No rows deleted for collection {collection_name}.")
                        return False
                except Exception as e:
                    print(f"An error occurred: {e}")
                    transaction.rollback()  # Rollback in case of error
                    return False

    def generate_embedding(self, data: str, **kwargs) -> List[float]:
        pass
