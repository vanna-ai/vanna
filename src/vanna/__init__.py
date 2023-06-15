print("Vanna.AI Imported")

import requests
import json
import dataclasses
import types

api_key: None | str = None
_endpoint = "https://ask.vanna.ai/py/rpc"

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
    params = [types.SQLAnswer(
        raw_answer="",
        prefix="",
        postfix="",
        sql=sql,
    )]

    result = __rpc_call(method="generate_explanation", params=params)

    return result