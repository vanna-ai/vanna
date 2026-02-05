from ..utils.response_format import (
    pydantic_model_from_json,
    response_format_from_pydantic_model,
    rec_strict_json_schema,
)
from pydantic import BaseModel, ValidationError

from ...models import ResponseFormat, JSONSchema
from ...types.basemodel import Unset

import unittest


class Student(BaseModel):
    name: str
    age: int


class Explanation(BaseModel):
    explanation: str
    output: str


class MathDemonstration(BaseModel):
    steps: list[Explanation]
    final_answer: str


mathdemo_schema = {
    "$defs": {
        "Explanation": {
            "properties": {
                "explanation": {"title": "Explanation", "type": "string"},
                "output": {"title": "Output", "type": "string"},
            },
            "required": ["explanation", "output"],
            "title": "Explanation",
            "type": "object",
        }
    },
    "properties": {
        "steps": {
            "items": {"$ref": "#/$defs/Explanation"},
            "title": "Steps",
            "type": "array",
        },
        "final_answer": {"title": "Final Answer", "type": "string"},
    },
    "required": ["steps", "final_answer"],
    "title": "MathDemonstration",
    "type": "object",
}

mathdemo_strict_schema = mathdemo_schema.copy()
mathdemo_strict_schema["$defs"]["Explanation"]["additionalProperties"] = False # type: ignore
mathdemo_strict_schema["additionalProperties"] = False

mathdemo_response_format = ResponseFormat(
    type="json_schema",
    json_schema=JSONSchema(
        name="MathDemonstration",
        schema_definition=mathdemo_strict_schema,
        description=Unset(),
        strict=True,
    ),
)


class TestResponseFormat(unittest.TestCase):
    def test_pydantic_model_from_json(self):
        missing_json_data = {"name": "Jean Dupont"}
        good_json_data = {"name": "Jean Dupont", "age": 25}
        extra_json_data = {
            "name": "Jean Dupont",
            "age": 25,
            "extra_field": "extra_value",
        }
        complex_json_data = {
            "final_answer": "x = -4",
            "steps": [
                {
                    "explanation": "Start with the given equation.",
                    "output": "8x + 7 = -23",
                },
                {
                    "explanation": "Subtract 7 from both sides to isolate the term with x.",
                    "output": "8x = -23 - 7",
                },
                {
                    "explanation": "Simplify the right side of the equation.",
                    "output": "8x = -30",
                },
                {
                    "explanation": "Divide both sides by 8 to solve for x.",
                    "output": "x = -30 / 8",
                },
                {
                    "explanation": "Simplify the fraction to get the final answer.",
                    "output": "x = -4",
                },
            ],
        }

        self.assertEqual(
            pydantic_model_from_json(good_json_data, Student),
            Student(name="Jean Dupont", age=25),
        )
        self.assertEqual(
            pydantic_model_from_json(extra_json_data, Student),
            Student(name="Jean Dupont", age=25),
        )
        self.assertEqual(
            pydantic_model_from_json(complex_json_data, MathDemonstration),
            MathDemonstration(
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
        )

        # Check it raises a validation error
        with self.assertRaises(ValidationError):
            pydantic_model_from_json(missing_json_data, Student)  # type: ignore

    def test_response_format_from_pydantic_model(self):
        self.assertEqual(
            response_format_from_pydantic_model(MathDemonstration),
            mathdemo_response_format,
        )

    def test_rec_strict_json_schema(self):
        invalid_schema = mathdemo_schema | {"wrong_value": 1}
        self.assertEqual(
            rec_strict_json_schema(mathdemo_schema), mathdemo_strict_schema
        )

        with self.assertRaises(ValueError):
            rec_strict_json_schema(invalid_schema)


if __name__ == "__main__":
    unittest.main()
