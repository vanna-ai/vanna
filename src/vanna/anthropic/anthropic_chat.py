import os

import anthropic

from ..base import VannaBase


class Anthropic_Chat(VannaBase):
    def __init__(self, client=None, config=None):
        VannaBase.__init__(self, config=config)
      
        # default parameters - can be overrided using config
        self.temperature = 0.7
        self.max_tokens = 500

        if "temperature" in config:
            self.temperature = config["temperature"]

        if "max_tokens" in config:
            self.max_tokens = config["max_tokens"]

        if client is not None:
            self.client = client
            return

        if config is None and client is None:
            self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
            return
      
        if "api_key" in config:
            self.client = anthropic.Anthropic(api_key=config["api_key"])

    def system_message(self, message: str) -> any:
        return {"role": "system", "content": message}

    def user_message(self, message: str) -> any:
        return {"role": "user", "content": message}

    def assistant_message(self, message: str) -> any:
        return {"role": "assistant", "content": message}

    def submit_prompt(self, prompt, **kwargs) -> str:
        if prompt is None:
            raise Exception("Prompt is None")

        if len(prompt) == 0:
            raise Exception("Prompt is empty")

        # Count the number of tokens in the message log
        # Use 4 as an approximation for the number of characters per token
        num_tokens = 0
        for message in prompt:
            num_tokens += len(message["content"]) / 4

        if self.config is not None and "model" in self.config:
            print(
                f"Using model {self.config['model']} for {num_tokens} tokens (approx)"
            )
            # claude required system message is a single filed
            # https://docs.anthropic.com/claude/reference/messages_post
            system_message = ''
            no_system_prompt = []
            for prompt_message in prompt:
                role = prompt_message['role']
                if role == 'system':
                    system_message = prompt_message['content']
                else:
                    no_system_prompt.append({"role": role, "content": prompt_message['content']})

            response = self.client.messages.create(
                model=self.config["model"],
                messages=no_system_prompt,
                system=system_message,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
            )

        return response.content[0].text
