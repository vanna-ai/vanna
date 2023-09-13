import dataclasses
import json
from typing import Callable, List, Tuple, Union

import requests

from .base import VannaBase
from .types import (
    AccuracyStats,
    ApiKey,
    DataFrameJSON,
    DataResult,
    Explanation,
    FullQuestionDocument,
    NewOrganization,
    NewOrganizationMember,
    Organization,
    OrganizationList,
    PlotlyResult,
    Question,
    QuestionCategory,
    QuestionId,
    QuestionList,
    QuestionSQLPair,
    QuestionStringList,
    SQLAnswer,
    Status,
    StringData,
    TrainingData,
    UserEmail,
    UserOTP,
    Visibility,
)


class VannaDefault(VannaBase):
    def __init__(self, model: str, api_key: str, config=None):
        VannaBase.__init__(self, config=config)

        self._model = model
        self._api_key = api_key

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


v = VannaDefault()
