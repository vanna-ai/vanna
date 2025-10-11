import qianfan

from ..base import VannaBase


class Qianfan_Chat(VannaBase):
  def __init__(self, client=None, config=None):
    VannaBase.__init__(self, config=config)

    if "api_key" not in config:
      raise Exception("Missing api_key in config")
    self.api_key = config["api_key"]

    if "secret_key" not in config:
      raise Exception("Missing secret_key in config")
    self.secret_key = config["secret_key"]

    # default parameters - can be overrided using config
    self.temperature = 0.9
    self.max_tokens = 1024

    if "temperature" in config:
      self.temperature = config["temperature"]

    if "max_tokens" in config:
      self.max_tokens = config["max_tokens"]

    self.model = config["model"] if "model" in config else "ERNIE-Speed"

    if client is not None:
      self.client = client
      return

    self.client = qianfan.ChatCompletion(ak=self.api_key,
                                         sk=self.secret_key)

  def system_message(self, message: str) -> any:
    return {"role": "system", "content": message}

  def user_message(self, message: str) -> any:
    return {"role": "user", "content": message}

  def assistant_message(self, message: str) -> any:
    return {"role": "assistant", "content": message}

  def get_sql_prompt(
    self,
    initial_prompt: str,
    question: str,
    question_sql_list: list,
    ddl_list: list,
    doc_list: list,
    **kwargs,
  ):
    """
    Example:
    ```python
    vn.get_sql_prompt(
        question="What are the top 10 customers by sales?",
        question_sql_list=[{"question": "What are the top 10 customers by sales?", "sql": "SELECT * FROM customers ORDER BY sales DESC LIMIT 10"}],
        ddl_list=["CREATE TABLE customers (id INT, name TEXT, sales DECIMAL)"],
        doc_list=["The customers table contains information about customers and their sales."],
    )

    ```

    This method is used to generate a prompt for the LLM to generate SQL.

    Args:
        question (str): The question to generate SQL for.
        question_sql_list (list): A list of questions and their corresponding SQL statements.
        ddl_list (list): A list of DDL statements.
        doc_list (list): A list of documentation.

    Returns:
        any: The prompt for the LLM to generate SQL.
    """

    if initial_prompt is None:
      initial_prompt = f"You are a {self.dialect} expert. " + \
                       "Please help to generate a SQL to answer the question based on some context.Please don't give any explanation for your answer. Just only generate a SQL \n"

    initial_prompt = self.add_ddl_to_prompt(
      initial_prompt, ddl_list, max_tokens=self.max_tokens
    )

    if self.static_documentation != "":
      doc_list.append(self.static_documentation)

    initial_prompt = self.add_documentation_to_prompt(
      initial_prompt, doc_list, max_tokens=self.max_tokens
    )
    message_log = []

    if question_sql_list is None or len(question_sql_list) == 0:
      initial_prompt = initial_prompt + f"question: {question}"
      message_log.append(self.user_message(initial_prompt))
    else:
      for i, example in question_sql_list:
        if example is None:
          print("example is None")
        else:
          if example is not None and "question" in example and "sql" in example:
            if i == 0:
              initial_prompt = initial_prompt + f"question: {example['question']}"
              message_log.append(self.user_message(initial_prompt))
            else:
              message_log.append(self.user_message(example["question"]))
            message_log.append(self.assistant_message(example["sql"]))

      message_log.append(self.user_message(question))
    return message_log

  def submit_prompt(self, prompt, **kwargs) -> str:
    if prompt is None:
      raise Exception("Prompt is None")

    if len(prompt) == 0:
      raise Exception("Prompt is empty")

    # Count the number of tokens in the message log
    # Use 4 as an approximation for the number of characters per token
    num_tokens = 0
    for message in prompt:
      num_tokens += len(message["content"]) / 4

    if kwargs.get("model", None) is not None:
      model = kwargs.get("model", None)
      print(
        f"Using model {model} for {num_tokens} tokens (approx)"
      )
      response = self.client.do(
        model=self.model,
        messages=prompt,
        max_output_tokens=self.max_tokens,
        stop=None,
        temperature=self.temperature,
      )
    elif self.config is not None and "model" in self.config:
      print(
        f"Using model {self.config['model']} for {num_tokens} tokens (approx)"
      )
      response = self.client.do(
        model=self.config.get("model"),
        messages=prompt,
        max_output_tokens=self.max_tokens,
        stop=None,
        temperature=self.temperature,
      )
    else:
      if num_tokens > 3500:
        model = "ERNIE-Speed-128K"
      else:
        model = "ERNIE-Speed-8K"

      print(f"Using model {model} for {num_tokens} tokens (approx)")
      response = self.client.do(
        model=model,
        messages=prompt,
        max_output_tokens=self.max_tokens,
        stop=None,
        temperature=self.temperature,
      )

    return response.body.get("result")
