import qianfan

from ..base import VannaBase


class Qianfan_Embeddings(VannaBase):
  def __init__(self, client=None, config=None):
    VannaBase.__init__(self, config=config)

    if client is not None:
      self.client = client
      return

    if "api_key" not in config:
      raise Exception("Missing api_key in config")
    self.api_key = config["api_key"]

    if "secret_key" not in config:
      raise Exception("Missing secret_key in config")
    self.secret_key = config["secret_key"]

    self.client = qianfan.Embedding(ak=self.api_key, sk=self.secret_key)

    self.embedding_cache = {
      'question': None,
      'embedding': None
    }

  def generate_embedding(self, data: str, **kwargs) -> list[float]:
    if self.embedding_cache['question'] == data:
        return self.embedding_cache['embedding'].get("data")[0]["embedding"]
    else:
        if self.config is not None and "model" in self.config:
          embedding = self.client.do(
            model=self.config["model"],
            input=[data],
          )
        else:
          embedding = self.client.do(
            model="bge-large-zh",
            input=[data],
          )
        self.embedding_cache['question'] = data
        self.embedding_cache['embedding'] = embedding

        return embedding.get("data")[0]["embedding"]
