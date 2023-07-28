r'''
# Basic Usage

## Getting an API key
```python
import vanna as vn
api_key = vn.get_api_key('my-email@example.com')
vn.set_api_key(api_key)
```

## Setting the model
```python
vn.set_model('demo-tpc-h')
```

## Asking a question
```python
sql, df, fig, followup_questions = vn.ask(question='What are the top 10 customers by sales?')
```

For a more comprehensive starting guide see the [Starter Notebook](/notebooks/vn-starter/).

# Nomenclature

| Prefix | Definition | Examples |
| --- | --- | --- |
| `vn.set_` | Sets the variable for the current session | [`vn.set_model(...)`][vanna.set_model] <br> [`vn.set_api_key(...)`][vanna.set_api_key]  |
| `vn.get_` | Performs a read-only operation | [`vn.get_model()`][vanna.get_models] |
| `vn.add_` | Adds something to the model | [`vn.add_sql(...)`][vanna.add_sql] <br> [`vn.add_ddl(...)`][vanna.add_ddl] |
| `vn.generate_` | Generates something using AI based on the information in the model | [`vn.generate_sql(...)`][vanna.generate_sql] <br> [`vn.generate_explanation()`][vanna.generate_explanation] |
| `vn.run_` | Runs code (SQL or Plotly) | [`vn.run_sql`][vanna.run_sql] |
| `vn.remove_` | Removes something from the model | [`vn.remove_training_data`][vanna.remove_training_data] |
| `vn.update_` | Updates something in the model | [`vn.update_model_visibility(...)`][vanna.update_model_visibility] |
| `vn.connect_` | Connects to a database | [`vn.connect_to_snowflake(...)`][vanna.connect_to_snowflake] |

# Permissions
By default when you create a model it is private. You can add members or admins to your model or make it public.

<table>
  <tr>
    <th rowspan="2">User Role</th>
    <th colspan="2">Public Model</th>
    <th colspan="2">Private Model</th>
  </tr>
  <tr>
    <td>Use</td>
    <td>Train</td>
    <td>Use</td>
    <td>Train</td>
  </tr>
  <tr>
    <td>Non-Member</td>
    <td>✅</td>
    <td>❌</td>
    <td>❌</td>
    <td>❌</td>
  </tr>
  <tr>
    <td>Member</td>
    <td>✅</td>
    <td>❌</td>
    <td>✅</td>
    <td>❌</td>
  </tr>
  <tr>
    <td>Admin</td>
    <td>✅</td>
    <td>✅</td>
    <td>✅</td>
    <td>✅</td>
  </tr>
</table>


# API Reference
'''

import requests
import pandas as pd
import json
import dataclasses
import plotly
import plotly.express as px
import plotly.graph_objects as go
import sqlparse
from dataclasses import dataclass

from .types import SQLAnswer, Explanation, QuestionSQLPair, Question, QuestionId, DataResult, PlotlyResult, Status, \
    FullQuestionDocument, QuestionList, QuestionCategory, AccuracyStats, UserEmail, UserOTP, ApiKey, OrganizationList, \
    Organization, NewOrganization, StringData, QuestionStringList, Visibility, NewOrganizationMember, DataFrameJSON
from typing import List, Union, Callable, Tuple
from .exceptions import ImproperlyConfigured, DependencyError, ConnectionError, OtpCodeError, SQLRemoveError, \
    ValidationError, APIError
from .utils import validate_config_path
import warnings
import traceback
import os

api_key: Union[str, None] = None  # API key for Vanna.AI

run_sql: Union[Callable[[str], pd.DataFrame], None] = None  # Function to convert SQL to a Pandas DataFrame
"""
**Example**
```python
vn.run_sql = lambda sql: pd.read_sql(sql, engine)
```

Set the SQL to DataFrame function for Vanna.AI. This is used in the [`vn.ask(...)`][vanna.ask] function.
Instead of setting this directly you can also use [`vn.connect_to_snowflake(...)`][vanna.connect_to_snowflake] to set this.

"""

__org: Union[str, None] = None  # Organization name for Vanna.AI

_endpoint = "https://ask.vanna.ai/rpc"
_unauthenticated_endpoint = "https://ask.vanna.ai/unauthenticated_rpc"

def __unauthenticated_rpc_call(method, params):
    headers = {
        'Content-Type': 'application/json',
    }
    data = {
        "method": method,
        "params": [__dataclass_to_dict(obj) for obj in params]
    }

    response = requests.post(_unauthenticated_endpoint, headers=headers, data=json.dumps(data))
    return response.json()


def __rpc_call(method, params):
    global api_key
    global __org

    if api_key is None:
        raise ImproperlyConfigured("API key not set. Use vn.get_api_key(...) to get an API key.")

    if __org is None and method != "list_orgs":
        raise ImproperlyConfigured("model not set. Use vn.set_model(...) to set the model to use.")

    if method != "list_orgs":
        headers = {
            'Content-Type': 'application/json',
            'Vanna-Key': api_key,
            'Vanna-Org': __org
        }
    else:
        headers = {
            'Content-Type': 'application/json',
            'Vanna-Key': api_key,
            'Vanna-Org': 'demo-tpc-h'
        }

    data = {
        "method": method,
        "params": [__dataclass_to_dict(obj) for obj in params]
    }

    response = requests.post(_endpoint, headers=headers, data=json.dumps(data))
    return response.json()

def __dataclass_to_dict(obj):
    return dataclasses.asdict(obj)

def get_api_key(email: str, otp_code: Union[str, None] = None) -> str:
    """
    **Example:**
    ```python
    vn.get_api_key(email="my-email@example.com")
    ```

    Login to the Vanna.AI API.

    Args:
        email (str): The email address to login with.
        otp_code (Union[str, None]): The OTP code to login with. If None, an OTP code will be sent to the email address.

    Returns:
        str: The API key.
    """
    vanna_api_key = os.environ.get('VANNA_API_KEY', None)

    if vanna_api_key is not None:
        return vanna_api_key

    if email == 'my-email@example.com':
        raise ValidationError("Please replace 'my-email@example.com' with your email address.")

    if otp_code is None:
        params = [UserEmail(email=email)]

        d = __unauthenticated_rpc_call(method="send_otp", params=params)

        if 'result' not in d:
            raise OtpCodeError("Error sending OTP code.")

        status = Status(**d['result'])

        if not status.success:
            raise OtpCodeError(f"Error sending OTP code: {status.message}")

        otp_code = input("Check your email for the code and enter it here: ")

    params = [UserOTP(email=email, otp=otp_code)]

    d = __unauthenticated_rpc_call(method="verify_otp", params=params)

    if 'result' not in d:
        raise OtpCodeError("Error verifying OTP code.")

    key = ApiKey(**d['result'])

    if key is None:
        raise OtpCodeError("Error verifying OTP code.")

    api_key = key.key

    return api_key


def set_api_key(key: str) -> None:
    """
    Sets the API key for Vanna.AI.

    **Example:**
    ```python
    api_key = vn.get_api_key(email="my-email@example.com")
    vn.set_api_key(api_key)
    ```

    Args:
        key (str): The API key.
    """
    global api_key
    api_key = key

    models = get_models()

    if len(models) == 0:
        raise ConnectionError("There was an error communicating with the Vanna.AI API. Please try again or contact support@vanna.ai")

def get_models() -> List[str]:
    """
    **Example:**
    ```python
    models = vn.get_models()
    ```

    List the models that the user is a member of.

    Returns:
        List[str]: A list of model names.
    """
    d = __rpc_call(method="list_orgs", params=[])

    if 'result' not in d:
        return []

    orgs = OrganizationList(**d['result'])

    return orgs.organizations


def create_model(model: str, db_type: str) -> bool:
    """
    **Example:**
    ```python
    vn.create_model(model="my-model", db_type="postgres")
    ```

    Create a new model.

    Args:
        model (str): The name of the model to create.
        db_type (str): The type of database to use for the model. This can be "Snowflake", "BigQuery", "Postgres", or anything else.

    Returns:
        bool: True if the model was created successfully, False otherwise.
    """
    global __org
    if __org is None:
        __org = 'demo-tpc-h'

    params = [NewOrganization(org_name=model, db_type=db_type)]

    d = __rpc_call(method="create_org", params=params)

    if 'result' not in d:
        return False

    status = Status(**d['result'])

    if status.success:
        __org = model

    return status.success


def add_user_to_model(model: str, email: str, is_admin: bool) -> bool:
    """
    **Example:**
    ```python
    vn.add_user_to_model(model="my-model", email="user@example.com")
    ```

    Add a user to an model.

    Args:
        model (str): The name of the model to add the user to.
        email (str): The email address of the user to add.
        is_admin (bool): Whether or not the user should be an admin.

    Returns:
        bool: True if the user was added successfully, False otherwise.
    """

    params = [NewOrganizationMember(org_name=model, email=email, is_admin=is_admin)]

    d = __rpc_call(method="add_user_to_org", params=params)

    if 'result' not in d:
        return False

    status = Status(**d['result'])

    if not status.success:
        print(status.message)

    return status.success


def update_model_visibility(public: bool) -> bool:
    """
    **Example:**
    ```python
    vn.update_model_visibility(public=True)
    ```

    Set the visibility of the current model. If a model is visible, anyone can see it. If it is not visible, only members of the model can see it.

    Args:
        public (bool): Whether or not the model should be publicly visible.

    Returns:
        bool: True if the model visibility was set successfully, False otherwise.
    """
    params = [Visibility(visibility=public)]

    d = __rpc_call(method="set_org_visibility", params=params)

    if 'result' not in d:
        return False

    status = Status(**d['result'])

    return status.success


def _set_org(org: str) -> None:
    global __org

    my_orgs = get_models()
    if org not in my_orgs:
        # Check if org exists
        d = __unauthenticated_rpc_call(method="check_org_exists",
                                       params=[Organization(name=org, user=None, connection=None)])

        if 'result' not in d:
            raise ValidationError("Failed to check if model exists")

        status = Status(**d['result'])

        if status.success:
            raise ValidationError(f"An organization with the name {org} already exists")

        create = input(f"Would you like to create model '{org}'? (y/n): ")

        if create.lower() == 'y':
            db_type = input("What type of database would you like to use? (Snowflake, BigQuery, Postgres, etc.): ")
            if create_model(model=org, db_type=db_type):
                __org = org
            else:
                __org = None
                raise ValidationError("Failed to create model")
    else:
        __org = org


def set_model(model: str):
    """
    Set the models to use for the Vanna.AI API.

    **Example:**
    ```python
    vn.set_model("my-model")
    ```

    Args:
        model (str): The name of the model to use.
    """
    if model == 'my-model':
        env_model = os.environ.get('VANNA_MODEL', None)

        if env_model is not None:
            model = env_model
        else:
            raise ValidationError("Please replace 'my-model' with the name of your model")

    _set_org(org=model)


def add_sql(question: str, sql: str, tag: Union[str, None] = "Manually Trained") -> bool:
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

    d = __rpc_call(method="store_sql", params=params)

    if 'result' not in d:
        return False

    status = Status(**d['result'])

    return status.success


def add_ddl(ddl: str) -> bool:
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

    d = __rpc_call(method="store_ddl", params=params)

    if 'result' not in d:
        return False

    status = Status(**d['result'])

    return status.success


def add_documentation(documentation: str) -> bool:
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

    d = __rpc_call(method="store_documentation", params=params)

    if 'result' not in d:
        return False

    status = Status(**d['result'])

    return status.success

@dataclass
class TrainingPlanItem:
    item_type: str
    item_group: str
    item_name: str
    item_value: str

    def __str__(self):
        if self.item_type == self.ITEM_TYPE_SQL:
            return f"Train on SQL: {self.item_group} {self.item_name}"
        elif self.item_type == self.ITEM_TYPE_DDL:
            return f"Train on DDL: {self.item_group} {self.item_name}"
        elif self.item_type == self.ITEM_TYPE_IS:
            return f"Train on Information Schema: {self.item_group} {self.item_name}"

    ITEM_TYPE_SQL = "sql"
    ITEM_TYPE_DDL = "ddl"
    ITEM_TYPE_IS = "is"


class TrainingPlan:
    """
    A class representing a training plan. You can see what's in it, and remove items from it that you don't want trained.

    **Example:**
    ```python
    plan = vn.get_training_plan()

    plan.get_summary()
    ```

    """
    _plan: List[TrainingPlanItem]

    def __init__(self, plan: List[TrainingPlanItem]):
        self._plan = plan

    def __str__(self):
        return "\n".join(self.get_summary())
    
    def __repr__(self):
        return self.__str__()

    def get_summary(self) -> List[str]:
        """
        **Example:**
        ```python
        plan = vn.get_training_plan()

        plan.get_summary()
        ```

        Get a summary of the training plan.

        Returns:
            List[str]: A list of strings describing the training plan.
        """

        return [f"{item}" for item in self._plan]

    def remove_item(self, item: str):
        """
        **Example:**
        ```python
        plan = vn.get_training_plan()

        plan.remove_item("Train on SQL: What is the average salary of employees?")
        ```

        Remove an item from the training plan.

        Args:
            item (str): The item to remove.
        """
        for plan_item in self._plan:
            if str(plan_item) == item:
                self._plan.remove(plan_item)
                break

    

def get_training_plan() -> TrainingPlan:
    """
    **Example:**
    ```python
    plan = vn.get_training_plan()

    vn.train(plan=plan)
    ```

    Get the training plan for the model.

    Returns:
        TrainingPlan: The training plan for the model.
    """
    d = __rpc_call(method="get_training_plan", params=[])

    if 'result' not in d:
        raise ValidationError("Failed to get training plan")

    training_plan = TrainingPlan(**d['result'])

    return training_plan

def train(question: str = None, sql: str = None, ddl: str = None, documentation: str = None, json_file: str = None,
          sql_file: str = None) -> bool:
    """
    **Example:**
    ```python
    vn.train()
    ```

    Train Vanna.AI on a question and its corresponding SQL query. 
    If you call it with no arguments, it will check if you connected to a database and it will attempt to train on the metadata of that database.
    If you call it with the sql argument, it's equivalent to [`add_sql()`][vanna.add_sql].
    If you call it with the ddl argument, it's equivalent to [`add_ddl()`][vanna.add_ddl].
    If you call it with the documentation argument, it's equivalent to [`add_documentation()`][vanna.add_documentation].
    It can also accept a JSON file path or SQL file path to train on a batch of questions and SQL queries or a list of SQL queries respectively.

    Args:
        question (str): The question to train on.
        sql (str): The SQL query to train on.
        sql_file (str): The SQL file path.
        json_file (str): The JSON file path.
        ddl (str):  The DDL statement.
        documentation (str): The documentation to train on.
    """

    if question and not sql:
        example_question = "What is the average salary of employees?"
        raise ValidationError(
            f"Please also provide a SQL query \n Example Question:  {example_question}\n Answer: {ask(question=example_question)}")

    if documentation:
        print("Adding documentation....")
        return add_documentation(sql)

    if sql:
        if question is None:
            question = generate_question(sql)
            print("Question generated with sql:", Question, '\nAdding SQL...')
        return add_sql(question=question, sql=sql)

    if ddl:
        print("Adding ddl:", ddl)
        return add_ddl(sql)

    if json_file:
        validate_config_path(json_file)
        with open(json_file, 'r') as js_file:
            data = json.load(js_file)
            print("Adding Questions And SQLs using file:", json_file)
            for question in data:
                if not add_sql(question=question['question'], sql=question['answer']):
                    logger.warning(f"Not able to add sql for question: {question['question']} from {json_file}")
                    return False
        return True

    if sql_file:
        validate_config_path(sql_file)
        with open(sql_file, 'r') as file:
            sql_statements = sqlparse.split(file.read())
            for statement in sql_statements:
                if 'CREATE TABLE' in statement:
                    if add_ddl(statement):
                        print("ddl Added!")
                        return True
                    print("Not able to add DDL")
                    return False
                else:
                    question = generate_question(sql=statement)
                    if add_sql(question=question, sql=statement):
                        print("SQL added!")
                        return True
                    logger.warning("Not able to add sql.")
                    return False
        return False
    
    # Here we're going to attempt auto training


def flag_sql_for_review(question: str, sql: Union[str, None] = None, error_msg: Union[str, None] = None) -> bool:
    """
    **Example:**
    ```python
    vn.flag_sql_for_review(question="What is the average salary of employees?")
    ```
    Flag a question and its corresponding SQL query for review. You can see the tag show up in [`vn.get_all_questions()`][vanna.get_all_questions]

    Args:
        question (str): The question to flag.
        sql (str): The SQL query to flag.
        error_msg (str): The error message to flag.

    Returns:
        bool: True if the question and SQL query were flagged successfully, False otherwise.
    """
    params = [
        QuestionCategory(
            question=question,
            category=QuestionCategory.FLAGGED_FOR_REVIEW,
        )
    ]

    d = __rpc_call(method="set_accuracy_category", params=params)

    if 'result' not in d:
        return False

    status = Status(**d['result'])

    return status.success


# def read_questions_from_github(url: str) -> List[QuestionSQLPair]:
#     """
#     **Example:**
#     ```python
#     url = "https://raw.githubusercontent.com/vanna-ai/vanna-ai/main/data/questions.json"
#     questions = vn.read_questions_from_github(url)
#     ```
#     Read questions and SQL queries from a GitHub URL.

#     Args:
#         url (str): The URL to read from.

#     Returns:
#         List[QuestionSQLPair]: A list of [`QuestionSQLPair`][vanna.QuestionSQLPair] objects.
#     """
#     response = requests.get(url)
#     data = response.json()

#     question_sql_pairs = []
#     for item in data:
#         question = item.get('question')
#         sql = item.get('sql')
#         if question and sql:
#             question_sql_pair = QuestionSQLPair(question=question, sql=sql)
#             question_sql_pairs.append(question_sql_pair)

#     return question_sql_pairs

def remove_sql(question: str) -> bool:
    """
    Remove a question and its corresponding SQL query from the model's training data

    **Example:**
    ```python
    vn.remove_sql(question="What is the average salary of employees?")
    ```

    Args:
        question (str): The question to remove.
    """
    params = [Question(question=question)]

    d = __rpc_call(method="remove_sql", params=params)

    if 'result' not in d:
        raise Exception(f"Error removing SQL")
        return False
    
    status = Status(**d['result'])

    if not status.success:
        raise SQLRemoveError(f"Error removing SQL: {status.message}")

    return status.success


def remove_training_data(id: str) -> bool:
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

    d = __rpc_call(method="remove_training_data", params=params)

    if 'result' not in d:
        raise APIError(f"Error removing training data")

    status = Status(**d['result'])

    if not status.success:
        raise APIError(f"Error removing training data: {status.message}")

    return status.success


def generate_sql(question: str) -> str:
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

    d = __rpc_call(method="generate_sql_from_question", params=params)

    if 'result' not in d:
        return None

    # Load the result into a dataclass
    sql_answer = SQLAnswer(**d['result'])

    return sql_answer.sql


def generate_meta(question: str) -> str:
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

    d = __rpc_call(method="generate_meta_from_question", params=params)

    if 'result' not in d:
        return None

    # Load the result into a dataclass
    string_data = StringData(**d['result'])

    return string_data.data


def generate_followup_questions(question: str, df: pd.DataFrame) -> List[str]:
    """
    **Example:**
    ```python
    vn.generate_followup_questions(question="What is the average salary of employees?", df=df)
    # ['What is the average salary of employees in the Sales department?', 'What is the average salary of employees in the Engineering department?', ...]
    ```

    Generate follow-up questions using the Vanna.AI API.

    Args:
        question (str): The question to generate follow-up questions for.
        df (pd.DataFrame): The DataFrame to generate follow-up questions for.

    Returns:
        List[str] or None: The follow-up questions, or None if an error occurred.
    """
    params = [DataResult(
        question=question,
        sql=None,
        table_markdown=df.head().to_markdown(),
        error=None,
        correction_attempts=0,
    )]

    d = __rpc_call(method="generate_followup_questions", params=params)

    if 'result' not in d:
        return None

    # Load the result into a dataclass
    question_string_list = QuestionStringList(**d['result'])

    return question_string_list.questions


def generate_questions() -> List[str]:
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
    d = __rpc_call(method="generate_questions", params=[])

    if 'result' not in d:
        return None

    # Load the result into a dataclass
    question_string_list = QuestionStringList(**d['result'])

    return question_string_list.questions


def ask(question: Union[str, None] = None, print_results: bool = True, auto_train: bool = True, generate_followups: bool = True) -> Union[Tuple[Union[str, None], Union[pd.DataFrame, None], Union[plotly.graph_objs.Figure, None], Union[List[str], None]], None]:
    """
    **Example:**
    ```python
    # RECOMMENDED IN A NOTEBOOK:
    sql, df, fig, followup_questions = vn.ask()


    sql, df, fig, followup_questions = vn.ask(question="What is the average salary of employees?")
    # SELECT AVG(salary) FROM employees
    ```

    Ask a question using the Vanna.AI API. This generates an SQL query, runs it, and returns the results in a dataframe and a Plotly figure.
    If you set print_results to True, the sql, dataframe, and figure will be output to the screen instead of returned.

    Args:
        question (str): The question to ask. If None, you will be prompted to enter a question.
        print_results (bool): Whether to print the SQL query and results.
        auto_train (bool): Whether to automatically train the model if the SQL query is incorrect.
        generate_followups (bool): Whether to generate follow-up questions.

    Returns:
        str or None: The SQL query, or None if an error occurred.
        pd.DataFrame or None: The results of the SQL query, or None if an error occurred.
        plotly.graph_objs.Figure or None: The Plotly figure, or None if an error occurred.
        List[str] or None: The follow-up questions, or None if an error occurred.
    """

    if question is None:
        question = input("Enter a question: ")

    try:
        sql = generate_sql(question=question)
    except Exception as e:
        print(e)
        return None, None, None, None

    if print_results:
        try:
                Code = __import__('IPython.display', fromlist=['Code']).Code
                display(Code(sql))
        except Exception as e:
            print(sql)
        
    if run_sql is None:
        print("If you want to run the SQL query, provide a vn.run_sql function.")

        if print_results:
            return None
        else:
            return sql, None, None, None

    try:
        df = run_sql(sql)

        if print_results:
            try:
                display = __import__('IPython.display', fromlist=['display']).display
                display(df)
            except Exception as e:
                print(df)

        if len(df) > 0 and auto_train:
            add_sql(question=question, sql=sql, tag=types.QuestionCategory.SQL_RAN)

        try:
            plotly_code = generate_plotly_code(question=question, sql=sql, df=df)
            fig = get_plotly_figure(plotly_code=plotly_code, df=df)
            if print_results:
                try:
                    display = __import__('IPython.display', fromlist=['display']).display
                    Image = __import__('IPython.display', fromlist=['Image']).Image
                    img_bytes = fig.to_image(format="png", scale=2)
                    display(Image(img_bytes))
                except Exception as e:
                    fig.show()

            if generate_followups:
                followup_questions = generate_followup_questions(question=question, df=df)
                if print_results and followup_questions is not None and len(followup_questions) > 0:
                    md = "AI-generated follow-up questions:\n\n"
                    for followup_question in followup_questions:
                        md += f"* {followup_question}\n"

                    try:
                        display = __import__('IPython.display', fromlist=['display']).display
                        Markdown = __import__('IPython.display', fromlist=['Markdown']).Markdown
                        display(Markdown(md))
                    except Exception as e:
                        print(md)


                if print_results:
                    return None
                else:
                    return sql, df, fig, followup_questions

            if print_results:
                return None
            else:
                return sql, df, fig, None

        except Exception as e:
            # Print stack trace
            traceback.print_exc()
            print("Couldn't run plotly code: ", e)
            if print_results:
                return None
            else:
                return sql, df, None, None

    except Exception as e:
        print("Couldn't run sql: ", e)
        if print_results:
            return None
        else:
            return sql, None, None, None


def generate_plotly_code(question: Union[str, None], sql: Union[str, None], df: pd.DataFrame, chart_instructions: Union[str, None] = None) -> str:
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
        table_markdown=df.head().to_markdown(),
        error=None,
        correction_attempts=0,
    )]

    d = __rpc_call(method="generate_plotly_code", params=params)

    if 'result' not in d:
        return None

    # Load the result into a dataclass
    plotly_code = PlotlyResult(**d['result'])

    return plotly_code.plotly_code


def get_plotly_figure(plotly_code: str, df: pd.DataFrame, dark_mode: bool = True) -> plotly.graph_objs.Figure:
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


def get_results(cs, default_database: str, sql: str) -> pd.DataFrame:
    """
    DEPRECATED. Use `vn.run_sql` instead.
    Run the SQL query and return the results as a pandas dataframe. This is just a helper function that does not use the Vanna.AI API.

    Args:
        cs: Snowflake connection cursor.
        default_database (str): The default database to use.
        sql (str): The SQL query to execute.

    Returns:
        pd.DataFrame: The results of the SQL query.
    """
    print("`vn.get_results()` is deprecated. Use `vn.run_sql()` instead.")
    warnings.warn("`vn.get_results()` is deprecated. Use `vn.run_sql()` instead.")

    cs.execute(f"USE DATABASE {default_database}")

    cur = cs.execute(sql)

    results = cur.fetchall()

    # Create a pandas dataframe from the results
    df = pd.DataFrame(results, columns=[desc[0] for desc in cur.description])

    return df


def generate_explanation(sql: str) -> str:
    """

    **Example:**
    ```python
    vn.generate_explanation(sql="SELECT * FROM students WHERE name = 'John Doe'")
    # 'This query selects all columns from the students table where the name is John Doe.'
    ```

    Generate an explanation of an SQL query using the Vanna.AI API.

    Args:
        sql (str): The SQL query to generate an explanation for.

    Returns:
        str or None: The explanation, or None if an error occurred.

    """
    params = [SQLAnswer(
        raw_answer="",
        prefix="",
        postfix="",
        sql=sql,
    )]

    d = __rpc_call(method="generate_explanation", params=params)

    if 'result' not in d:
        return None

    # Load the result into a dataclass
    explanation = Explanation(**d['result'])

    return explanation.explanation

def generate_question(sql: str) -> str:
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

    d = __rpc_call(method="generate_question", params=params)

    if 'result' not in d:
        return None

    # Load the result into a dataclass
    question = Question(**d['result'])

    return question.question


def get_all_questions() -> pd.DataFrame:
    """
    Get a list of questions from the Vanna.AI API.

    **Example:**
    ```python
    questions = vn.get_all_questions()
    ```

    Returns:
        pd.DataFrame or None: The list of questions, or None if an error occurred.

    """
    # params = [Question(question="")]
    params = []

    d = __rpc_call(method="get_all_questions", params=params)

    if 'result' not in d:
        return None

    # Load the result into a dataclass
    all_questions = DataFrameJSON(**d['result'])

    df = pd.read_json(all_questions.data)

    return df


def get_training_data() -> pd.DataFrame:
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

    d = __rpc_call(method="get_training_data", params=params)

    if 'result' not in d:
        return None

    # Load the result into a dataclass
    training_data = DataFrameJSON(**d['result'])

    df = pd.read_json(training_data.data)

    return df


def connect_to_snowflake(account: str, username: str, password: str, database: str, role: Union[str, None] = None):
    """
    Connect to Snowflake using the Snowflake connector. This is just a helper function to set [`vn.run_sql`][vanna.run_sql]

    **Example:**
    ```python
    import snowflake.connector

    vn.connect_to_snowflake(
        account="myaccount",
        username="myusername",
        password="mypassword",
        database="mydatabase",
        role="myrole",
    )
    ```

    Args:
        account (str): The Snowflake account name.
        username (str): The Snowflake username.
        password (str): The Snowflake password.
        database (str): The default database to use.
        role (Union[str, None], optional): The role to use. Defaults to None.
    """

    try:
        snowflake = __import__('snowflake.connector')
    except ImportError:
        raise DependencyError("You need to install required dependencies to execute this method, run command:"
                                  " \npip install vanna[snowflake]")

    if username == 'my-username':
        username_env = os.getenv('SNOWFLAKE_USERNAME')

        if username_env is not None:
            username = username_env
        else:
            raise ImproperlyConfigured("Please set your Snowflake username.")

    if password == 'my-password':
        password_env = os.getenv('SNOWFLAKE_PASSWORD')

        if password_env is not None:
            password = password_env
        else:
            raise ImproperlyConfigured("Please set your Snowflake password.")

    if account == 'my-account':
        account_env = os.getenv('SNOWFLAKE_ACCOUNT')

        if account_env is not None:
            account = account_env
        else:
            raise ImproperlyConfigured("Please set your Snowflake account.")

    if database == 'my-database':
        database_env = os.getenv('SNOWFLAKE_DATABASE')

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

    global run_sql
    run_sql = run_sql_snowflake
