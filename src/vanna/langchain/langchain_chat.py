from typing import List

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import (
  AIMessage,
  BaseMessage,
  HumanMessage,
  SystemMessage,
)

from ..base import VannaBase


class LangChain_Chat(VannaBase):
    def __init__(self, chat_model: BaseChatModel, config=None):
        VannaBase.__init__(self, config=config)
        self.llm = chat_model
        self.model_name = (
            self.llm.model_name
            if hasattr(self.llm, "model_name")
            else type(self.llm).__name__
        )

    def system_message(self, message: str) -> any:
        return SystemMessage(message)

    def user_message(self, message: str) -> any:
        return HumanMessage(message)

    def assistant_message(self, message: str) -> any:
        return AIMessage(message)

    def count_prompt_tokens(
        self, input_messages: List[BaseMessage], output_message: AIMessage
    ) -> int:
        # OpenAI
        if (
            "token_usage" in output_message.response_metadata
            and "prompt_tokens" in output_message.response_metadata["token_usage"]
        ):
            return output_message.response_metadata["token_usage"]["prompt_tokens"]
        # Anthropic
        elif (
            "usage" in output_message.response_metadata
            and "input_tokens" in output_message.response_metadata["usage"]
        ):
            return output_message.response_metadata["usage"]["input_tokens"]
        # Other
        else:
            num_tokens = 0
            for message in input_messages:
                num_tokens += len(message.content) / 4
        return num_tokens

    def submit_prompt(self, prompt: List[BaseMessage], **kwargs) -> str:
        if prompt is None:
            raise Exception("Prompt is None")

        if len(prompt) == 0:
            raise Exception("Prompt is empty")

        response = self.llm.invoke(prompt)
        num_tokens = self.count_prompt_tokens(prompt, response)
        self.log(
            f"Used model {self.model_name} for {num_tokens} tokens (approx)",
            title="Model Used",
        )

        return response.content
