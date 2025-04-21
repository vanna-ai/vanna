import os
from abc import ABC
from typing import Any
from openai import OpenAI, DEFAULT_MAX_RETRIES
from ..base import VannaBase

class OpenAI_Chat(VannaBase, ABC):

    temperature : float = 0
    client : Any = None
    model : str = "gpt-3.5-turbo"
    max_retries : int = DEFAULT_MAX_RETRIES

    def __init__(self, client=None, config=None):
        VannaBase.__init__(self, config=config)

        # default parameters - can be override using config
        self.temperature = 0

        # default max_tokens - can be override using config
        if "temperature" in config:
            self.temperature = config["temperature"]

        # default model - can be override using config
        if "model" in config:
            self.model = config["model"]

        if "max_retries" in config:
            self.max_retries = config["max_retries"]

        if "api_type" in config:
            raise Exception(
                "Passing api_type is now deprecated. Please pass an OpenAI client instead."
            )

        if "api_base" in config:
            raise Exception(
                "Passing api_base is now deprecated. Please pass an OpenAI client instead."
            )

        if "api_version" in config:
            raise Exception(
                "Passing api_version is now deprecated. Please pass an OpenAI client instead."
            )

        if client is not None:
            self.client = client
            return

        if config is None and client is None:
            self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"),
                                 max_retries = self.max_retries)
            return

        if "api_key" in config:
            self.client = OpenAI(api_key=config["api_key"],
                                 max_retries = self.max_retries)

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
            # claude required system message is a single filed
            response = self.client.chat.completions.create(
                model=model,
                messages=prompt,
                stop=None,
                temperature=self.temperature,
            )
        elif kwargs.get("engine", None) is not None:
            engine = kwargs.get("engine", None)
            print(
                f"Using model {engine} for {num_tokens} tokens (approx)"
            )
            response = self.client.chat.completions.create(
                engine=engine,
                messages=prompt,
                stop=None,
                temperature=self.temperature,
            )
        elif self.config is not None and "engine" in self.config:
            print(
                f"Using engine {self.config['engine']} for {num_tokens} tokens (approx)"
            )
            # claude required system message is a single filed
            response = self.client.chat.completions.create(
                engine=self.config["engine"],
                messages=prompt,
                stop=None,
                temperature=self.temperature,
            )
        elif self.config is not None and "model" in self.config:
            print(
                f"Using model {self.config['model']} for {num_tokens} tokens (approx)"
            )
            # claude required system message is a single filed
            response = self.client.chat.completions.create(
                model=self.config["model"],
                messages=prompt,
                stop=None,
                temperature=self.temperature,
            )
        else:

            # Default to gpt-3.5-turbo if no model is specified
            if self.model is None:
              if num_tokens > 3500:
                  model = "gpt-3.5-turbo-16k"
              else:
                  model = "gpt-3.5-turbo"
            else:
              model = self.model

            print(f"Using model {model} for {num_tokens} tokens (approx)")
            response = self.client.chat.completions.create(
                model=model,
                messages=prompt,
                stop=None,
                temperature=self.temperature,
            )

        # Find the first response from the chatbot that has text in it (some responses may not have text)
        for choice in response.choices:
            if "text" in choice:
                return choice.text

        # If no response with text is found, return the first response's content (which may be empty)
        return response.choices[0].message.content
