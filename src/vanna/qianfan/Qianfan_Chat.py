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

    if config is None and client is None:
      self.client = qianfan.ChatCompletion(model=self.model, access_key=self.api_key, secret_key=self.secret_key)
      return

  def system_message(self, message: str) -> any:
    return {"role": "system", "content": message}

  def user_message(self, message: str) -> any:
    return {"role": "user", "content": message}

  def assistant_message(self, message: str) -> any:
    return {"role": "assistant", "content": message}

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
