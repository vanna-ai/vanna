import os

from mistralai import Mistral as MistralClient
from mistralai import UserMessage

from ..base import VannaBase


class Mistral(VannaBase):
    def __init__(self, config=None):
        if config is None:
            raise ValueError(
                "For Mistral, config must be provided with an api_key and model"
            )

        if "api_key" not in config:
            raise ValueError("config must contain a Mistral api_key")

        if "model" not in config:
            raise ValueError("config must contain a Mistral model")

        api_key = config["api_key"]
        model = config["model"]
        self.client = MistralClient(api_key=api_key)
        self.model = model

    def system_message(self, message: str) -> any:
        return {"role": "system", "content": message}

    def user_message(self, message: str) -> any:
        return {"role": "user", "content": message}

    def assistant_message(self, message: str) -> any:
        return {"role": "assistant", "content": message}

    def generate_sql(self, question: str, **kwargs) -> str:
        # Use the super generate_sql
        sql = super().generate_sql(question, **kwargs)

        # Replace "\_" with "_"
        sql = sql.replace("\\_", "_")

        return sql

    def submit_prompt(self, prompt, **kwargs) -> str:
        chat_response = self.client.chat.complete(
            model=self.model,
            messages=prompt,
        )

        return chat_response.choices[0].message.content
