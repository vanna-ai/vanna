from abc import abstractmethod

import openai

from .base import VannaBase


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

    def get_prompt(
        self,
        question: str,
        question_sql_list: list,
        ddl_list: list,
        doc_list: list,
        **kwargs,
    ) -> str:
        initial_prompt = "The user provides a question and you provide SQL. You will only respond with SQL code and not with any explanations.\n\nRespond with only SQL code. Do not answer with any explanations -- just the code.\n"

        if len(ddl_list) > 0:
            initial_prompt += f"\nYou may use the following DDL statements as a reference for what tables might be available. Use responses to past questions also to guide you:\n\n"

            for ddl in ddl_list:
                if len(initial_prompt) < 50000:  # Add DDL if it fits
                    initial_prompt += f"{ddl}\n\n"

        if len(doc_list) > 0:
            initial_prompt += f"The following information may or may not be useful in constructing the SQL to answer the question\n"

            for doc in doc_list:
                if len(initial_prompt) < 60000:  # Add Documentation if it fits
                    initial_prompt += f"{doc}\n\n"

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
