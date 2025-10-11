from typing import List
from zhipuai import ZhipuAI
from chromadb import Documents, EmbeddingFunction, Embeddings
from ..base import VannaBase

class ZhipuAI_Embeddings(VannaBase):
    """
    [future functionality] This function is used to generate embeddings from ZhipuAI.

    Args:
        VannaBase (_type_): _description_
    """
    def __init__(self, config=None):
        VannaBase.__init__(self, config=config)
        if "api_key" not in config:
            raise Exception("Missing api_key in config")
        self.api_key = config["api_key"]
        self.client = ZhipuAI(api_key=self.api_key)

    def generate_embedding(self, data: str, **kwargs) -> List[float]:
        
        embedding = self.client.embeddings.create(
            model="embedding-2",
            input=data,
        )

        return embedding.data[0].embedding
    


class ZhipuAIEmbeddingFunction(EmbeddingFunction[Documents]):
    """
    A embeddingFunction that uses ZhipuAI to generate embeddings which can use in chromadb.
    usage: 
    class MyVanna(ChromaDB_VectorStore, ZhipuAI_Chat):
        def __init__(self, config=None):
            ChromaDB_VectorStore.__init__(self, config=config)
            ZhipuAI_Chat.__init__(self, config=config)
    
    config={'api_key': 'xxx'}
    zhipu_embedding_function = ZhipuAIEmbeddingFunction(config=config)
    config = {"api_key": "xxx", "model": "glm-4","path":"xy","embedding_function":zhipu_embedding_function}
    
    vn = MyVanna(config)
    
    """
    def __init__(self, config=None):
        if config is None or "api_key" not in config:
            raise ValueError("Missing 'api_key' in config")
        
        self.api_key = config["api_key"]
        self.model_name = config.get("model_name", "embedding-2")
        
        try:
            self.client = ZhipuAI(api_key=self.api_key)
        except Exception as e:
            raise ValueError(f"Error initializing ZhipuAI client: {e}")

    def __call__(self, input: Documents) -> Embeddings:
        # Replace newlines, which can negatively affect performance.
        input = [t.replace("\n", " ") for t in input]
        all_embeddings = []
        print(f"Generating embeddings for {len(input)} documents")

        # Iterating over each document for individual API calls
        for document in input:
            try:
                response = self.client.embeddings.create(
                    model=self.model_name,
                    input=document
                )
                # print(response)
                embedding = response.data[0].embedding
                all_embeddings.append(embedding)
                # print(f"Cost required: {response.usage.total_tokens}")
            except Exception as e:
                raise ValueError(f"Error generating embedding for document: {e}")

        return all_embeddings