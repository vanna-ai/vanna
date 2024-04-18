## 🤖 ZhipuAI_Chat 🤖

### Table of Contents

- [Introduction](#introduction)
- [Dependencies](#dependencies)
- [Class Definition](#class-definition)
  - [Attributes](#attributes)
  - [Methods](#methods)
- [Usage](#usage)
- [Example](#example)

### Introduction

The `ZhipuAI_Chat` class is an easy-to-use wrapper for the ZhipuAI Chat API, which allows you to generate text and code from natural language prompts. It provides a simplified interface for sending prompts to the API and receiving the results.

### Dependencies

This library depends on the following:

- `pandas`
- `zhipuai`

### Class Definition

#### Attributes

- `api_key`: Your ZhipuAI API key.
- `model`: The ZhipuAI model to use. The default is "glm-4".

#### Methods

- `get_sql_prompt`: Generates a prompt for the ZhipuAI Chat API to generate SQL code from a natural language prompt.
- `get_followup_questions_prompt`: Generates a prompt for the ZhipuAI Chat API to generate followup questions from a previous question and SQL code.
- `generate_question`: Generates a natural language question from a SQL query.
- `generate_plotly_code`: Generates Python Plotly code to chart the results of a pandas DataFrame.
- `submit_prompt`: Sends a prompt to the ZhipuAI Chat API and returns the response.

### Usage

To use the `ZhipuAI_Chat` class, simply initialize it with your API key. You can then use the `get_sql_prompt`, `get_followup_questions_prompt`, `generate_question`, `generate_plotly_code`, and `submit_prompt` methods to interact with the ZhipuAI Chat API.

### Example

The following code shows how to use the `ZhipuAI_Chat` class to generate SQL code from a natural language prompt:

```
from zhipuai_chat import ZhipuAI_Chat

# Initialize the ZhipuAI_Chat class with your API key
chat = ZhipuAI_Chat(api_key="YOUR_API_KEY")

# Generate a prompt for the ZhipuAI Chat API to generate SQL code
prompt = chat.get_sql_prompt(
    "What is the total sales for each product category?",
    question_sql_list=[],
    ddl_list=[],
    doc_list=[],
)

# Send the prompt to the ZhipuAI Chat API and receive the response
response = chat.submit_prompt(prompt)

# The response will be a SQL query that answers the natural language prompt
print(response)
```

### Example Usage - Generate SQL

```python
from zhipuai_chat import ZhipuAI_Chat

# Initialize the ZhipuAI_Chat class with your API key
chat = ZhipuAI_Chat(api_key="YOUR_API_KEY")

# Generate a prompt for the ZhipuAI Chat API to generate SQL code
prompt = chat.get_sql_prompt(
    "What is the total sales for each product category?",
    question_sql_list=[],
    ddl_list=[],
    doc_list=[],
)

# Send the prompt to the ZhipuAI Chat API and receive the response
response = chat.submit_prompt(prompt)

# The response will be a SQL query that answers the natural language prompt
sql_query = response
```

### Example Usage - Generate Follow-up Question

```python
from zhipuai_chat import ZhipuAI_Chat

# Initialize the ZhipuAI_Chat class with your API key
chat = ZhipuAI_Chat(api_key="YOUR_API_KEY")

# Generate a prompt for the ZhipuAI Chat API to generate SQL code
prompt = chat.get_followup_questions_prompt(
    "What is the total sales for each product category?",
    df=pd.DataFrame(),
    question_sql_list=[],
    ddl_list=[],
    doc_list=[],
)

# Send the prompt to the ZhipuAI Chat API and receive the response
response = chat.submit_prompt(prompt)

# The response will be a list of follow-up questions
followup_questions = response
```

### Example Usage - Generate Question from SQL

```python
from zhipuai_chat import ZhipuAI_Chat

# Initialize the ZhipuAI_Chat class with your API key
chat = ZhipuAI_Chat(api_key="YOUR_API_KEY")

# Generate a prompt for the ZhipuAI Chat API to generate SQL code
prompt = chat.generate_question(
    "SELECT SUM(sales) FROM products GROUP BY product_category"
)

# Send the prompt to the ZhipuAI Chat API and receive the response
response = chat.submit_prompt(prompt)

# The response will be a question in natural language
question = response
```

### Example Usage - Generate Plotly Code

```python
from zhipuai_chat import ZhipuAI_Chat

# Initialize the ZhipuAI_Chat class with your API key
chat = ZhipuAI_Chat(api_key="YOUR_API_KEY")

# Generate a prompt for the ZhipuAI Chat API to generate SQL code
prompt = chat.generate_plotly_code(
    df=pd.DataFrame(),
)

# Send the prompt to the ZhipuAI Chat API and receive the response
response = chat.submit_prompt(prompt)

# The response will be Python Plotly code
plotly_code = response
```