import re
from abc import abstractmethod

import openai
import pandas as pd

from ..base import VannaBase


class OpenAI_Chat(VannaBase):
    def __init__(self, config=None):
        VannaBase.__init__(self, config=config)

        if config is None:
            return

        if "api_type" in config:
            openai.api_type = config["api_type"]

        if "api_base" in config:
            openai.api_base = config["api_base"]

        if "api_version" in config:
            openai.api_version = config["api_version"]

        if "api_key" in config:
            openai.api_key = config["api_key"]

    @staticmethod
    def system_message(message: str) -> dict:
        return {"role": "system", "content": message}

    @staticmethod
    def user_message(message: str) -> dict:
        return {"role": "user", "content": message}

    @staticmethod
    def assistant_message(message: str) -> dict:
        return {"role": "assistant", "content": message}

    @staticmethod
    def str_to_approx_token_count(string: str) -> int:
        return len(string) / 4

    @staticmethod
    def add_ddl_to_prompt(initial_prompt: str, ddl_list: list[str], max_tokens: int = 14000) -> str:
        if len(ddl_list) > 0:
            initial_prompt += f"\nYou may use the following DDL statements as a reference for what tables might be available. Use responses to past questions also to guide you:\n\n"

            for ddl in ddl_list:
                if OpenAI_Chat.str_to_approx_token_count(initial_prompt) + OpenAI_Chat.str_to_approx_token_count(ddl) < max_tokens:
                    initial_prompt += f"{ddl}\n\n"

        return initial_prompt

    @staticmethod
    def add_documentation_to_prompt(initial_prompt: str, documentation_list: list[str], max_tokens: int = 14000) -> str:
        if len(documentation_list) > 0:
            initial_prompt += f"\nYou may use the following documentation as a reference for what tables might be available. Use responses to past questions also to guide you:\n\n"

            for documentation in documentation_list:
                if OpenAI_Chat.str_to_approx_token_count(initial_prompt) + OpenAI_Chat.str_to_approx_token_count(documentation) < max_tokens:
                    initial_prompt += f"{documentation}\n\n"

        return initial_prompt

    @staticmethod
    def add_sql_to_prompt(initial_prompt: str, sql_list: list[str], max_tokens: int = 14000) -> str:
        if len(sql_list) > 0:
            initial_prompt += f"\nYou may use the following SQL statements as a reference for what tables might be available. Use responses to past questions also to guide you:\n\n"

            for question in sql_list:
                if OpenAI_Chat.str_to_approx_token_count(initial_prompt) + OpenAI_Chat.str_to_approx_token_count(question["sql"]) < max_tokens:
                    initial_prompt += f"{question['question']}\n{question['sql']}\n\n"

        return initial_prompt

    def get_sql_prompt(
        self,
        question: str,
        question_sql_list: list,
        ddl_list: list,
        doc_list: list,
        **kwargs,
    ):
        initial_prompt = "The user provides a question and you provide SQL. You will only respond with SQL code and not with any explanations.\n\nRespond with only SQL code. Do not answer with any explanations -- just the code.\n"

        initial_prompt = OpenAI_Chat.add_ddl_to_prompt(initial_prompt, ddl_list, max_tokens=14000)

        initial_prompt = OpenAI_Chat.add_documentation_to_prompt(initial_prompt, doc_list, max_tokens=14000)

        message_log = [OpenAI_Chat.system_message(initial_prompt)]

        for example in question_sql_list:
            if example is None:
                print("example is None")
            else:
                if example is not None and "question" in example and "sql" in example:
                    message_log.append(OpenAI_Chat.user_message(example["question"]))
                    message_log.append(OpenAI_Chat.assistant_message(example["sql"]))

        message_log.append({"role": "user", "content": question})

        return message_log

    def get_followup_questions_prompt(
        self, 
        question: str, 
        df: pd.DataFrame,
        question_sql_list: list,
        ddl_list: list,
        doc_list: list, 
        **kwargs
    ):
        initial_prompt = f"The user initially asked the question: '{question}': \n\n"

        initial_prompt = OpenAI_Chat.add_ddl_to_prompt(initial_prompt, ddl_list, max_tokens=14000)

        initial_prompt = OpenAI_Chat.add_documentation_to_prompt(initial_prompt, doc_list, max_tokens=14000)

        initial_prompt = OpenAI_Chat.add_sql_to_prompt(initial_prompt, question_sql_list, max_tokens=14000)

        message_log = [OpenAI_Chat.system_message(initial_prompt)]
        message_log.append(OpenAI_Chat.user_message("Generate a list of followup questions that the user might ask about this data. Respond with a list of questions, one per line. Do not answer with any explanations -- just the questions."))

        return message_log

    def generate_question(self, sql: str, **kwargs) -> str:
        response = self.submit_prompt(
            [
                self.system_message(
                    "The user will give you SQL and you will try to guess what the business question this query is answering. Return just the question without any additional explanation. Do not reference the table name in the question."
                ),
                self.user_message(sql),
            ],
            **kwargs,
        )

        return response

    def _extract_python_code(self, markdown_string: str) -> str:
        # Regex pattern to match Python code blocks
        pattern = r"```[\w\s]*python\n([\s\S]*?)```|```([\s\S]*?)```"

        # Find all matches in the markdown string
        matches = re.findall(pattern, markdown_string, re.IGNORECASE)

        # Extract the Python code from the matches
        python_code = []
        for match in matches:
            python = match[0] if match[0] else match[1]
            python_code.append(python.strip())

        if len(python_code) == 0:
            return markdown_string

        return python_code[0]

    def _sanitize_plotly_code(self, raw_plotly_code: str) -> str:
        # Remove the fig.show() statement from the plotly code
        plotly_code = raw_plotly_code.replace("fig.show()", "")

        return plotly_code

    def generate_plotly_code(
        self, question: str = None, sql: str = None, df_metadata: str = None, **kwargs
    ) -> str:
        if question is not None:
            system_msg = f"The following is a pandas DataFrame that contains the results of the query that answers the question the user asked: '{question}'"
        else:
            system_msg = "The following is a pandas DataFrame "

        if sql is not None:
            system_msg += f"\n\nThe DataFrame was produced using this query: {sql}\n\n"

        system_msg += f"The following is information about the resulting pandas DataFrame 'df': \n{df_metadata}"

        message_log = [
            self.system_message(system_msg),
            self.user_message(
                "Can you generate the Python plotly code to chart the results of the dataframe? Assume the data is in a pandas dataframe called 'df'. If there is only one value in the dataframe, use an Indicator. Respond with only Python code. Do not answer with any explanations -- just the code."
            ),
        ]

        plotly_code = self.submit_prompt(message_log, kwargs=kwargs)

        return self._sanitize_plotly_code(self._extract_python_code(plotly_code))

    def submit_prompt(self, prompt, **kwargs) -> str:
        if prompt is None:
            raise Exception("Prompt is None")

        if len(prompt) == 0:
            raise Exception("Prompt is empty")

        # Count the number of tokens in the message log
        num_tokens = 0
        for message in prompt:
            num_tokens += (
                len(message["content"]) / 4
            )  # Use 4 as an approximation for the number of characters per token

        if self.config is not None and "engine" in self.config:
            print(
                f"Using engine {self.config['engine']} for {num_tokens} tokens (approx)"
            )
            response = openai.ChatCompletion.create(
                engine=self.config["engine"],
                messages=prompt,
                max_tokens=500,
                stop=None,
                temperature=0.7,
            )
        elif self.config is not None and "model" in self.config:
            print(
                f"Using model {self.config['model']} for {num_tokens} tokens (approx)"
            )
            response = openai.ChatCompletion.create(
                model=self.config["model"],
                messages=prompt,
                max_tokens=500,
                stop=None,
                temperature=0.7,
            )
        else:
            if num_tokens > 3500:
                model = "gpt-3.5-turbo-16k"
            else:
                model = "gpt-3.5-turbo"

            print(f"Using model {model} for {num_tokens} tokens (approx)")
            response = openai.ChatCompletion.create(
                model=model, messages=prompt, max_tokens=500, stop=None, temperature=0.7
            )

        for (
            choice
        ) in (
            response.choices
        ):  # Find the first response from the chatbot that has text in it (some responses may not have text)
            if "text" in choice:
                return choice.text

        return response.choices[
            0
        ].message.content  # If no response with text is found, return the first response's content (which may be empty)
