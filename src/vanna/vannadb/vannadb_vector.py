import dataclasses
import json
from io import StringIO

import pandas as pd
import requests

from ..base import VannaBase
from ..types import (
    DataFrameJSON,
    Question,
    QuestionSQLPair,
    Status,
    StatusWithId,
    StringData,
    TrainingData,
)


class VannaDB_VectorStore(VannaBase):
    def __init__(self, vanna_model: str, vanna_api_key: str, config=None):
        VannaBase.__init__(self, config=config)

        self._model = vanna_model
        self._api_key = vanna_api_key

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
        self.related_training_data = {}

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
            raise Exception(f"Error removing training data")

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
