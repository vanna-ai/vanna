import dataclasses
import json
from typing import Callable, List, Tuple, Union

import requests

from .base import VannaBase
from .types import (
    AccuracyStats,
    ApiKey,
    DataFrameJSON,
    DataResult,
    Explanation,
    FullQuestionDocument,
    NewOrganization,
    NewOrganizationMember,
    Organization,
    OrganizationList,
    PlotlyResult,
    Question,
    QuestionCategory,
    QuestionId,
    QuestionList,
    QuestionSQLPair,
    QuestionStringList,
    SQLAnswer,
    Status,
    StringData,
    TrainingData,
    UserEmail,
    UserOTP,
    Visibility,
)


class VannaDefault(VannaBase):
    def __init__(self, model: str, api_key: str, config=None):
        VannaBase.__init__(self, config=config)

        self._model = model
        self._api_key = api_key

        self._endpoint = (
            "https://ask.vanna.ai/rpc"
            if config is None or "endpoint" not in config
            else config["endpoint"]
        )
        self._unauthenticated_endpoint = (
            "https://ask.vanna.ai/unauthenticated_rpc"
            if config is None or "unauthenticated_endpoint" not in config
            else config["unauthenticated_endpoint"]
        )

    def _unauthenticated_rpc_call(self, method, params):
        headers = {
            "Content-Type": "application/json",
        }
        data = {
            "method": method,
            "params": [self._dataclass_to_dict(obj) for obj in params],
        }

        response = requests.post(
            self._unauthenticated_endpoint, headers=headers, data=json.dumps(data)
        )
        return response.json()

    def _rpc_call(self, method, params):
        if method != "list_orgs":
            headers = {
                "Content-Type": "application/json",
                "Vanna-Key": self._api_key,
                "Vanna-Org": self._model,
            }
        else:
            headers = {
                "Content-Type": "application/json",
                "Vanna-Key": self._api_key,
                "Vanna-Org": "demo-tpc-h",
            }

        data = {
            "method": method,
            "params": [self._dataclass_to_dict(obj) for obj in params],
        }

        response = requests.post(self._endpoint, headers=headers, data=json.dumps(data))
        return response.json()

    def _dataclass_to_dict(self, obj):
        return dataclasses.asdict(obj)

    def add_ddl(self, ddl: str, **kwargs) -> bool:
        """
        Adds a DDL statement to the model's training data

        **Example:**
        ```python
        vn.add_ddl(
            ddl="CREATE TABLE employees (id INT, name VARCHAR(255), salary INT)"
        )
        ```

        Args:
            ddl (str): The DDL statement to store.

        Returns:
            bool: True if the DDL statement was stored successfully, False otherwise.
        """
        params = [StringData(data=ddl)]

        d = self._rpc_call(method="store_ddl", params=params)

        if "result" not in d:
            return False

        status = Status(**d["result"])

        return status.success

    def add_documentation(self, documentation: str, **kwargs) -> bool:
        """
        Adds documentation to the model's training data

        **Example:**
        ```python
        vn.add_documentation(
            documentation="Our organization's definition of sales is the discount price of an item multiplied by the quantity sold."
        )
        ```

        Args:
            documentation (str): The documentation string to store.

        Returns:
            bool: True if the documentation string was stored successfully, False otherwise.
        """
        params = [StringData(data=documentation)]

        d = self._rpc_call(method="store_documentation", params=params)

        if "result" not in d:
            return False

        status = Status(**d["result"])

        return status.success

    def add_question_sql(self, question: str, sql: str, **kwargs) -> bool:
        """
        Adds a question and its corresponding SQL query to the model's training data. The preferred way to call this is to use [`vn.train(sql=...)`][vanna.train].

        **Example:**
        ```python
        vn.add_sql(
            question="What is the average salary of employees?",
            sql="SELECT AVG(salary) FROM employees"
        )
        ```

        Args:
            question (str): The question to store.
            sql (str): The SQL query to store.
            tag (Union[str, None]): A tag to associate with the question and SQL query.

        Returns:
            bool: True if the question and SQL query were stored successfully, False otherwise.
        """
        if "tag" in kwargs:
            tag = kwargs["tag"]
        else:
            tag = "Manually Trained"

        params = [QuestionSQLPair(question=question, sql=sql, tag=tag)]

        d = self._rpc_call(method="store_sql", params=params)

        if "result" not in d:
            return False

        status = Status(**d["result"])

        return status.success

    def generate_embedding(self, data: str, **kwargs) -> list[float]:
        """
        Not necessary for remote models as embeddings are generated on the server side.
        """
        pass

    def generate_plotly_code(
        self, question: str = None, sql: str = None, df_metadata: str = None, **kwargs
    ) -> str:
        """
        **Example:**
        ```python
        vn.generate_plotly_code(
            question="What is the average salary of employees?",
            sql="SELECT AVG(salary) FROM employees",
            df_metadata=df.dtypes
        )
        # fig = px.bar(df, x="name", y="salary")
        ```
        Generate Plotly code using the Vanna.AI API.

        Args:
            question (str): The question to generate Plotly code for.
            sql (str): The SQL query to generate Plotly code for.
            df (pd.DataFrame): The dataframe to generate Plotly code for.
            chart_instructions (str): Optional instructions for how to plot the chart.

        Returns:
            str or None: The Plotly code, or None if an error occurred.
        """
        if kwargs is not None and "chart_instructions" in kwargs:
            if question is not None:
                question = (
                    question
                    + " -- When plotting, follow these instructions: "
                    + kwargs["chart_instructions"]
                )
            else:
                question = (
                    "When plotting, follow these instructions: "
                    + kwargs["chart_instructions"]
                )

        params = [
            DataResult(
                question=question,
                sql=sql,
                table_markdown=df_metadata,
                error=None,
                correction_attempts=0,
            )
        ]

        d = self._rpc_call(method="generate_plotly_code", params=params)

        if "result" not in d:
            return None

        # Load the result into a dataclass
        plotly_code = PlotlyResult(**d["result"])

        return plotly_code.plotly_code

    def generate_question(self, sql: str, **kwargs) -> str:
        """

        **Example:**
        ```python
        vn.generate_question(sql="SELECT * FROM students WHERE name = 'John Doe'")
        # 'What is the name of the student?'
        ```

        Generate a question from an SQL query using the Vanna.AI API.

        Args:
            sql (str): The SQL query to generate a question for.

        Returns:
            str or None: The question, or None if an error occurred.

        """
        params = [
            SQLAnswer(
                raw_answer="",
                prefix="",
                postfix="",
                sql=sql,
            )
        ]

        d = self._rpc_call(method="generate_question", params=params)

        if "result" not in d:
            return None

        # Load the result into a dataclass
        question = Question(**d["result"])

        return question.question

    def get_prompt(
        self,
        question: str,
        question_sql_list: list,
        ddl_list: list,
        doc_list: list,
        **kwargs,
    ):
        """
        Not necessary for remote models as prompts are generated on the server side.
        """

    def submit_prompt(self, prompt, **kwargs) -> str:
        """
        Not necessary for remote models as prompts are handled on the server side.
        """

    def get_similar_question_sql(self, question: str, **kwargs) -> list:
        """
        Not necessary for remote models as similar questions are generated on the server side.
        """

    def get_related_ddl(self, question: str, **kwargs) -> list:
        """
        Not necessary for remote models as related DDL statements are generated on the server side.
        """

    def get_related_documentation(self, question: str, **kwargs) -> list:
        """
        Not necessary for remote models as related documentation is generated on the server side.
        """

    def generate_sql_from_question(self, question: str, **kwargs) -> str:
        """
        **Example:**
        ```python
        vn.generate_sql_from_question(question="What is the average salary of employees?")
        # SELECT AVG(salary) FROM employees
        ```

        Generate an SQL query using the Vanna.AI API.

        Args:
            question (str): The question to generate an SQL query for.

        Returns:
            str or None: The SQL query, or None if an error occurred.
        """
        params = [Question(question=question)]

        d = self._rpc_call(method="generate_sql_from_question", params=params)

        if "result" not in d:
            return None

        # Load the result into a dataclass
        sql_answer = SQLAnswer(**d["result"])

        return sql_answer.sql