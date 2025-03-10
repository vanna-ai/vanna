import dataclasses
import json
from io import StringIO
from typing import Callable, List, Tuple, Union

import pandas as pd
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
  StatusWithId,
  StringData,
  TrainingData,
  UserEmail,
  UserOTP,
  Visibility,
)
from .vannadb import VannaDB_VectorStore


class VannaDefault(VannaDB_VectorStore):
    """
    VannaDefault is a class that extends VannaDB_VectorStore and provides methods to interact with the Vanna AI system.
    Attributes:
        model (str): The model identifier for the Vanna AI.
        api_key (str): The API key for authenticating with the Vanna AI.
        config (dict, optional): Configuration dictionary for additional settings.
    Methods:
        __init__(model: str, api_key: str, config=None):
            Initializes the VannaDefault instance with the specified model, API key, and optional configuration.
        system_message(message: str) -> any:
            Creates a system message dictionary with the specified message content.
        user_message(message: str) -> any:
            Creates a user message dictionary with the specified message content.
        assistant_message(message: str) -> any:
            Creates an assistant message dictionary with the specified message content.
        submit_prompt(prompt, **kwargs) -> str:
            Submits a prompt to the Vanna AI system and returns the response as a string.
    """
    def __init__(self, model: str, api_key: str, config=None):
        """
        Initialize the remote Vanna model.
        Args:
            model (str): The model identifier.
            api_key (str): The API key for authentication.
            config (dict, optional): Configuration dictionary. Defaults to None.
        Attributes:
            _model (str): The model identifier.
            _api_key (str): The API key for authentication.
            _endpoint (str): The endpoint URL for the Vanna API.
        """
        VannaBase.__init__(self, config=config)
        VannaDB_VectorStore.__init__(self, vanna_model=model, vanna_api_key=api_key, config=config)

        self._model = model
        self._api_key = api_key

        self._endpoint = (
            "https://ask.vanna.ai/rpc"
            if config is None or "endpoint" not in config
            else config["endpoint"]
        )

    def system_message(self, message: str) -> any:
        """
        Creates a system message dictionary.

        Args:
            message (str): The content of the system message.

        Returns:
            dict: A dictionary with the role set to "system" and the content set to the provided message.
        """
        return {"role": "system", "content": message}

    def user_message(self, message: str) -> any:
        """
        Constructs a dictionary representing a user message.

        Args:
            message (str): The content of the user's message.

        Returns:
            dict: A dictionary with keys 'role' and 'content', where 'role' is set to 'user' and 'content' is set to the provided message.
        """
        return {"role": "user", "content": message}

    def assistant_message(self, message: str) -> any:
        """
        Constructs a dictionary representing an assistant message.

        Args:
            message (str): The message content from the assistant.

        Returns:
            dict: A dictionary with keys 'role' and 'content', where 'role' is set to 'assistant' and 'content' is the provided message.
        """
        return {"role": "assistant", "content": message}

    def submit_prompt(self, prompt, **kwargs) -> str:
        """
        Submits a prompt to a remote service and returns the result.
        Args:
            prompt (str): The prompt to be submitted.
            **kwargs: Additional keyword arguments.
        Returns:
            str: The result from the remote service, or None if the result is not present.
        """
        # JSON-ify the prompt
        json_prompt = json.dumps(prompt, ensure_ascii=False)

        params = [StringData(data=json_prompt)]

        d = self._rpc_call(method="submit_prompt", params=params)

        if "result" not in d:
            return None

        # Load the result into a dataclass
        results = StringData(**d["result"])

        return results.data
