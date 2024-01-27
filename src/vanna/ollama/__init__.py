from ..base import VannaBase
import requests
import json

class Ollama(VannaBase):
    def __init__(self, config=None):
        if config is None or 'ollama_host' not in config:
            self.host = "http://localhost:11434"
        else:
            self.host = config['ollama_host']

        if config is None or 'model' not in config:
            raise ValueError("config must contain a Ollama model")
        else:
            self.model = config['model']

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
        url = f"{self.host}/api/chat"
        data = {
            "model": self.model,
            "stream": False,
            "messages": prompt,
        }

        response = requests.post(url, json=data)

        response_dict = response.json()

        self.log(response.text)
        
        return response_dict['message']['content']

