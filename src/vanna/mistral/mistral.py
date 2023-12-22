from mistralai.client import MistralClient
from mistralai.models.chat_completion import ChatMessage
from ..base import VannaBase
import re

class Mistral(VannaBase):
    def __init__(self, config=None):
        if config is None:
            raise ValueError("For Mistral, config must be provided with an api_key and model")

        if 'api_key' not in config:
            raise ValueError("config must contain a Mistral api_key")
        
        if 'model' not in config:
            raise ValueError("config must contain a Mistral model")

        api_key = config['api_key']
        model = config['model']
        self.client = MistralClient(api_key=api_key)
        self.model = model

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

    def generate_plotly_code(self, question: str = None, sql: str = None, df_metadata: str = None, **kwargs) -> str:
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
    
    def get_followup_questions_prompt(self, question: str, question_sql_list: list, ddl_list: list, doc_list: list, **kwargs):
        initial_prompt = f"The user initially asked the question: '{question}': \n\n"

        initial_prompt = Mistral.add_ddl_to_prompt(initial_prompt, ddl_list, max_tokens=14000)

        initial_prompt = Mistral.add_documentation_to_prompt(initial_prompt, doc_list, max_tokens=14000)

        initial_prompt = Mistral.add_sql_to_prompt(initial_prompt, question_sql_list, max_tokens=14000)

        message_log = [Mistral.system_message(initial_prompt)]
        message_log.append(Mistral.user_message("Generate a list of followup questions that the user might ask about this data. Respond with a list of questions, one per line. Do not answer with any explanations -- just the questions."))

        return message_log

    @staticmethod
    def system_message(message: str) -> dict:
        return ChatMessage(role="system", content=message)
    
    @staticmethod
    def user_message(message: str) -> dict:
        return ChatMessage(role="user", content=message)
    
    @staticmethod
    def assistant_message(message: str) -> dict:
        return ChatMessage(role="assistant", content=message)
    
    @staticmethod
    def str_to_approx_token_count(string: str) -> int:
        return len(string) / 4
    
    @staticmethod
    def add_ddl_to_prompt(initial_prompt: str, ddl_list: list[str], max_tokens: int = 14000) -> str:
        if len(ddl_list) > 0:
            initial_prompt += f"\nYou may use the following DDL statements as a reference for what tables might be available. Use responses to past questions also to guide you:\n\n"
    
            for ddl in ddl_list:
                if Mistral.str_to_approx_token_count(initial_prompt) + Mistral.str_to_approx_token_count(ddl) < max_tokens:
                    initial_prompt += f"{ddl}\n\n"
    
        return initial_prompt
    
    @staticmethod
    def add_documentation_to_prompt(initial_prompt: str, documentation_list: list[str], max_tokens: int = 14000) -> str:
        if len(documentation_list) > 0:
            initial_prompt += f"\nYou may use the following documentation as a reference for what tables might be available. Use responses to past questions also to guide you:\n\n"
    
            for documentation in documentation_list:
                if Mistral.str_to_approx_token_count(initial_prompt) + Mistral.str_to_approx_token_count(documentation) < max_tokens:
                    initial_prompt += f"{documentation}\n\n"
    
        return initial_prompt
    
    @staticmethod
    def add_sql_to_prompt(initial_prompt: str, sql_list: list[str], max_tokens: int = 14000) -> str:
        if len(sql_list) > 0:
            initial_prompt += f"\nYou may use the following SQL statements as a reference for what tables might be available. Use responses to past questions also to guide you:\n\n"
    
            for question in sql_list:
                if Mistral.str_to_approx_token_count(initial_prompt) + Mistral.str_to_approx_token_count(question["sql"]) < max_tokens:
                    initial_prompt += f"{question['question']}\n{question['sql']}\n\n"
    
        return initial_prompt
    
    def get_sql_prompt(self, question: str, question_sql_list: list, ddl_list: list, doc_list: list, **kwargs):
        initial_prompt = "The user provides a question and you provide SQL. You will only respond with SQL code and not with any explanations.\n\nRespond with only SQL code. Do not answer with any explanations -- just the code.\n"
        
        initial_prompt = Mistral.add_ddl_to_prompt(initial_prompt, ddl_list, max_tokens=14000)
        
        initial_prompt = Mistral.add_documentation_to_prompt(initial_prompt, doc_list, max_tokens=14000)
        
        message_log = [Mistral.system_message(initial_prompt)]
        
        for example in question_sql_list:
            if example is None:
                print("example is None")
            else:
                if example is not None and "question" in example and "sql" in example:
                    message_log.append(Mistral.user_message(example["question"]))
                    message_log.append(Mistral.assistant_message(example["sql"]))
        
        message_log.append(ChatMessage(role="user", content=question))
        
        return message_log

    def generate_sql(self, question: str, **kwargs) -> str:
        # Use the super generate_sql
        sql = super().generate_sql(question, **kwargs)

        # Replace "\_" with "_"
        sql = sql.replace("\\_", "_")

        return sql

    def submit_prompt(self, prompt, **kwargs) -> str:
        chat_response = self.client.chat(
            model=self.model,
            messages=prompt,
        )
        
        return chat_response.choices[0].message.content
