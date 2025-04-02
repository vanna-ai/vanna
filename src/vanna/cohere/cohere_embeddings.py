import os

from openai import OpenAI

from ..base import VannaBase


class Cohere_Embeddings(VannaBase):
    def __init__(self, client=None, config=None):
        VannaBase.__init__(self, config=config)
        
        # Default embedding model
        self.model = "embed-multilingual-v3.0"
        
        if config is not None and "model" in config:
            self.model = config["model"]

        if client is not None:
            self.client = client
            return

        if config is None and client is None:
            self.client = OpenAI(
                base_url="https://api.cohere.ai/compatibility/v1",
                api_key=os.getenv("COHERE_API_KEY"),
            )
            return

        if "api_key" in config:
            self.client = OpenAI(
                base_url="https://api.cohere.ai/compatibility/v1",
                api_key=config["api_key"],
            )

    def generate_embedding(self, data: str, **kwargs) -> list[float]:
        # Use model from kwargs, config, or default
        model = kwargs.get("model", self.model)
        if self.config is not None and "model" in self.config and model == self.model:
            model = self.config["model"]
            
        embedding = self.client.embeddings.create(
            model=model,
            input=data,
            encoding_format="float",  # Ensure we get float values
        )

        return embedding.data[0].embedding 