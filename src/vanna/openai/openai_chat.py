import os

from openai import OpenAI

from ..base import VannaBase


class OpenAI_Chat(VannaBase):
    def __init__(self, client=None, config=None):
        VannaBase.__init__(self, config=config)

        # Ensure config is a dictionary
        config = config or {}

        # Default parameters - can be overridden using config
        self.temperature = config.get("temperature", 0.7)

        # Raise exceptions for deprecated parameters
        for deprecated_param in ["api_type", "api_base", "api_version"]:
            if deprecated_param in config:
                raise ValueError(
                    f"Passing {deprecated_param} is now deprecated. Please pass an OpenAI client instead."
                )

        if client is not None:
            self.client = client
            return

        # Initialize the OpenAI client with optional overrides from config
        self.client = OpenAI(
            api_key=config.get("api_key"),
            base_url=config.get("base_url")
        )

    def system_message(self, message: str) -> dict:
        return {"role": "system", "content": message}

    def user_message(self, message: str) -> dict:
        return {"role": "user", "content": message}

    def assistant_message(self, message: str) -> dict:
        return {"role": "assistant", "content": message}

    def generate_response(self, prompt, num_tokens):
        model = self.config.get("model", "gpt-4o-mini")
        print(f"Using model {model} for {num_tokens} tokens (approx)")
        response = self.client.chat.completions.create(
            model=model,
            messages=prompt,
            stop=None,
            temperature=self.temperature,
        )
        return response

    def submit_prompt(self, prompt, **kwargs) -> str:
        if prompt is None:
            raise ValueError("Prompt is None")

        if len(prompt) == 0:
            raise ValueError("Prompt is empty")

        # Count the number of tokens in the message log
        # Use 4 as an approximation for the number of characters per token
        num_tokens = 0
        for message in prompt:
            num_tokens += len(message["content"]) / 4

        # Use the generate_response method to get the response
        response = self.generate_response(prompt, num_tokens)

        # Find the first response from the chatbot that has text in it
        # (some responses may not have text)
        for choice in response.choices:
            if "text" in choice:
                return choice.text

        # If no response with text is found, return the first response's content
        return response.choices[0].message.content