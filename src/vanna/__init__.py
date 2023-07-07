r'''
# What is Vanna.AI?
Vanna.AI is a platform that allows you to ask questions about your data in plain English. It is an AI-powered data analyst that can answer questions about your data, generate SQL, and create visualizations.

# API Reference
'''
print("Vanna.AI Imported")

import requests
import pandas as pd
import json
import dataclasses
import plotly
import plotly.express as px
import plotly.graph_objects as go
from .types import SQLAnswer, Explanation, QuestionSQLPair, Question, QuestionId, DataResult, PlotlyResult, Status, FullQuestionDocument, QuestionList, QuestionCategory, AccuracyStats, UserEmail, UserOTP, ApiKey, OrganizationList, Organization, NewOrganization
from typing import List, Dict, Any, Union, Optional

"""Set the API key for Vanna.AI."""
api_key: Union[str, None] = None # API key for Vanna.AI

__org: Union[str, None] = None # Organization name for Vanna.AI

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
        raise Exception("API key not set")
    
    if __org is None and method != "list_orgs":
        raise Exception("Organization name not set")

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
            'Vanna-Org': 'demo-sales'
        }

    data = {
        "method": method,
        "params": [__dataclass_to_dict(obj) for obj in params]
    }

    response = requests.post(_endpoint, headers=headers, data=json.dumps(data))
    return response.json()

def __dataclass_to_dict(obj):
    return dataclasses.asdict(obj)

def login(email: str, otp_code: Union[str, None] = None) -> bool:
    """
    ## Example
    ```python
    vn.login(email="username@example.com")
    ```

    Login to the Vanna.AI API.

    Args:
        email (str): The email address to login with.
        otp_code (Union[str, None]): The OTP code to login with. If None, an OTP code will be sent to the email address.

    Returns:
        bool: True if the login was successful, False otherwise.
    """
    global api_key

    if otp_code is None:
        params = [UserEmail(email=email)]

        d = __unauthenticated_rpc_call(method="send_otp", params=params)

        if 'result' not in d:
            return False

        status = Status(**d['result'])

        if not status.success:
            return False

        otp = input("Check your email for the code and enter it here: ")

    params = [UserOTP(email=email, otp=otp)]

    d = __unauthenticated_rpc_call(method="verify_otp", params=params)

    if 'result' not in d:
        return False

    key = ApiKey(**d['result'])

    if key is None:
        return False

    api_key = key.key
    print("Login successful. API key set. If you'd like to stay logged in, save your vn.api_key.")

    return True

def list_orgs() -> List[str]:
    """
    ## Example
    ```python
    orgs = vn.list_orgs()
    ```

    List the organizations that the user is a member of.

    Returns:
        List[str]: A list of organization names.
    """
    d = __rpc_call(method="list_orgs", params=[])

    if 'result' not in d:
        return []

    orgs = OrganizationList(**d['result'])

    return orgs.organizations

def create_org(org: str, db_type: str) -> bool:
    """
    ## Example
    ```python
    vn.create_org(org="my-org", db_type="postgres")
    ```

    Create a new organization.

    Args:
        org (str): The name of the organization to create.
        db_type (str): The type of database to use for the organization. This can be "Snowflake", "BigQuery", "Postgres", or anything else.

    Returns:
        bool: True if the organization was created successfully, False otherwise.
    """
    params = [NewOrganization(org_name=org, db_type=db_type)]

    d = __rpc_call(method="create_org", params=params)

    if 'result' not in d:
        return False

    status = Status(**d['result'])

    return status.success


def set_org(org: str) -> None:
    """
    ## Example
    ```python
    vn.set_org("my-org")
    ```

    Set the organization name for the Vanna.AI API.

    Args:
        org (str): The organization name.
    """
    global __org

    my_orgs = list_orgs()
    if org not in my_orgs:
        # Check if org exists
        d = __unauthenticated_rpc_call(method="check_org_exists", params=[Organization(name=org, user=None, connection=None)])

        if 'result' not in d:
            raise Exception("Failed to check if organization exists")

        status = Status(**d['result'])

        if status.success:
            raise Exception(f"An organization with the name {org} already exists")

        create = input(f"Would you like to create organization '{org}'? (y/n): ")

        if create.lower() == 'y':
            db_type = input("What type of database would you like to use? (Snowflake, BigQuery, Postgres, etc.): ")
            __org = 'demo-sales'
            if create_org(org=org, db_type=db_type):
                __org = org
            else:
                __org = None
                raise Exception("Failed to create organization")
    else:
        __org = org

def store_sql(question: str, sql: str) -> bool:
    """
    ## Example
    ```python
    vn.store_sql(
        question="What is the average salary of employees?", 
        sql="SELECT AVG(salary) FROM employees"
    )
    ```

    Store a question and its corresponding SQL query in the Vanna.AI database.

    Args:
        question (str): The question to store.
        sql (str): The SQL query to store.
    """
    params = [QuestionSQLPair(        
        question=question,
        sql=sql,
    )]

    d = __rpc_call(method="store_sql", params=params)

    if 'result' not in d:
        return False
    
    status = Status(**d['result'])

    return status.success

def train(question: str, sql: str) -> bool:
    """
    ## Example
    ```python
    vn.train(
        question="What is the average salary of employees?", 
        sql="SELECT AVG(salary) FROM employees"
    )
    ```

    Train Vanna.AI on a question and its corresponding SQL query. This is equivalent to calling [`store_sql()`][vanna.store_sql].

    Args:
        question (str): The question to train on.
        sql (str): The SQL query to train on.
    """
    return store_sql(question=question, sql=sql)

def flag_sql_for_review(question: str, sql: Union[str, None] = None, error_msg: Union[str, None] = None) -> bool:
    """
    ## Example
    ```python
    vn.flag_sql_for_review(question="What is the average salary of employees?")
    ```
    Flag a question and its corresponding SQL query for review. You can later retrieve the flagged questions using [`get_flagged_questions()`][vanna.get_flagged_questions].

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

def remove_sql(question: str) -> bool:
    """
    ## Example
    ```python
    vn.remove_sql(question="What is the average salary of employees?")
    ```
    Remove a question and its corresponding SQL query from the Vanna.AI database.

    Args:
        question (str): The question to remove.
    """
    params = [Question(question=question)]

    d = __rpc_call(method="remove_sql", params=params)

    if 'result' not in d:
        return False
    
    status = Status(**d['result'])

    return status.success

def generate_sql(question: str) -> str:
    """
    ## Example
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

def ask(question: str) -> str:
    """
    ## Example
    ```python
    vn.ask(question="What is the average salary of employees?")
    # SELECT AVG(salary) FROM employees
    ```

    Ask a question using the Vanna.AI API. This is equivalent to calling [`generate_sql()`][vanna.generate_sql].

    Args:
        question (str): The question to ask.

    Returns:
        str or None: The SQL query, or None if an error occurred.
    """
    return generate_sql(question=question)

def generate_plotly_code(question: Union[str, None], sql: Union[str, None], df: pd.DataFrame) -> str:
    """
    ## Example
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

    Returns:
        str or None: The Plotly code, or None if an error occurred.
    """
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
    ## Example
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
    ## Example
    ```python
    df = vn.get_results(cs=cs, default_database="PUBLIC", sql="SELECT * FROM students")
    ```
    Run the SQL query and return the results as a pandas dataframe. This is just a helper function that does not use the Vanna.AI API.

    Args:
        cs: Snowflake connection cursor.
        default_database (str): The default database to use.
        sql (str): The SQL query to execute.

    Returns:
        pd.DataFrame: The results of the SQL query.
    """
    cs.execute(f"USE DATABASE {default_database}")

    cur = cs.execute(sql)

    results = cur.fetchall()
        
    # Create a pandas dataframe from the results
    df = pd.DataFrame(results, columns=[desc[0] for desc in cur.description])

    return df


def generate_explanation(sql: str) -> str:
    """

    ## Example
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

    ## Example
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

def get_flagged_questions() -> QuestionList:
    """

    ## Example
    ```python
    questions = vn.get_flagged_questions()
    ```
    
    Get a list of flagged questions from the Vanna.AI API.

    Returns:
        List[FullQuestionDocument] or None: The list of flagged questions, or None if an error occurred.

    """
    # params = [Question(question="")]
    params = []

    d = __rpc_call(method="get_flagged_questions", params=params)

    if 'result' not in d:
        return None

    # Load the result into a dataclass
    flagged_questions = QuestionList(**d['result'])

    return flagged_questions

def get_accuracy_stats() -> AccuracyStats:
    """

    ## Example
    ```python
    vn.get_accuracy_stats()
    ```
    
    Get the accuracy statistics from the Vanna.AI API.

    Returns:
        dict or None: The accuracy statistics, or None if an error occurred.

    """
    params = []

    d = __rpc_call(method="get_accuracy_stats", params=params)

    if 'result' not in d:
        return None

    # Load the result into a dataclass
    accuracy_stats = AccuracyStats(**d['result'])

    return accuracy_stats