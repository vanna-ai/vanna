import os
import traceback
from abc import ABC, abstractmethod
from typing import List, Tuple, Union

import pandas as pd
import plotly

from .exceptions import DependencyError, ImproperlyConfigured


class VannaBase(ABC):
    def __init__(self, config=None):
        self.config = config
        self.run_sql_is_set = False

    def generate_sql_from_question(self, question: str, **kwargs) -> str:
        question_sql_list = self.get_similar_question_sql(question, **kwargs)
        ddl_list = self.get_related_ddl(question, **kwargs)
        doc_list = self.get_related_documentation(question, **kwargs)
        prompt = self.get_prompt(
            question=question,
            question_sql_list=question_sql_list,
            ddl_list=ddl_list,
            doc_list=doc_list,
            **kwargs,
        )
        llm_response = self.submit_prompt(prompt, **kwargs)
        return llm_response

    # ----------------- Use Any Embeddings API ----------------- #
    @abstractmethod
    def generate_embedding(self, data: str, **kwargs) -> list[float]:
        pass

    # ----------------- Use Any Database to Store and Retrieve Context ----------------- #
    @abstractmethod
    def get_similar_question_sql(self, question: str, **kwargs) -> list:
        pass

    @abstractmethod
    def get_related_ddl(self, question: str, **kwargs) -> list:
        pass

    @abstractmethod
    def get_related_documentation(self, question: str, **kwargs) -> list:
        pass

    @abstractmethod
    def store_question_sql(self, question: str, sql: str, **kwargs):
        pass

    @abstractmethod
    def store_ddl(self, ddl: str, **kwargs):
        pass

    @abstractmethod
    def store_documentation(self, doc: str, **kwargs):
        pass

    # ----------------- Use Any Language Model API ----------------- #

    @abstractmethod
    def get_prompt(
        self,
        question: str,
        question_sql_list: list,
        ddl_list: list,
        doc_list: list,
        **kwargs,
    ):
        pass

    @abstractmethod
    def submit_prompt(self, prompt, **kwargs) -> str:
        pass

    # ----------------- Connect to Any Database to run the Generated SQL ----------------- #

    def connect_to_snowflake(
        self,
        account: str,
        username: str,
        password: str,
        database: str,
        role: Union[str, None] = None,
    ):
        try:
            snowflake = __import__("snowflake.connector")
        except ImportError:
            raise DependencyError(
                "You need to install required dependencies to execute this method, run command:"
                " \npip install vanna[snowflake]"
            )

        if username == "my-username":
            username_env = os.getenv("SNOWFLAKE_USERNAME")

            if username_env is not None:
                username = username_env
            else:
                raise ImproperlyConfigured("Please set your Snowflake username.")

        if password == "my-password":
            password_env = os.getenv("SNOWFLAKE_PASSWORD")

            if password_env is not None:
                password = password_env
            else:
                raise ImproperlyConfigured("Please set your Snowflake password.")

        if account == "my-account":
            account_env = os.getenv("SNOWFLAKE_ACCOUNT")

            if account_env is not None:
                account = account_env
            else:
                raise ImproperlyConfigured("Please set your Snowflake account.")

        if database == "my-database":
            database_env = os.getenv("SNOWFLAKE_DATABASE")

            if database_env is not None:
                database = database_env
            else:
                raise ImproperlyConfigured("Please set your Snowflake database.")

        conn = snowflake.connector.connect(
            user=username,
            password=password,
            account=account,
            database=database,
        )

        def run_sql_snowflake(sql: str) -> pd.DataFrame:
            cs = conn.cursor()

            if role is not None:
                cs.execute(f"USE ROLE {role}")
            cs.execute(f"USE DATABASE {database}")

            cur = cs.execute(sql)

            results = cur.fetchall()

            # Create a pandas dataframe from the results
            df = pd.DataFrame(results, columns=[desc[0] for desc in cur.description])

            return df

        self.run_sql = run_sql_snowflake
        self.run_sql_is_set = True

    def run_sql(sql: str, **kwargs) -> pd.DataFrame:
        raise NotImplementedError(
            "You need to connect_to_snowflake or other database first."
        )

    def ask(
        self,
        question: Union[str, None] = None,
        print_results: bool = True,
        auto_train: bool = True,
    ) -> Union[Tuple[Union[str, None], Union[pd.DataFrame, None]], None]:
        if question is None:
            question = input("Enter a question: ")

        try:
            sql = self.generate_sql_from_question(question=question)
        except Exception as e:
            print(e)
            return None, None

        if print_results:
            try:
                Code = __import__("IPython.display", fromlist=["Code"]).Code
                display(Code(sql))
            except Exception as e:
                print(sql)

        if self.run_sql_is_set is False:
            print("If you want to run the SQL query, provide a run_sql function.")

            if print_results:
                return None
            else:
                return sql, None

        try:
            df = self.run_sql(sql)

            if print_results:
                try:
                    display = __import__(
                        "IPython.display", fromlist=["display"]
                    ).display
                    display(df)
                except Exception as e:
                    print(df)

            if len(df) > 0 and auto_train:
                self.store_question_sql(question=question, sql=sql)

        except Exception as e:
            print("Couldn't run sql: ", e)
            if print_results:
                return None
            else:
                return sql, None


class SplitStorage(VannaBase):
    def __init__(self, config=None):
        VannaBase.__init__(self, config=config)

    def get_similar_question_sql(self, embedding: str, **kwargs) -> list:
        question_sql_ids = self.get_similar_question_sql_ids(embedding, **kwargs)
        question_sql_list = self.get_question_sql(question_sql_ids, **kwargs)
        return question_sql_list

    def get_related_ddl(self, embedding: str, **kwargs) -> list:
        ddl_ids = self.get_related_ddl_ids(embedding, **kwargs)
        ddl_list = self.get_ddl(ddl_ids, **kwargs)
        return ddl_list

    def get_related_documentation(self, embedding: str, **kwargs) -> list:
        doc_ids = self.get_related_documentation_ids(embedding, **kwargs)
        doc_list = self.get_documentation(doc_ids, **kwargs)
        return doc_list

    # ----------------- Use Any Vector Database to Store and Lookup Embedding Similarity ----------------- #
    @abstractmethod
    def store_question_sql_embedding(self, embedding: str, **kwargs) -> str:
        pass

    @abstractmethod
    def store_ddl_embedding(self, embedding: str, **kwargs) -> str:
        pass

    @abstractmethod
    def store_documentation_embedding(self, embedding: str, **kwargs) -> str:
        pass

    @abstractmethod
    def get_similar_question_sql_ids(self, embedding: str, **kwargs) -> list:
        pass

    @abstractmethod
    def get_related_ddl_ids(self, embedding: str, **kwargs) -> list:
        pass

    @abstractmethod
    def get_related_documentation_ids(self, embedding: str, **kwargs) -> list:
        pass

    # ----------------- Use Database to Retrieve the Documents from ID Lists ----------------- #
    @abstractmethod
    def get_question_sql(self, question_sql_ids: list, **kwargs) -> list:
        pass

    @abstractmethod
    def get_documentation(self, doc_ids: list, **kwargs) -> list:
        pass

    @abstractmethod
    def get_ddl(self, ddl_ids: list, **kwargs) -> list:
        pass
