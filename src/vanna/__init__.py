r'''
A module to interact with the Vanna.AI API, providing the functionality to generate SQL explanations.

```python
import vanna as vn

vn.api_key = 'vanna-key-...' # Set your API key
vn.set_org('') # Set your organization name

my_question = 'What are the top 10 ABC by XYZ?'

sql = vn.generate_sql(question=my_question, error_msg=None) 
# SELECT * FROM table_name WHERE column_name = 'value'

(my_df, error_msg) = vn.run_sql(cs: snowflake.Cursor, sql=sql)

vn.generate_plotly_code(question=my_question, df=my_df)
# fig = px.bar(df, x='column_name', y='column_name')

vn.run_plotly_code(plotly_code=fig, df=my_df)

```
'''
print("Vanna.AI Imported")

import requests
import json
import dataclasses
from .types import SQLAnswer, Explanation, FullQuestionDocument, Question, QuestionId

api_key: None | str = None # API key for Vanna.AI
__org: None | str = None # Organization name for Vanna.AI
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

def store_sql(question: str, sql: str) -> None:
    """
    Store a question and its corresponding SQL query in the Vanna.AI database.

    Args:
        question (str): The question to store.
        sql (str): The SQL query to store.
    """
    params = [FullQuestionDocument(
        id=QuestionId(id=""),
        question=Question(question=question),
        answer=SQLAnswer(
            raw_answer="",
            prefix="",
            postfix="",
            sql=sql,
        ),
        data=None,
        plotly=None,
    )]

    __rpc_call(method="store_sql", params=params)

def generate_sql(question: str) -> str | None:
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


# Think about this generically -- the parameters should probably be flat but also be chainable
def generate_explanation(sql: str) -> str | None:
    """

    ## Example
    ```python
    vn.generate_explanation(sql="SELECT * FROM students WHERE name = 'John Doe'")
    # 'AI Response'
    ```
    
    Generate an explanation of an SQL query using the Vanna.AI API.

    :param sql: The SQL query to explain.
    :type sql: str

    :return: The explanation of the SQL query, or None if an error occurred.
    :rtype: str or None

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
