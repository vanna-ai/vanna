import re
from transformers import AutoTokenizer, AutoModelForCausalLM

from ..base import VannaBase


class Hf(VannaBase):
    def __init__(self, config=None):
        model_name_or_path = self.config.get(
            "model_name_or_path", None
        )  # e.g. meta-llama/Meta-Llama-3-8B-Instruct or local path to the model checkpoint files
        # list of quantization methods supported by transformers package: https://huggingface.co/docs/transformers/main/en/quantization/overview
        quantization_config = self.config.get("quantization_config", None)
        self.tokenizer = AutoTokenizer.from_pretrained(model_name_or_path)
        self.model = AutoModelForCausalLM.from_pretrained(
            model_name_or_path,
            quantization_config=quantization_config,
            device_map="auto",
        )

    def system_message(self, message: str) -> any:
        return {"role": "system", "content": message}

    def user_message(self, message: str) -> any:
        return {"role": "user", "content": message}

    def assistant_message(self, message: str) -> any:
        return {"role": "assistant", "content": message}

    def extract_sql_query(self, text):
        """
        Extracts the first SQL statement after the word 'select', ignoring case,
        matches until the first semicolon, three backticks, or the end of the string,
        and removes three backticks if they exist in the extracted string.

        Args:
        - text (str): The string to search within for an SQL statement.

        Returns:
        - str: The first SQL statement found, with three backticks removed, or an empty string if no match is found.
        """
        # Regular expression to find 'select' (ignoring case) and capture until ';', '```', or end of string
        pattern = re.compile(r"select.*?(?:;|```|$)", re.IGNORECASE | re.DOTALL)

        match = pattern.search(text)
        if match:
            # Remove three backticks from the matched string if they exist
            return match.group(0).replace("```", "")
        else:
            return text

    def generate_sql(self, question: str, **kwargs) -> str:
        # Use the super generate_sql
        sql = super().generate_sql(question, **kwargs)

        # Replace "\_" with "_"
        sql = sql.replace("\\_", "_")

        sql = sql.replace("\\", "")

        return self.extract_sql_query(sql)

    def submit_prompt(self, prompt, **kwargs) -> str:

        input_ids = self.tokenizer.apply_chat_template(
            prompt, add_generation_prompt=True, return_tensors="pt"
        ).to(self.model.device)

        outputs = self.model.generate(
            input_ids,
            max_new_tokens=512,
            eos_token_id=self.tokenizer.eos_token_id,
            do_sample=True,
            temperature=1,
            top_p=0.9,
        )
        response = outputs[0][input_ids.shape[-1] :]
        response = self.tokenizer.decode(response, skip_special_tokens=True)
        self.log(response)

        return response
