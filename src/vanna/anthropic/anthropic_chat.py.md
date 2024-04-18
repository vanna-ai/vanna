## Table of Contents

- [Overview](#overview)
- [Initialization](#initialization)
    - [Using a Custom Client](#using-a-custom-client)
    - [Using the Default Client with Custom Parameters](#using-the-default-client-with-custom-parameters)
- [Message Formatting](#message-formatting)
    - [System Message](#system-message)
    - [User Message](#user-message)
    - [Assistant Message](#assistant-message)
- [Prompt Submission](#prompt-submission)
- [Example Usage](#example-usage)

## Overview

The `Anthropic_Chat` class is a Vanna AI wrapper for the [Anthropic API](https://anthropic.com/docs/api). It allows you to easily send and receive messages from the Anthropic language model.

## Initialization

### Using a Custom Client

You can pass an existing `anthropic.Anthropic` client to the `Anthropic_Chat` constructor. This is useful if you want to use a custom API key or model.

```python
import os

import anthropic

from ..base import VannaBase


class Anthropic_Chat(VannaBase):
    def __init__(self, client=None, config=None):
        VannaBase.__init__(self, config=config)

        if client is not None:
            self.client = client
            return

        if config is None and client is None:
            self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
            return

        # default parameters - can be overrided using config
        self.temperature = 0.7
        self.max_tokens = 500

        if "temperature" in config:
            self.temperature = config["temperature"]

        if "max_tokens" in config:
            self.max_tokens = config["max_tokens"]

        if "api_key" in config:
            self.client = anthropic.Anthropic(api_key=config["api_key"])
```

### Using the Default Client with Custom Parameters

You can also use the default client with custom parameters. This is useful if you want to use a different temperature or max tokens value.

```python
import os

from ..base import VannaBase


class Anthropic_Chat(VannaBase):
    def __init__(self, config=None):
        VannaBase.__init__(self, config=config)

        if config is None:
            self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
            return

        # default parameters - can be overrided using config
        self.temperature = 0.7
        self.max_tokens = 500

        if "temperature" in config:
            self.temperature = config["temperature"]

        if "max_tokens" in config:
            self.max_tokens = config["max_tokens"]

        if "api_key" in config:
            self.client = anthropic.Anthropic(api_key=config["api_key"])
```

## Message Formatting

### System Message

```python
def system_message(self, message: str) -> any:
    return {"role": "system", "content": message}
```

### User Message

```python
def user_message(self, message: str) -> any:
    return {"role": "user", "content": message}
```

### Assistant Message

```python
def assistant_message(self, message: str) -> any:
    return {"role": "assistant", "content": message}
```

## Prompt Submission

```python
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
```

## Example Usage

```python
import os

from ..base import VannaBase


class Anthropic_Chat(VannaBase):
    def __init__(self, config=None):
        VannaBase.__init__(self, config=config)

        if config is None:
            self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
            return

        # default parameters - can be overrided using config
        self.temperature = 0.7
        self.max_tokens = 500

        if "temperature" in config:
            self.temperature = config["temperature"]

        if "max_tokens" in config:
            self.max_tokens = config["max_tokens"]

        if "api_key" in config:
            self.client = anthropic.Anthropic(api_key=config["api_key"])

# Create an `Anthropic_Chat` instance
chat = Anthropic_Chat(
    config={
        "model": "text-vaughan-001",
        "temperature": 0.3,
        "max_tokens": 500,
    }
)

# Send a message to the assistant
response = chat.submit_prompt([
    chat.user_message("Hello, can you help me with a task?"),
])

# Print the assistant's response
print(response)
```