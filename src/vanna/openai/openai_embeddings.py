from openai import OpenAI

from ..base import VannaBase


class OpenAI_Embeddings(VannaBase):
    def __init__(self, client=None, config=None):
        VannaBase.__init__(self, config=config)

        if client is not None:
            self.client = client
            return

        if self.client is not None:
            return

        self.client = OpenAI()

        if config is None:
            return

        if "api_type" in config:
            self.client.api_type = config["api_type"]

        if "api_base" in config:
            self.client.api_base = config["api_base"]

        if "api_version" in config:
            self.client.api_version = config["api_version"]

        if "api_key" in config:
            self.client.api_key = config["api_key"]

    def generate_embedding(self, data: str, **kwargs) -> list[float]:
        if self.config is not None and "engine" in self.config:
            embedding = self.client.embeddings.create(
                engine=self.config["engine"],
                input=data,
            )
        else:
            embedding = self.client.embeddings.create(
                model="text-embedding-ada-002",
                input=data,
            )

        return embedding.get("data")[0]["embedding"]
