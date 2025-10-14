import json
import re
from typing import Optional, Dict, Any
import requests

from ..base import VannaBase
from ..exceptions import DependencyError


class LlamaCppServer(VannaBase):
    def __init__(self, config=None):
        if not config:
            raise ValueError("config must contain at least base_url")
        if 'base_url' not in config:
            raise ValueError("config must contain base_url")

        # Server configuration
        self.base_url = config["base_url"].rstrip('/')
        self.model_id = config.get("model_id", "phi-4-q4_k_m.gguf")
        self.api_key = config.get("api_key", "sk-local")
        self.temperature = config.get("temperature", 0.2)
        self.max_tokens = config.get("max_tokens", 512)
        self.timeout = config.get("timeout", 60)

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
            f"LlamaCpp Server parameters:\n"
            f"base_url={self.base_url},\n"
            f"model_id={self.model_id},\n"
            f"temperature={self.temperature},\n"
            f"max_tokens={self.max_tokens}"
        )
        self.log(f"Prompt Content:\n{json.dumps(prompt, ensure_ascii=False)}")

        url = f"{self.base_url}/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        
        payload = {
            "model": self.model_id,
            "messages": prompt,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=self.timeout)
            response.raise_for_status()
            result = response.json()
            response_text = result["choices"][0]["message"]["content"]
            
            self.log(f"LlamaCpp Server Response:\n{response_text}")
            return response_text
            
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Failed to connect to llama.cpp server: {str(e)}")