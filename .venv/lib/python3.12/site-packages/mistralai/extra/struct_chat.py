import json
from typing import Generic

from ..models import AssistantMessage, ChatCompletionChoice, ChatCompletionResponse
from .utils.response_format import CustomPydanticModel, pydantic_model_from_json


class ParsedAssistantMessage(AssistantMessage, Generic[CustomPydanticModel]):
    parsed: CustomPydanticModel | None


class ParsedChatCompletionChoice(ChatCompletionChoice, Generic[CustomPydanticModel]):
    message: ParsedAssistantMessage[CustomPydanticModel] | None  # type: ignore


class ParsedChatCompletionResponse(ChatCompletionResponse, Generic[CustomPydanticModel]):
    choices: list[ParsedChatCompletionChoice[CustomPydanticModel]] | None  # type: ignore


def convert_to_parsed_chat_completion_response(
    response: ChatCompletionResponse,
    response_format: type[CustomPydanticModel],
) -> ParsedChatCompletionResponse[CustomPydanticModel]:
    parsed_choices = []

    if response.choices:
        for choice in response.choices:
            if choice.message:
                parsed_message: ParsedAssistantMessage = ParsedAssistantMessage(
                    **choice.message.model_dump(),
                    parsed=None
                )
                if isinstance(parsed_message.content, str):
                    parsed_message.parsed = pydantic_model_from_json(json.loads(parsed_message.content), response_format)
                elif parsed_message.content is None:
                    parsed_message.parsed = None
                else:
                    raise TypeError(f"Unexpected type for message.content: {type(parsed_message.content)}")
                choice_dict = choice.model_dump()
                choice_dict["message"] = parsed_message
                parsed_choice: ParsedChatCompletionChoice = ParsedChatCompletionChoice(**choice_dict)
                parsed_choices.append(parsed_choice)
            else:
                parsed_choice = ParsedChatCompletionChoice(**choice.model_dump())
                parsed_choices.append(parsed_choice)
    response_dict = response.model_dump()
    response_dict["choices"] = parsed_choices
    return ParsedChatCompletionResponse(**response_dict)
