import json
import re

from httpx import Timeout

from ..base import VannaBase
from ..exceptions import DependencyError


class Ollama(VannaBase):
  def __init__(self, config=None):

    try:
      ollama = __import__("ollama")
    except ImportError:
      raise DependencyError(
        "You need to install required dependencies to execute this method, run command:"
        " \npip install ollama"
      )

    if not config:
      raise ValueError("config must contain at least Ollama model")
    if 'model' not in config.keys():
      raise ValueError("config must contain at least Ollama model")
    self.host = config.get("ollama_host", "http://localhost:11434")
    self.model = config["model"]

    self.ollama_client = ollama.Client(self.host, timeout=Timeout(240.0))
    self.keep_alive = config.get('keep_alive', None)
    self.ollama_options = config.get('options', {})
    self.num_ctx = self.ollama_options.get('num_ctx', 2048)

  def system_message(self, message: str) -> any:
    return {"role": "system", "content": message}

  def user_message(self, message: str) -> any:
    return {"role": "user", "content": message}

  def assistant_message(self, message: str) -> any:
    return {"role": "assistant", "content": message}

  def extract_sql(self, llm_response):
    """
    Extracts the first SQL statement after the word 'select', ignoring case,
    matches until the first semicolon, three backticks, or the end of the string,
    and removes three backticks if they exist in the extracted string.

    Args:
    - llm_response (str): The string to search within for an SQL statement.

    Returns:
    - str: The first SQL statement found, with three backticks removed, or an empty string if no match is found.
    """
    # Remove ollama-generated extra characters
    llm_response = llm_response.replace("\\_", "_")
    llm_response = llm_response.replace("\\", "")

    # Regular expression to find 'select, with and ```sql' (ignoring case) and capture until ';', '```', [ (this happens in case of mistral) or end of string
    pattern = re.compile(r'(?:select|with|```sql).*?(?=;|\[|```|$)',
                         re.IGNORECASE | re.DOTALL)

    match = pattern.search(llm_response)
    if match:
      # Remove three backticks from the matched string if they exist
      return match.group(0).replace("```", "")
    else:
      return llm_response

  def __pull_model_if_ne(self, ):
    model_response = self.ollama_client.list()
    model_lists = [model_element['model'] for model_element in
                   model_response.get('models', [])]
    if self.model not in model_lists:
      self.log(f"Pulling model {self.model}....")
      self.ollama_client.pull(self.model)

  def submit_prompt(self, prompt, **kwargs) -> str:
    self.log(
      f"Ollama parameters:\n"
      f"model={self.model},\n"
      f"options={self.ollama_options},\n"
      f"keep_alive={self.keep_alive}")
    self.log(f"Prompt Content:\n{json.dumps(prompt)}")
    self.__pull_model_if_ne()
    response_dict = self.ollama_client.chat(model=self.model,
                                            messages=prompt,
                                            stream=False,
                                            options=self.ollama_options,
                                            keep_alive=self.keep_alive)

    self.log(f"Ollama Response:\n{str(response_dict)}")

    return response_dict['message']['content']
