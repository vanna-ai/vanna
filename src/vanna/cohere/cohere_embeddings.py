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

        # Check for API key in environment variable
        api_key = os.getenv("COHERE_API_KEY")
        
        # Check for API key in config
        if config is not None and "api_key" in config:
            api_key = config["api_key"]
            
        # Validate API key
        if not api_key:
            raise ValueError("Cohere API key is required. Please provide it via config or set the COHERE_API_KEY environment variable.")
            
        # Initialize client with validated API key
        self.client = OpenAI(
            base_url="https://api.cohere.ai/compatibility/v1",
            api_key=api_key,
        )

    def generate_embedding(self, data: str, **kwargs) -> list[float]:
        if not data:
            raise ValueError("Cannot generate embedding for empty input data")
            
        # Use model from kwargs, config, or default
        model = kwargs.get("model", self.model)
        if self.config is not None and "model" in self.config and model == self.model:
            model = self.config["model"]
        
        try:    
            embedding = self.client.embeddings.create(
                model=model,
                input=data,
                encoding_format="float",  # Ensure we get float values
            )
            
            # Check if response has expected structure
            if not embedding or not hasattr(embedding, 'data') or not embedding.data:
                raise ValueError("Received empty or malformed embedding response from API")
                
            if not embedding.data[0] or not hasattr(embedding.data[0], 'embedding'):
                raise ValueError("Embedding response is missing expected 'embedding' field")
                
            if not embedding.data[0].embedding:
                raise ValueError("Received empty embedding vector")
                
            return embedding.data[0].embedding
            
        except Exception as e:
            # Log the error and raise a more informative exception
            error_msg = f"Error generating embedding with Cohere: {str(e)}"
            print(error_msg)
            raise Exception(error_msg) 