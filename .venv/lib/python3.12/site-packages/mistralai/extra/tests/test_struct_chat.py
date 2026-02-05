import unittest
from ..struct_chat import (
    convert_to_parsed_chat_completion_response,
    ParsedChatCompletionResponse,
    ParsedChatCompletionChoice,
    ParsedAssistantMessage,
)
from ...models import (
    ChatCompletionResponse,
    UsageInfo,
    ChatCompletionChoice,
    AssistantMessage,
)
from pydantic import BaseModel


class Explanation(BaseModel):
    explanation: str
    output: str


class MathDemonstration(BaseModel):
    steps: list[Explanation]
    final_answer: str


mock_cc_response = ChatCompletionResponse(
    id="c0271b2098954c6094231703875ca0bc",
    object="chat.completion",
    model="mistral-large-latest",
    usage=UsageInfo(prompt_tokens=75, completion_tokens=220, total_tokens=295),
    created=1737727558,
    choices=[
        ChatCompletionChoice(
            index=0,
            message=AssistantMessage(
                content='{\n  "final_answer": "x = -4",\n  "steps": [\n    {\n      "explanation": "Start with the given equation.",\n      "output": "8x + 7 = -23"\n    },\n    {\n      "explanation": "Subtract 7 from both sides to isolate the term with x.",\n      "output": "8x = -23 - 7"\n    },\n    {\n      "explanation": "Simplify the right side of the equation.",\n      "output": "8x = -30"\n    },\n    {\n      "explanation": "Divide both sides by 8 to solve for x.",\n      "output": "x = -30 / 8"\n    },\n    {\n      "explanation": "Simplify the fraction to get the final answer.",\n      "output": "x = -4"\n    }\n  ]\n}',
                tool_calls=None,
                prefix=False,
                role="assistant",
            ),
            finish_reason="stop",
        )
    ],
)


expected_response: ParsedChatCompletionResponse = ParsedChatCompletionResponse(
    choices=[
        ParsedChatCompletionChoice(
            index=0,
            message=ParsedAssistantMessage(
                content='{\n  "final_answer": "x = -4",\n  "steps": [\n    {\n      "explanation": "Start with the given equation.",\n      "output": "8x + 7 = -23"\n    },\n    {\n      "explanation": "Subtract 7 from both sides to isolate the term with x.",\n      "output": "8x = -23 - 7"\n    },\n    {\n      "explanation": "Simplify the right side of the equation.",\n      "output": "8x = -30"\n    },\n    {\n      "explanation": "Divide both sides by 8 to solve for x.",\n      "output": "x = -30 / 8"\n    },\n    {\n      "explanation": "Simplify the fraction to get the final answer.",\n      "output": "x = -4"\n    }\n  ]\n}',
                tool_calls=None,
                prefix=False,
                role="assistant",
                parsed=MathDemonstration(
                    steps=[
                        Explanation(
                            explanation="Start with the given equation.",
                            output="8x + 7 = -23",
                        ),
                        Explanation(
                            explanation="Subtract 7 from both sides to isolate the term with x.",
                            output="8x = -23 - 7",
                        ),
                        Explanation(
                            explanation="Simplify the right side of the equation.",
                            output="8x = -30",
                        ),
                        Explanation(
                            explanation="Divide both sides by 8 to solve for x.",
                            output="x = -30 / 8",
                        ),
                        Explanation(
                            explanation="Simplify the fraction to get the final answer.",
                            output="x = -4",
                        ),
                    ],
                    final_answer="x = -4",
                ),
            ),
            finish_reason="stop",
        )
    ],
    created=1737727558,
    id="c0271b2098954c6094231703875ca0bc",
    model="mistral-large-latest",
    object="chat.completion",
    usage=UsageInfo(prompt_tokens=75, completion_tokens=220, total_tokens=295),
)


class TestConvertToParsedChatCompletionResponse(unittest.TestCase):
    def test_convert_to_parsed_chat_completion_response(self):
        output = convert_to_parsed_chat_completion_response(
            mock_cc_response, MathDemonstration
        )
        self.assertEqual(output, expected_response)


if __name__ == "__main__":
    unittest.main()
