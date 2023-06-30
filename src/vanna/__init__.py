r'''
# What is Vanna.AI?
Vanna.AI is a platform that allows you to ask questions about your data in plain English. It is an AI-powered data analyst that can answer questions about your data, generate SQL, and create visualizations.

# How do I use Vanna.AI?
- Import the Vanna.AI library
- Set your API key
- Set your organization name
- Train Vanna.AI on your data
- Ask questions about your data

# How does Vanna.AI work?
```mermaid
flowchart TD
    DB[(Known Correct Question-SQL)]
    Try[Try to Use DDL/Documentation]
    SQL(SQL)
    Check{Is the SQL correct?}
    Generate[fa:fa-circle-question Use Examples to Generate]
    DB --> Find
    Question[fa:fa-circle-question Question] --> Find{fa:fa-magnifying-glass Do we have similar questions?}
    Find -- Yes --> Generate
    Find -- No --> Try
    Generate --> SQL
    Try --> SQL
    SQL --> Check
    Check -- Yes --> DB
    Check -- No --> Analyst[fa:fa-glasses Analyst Writes the SQL]
    Analyst -- Adds --> DB
```

# Getting Started

## How do I import the Vanna.AI library?
```python
import vanna as vn
```

## How do I set my API key?
```python
vn.api_key = 'vanna-key-...'
```

## How do I set my organization name?
```python
vn.set_org('my_org')
```

## How do I train Vanna.AI on my data?
```python
vn.store_sql(
    question="Who are the top 10 customers by Sales?", 
    sql="SELECT customer_name, sales FROM customers ORDER BY sales DESC LIMIT 10"
)
```

## How do I ask questions about my data?
```python
my_question = 'What are the top 10 ABC by XYZ?'

sql = vn.generate_sql(question=my_question, error_msg=None)
# SELECT * FROM table_name WHERE column_name = 'value'
```

## Full Example
```python
import vanna as vn

vn.api_key = 'vanna-key-...' # Set your API key
vn.set_org('') # Set your organization name

# Train Vanna.AI on your data
vn.store_sql(
    question="Who are the top 10 customers by Sales?", 
    sql="SELECT customer_name, sales FROM customers ORDER BY sales DESC LIMIT 10"
)

# Ask questions about your data
my_question = 'What are the top 10 ABC by XYZ?'

# Generate SQL
sql = vn.generate_sql(question=my_question, error_msg=None) 

# Connect to your database
conn = snowflake.connector.connect(
        user='my_user',
        password='my_password',
        account='my_account',
        database='my_database',
    )

cs = conn.cursor()

# Get results
df = vn.get_results(
    cs=cs, 
    default_db=my_default_db, 
    sql=sql
    )

# Generate Plotly code
plotly_code = vn.generate_plotly_code(
    question=my_question, 
    sql=sql, 
    df=df
    )

# Get Plotly figure
fig = vn.get_plotly_figure(
    plotly_code=plotly_code, 
    df=df
    )

```

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
from .types import SQLAnswer, Explanation, QuestionSQLPair, Question, QuestionId, DataResult, PlotlyResult, Status, FullQuestionDocument, QuestionList, QuestionCategory, AccuracyStats
from typing import List, Dict, Any, Union, Optional

"""Set the API key for Vanna.AI."""
api_key: Union[str, None] = None # API key for Vanna.AI

__org: Union[str, None] = None # Organization name for Vanna.AI

_endpoint = "https://ask.vanna.ai/rpc"

def __rpc_call(method, params):
    """
    Make a RPC call to the Vanna.AI API.

    Args:
        method (str): The name of the method to call.
        params (list): A list of parameters for the method.

    Returns:
        dict: The JSON response from the API converted into a dictionary.
    """
    global api_key
    global __org

    if api_key is None:
        raise Exception("API key not set")
    
    if __org is None:
        raise Exception("Organization name not set")

    headers = {
        'Content-Type': 'application/json',
        'Vanna-Key': api_key,
        'Vanna-Org': __org
    }
    data = {
        "method": method,
        "params": [__dataclass_to_dict(obj) for obj in params]
    }

    response = requests.post(_endpoint, headers=headers, data=json.dumps(data))
    return response.json()

def __dataclass_to_dict(obj):
    """
    Converts a dataclass object to a dictionary.

    Args:
        obj (object): The dataclass object to convert.

    Returns:
        dict: The dataclass object as a dictionary.
    """
    return dataclasses.asdict(obj)

def set_org(org: str) -> None:
    """
    Set the organization name for the Vanna.AI API.

    Args:
        org (str): The organization name.
    """
    global __org
    __org = org

def store_sql(question: str, sql: str) -> bool:
    """
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

def flag_sql_for_review(question: str, sql: Union[str, None] = None, error_msg: Union[str, None] = None) -> bool:
    """
    Flag a question and its corresponding SQL query for review by the Vanna.AI team.

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

def generate_plotly_code(question: Union[str, None], sql: Union[str, None], df: pd.DataFrame) -> str:
    """
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
    Run the SQL query and return the results as a pandas dataframe.

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
    # 'AI Response'
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
    # 'AI Response'
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
    vn.get_flagged_questions()
    # [FullQuestionDocument(...), ...]
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
    # {'accuracy': 0.0, 'total': 0, 'correct': 0}
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