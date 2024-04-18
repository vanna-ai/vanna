## 🤖 Anthropic Chat 💬

### Table of Contents 📖

- [Description](#description)
- [Requirements](#requirements)
- [Installation](#installation)
- [Usage](#usage)
- [Methods](#methods)
- [Examples](#examples)

### Description 📙

The `Anthropic_Chat` class provides a simple interface to interact with Anthropic's artificial intelligence chatbot service.

### Requirements 🛠️

- Python 3.6 or later
- Internet connection

### Installation 📥

```bash
pip install anthropic-chat
```

### Usage 📚

To use the `Anthropic_Chat` class, first create an instance of the class and provide your API key.

```python
from anthropic_chat import Anthropic_Chat

# Create an instance of the class
chat_client = Anthropic_Chat(api_key="YOUR_API_KEY")
```

### Methods 📋

The `Anthropic_Chat` class has the following methods:

- `get_chat_response`: Sends a message to the chatbot and returns the response.

### Examples 💡

```python
# Send a message to the chatbot
response = chat_client.get_chat_response(message="Hello, world!")

# Print the chatbot's response
print(response)
```

### Output 💬

```
Hello, world! I am an artificial intelligence chatbot. What can I help you with today?
```