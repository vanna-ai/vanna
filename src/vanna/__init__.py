import dataclasses
import json
import os
from dataclasses import dataclass
from typing import Callable, List, Tuple, Union

import pandas as pd
import requests
import plotly.graph_objs

from .exceptions import (
    OTPCodeError,
    ValidationError,
)
from .types import (
    ApiKey,
    Status,
    TrainingData,
    UserEmail,
    UserOTP,
)
from .utils import sanitize_model_name, validate_config_path

api_key: Union[str, None] = None  # API key for Vanna.AI

fig_as_img: bool = False  # Whether or not to return Plotly figures as images

run_sql: Union[
    Callable[[str], pd.DataFrame], None
] = None  # Function to convert SQL to a Pandas DataFrame
"""
**Example**
```python
vn.run_sql = lambda sql: pd.read_sql(sql, engine)
```

Set the SQL to DataFrame function for Vanna.AI. This is used in the [`vn.ask(...)`][vanna.ask] function.
Instead of setting this directly you can also use [`vn.connect_to_snowflake(...)`][vanna.connect_to_snowflake] to set this.

"""

__org: Union[str, None] = None  # Organization name for Vanna.AI

_unauthenticated_endpoint = "https://ask.vanna.ai/unauthenticated_rpc"

def error_deprecation():
    raise Exception("""
Please switch to the following method for initializing Vanna:

from vanna.remote import VannaDefault

api_key = # Your API key from https://vanna.ai/account/profile 
vanna_model_name = # Your model name from https://vanna.ai/account/profile
                    
vn = VannaDefault(model=vanna_model_name, api_key=api_key)
""")

def __unauthenticated_rpc_call(method, params):
    headers = {
        "Content-Type": "application/json",
    }
    data = {"method": method, "params": [__dataclass_to_dict(obj) for obj in params]}

    response = requests.post(
        _unauthenticated_endpoint, headers=headers, data=json.dumps(data)
    )
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
    vanna_api_key = os.environ.get("VANNA_API_KEY", None)

    if vanna_api_key is not None:
        return vanna_api_key

    if email == "my-email@example.com":
        raise ValidationError(
            "Please replace 'my-email@example.com' with your email address."
        )

    if otp_code is None:
        params = [UserEmail(email=email)]

        d = __unauthenticated_rpc_call(method="send_otp", params=params)

        if "result" not in d:
            raise OTPCodeError("Error sending OTP code.")

        status = Status(**d["result"])

        if not status.success:
            raise OTPCodeError(f"Error sending OTP code: {status.message}")

        otp_code = input("Check your email for the code and enter it here: ")

    params = [UserOTP(email=email, otp=otp_code)]

    d = __unauthenticated_rpc_call(method="verify_otp", params=params)

    if "result" not in d:
        raise OTPCodeError("Error verifying OTP code.")

    key = ApiKey(**d["result"])

    if key is None:
        raise OTPCodeError("Error verifying OTP code.")

    api_key = key.key

    return api_key


def set_api_key(key: str) -> None:
    error_deprecation()


def get_models() -> List[str]:
    error_deprecation()


def create_model(model: str, db_type: str) -> bool:
    error_deprecation()


def add_user_to_model(model: str, email: str, is_admin: bool) -> bool:
    error_deprecation()


def update_model_visibility(public: bool) -> bool:
    error_deprecation()


def set_model(model: str):
    error_deprecation()


def add_sql(
    question: str, sql: str, tag: Union[str, None] = "Manually Trained"
) -> bool:
    error_deprecation()


def add_ddl(ddl: str) -> bool:
    error_deprecation()


def add_documentation(documentation: str) -> bool:
    error_deprecation()


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


def get_training_plan_postgres(
    filter_databases: Union[List[str], None] = None,
    filter_schemas: Union[List[str], None] = None,
    include_information_schema: bool = False,
    use_historical_queries: bool = True,
) -> TrainingPlan:
    error_deprecation()


def get_training_plan_generic(df) -> TrainingPlan:
    error_deprecation()


def get_training_plan_experimental(
    filter_databases: Union[List[str], None] = None,
    filter_schemas: Union[List[str], None] = None,
    include_information_schema: bool = False,
    use_historical_queries: bool = True,
) -> TrainingPlan:
    error_deprecation()


def train(
    question: str = None,
    sql: str = None,
    ddl: str = None,
    documentation: str = None,
    json_file: str = None,
    sql_file: str = None,
    plan: TrainingPlan = None,
) -> bool:
    error_deprecation()


def flag_sql_for_review(
    question: str, sql: Union[str, None] = None, error_msg: Union[str, None] = None
) -> bool:
    error_deprecation()


def remove_sql(question: str) -> bool:
    error_deprecation()


def remove_training_data(id: str) -> bool:
    error_deprecation()


def generate_sql(question: str) -> str:
    error_deprecation()


def get_related_training_data(question: str) -> TrainingData:
    error_deprecation()


def generate_meta(question: str) -> str:
    error_deprecation()


def generate_followup_questions(question: str, df: pd.DataFrame) -> List[str]:
    error_deprecation()


def generate_questions() -> List[str]:
    error_deprecation()


def ask(
    question: Union[str, None] = None,
    print_results: bool = True,
    auto_train: bool = True,
    generate_followups: bool = True,
) -> Union[
    Tuple[
        Union[str, None],
        Union[pd.DataFrame, None],
        Union[plotly.graph_objs.Figure, None],
        Union[List[str], None],
    ],
    None,
]:
    error_deprecation()

def generate_plotly_code(
    question: Union[str, None],
    sql: Union[str, None],
    df: pd.DataFrame,
    chart_instructions: Union[str, None] = None,
) -> str:
    error_deprecation()


def get_plotly_figure(
    plotly_code: str, df: pd.DataFrame, dark_mode: bool = True
) -> plotly.graph_objs.Figure:
    error_deprecation()


def get_results(cs, default_database: str, sql: str) -> pd.DataFrame:
    error_deprecation()


def generate_explanation(sql: str) -> str:
    error_deprecation()


def generate_question(sql: str) -> str:
    error_deprecation()


def get_all_questions() -> pd.DataFrame:
    error_deprecation()


def get_training_data() -> pd.DataFrame:
    error_deprecation()


def connect_to_sqlite(url: str):
    error_deprecation()


def connect_to_snowflake(
    account: str,
    username: str,
    password: str,
    database: str,
    schema: Union[str, None] = None,
    role: Union[str, None] = None,
):
    error_deprecation()


def connect_to_postgres(
    host: str = None,
    dbname: str = None,
    user: str = None,
    password: str = None,
    port: int = None,
):
    error_deprecation()


def connect_to_bigquery(cred_file_path: str = None, project_id: str = None):
    error_deprecation()

def connect_to_duckdb(url: str="memory", init_sql: str = None):
    error_deprecation()