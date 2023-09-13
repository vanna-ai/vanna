from abc import abstractmethod

import openai

from ..base import VannaBase


class OpenAI_Embeddings(VannaBase):
    def __init__(self, config=None):
        VannaBase.__init__(self, config=config)

        if config is None:
            return

        if "api_type" in config:
            openai.api_type = config["api_type"]

        if "api_base" in config:
            openai.api_base = config["api_base"]

        if "api_version" in config:
            openai.api_version = config["api_version"]

        if "api_key" in config:
            openai.api_key = config["api_key"]

    def generate_embedding(self, data: str, **kwargs) -> list[float]:
        if self.config is not None and "engine" in self.config:
            embedding = openai.Embedding.create(
                engine=self.config["engine"],
                input=data,
            )
        else:
            embedding = openai.Embedding.create(
                model="text-embedding-ada-002",
                input=data,
            )

        return embedding.get("data")[0]["embedding"]
