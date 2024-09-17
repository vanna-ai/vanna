import dataclasses
import json
from io import StringIO

import pandas as pd
import requests

from ..advanced import VannaAdvanced
from ..base import VannaBase
from ..types import (
  DataFrameJSON,
  NewOrganization,
  OrganizationList,
  Question,
  QuestionSQLPair,
  Status,
  StatusWithId,
  StringData,
  TrainingData,
)
from ..utils import sanitize_model_name


class VannaDB_VectorStore(VannaBase, VannaAdvanced):
    def __init__(self, vanna_model: str, vanna_api_key: str, config=None):
        VannaBase.__init__(self, config=config)

        self._model = vanna_model
        self._api_key = vanna_api_key

        self._endpoint = (
            "https://ask.vanna.ai/rpc"
            if config is None or "endpoint" not in config
            else config["endpoint"]
        )
        self.related_training_data = {}
        self._graphql_endpoint = "https://functionrag.com/query"
        self._graphql_headers = {
            "Content-Type": "application/json",
            "API-KEY": self._api_key,
            "NAMESPACE": self._model,
        }

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

    def get_all_functions(self) -> list:
        query = """
            {
                get_all_sql_functions {
                    function_name
                    description
                    post_processing_code_template
                    arguments {
                        name
                        description
                        general_type
                        is_user_editable
                        available_values
                    }
                    sql_template
                }
            }
        """

        response = requests.post(self._graphql_endpoint, headers=self._graphql_headers, json={'query': query})
        response_json = response.json()
        if response.status_code == 200 and 'data' in response_json and 'get_all_sql_functions' in response_json['data']:
            self.log(response_json['data']['get_all_sql_functions'])
            resp = response_json['data']['get_all_sql_functions']

            print(resp)

            return resp
        else:
            raise Exception(f"Query failed to run by returning code of {response.status_code}. {response.text}")


    def get_function(self, question: str, additional_data: dict = {}) -> dict:
        query = """
        query GetFunction($question: String!, $staticFunctionArguments: [StaticFunctionArgument]) {
            get_and_instantiate_function(question: $question, static_function_arguments: $staticFunctionArguments) {
                ... on SQLFunction {
                function_name
                description
                post_processing_code_template
                instantiated_post_processing_code
                arguments {
                    name
                    description
                    general_type
                    is_user_editable
                    instantiated_value
                    available_values
                }
                sql_template
                instantiated_sql
            }
            }
        }
        """
        static_function_arguments = [{"name": key, "value": str(value)} for key, value in additional_data.items()]
        variables = {"question": question, "staticFunctionArguments": static_function_arguments}
        response = requests.post(self._graphql_endpoint, headers=self._graphql_headers, json={'query': query, 'variables': variables})
        response_json = response.json()
        if response.status_code == 200 and 'data' in response_json and 'get_and_instantiate_function' in response_json['data']:
            self.log(response_json['data']['get_and_instantiate_function'])
            resp = response_json['data']['get_and_instantiate_function']

            print(resp)

            return resp
        else:
            raise Exception(f"Query failed to run by returning code of {response.status_code}. {response.text}")

    def create_function(self, question: str, sql: str, plotly_code: str, **kwargs) -> dict:
        query = """
        mutation CreateFunction($question: String!, $sql: String!, $plotly_code: String!) {
            generate_and_create_sql_function(question: $question, sql: $sql, post_processing_code: $plotly_code) {
                function_name
                description
                arguments {
                    name
                    description
                    general_type
                    is_user_editable
                }
                sql_template
                post_processing_code_template
            }
        }
        """
        variables = {"question": question, "sql": sql, "plotly_code": plotly_code}
        response = requests.post(self._graphql_endpoint, headers=self._graphql_headers, json={'query': query, 'variables': variables})
        response_json = response.json()
        if response.status_code == 200 and 'data' in response_json and response_json['data'] is not None and 'generate_and_create_sql_function' in response_json['data']:
            resp = response_json['data']['generate_and_create_sql_function']

            print(resp)

            return resp
        else:
            raise Exception(f"Query failed to run by returning code of {response.status_code}. {response.text}")

    def update_function(self, old_function_name: str, updated_function: dict) -> bool:
        """
        Update an existing SQL function based on the provided parameters.

        Args:
            old_function_name (str): The current name of the function to be updated.
            updated_function (dict): A dictionary containing the updated function details. Expected keys:
                - 'function_name': The new name of the function.
                - 'description': The new description of the function.
                - 'arguments': A list of dictionaries describing the function arguments.
                - 'sql_template': The new SQL template for the function.
                - 'post_processing_code_template': The new post-processing code template.

        Returns:
            bool: True if the function was successfully updated, False otherwise.
        """
        mutation = """
        mutation UpdateSQLFunction($input: SQLFunctionUpdate!) {
            update_sql_function(input: $input)
        }
        """

        SQLFunctionUpdate = {
            'function_name', 'description', 'arguments', 'sql_template', 'post_processing_code_template'
        }

        # Define the expected keys for each argument in the arguments list
        ArgumentKeys = {'name', 'general_type', 'description', 'is_user_editable', 'available_values'}

        # Function to validate and transform arguments
        def validate_arguments(args):
            return [
                {key: arg[key] for key in arg if key in ArgumentKeys}
                for arg in args
            ]

        # Keep only the keys that conform to the SQLFunctionUpdate GraphQL input type
        updated_function = {key: value for key, value in updated_function.items() if key in SQLFunctionUpdate}

        # Special handling for 'arguments' to ensure they conform to the spec
        if 'arguments' in updated_function:
            updated_function['arguments'] = validate_arguments(updated_function['arguments'])

        variables = {
            "input": {
                "old_function_name": old_function_name,
                **updated_function
            }
        }

        print("variables", variables)

        response = requests.post(self._graphql_endpoint, headers=self._graphql_headers, json={'query': mutation, 'variables': variables})
        response_json = response.json()
        if response.status_code == 200 and 'data' in response_json and response_json['data'] is not None and 'update_sql_function' in response_json['data']:
            return response_json['data']['update_sql_function']
        else:
            raise Exception(f"Mutation failed to run by returning code of {response.status_code}. {response.text}")

    def delete_function(self, function_name: str) -> bool:
        mutation = """
        mutation DeleteSQLFunction($function_name: String!) {
            delete_sql_function(function_name: $function_name)
        }
        """
        variables = {"function_name": function_name}
        response = requests.post(self._graphql_endpoint, headers=self._graphql_headers, json={'query': mutation, 'variables': variables})
        response_json = response.json()
        if response.status_code == 200 and 'data' in response_json and response_json['data'] is not None and 'delete_sql_function' in response_json['data']:
            return response_json['data']['delete_sql_function']
        else:
            raise Exception(f"Mutation failed to run by returning code of {response.status_code}. {response.text}")

    def create_model(self, model: str, **kwargs) -> bool:
        """
        **Example:**
        ```python
        success = vn.create_model("my_model")
        ```
        Create a new model.

        Args:
            model (str): The name of the model to create.

        Returns:
            bool: True if the model was created, False otherwise.
        """
        model = sanitize_model_name(model)
        params = [NewOrganization(org_name=model, db_type="")]

        d = self._rpc_call(method="create_org", params=params)

        if "result" not in d:
            return False

        status = Status(**d["result"])

        return status.success

    def get_models(self) -> list:
        """
        **Example:**
        ```python
        models = vn.get_models()
        ```

        List the models that belong to the user.

        Returns:
            List[str]: A list of model names.
        """
        d = self._rpc_call(method="list_my_models", params=[])

        if "result" not in d:
            return []

        orgs = OrganizationList(**d["result"])

        return orgs.organizations

    def generate_embedding(self, data: str, **kwargs) -> list[float]:
        # This is done server-side
        pass

    def add_question_sql(self, question: str, sql: str, **kwargs) -> str:
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

    def add_ddl(self, ddl: str, **kwargs) -> str:
        params = [StringData(data=ddl)]

        d = self._rpc_call(method="add_ddl", params=params)

        if "result" not in d:
            raise Exception("Error adding DDL", d)

        status = StatusWithId(**d["result"])

        return status.id

    def add_documentation(self, documentation: str, **kwargs) -> str:
        params = [StringData(data=documentation)]

        d = self._rpc_call(method="add_documentation", params=params)

        if "result" not in d:
            raise Exception("Error adding documentation", d)

        status = StatusWithId(**d["result"])

        return status.id

    def get_training_data(self, **kwargs) -> pd.DataFrame:
        params = []

        d = self._rpc_call(method="get_training_data", params=params)

        if "result" not in d:
            return None

        # Load the result into a dataclass
        training_data = DataFrameJSON(**d["result"])

        df = pd.read_json(StringIO(training_data.data))

        return df

    def remove_training_data(self, id: str, **kwargs) -> bool:
        params = [StringData(data=id)]

        d = self._rpc_call(method="remove_training_data", params=params)

        if "result" not in d:
            raise Exception("Error removing training data")

        status = Status(**d["result"])

        if not status.success:
            raise Exception(f"Error removing training data: {status.message}")

        return status.success

    def get_related_training_data_cached(self, question: str) -> TrainingData:
        params = [Question(question=question)]

        d = self._rpc_call(method="get_related_training_data", params=params)

        if "result" not in d:
            return None

        # Load the result into a dataclass
        training_data = TrainingData(**d["result"])

        self.related_training_data[question] = training_data

        return training_data

    def get_similar_question_sql(self, question: str, **kwargs) -> list:
        if question in self.related_training_data:
            training_data = self.related_training_data[question]
        else:
            training_data = self.get_related_training_data_cached(question)

        return training_data.questions

    def get_related_ddl(self, question: str, **kwargs) -> list:
        if question in self.related_training_data:
            training_data = self.related_training_data[question]
        else:
            training_data = self.get_related_training_data_cached(question)

        return training_data.ddl

    def get_related_documentation(self, question: str, **kwargs) -> list:
        if question in self.related_training_data:
            training_data = self.related_training_data[question]
        else:
            training_data = self.get_related_training_data_cached(question)

        return training_data.documentation
