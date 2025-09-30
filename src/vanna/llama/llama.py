import json
import re
from typing import Optional, Dict, Any

from ..base import VannaBase
from ..exceptions import DependencyError


class Llama(VannaBase):
    def __init__(self, config=None):
        try:
            from llama_cpp import Llama
        except ImportError:
            raise DependencyError(
                "You need to install required dependencies to execute this method, run command:"
                " \npip install llama-cpp-python"
            )

        if not config:
            raise ValueError("config must contain at least model_path")
        if 'model_path' not in config:
            raise ValueError("config must contain model_path")

        # Model configuration
        self.model_path = config["model_path"]
        self.n_ctx = config.get("n_ctx", 2048)
        self.n_threads = config.get("n_threads", 4)
        self.n_gpu_layers = config.get("n_gpu_layers", 0)
        self.temperature = config.get("temperature", 0.7)
        self.max_tokens = config.get("max_tokens", 512)
        
        # Initialize Llama model
        self.llm = Llama(
            model_path=self.model_path,
            n_ctx=self.n_ctx,
            n_threads=self.n_threads,
            n_gpu_layers=self.n_gpu_layers,
            verbose=config.get("verbose", False)
        )

    def system_message(self, message: str) -> dict:
        return {"role": "system", "content": message}

    def user_message(self, message: str) -> dict:
        return {"role": "user", "content": message}

    def assistant_message(self, message: str) -> dict:
        return {"role": "assistant", "content": message}

    def extract_sql(self, llm_response: str) -> str:
        """
        Extracts SQL from LLM response following the same logic as Ollama implementation.
        """
        # Clean up response
        llm_response = llm_response.replace("\\_", "_")
        llm_response = llm_response.replace("\\", "")

        # Try to find SQL in code blocks
        sql = re.search(r"```sql\n((.|\n)*?)(?=;|\[|```)", llm_response, re.DOTALL)
        
        # Try to find SELECT or WITH statements
        select_with = re.search(
            r'(select|(with.*?as \())(.*?)(?=;|\[|```)',
            llm_response,
            re.IGNORECASE | re.DOTALL
        )
        
        if sql:
            self.log(f"Output from LLM: {llm_response} \nExtracted SQL: {sql.group(1)}")
            return sql.group(1).replace("```", "")
        elif select_with:
            self.log(f"Output from LLM: {llm_response} \nExtracted SQL: {select_with.group(0)}")
            return select_with.group(0)
        else:
            return llm_response

    def submit_prompt(self, prompt, **kwargs) -> str:
        self.log(
            f"LlamaCpp parameters:\n"
            f"model_path={self.model_path},\n"
            f"n_ctx={self.n_ctx},\n"
            f"temperature={self.temperature},\n"
            f"max_tokens={self.max_tokens}"
        )
        self.log(f"Prompt Content:\n{json.dumps(prompt, ensure_ascii=False)}")

        # Format messages into a single prompt string
        formatted_prompt = self._format_messages(prompt)
        
        # Generate response
        response = self.llm(
            formatted_prompt,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            stop=["</s>", "\n\n\n"],  # Common stop sequences
            echo=False
        )
        
        response_text = response['choices'][0]['text']
        self.log(f"LlamaCpp Response:\n{response_text}")
        
        return response_text

    def _format_messages(self, messages) -> str:
        """
        Format chat messages into a prompt string for llama.cpp
        """
        formatted = ""
        for msg in messages:
            role = msg.get("role", "")
            content = msg.get("content", "")
            
            if role == "system":
                formatted += f"System: {content}\n\n"
            elif role == "user":
                formatted += f"User: {content}\n\n"
            elif role == "assistant":
                formatted += f"Assistant: {content}\n\n"
        
        # Add final Assistant prompt if last message wasn't from assistant
        if messages and messages[-1].get("role") != "assistant":
            formatted += "Assistant: "
        
        return formatted