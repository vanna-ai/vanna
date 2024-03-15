import re

from vertexai.language_models import ChatModel

from ..base import VannaBase


class Palm(VannaBase):
    def __init__(self, client=None, config=None):
        VannaBase.__init__(self, config=config)

        if client is not None:
            self.client = client
            return

        # default values for params
        self.temperature = 0.7
        self.max_tokens = 500
        self.top_p = 0.95
        self.top_k = 40

        if config is None:
            raise ValueError("config must be provided for Bison")

        if "api_key" not in config:
            raise ValueError("config must contain a Bison api_key")

        if "model" not in config:
            raise ValueError("config must contain a Bison model")

        if client is None:
            self.client = ChatModel.from_pretrained(config["model"])
        else:
            self.client = client

        if "temperature" in config:
            self.temperature = config["temperature"]

        if "max_tokens" in config:
            self.max_tokens = config["max_tokens"]

        if "top_p" in config:
            self.top_p = config["top_p"]

        if "top_k" in config:
            self.top_k = config["top_k"]

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
        params = {
            "temperature": self.temperature,
            "max_output_tokens": self.max_tokens,
            "top_p": self.top_p,
            "top_k": self.top_k,
        }
        response = self.client.send_message(prompt, **params)

        self.log(response.text)

        return response.text
