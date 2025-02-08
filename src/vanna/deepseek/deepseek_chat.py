import os

from openai import OpenAI

from ..base import VannaBase



# from vanna.chromadb import ChromaDB_VectorStore

# class DeepSeekVanna(ChromaDB_VectorStore, DeepSeekChat):
#     def __init__(self, config=None):
#         ChromaDB_VectorStore.__init__(self, config=config)
#         DeepSeekChat.__init__(self, config=config)

# vn = DeepSeekVanna(config={"api_key": "sk-************", "model": "deepseek-chat"})


class DeepSeekChat(VannaBase):
    def __init__(self, config=None):
        if config is None:
            raise ValueError(
                "For DeepSeek, config must be provided with an api_key and model"
            )
        if "api_key" not in config:
            raise ValueError("config must contain a DeepSeek api_key")

        if "model" not in config:
            raise ValueError("config must contain a DeepSeek model")
    
        api_key = config["api_key"]
        model = config["model"]
        self.model = model
        self.client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com/v1")
        
    def system_message(self, message: str) -> any:
        return {"role": "system", "content": message}

    def user_message(self, message: str) -> any:
        return {"role": "user", "content": message}

    def assistant_message(self, message: str) -> any:
        return {"role": "assistant", "content": message}

    def generate_sql(self, question: str, **kwargs) -> str:
        # 使用父类的 generate_sql
        sql = super().generate_sql(question, **kwargs)
        
        # 替换 "\_" 为 "_"
        sql = sql.replace("\\_", "_")
        
        return sql

    def submit_prompt(self, prompt, **kwargs) -> str:
        chat_response = self.client.chat.completions.create(
            model=self.model,
            messages=prompt,
        )
        
        return chat_response.choices[0].message.content
