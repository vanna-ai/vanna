## 📘 Vanna.AI Python SDK Documentation

This document provides a comprehensive guide to using the Vanna.AI Python SDK.

### Table of Contents

- [Introduction](#introduction)
- [Installation](#installation)
- [API Reference](#api-reference)
    - [Authentication](#authentication)
    - [Model Management](#model-management)
    - [Training Data Management](#training-data-management)
    - [SQL Generation](#sql-generation)
    - [Meta Generation](#meta-generation)
    - [Followup Question Generation](#followup-question-generation)
    - [Question Generation](#question-generation)
    - [Training](#training)
- [Example Usage](#example-usage)
- [Support](#support)

### Introduction

The Vanna.AI Python SDK is a library that enables you to interact with the Vanna.AI API from within your Python code. With this SDK, you can:

- Authenticate to the Vanna.AI API
- Manage models
- Manage training data
- Generate SQL queries
- Generate meta information about data
- Generate followup questions
- Generate questions
- Train models

### Installation

To install the Vanna.AI Python SDK, run the following command:

```
pip install vanna
```

### API Reference

**Authentication**

```python
from vanna.api import get_api_key

api_key = get_api_key(email="my-email@example.com")
```

**Model Management**

```python
from vanna.api import create_model, set_model

create_model(model="my-model", db_type="postgres")
set_model(model="my-model")
```

**Training Data Management**

```python
from vanna.api import add_sql, add_ddl, add_documentation, remove_sql

add_sql(question="What is the average salary of employees?", sql="SELECT AVG(salary) FROM employees")
add_ddl(ddl="CREATE TABLE employees (id INT, name VARCHAR(255), salary INT)")
add_documentation(documentation="This is a table of employees.")
remove_sql(question="What is the average salary of employees?")
```

**SQL Generation**

```python
from vanna.api import generate_sql

sql = generate_sql(question="What is the average salary of employees?")
```

**Meta Generation**

```python
from vanna.api import generate_meta

meta = generate_meta(question="What is the average salary of employees?")
```

**Followup Question Generation**

```python
from vanna.api import generate_followup_questions

followup_questions = generate_followup_questions(question="What is the average salary of employees?", df=pd.DataFrame())
```

**Question Generation**

```python
from vanna.api import generate_questions

questions = generate_questions()
```

**Training**

```python
from vanna.api import train

train(question="What is the average salary of employees?", sql="SELECT AVG(salary) FROM employees")
```

### Example Usage

The following code snippet shows you how to use the Vanna.AI Python SDK to generate a SQL query from a natural language question:

```python
from vanna.api import generate_sql

question = "What is the average salary of employees?"
sql = generate_sql(question)

print(sql)
```

### Support

If you have any questions or need help using the Vanna.AI Python SDK, please reach out to our support team at support@vanna.ai.

### Changelog

**0.1.0** (2023-08-08)

- Initial release