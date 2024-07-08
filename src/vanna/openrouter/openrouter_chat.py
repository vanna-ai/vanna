import os
from typing import Any, AsyncIterable

from openai import AsyncOpenAI, OpenAI
from openai.types.chat.chat_completion import Choice

from ..base import VannaBase


class OpenRouter_Chat(VannaBase):
    def __init__(
        self,
        client=None,
        aclient=None,
        config: dict[str, Any] = {},
    ):
        VannaBase.__init__(self, config=config)
        # default parameters - can be overrided using config
        self.temperature = 0.7
        self.max_tokens = 500

        if "temperature" in config:
            self.temperature = config["temperature"]

        if "max_tokens" in config:
            self.max_tokens = config["max_tokens"]

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
            self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            return

        if aclient is not None:
            self.aclient = aclient
            return

        if config is None and aclient is None:
            self.client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            return

        if "api_key" in config:
            self.client = OpenAI(api_key=config["api_key"])
            self.aclient = AsyncOpenAI(api_key=config["api_key"])

    def system_message(self, message: str) -> Any:
        return {"role": "system", "content": message}

    def user_message(self, message: str) -> Any:
        return {"role": "user", "content": message}

    def assistant_message(self, message: str) -> Any:
        return {"role": "assistant", "content": message}

    def submit_prompt(
        self, prompt, model: str = "deepseek/deepseek-chat", **kwargs
    ) -> str:
        if prompt is None:
            raise Exception("Prompt is None")

        if len(prompt) == 0:
            raise Exception("Prompt is empty")

        # Count the number of tokens in the message log
        # Use 4 as an approximation for the number of characters per token
        num_tokens = 0
        for message in prompt:
            num_tokens += len(message["content"]) / 4

        print(f"Using model {model} for {num_tokens} tokens (approx)")
        response = self.client.chat.completions.create(
            model=model,
            messages=prompt,
            max_tokens=self.max_tokens,
            stop=None,
            temperature=self.temperature,
        )

        # Find the first response from the chatbot that has text in it (some responses may not have text)
        for choice in response.choices:
            if not isinstance(choice, Choice):
                return str(choice.text)
            # If no response with text is found, return the first response's content (which may be empty)
            elif (
                isinstance(choice, Choice)
                and choice.message is not None
                and choice.message.content is not None
            ):
                return choice.message.content
            else:
                return ""

        return ""

    async def asubmit_prompt(
        self, prompt, model: str = "deepseek/deepseek-chat", **kwargs
    ) -> str:
        if prompt is None:
            raise Exception("Prompt is None")

        if len(prompt) == 0:
            raise Exception("Prompt is empty")

        # Count the number of tokens in the message log
        # Use 4 as an approximation for the number of characters per token
        num_tokens = 0
        for message in prompt:
            num_tokens += len(message["content"]) / 4

        print(f"Using model {model} for {num_tokens} tokens (approx)")
        response = await self.aclient.chat.completions.create(
            model=model,
            messages=prompt,
            max_tokens=self.max_tokens,
            stop=None,
            temperature=self.temperature,
        )

        # Find the first response from the chatbot that has text in it (some responses may not have text)
        for choice in response.choices:
            if not isinstance(choice, Choice):
                return str(choice.text)
            # If no response with text is found, return the first response's content (which may be empty)
            elif (
                isinstance(choice, Choice)
                and choice.message is not None
                and choice.message.content is not None
            ):
                return choice.message.content
            else:
                return ""

        return ""

    async def astream_submit_prompt(
        self, prompt, model: str = "deepseek/deepseek-chat", **kwargs
    ) -> AsyncIterable[str]:
        if prompt is None:
            raise Exception("Prompt is None")

        if len(prompt) == 0:
            raise Exception("Prompt is empty")

        # Count the number of tokens in the message log
        # Use 4 as an approximation for the number of characters per token
        num_tokens = 0
        for message in prompt:
            num_tokens += len(message["content"]) / 4

        print(f"Using model {model} for {num_tokens} tokens (approx)")
        stream = await self.aclient.chat.completions.create(
            model=model,
            messages=prompt,
            max_tokens=self.max_tokens,
            stop=None,
            temperature=self.temperature,
            stream=True,
        )

        async for chunk in stream:
            if chunk.choices[0].delta is not None:
                yield chunk.choices[0].delta.content or ""
