print("Vanna.AI Imported")

import requests
import json
import dataclasses
from .types import SQLAnswer, Explanation

api_key: None | str = None
_endpoint = "https://ask.vanna.ai/rpc"

def __rpc_call(method, params):
    headers = {'Content-Type': 'application/json'}
    data = {
        "method": method,
        "params": [__dataclass_to_dict(obj) for obj in params]
    }

    response = requests.post(_endpoint, headers=headers, data=json.dumps(data))
    return response.json()

def __dataclass_to_dict(obj):
    """Converts a dataclass object to a dictionary."""
    return dataclasses.asdict(obj)

# Think about this generically -- the parameters should probably be flat but also be chainable
def generate_explanation(sql: str) -> str | None:
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
