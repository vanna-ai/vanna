import re

import requests

from ..base import VannaBase


class Vllm(VannaBase):
    def __init__(self, config=None):
        if config is None or "vllm_host" not in config:
            self.host = "http://localhost:8000"
        else:
            self.host = config["vllm_host"]

        if config is None or "model" not in config:
            raise ValueError("check the config for vllm")
        else:
            self.model = config["model"]

        if "auth-key" in config:
            self.auth_key = config["auth-key"]
        else:
            self.auth_key = None

        if "temperature" in config:
            self.temperature = config["temperature"]
        else:
            # default temperature - can be overrided using config
            self.temperature = 0.7

    def system_message(self, message: str) -> any:
        return {"role": "system", "content": message}

    def user_message(self, message: str) -> any:
        return {"role": "user", "content": message}

    def assistant_message(self, message: str) -> any:
        return {"role": "assistant", "content": message}

    def extract_sql_query(self, text):
        """
        Extracts the first SQL statement after the word 'select', ignoring case,
        matches until the first semicolon, three backticks, or the end of the string,
        and removes three backticks if they exist in the extracted string.

        Args:
        - text (str): The string to search within for an SQL statement.

        Returns:
        - str: The first SQL statement found, with three backticks removed, or an empty string if no match is found.
        """
        # Regular expression to find 'select' (ignoring case) and capture until ';', '```', or end of string
        pattern = re.compile(r"select.*?(?:;|```|$)", re.IGNORECASE | re.DOTALL)

        match = pattern.search(text)
        if match:
            # Remove three backticks from the matched string if they exist
            return match.group(0).replace("```", "")
        else:
            return text

    def generate_sql(self, question: str, **kwargs) -> str:
        # Use the super generate_sql
        sql = super().generate_sql(question, **kwargs)

        # Replace "\_" with "_"
        sql = sql.replace("\\_", "_")

        sql = sql.replace("\\", "")

        return self.extract_sql_query(sql)

    def submit_prompt(self, prompt, **kwargs) -> str:
        url = f"{self.host}/v1/chat/completions"
        data = {
            "model": self.model,
            "temperature": self.temperature,
            "stream": False,
            "messages": prompt,
        }

        if self.auth_key is not None:
            headers = { 
            'Content-Type': 'application/json', 
            'Authorization': f'Bearer {self.auth_key}' 
            }

            response = requests.post(url, headers=headers,json=data)


        else:
            response = requests.post(url, json=data)

        response_dict = response.json()

        self.log(response.text)

        return response_dict['choices'][0]['message']['content']
