import json
import re

from httpx import Timeout

from ..base import VannaBase
from ..exceptions import DependencyError


class LMStudio(VannaBase):
  def __init__(self, config=None):

    try:
      lmstudio = __import__("lmstudio")
    except ImportError:
      raise DependencyError(
        "You need to install required dependencies to execute this method,"
        " run command:\npip install lmstudio"
      )

    if not config:
      raise ValueError("config must contain at least model name")
    if 'model' not in config.keys():
      raise ValueError("config must contain at least model name")

    self.host = config.get("lmstudio_host", "http://localhost:1234/v1")
    self.model = config.get("model", "default")
    self.lmstudio_timeout = config.get("lmstudio_timeout", 240.0)

    # Initialize client without timeout parameter since it's not supported
    self.lmstudio_client = lmstudio.Client(self.host)
    self.lmstudio_options = config.get('options', {})
    self.temperature = self.lmstudio_options.get('temperature', 0.1)
    self.max_tokens = self.lmstudio_options.get('max_tokens', 4096)

    # Load context settings if provided
    self.context_length = self.lmstudio_options.get('contextLength', 4096)
    self.gpu_offload = self.lmstudio_options.get('gpuOffload', 1.0)

    # Check if model is loaded or load it if not available
    self.__pull_model_if_ne(self.lmstudio_client, self.model)

  @staticmethod
  def __pull_model_if_ne(lmstudio_client, model):
    """
    Ensures the specified model is loaded in LM Studio.
    If the model is not already loaded, it will load it.

    Args:
        lmstudio_client: The LM Studio client
        model: The model identifier to load
    """
    try:
      # Get list of loaded models
      loaded_models = lmstudio_client.llm.list_loaded()
      model_names = [loaded_model.key for loaded_model in loaded_models]

      # If model is not loaded, load it with default settings
      if model not in model_names:
        lmstudio_client.llm.model(model, config={
          "contextLength": 4096,  # Default context length
          "gpuOffload": 1.0       # Default GPU offload setting
        })
    except Exception as e:
      # Log error but don't fail, as the model might be loaded via GUI
      print(f"Warning: Could not verify model '{model}' is loaded: {str(e)}")

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
    - str: The first SQL statement found, with three backticks removed,
      or an empty string if no match is found.
    """
    # Regular expression to find ```sql' and capture until '```'
    sql = re.search(r"```sql\n((.|\n)*?)(?=;|\[|```)", llm_response, re.DOTALL)
    # Regular expression to find 'select, with (ignoring case) and
    # capture until ';', or end of string
    select_with = re.search(
      r'(select|(with.*?as \())(.*?)(?=;|\[|```)',
      llm_response,
      re.IGNORECASE | re.DOTALL
    )
    if sql:
      self.log(
        f"Output from LLM: {llm_response} \nExtracted SQL: {sql.group(1)}")
      return sql.group(1).replace("```", "")
    elif select_with:
      self.log(
        f"Output from LLM: {llm_response} \nExtracted SQL: {select_with.group(0)}")
      return select_with.group(0)
    else:
      return llm_response

  def submit_prompt(self, prompt, **kwargs) -> str:
    self.log(
      f"LMStudio parameters:\n"
      f"model={self.model},\n"
      f"temperature={self.temperature},\n"
      f"max_tokens={self.max_tokens}")
    self.log(f"Prompt Content:\n{json.dumps(prompt, ensure_ascii=False)}")

    response_dict = self.lmstudio_client.chat.completions.create(
      model=self.model,
      messages=prompt,
      temperature=self.temperature,
      max_tokens=self.max_tokens
    )

    self.log(f"LMStudio Response:\n{str(response_dict)}")

    return response_dict.choices[0].message.content
