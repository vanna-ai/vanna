import dataclasses
import json
from io import StringIO
from typing import Callable, List, Tuple, Union

import pandas as pd
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
  StatusWithId,
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

    def system_message(self, message: str) -> any:
        return {"role": "system", "content": message}

    def user_message(self, message: str) -> any:
        return {"role": "user", "content": message}

    def assistant_message(self, message: str) -> any:
        return {"role": "assistant", "content": message}

    def get_training_data(self, **kwargs) -> pd.DataFrame:
        """
        Get the training data for the current model

        **Example:**
        ```python
        training_data = vn.get_training_data()
        ```

        Returns:
            pd.DataFrame or None: The training data, or None if an error occurred.

        """
        params = []

        d = self._rpc_call(method="get_training_data", params=params)

        if "result" not in d:
            return None

        # Load the result into a dataclass
        training_data = DataFrameJSON(**d["result"])

        df = pd.read_json(StringIO(training_data.data))

        return df

    def remove_training_data(self, id: str, **kwargs) -> bool:
        """
        Remove training data from the model

        **Example:**
        ```python
        vn.remove_training_data(id="1-ddl")
        ```

        Args:
            id (str): The ID of the training data to remove.
        """
        params = [StringData(data=id)]

        d = self._rpc_call(method="remove_training_data", params=params)

        if "result" not in d:
            raise Exception(f"Error removing training data")

        status = Status(**d["result"])

        if not status.success:
            raise Exception(f"Error removing training data: {status.message}")

        return status.success

    def generate_questions(self) -> list[str]:
        """
        **Example:**
        ```python
        vn.generate_questions()
        # ['What is the average salary of employees?', 'What is the total salary of employees?', ...]
        ```

        Generate questions using the Vanna.AI API.

        Returns:
            List[str] or None: The questions, or None if an error occurred.
        """
        d = self._rpc_call(method="generate_questions", params=[])

        if "result" not in d:
            return None

        # Load the result into a dataclass
        question_string_list = QuestionStringList(**d["result"])

        return question_string_list.questions

    def add_ddl(self, ddl: str, **kwargs) -> str:
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
            str: The ID of the DDL statement.
        """
        params = [StringData(data=ddl)]

        d = self._rpc_call(method="add_ddl", params=params)

        if "result" not in d:
            raise Exception("Error adding DDL", d)

        status = StatusWithId(**d["result"])

        return status.id

    def add_documentation(self, documentation: str, **kwargs) -> str:
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
            str: The ID of the documentation string.
        """
        params = [StringData(data=documentation)]

        d = self._rpc_call(method="add_documentation", params=params)

        if "result" not in d:
            raise Exception("Error adding documentation", d)

        status = StatusWithId(**d["result"])

        return status.id

    def add_question_sql(self, question: str, sql: str, **kwargs) -> str:
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
            str: The ID of the question and SQL query.
        """
        if "tag" in kwargs:
            tag = kwargs["tag"]
        else:
            tag = "Manually Trained"

        params = [QuestionSQLPair(question=question, sql=sql, tag=tag)]

        d = self._rpc_call(method="add_sql", params=params)

        if "result" not in d:
            raise Exception("Error adding question and SQL pair", d)

        status = StatusWithId(**d["result"])

        return status.id

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

    def get_sql_prompt(
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

    def get_followup_questions_prompt(
        self,
        question: str,
        df: pd.DataFrame,
        question_sql_list: list,
        ddl_list: list,
        doc_list: list,
        **kwargs,
    ):
        """
        Not necessary for remote models as prompts are generated on the server side.
        """

    def submit_prompt(self, prompt, **kwargs) -> str:
        # JSON-ify the prompt
        json_prompt = json.dumps(prompt)

        params = [StringData(data=json_prompt)]

        d = self._rpc_call(method="submit_prompt", params=params)

        if "result" not in d:
            return None

        # Load the result into a dataclass
        results = StringData(**d["result"])

        return results.data

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

    def generate_sql(self, question: str, **kwargs) -> str:
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
