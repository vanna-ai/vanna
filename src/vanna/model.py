from typing import Union, Callable
import requests
import json
from exceptions import ImproperlyConfigured
import dataclasses
from types import StringData, Status, QuestionSQLPair, APIError, SQLAnswer, Question, DataResult, PlotlyResult, DataFrameJSON

import plotly
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

class Model:
    api_key: Union[str, None] = None  # API key for Vanna.AI
    run_sql: Union[Callable[[str], pd.DataFrame], None] = None  # Function to convert SQL to a Pandas DataFrame

    __org: Union[str, None] = None  # Organization name for Vanna.AI

    def __init__(self, model_name: str, api_key: Union[str, None] = None, domain: str = "https://ask.vanna.ai"):
        self._endpoint = f"{domain}/rpc"
        self.__org = model_name
        self.api_key = api_key

    def __rpc_call(self, method, params):
        global api_key
        global __org

        if api_key is None:
            raise ImproperlyConfigured("API key not set. Use vn.get_api_key(...) to get an API key.")

        if __org is None and method != "list_orgs":
            raise ImproperlyConfigured("model not set. Use vn.set_model(...) to set the model to use.")

        if method != "list_orgs":
            headers = {
                'Content-Type': 'application/json',
                'Vanna-Key': self.api_key,
                'Vanna-Org': self.__org
            }
        else:
            headers = {
                'Content-Type': 'application/json',
                'Vanna-Key': self.api_key,
                'Vanna-Org': 'demo-tpc-h'
            }

        data = {
            "method": method,
            "params": [self.__dataclass_to_dict(obj) for obj in params]
        }

        response = requests.post(self._endpoint, headers=headers, data=json.dumps(data))
        return response.json()

    def __dataclass_to_dict(obj):
        return dataclasses.asdict(obj)
    
    def add_sql(self, question: str, sql: str, tag: Union[str, None] = "Manually Trained") -> bool:
        """
        Adds a question and its corresponding SQL query to the model's training data

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
        params = [QuestionSQLPair(
            question=question,
            sql=sql,
            tag=tag
        )]

        d = self.__rpc_call(method="store_sql", params=params)

        if 'result' not in d:
            return False

        status = Status(**d['result'])

        return status.success


    def add_ddl(self, ddl: str) -> bool:
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

        d = self.__rpc_call(method="store_ddl", params=params)

        if 'result' not in d:
            return False

        status = Status(**d['result'])

        return status.success


    def add_documentation(self, documentation: str) -> bool:
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

        d = self.__rpc_call(method="store_documentation", params=params)

        if 'result' not in d:
            return False

        status = Status(**d['result'])

        return status.success
    
    def remove_training_data(self, id: str) -> bool:
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

        d = self.__rpc_call(method="remove_training_data", params=params)

        if 'result' not in d:
            raise APIError(f"Error removing training data")

        status = Status(**d['result'])

        if not status.success:
            raise APIError(f"Error removing training data: {status.message}")

        return status.success
    
    def generate_sql(self, question: str) -> str:
        """
        **Example:**
        ```python
        vn.generate_sql(question="What is the average salary of employees?")
        # SELECT AVG(salary) FROM employees
        ```

        Generate an SQL query using the Vanna.AI API.

        Args:
            question (str): The question to generate an SQL query for.

        Returns:
            str or None: The SQL query, or None if an error occurred.
        """
        params = [Question(question=question)]

        d = self.__rpc_call(method="generate_sql_from_question", params=params)

        if 'result' not in d:
            return None

        # Load the result into a dataclass
        sql_answer = SQLAnswer(**d['result'])

        return sql_answer.sql
    
    def generate_meta(self, question: str) -> str:
        """
        **Example:**
        ```python
        vn.generate_meta(question="What tables are in the database?")
        # Information about the tables in the database
        ```

        Generate answers about the metadata of a database using the Vanna.AI API.

        Args:
            question (str): The question to generate an answer for.

        Returns:
            str or None: The answer, or None if an error occurred.
        """
        params = [Question(question=question)]

        d = self.__rpc_call(method="generate_meta_from_question", params=params)

        if 'result' not in d:
            return None

        # Load the result into a dataclass
        string_data = StringData(**d['result'])

        return string_data.data
    
    def generate_plotly_code(self, question: Union[str, None], sql: Union[str, None], df: 'pd.DataFrame', chart_instructions: Union[str, None] = None) -> str:
        """
        **Example:**
        ```python
        vn.generate_plotly_code(
            question="What is the average salary of employees?",
            sql="SELECT AVG(salary) FROM employees",
            df=df
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
        if chart_instructions is not None:
            if question is not None:
                question = question + " -- When plotting, follow these instructions: " + chart_instructions
            else:
                question = "When plotting, follow these instructions: " + chart_instructions

        params = [DataResult(
            question=question,
            sql=sql,
            table_markdown=str(df.dtypes),
            error=None,
            correction_attempts=0,
        )]

        d = self.__rpc_call(method="generate_plotly_code", params=params)

        if 'result' not in d:
            return None

        # Load the result into a dataclass
        plotly_code = PlotlyResult(**d['result'])

        return plotly_code.plotly_code
    
    def get_plotly_figure(self, plotly_code: str, df: pd.DataFrame, dark_mode: bool = True) -> plotly.graph_objs.Figure:
        """
        **Example:**
        ```python
        fig = vn.get_plotly_figure(
            plotly_code="fig = px.bar(df, x='name', y='salary')",
            df=df
        )
        fig.show()
        ```
        Get a Plotly figure from a dataframe and Plotly code.

        Args:
            df (pd.DataFrame): The dataframe to use.
            plotly_code (str): The Plotly code to use.

        Returns:
            plotly.graph_objs.Figure: The Plotly figure.
        """
        ldict = {'df': df, 'px': px, 'go': go}
        exec(plotly_code, globals(), ldict)

        fig = ldict.get('fig', None)

        if fig is None:
            return None

        if dark_mode:
            fig.update_layout(template="plotly_dark")

        return fig

    def generate_question(self, sql: str) -> str:
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
        params = [SQLAnswer(
            raw_answer="",
            prefix="",
            postfix="",
            sql=sql,
        )]

        d = self.__rpc_call(method="generate_question", params=params)

        if 'result' not in d:
            return None

        # Load the result into a dataclass
        question = Question(**d['result'])

        return question.question
    
    def get_training_data(self) -> pd.DataFrame:
        """
        Get the training data for the current model

        **Example:**
        ```python
        training_data = vn.get_training_data()
        ```

        Returns:
            pd.DataFrame or None: The training data, or None if an error occurred.

        """
        # params = [Question(question="")]
        params = []

        d = self.__rpc_call(method="get_training_data", params=params)

        if 'result' not in d:
            return None

        # Load the result into a dataclass
        training_data = DataFrameJSON(**d['result'])

        df = pd.read_json(training_data.data)

        return df