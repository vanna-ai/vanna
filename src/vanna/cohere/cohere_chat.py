import os

from openai import OpenAI

from ..base import VannaBase


class Cohere_Chat(VannaBase):
    def __init__(self, client=None, config=None):
        VannaBase.__init__(self, config=config)

        # default parameters - can be overridden using config
        self.temperature = 0.2  # Lower temperature for more precise SQL generation
        self.model = "command-a-03-2025"  # Cohere's default model

        if config is not None:
            if "temperature" in config:
                self.temperature = config["temperature"]
            if "model" in config:
                self.model = config["model"]

        if client is not None:
            self.client = client
            return

        if config is None and client is None:
            self.client = OpenAI(
                base_url="https://api.cohere.ai/compatibility/v1",
                api_key=os.getenv("COHERE_API_KEY"),
            )
            return

        if "api_key" in config:
            self.client = OpenAI(
                base_url="https://api.cohere.ai/compatibility/v1",
                api_key=config["api_key"],
            )

    def system_message(self, message: str) -> any:
        return {"role": "developer", "content": message}  # Cohere uses 'developer' for system role

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

        # Use model from kwargs, config, or default
        model = kwargs.get("model", self.model)
        if self.config is not None and "model" in self.config and model == self.model:
            model = self.config["model"]

        print(f"Using model {model} for {num_tokens} tokens (approx)")
        response = self.client.chat.completions.create(
            model=model,
            messages=prompt,
            temperature=self.temperature,
        )

        return response.choices[0].message.content 