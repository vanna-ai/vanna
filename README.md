| GitHub | PyPI | Documentation | Gurubase |
| ------ | ---- | ------------- | -------- |
| [![GitHub](https://img.shields.io/badge/GitHub-vanna-blue?logo=github)](https://github.com/vanna-ai/vanna) | [![PyPI](https://img.shields.io/pypi/v/vanna?logo=pypi)](https://pypi.org/project/vanna/) | [![Documentation](https://img.shields.io/badge/Documentation-vanna-blue?logo=read-the-docs)](https://vanna.ai/docs/) | [![Gurubase](https://img.shields.io/badge/Gurubase-Ask%20Vanna%20Guru-006BFF)](https://gurubase.io/g/vanna) |

# Vanna
Vanna is an MIT-licensed open-source Python RAG (Retrieval-Augmented Generation) framework for SQL generation and related functionality.

https://github.com/vanna-ai/vanna/assets/7146154/1901f47a-515d-4982-af50-f12761a3b2ce

![vanna-quadrants](https://github.com/vanna-ai/vanna/assets/7146154/1c7c88ba-c144-4ecf-a028-cf5ba7344ca2)

## How Vanna works
![Screen Recording 2024-01-24 at 11 21 37 AM](https://github.com/vanna-ai/vanna/assets/7146154/1d2718ad-12a8-4a76-afa2-c61754462f93)

Vanna works in two easy steps - train a RAG "model" on your data, and then ask questions which will return SQL queries that can be set up to automatically run on your database.

1. **Train a RAG "model" on your data**.
2. **Ask questions**.

![](img/vanna-readme-diagram.png)

If you don't know what RAG is, don't worry -- you don't need to know how this works under the hood to use it. You just need to know that you "train" a model, which stores some metadata and then use it to "ask" questions.

See the [base class](https://github.com/vanna-ai/vanna/blob/main/src/vanna/base/base.py) for more details on how this works under the hood.

## User Interfaces
These are some of the user interfaces that we've built using Vanna. You can use these as-is or as a starting point for your own custom interface.
- [Jupyter Notebook](https://vanna.ai/docs/postgres-openai-vanna-vannadb/)
- [vanna-ai/vanna-streamlit](https://github.com/vanna-ai/vanna-streamlit)
- [vanna-ai/vanna-flask](https://github.com/vanna-ai/vanna-flask)
- [vanna-ai/vanna-slack](https://github.com/vanna-ai/vanna-slack)

## Supported LLMs
- [OpenAI](https://github.com/vanna-ai/vanna/tree/main/src/vanna/openai)
- [Anthropic](https://github.com/vanna-ai/vanna/tree/main/src/vanna/anthropic)
- [Gemini](https://github.com/vanna-ai/vanna/blob/main/src/vanna/google/gemini_chat.py)
- [HuggingFace](https://github.com/vanna-ai/vanna/blob/main/src/vanna/hf/hf.py)
- [AWS Bedrock](https://github.com/vanna-ai/vanna/tree/main/src/vanna/bedrock)
- [Ollama](https://github.com/vanna-ai/vanna/tree/main/src/vanna/ollama)
- [Qianwen](https://github.com/vanna-ai/vanna/tree/main/src/vanna/qianwen)
- [Qianfan](https://github.com/vanna-ai/vanna/tree/main/src/vanna/qianfan)
- [Zhipu](https://github.com/vanna-ai/vanna/tree/main/src/vanna/ZhipuAI)

## Supported VectorStores
- [AzureSearch](https://github.com/vanna-ai/vanna/tree/main/src/vanna/azuresearch)
- [Opensearch](https://github.com/vanna-ai/vanna/tree/main/src/vanna/opensearch)
- [PgVector](https://github.com/vanna-ai/vanna/tree/main/src/vanna/pgvector)
- [PineCone](https://github.com/vanna-ai/vanna/tree/main/src/vanna/pinecone)
- [ChromaDB](https://github.com/vanna-ai/vanna/tree/main/src/vanna/chromadb)
- [FAISS](https://github.com/vanna-ai/vanna/tree/main/src/vanna/faiss)
- [Marqo](https://github.com/vanna-ai/vanna/tree/main/src/vanna/marqo)
- [Qdrant](https://github.com/vanna-ai/vanna/tree/main/src/vanna/qdrant)
- [Milvus](https://github.com/vanna-ai/vanna/tree/main/src/vanna/milvus)
- [ZillizCloud](https://github.com/vanna-ai/vanna/tree/main/src/vanna/zilliz)
- [Weaviate](https://github.com/vanna-ai/vanna/tree/main/src/vanna/weaviate)

## Getting started

![Screen Recording 2024-01-24 at 11 12 43 AM](https://github.com/vanna-ai/vanna/assets/7146154/8705e73b-0bd9-456f-8c5a-a841e31c1a48)

See the [documentation](https://vanna.ai/docs/) for more details.

### Install the necessary packages

```bash
pip install vanna
```

There are a number of optional packages that you can install for specific database or LLM types. See the [documentation](https://vanna.ai/docs/) for more details. Generally you'll want at least two packages -- one for the LLM and one for the vector database.

```bash
pip install vanna[postgres,openai,chromadb]
```

### Import Vanna and initialize it

```python
from vanna.openai import OpenAI_Chat
from vanna.chromadb import ChromaDB_VectorStore


class MyVanna(ChromaDB_VectorStore, OpenAI_Chat):
    def __init__(self, config=None):
        ChromaDB_VectorStore.__init__(self, config=config)
        OpenAI_Chat.__init__(self, config=config)

vn = MyVanna(config={'api_key': 'sk-...', 'model': 'gpt-4-...'})
```

See the [documentation](https://vanna.ai/docs/) for more details on how to customize initialization for your database and LLM.

### Train with DDL Statements

DDL statements contain information about the table names, columns, data types, and relationships in your database.

```python
vn.train(ddl="""
    CREATE TABLE IF NOT EXISTS my_table (
        id INT PRIMARY KEY,
        name VARCHAR(100),
        age INT
    )
""")
```

### Train with Documentation

Sometimes you may want to add documentation about your business terminology or definitions.

```python
vn.train(documentation="Our business defines OTIF score as the percentage of orders that are delivered on time and in full")
```

### Train with SQL

You can also add SQL queries to your training data. This is useful if you have some queries already laying around. You can just copy and paste those from your editor to begin generating new SQL.

```python
vn.train(sql="SELECT name, age FROM my_table WHERE name = 'John Doe'")
```

### Note on SQL Identifiers

**Important**: Use underscores (`_`) rather than hyphens (`-`) in SQL table and column names. While some databases accept hyphens with quoted identifiers (e.g., `"my-table"`), this approach:
- Requires verbose quoting in every query
- Varies by database (MySQL uses backticks, PostgreSQL/SQL Server use double quotes)
- Reduces portability across database systems

Using underscores (e.g., `my_table`) ensures your SQL is clean, portable, and works consistently across all major databases without special quoting.

## Asking the model

This will return SQL:
```python
vn.ask("What are the top 10 customers by sales?")
```

You can also get just the SQL:
```python
sql = vn.generate_sql("What are the top 10 customers by sales?")
```

You can also have it run the SQL on your database:
```python
df = vn.run_sql("What are the top 10 customers by sales?")
```

Or you can do the whole thing at once:
```python
vn.ask("What are the top 10 customers by sales?", auto_train=True)
```

You'll get back a Pandas dataframe:
```
|    | c_name                | total_value         |
|---:|:----------------------|:--------------------|
|  0 | Customer#000000002    | 7142817.809100      |
|  1 | Customer#000000004    | 6103330.669600      |
|  2 | Customer#000000007    | 6123133.900100      |
|  3 | Customer#000000008    | 6121548.656300      |
|  4 | Customer#000000010    | 6094372.955100      |
|  5 | Customer#000000013    | 6060358.426900      |
|  6 | Customer#000000016    | 6057779.034800      |
|  7 | Customer#000000022    | 6039653.633500      |
|  8 | Customer#000000098587 | 6027021.585500      |
|  9 | Customer#000000064660 | 5905659.615900      |
```

You'll also get an automated Plotly chart:
![](img/top-10-customers.png)

## RAG vs. Fine-Tuning
RAG
- Portable across LLMs
- Easy to remove training data if any of it becomes obsolete
- Much cheaper to run than fine-tuning
- More future-proof -- if a better LLM comes out, you can just swap it out

Fine-Tuning
- Good if you need to minimize tokens in the prompt
- Slow to get started
- Expensive to train and run (generally)

## Why Vanna?
1. **High accuracy on complex datasets.**
    - Vanna's capabilities are tied to the training data you give it
    - More training data means better accuracy for large and complex datasets
2. **Secure and private.**
    - Your database contents are never sent to the LLM or the vector database
    - SQL execution happens in your local environment
3. **Self learning.**
    - If using via Jupyter, you can choose to "auto-train" it on the queries that were successfully executed
    - If using via other interfaces, you can have the interface prompt the user to provide feedback on the results
    - Correct question to SQL pairs are stored for future reference and make the future results more accurate
4. **Supports any SQL database.**
    - The package allows you to connect to any SQL database that you can otherwise connect to with Python
5. **Choose your front end.**
    - Most people start in a Jupyter Notebook.
    - Expose to your end users via Slackbot, web app, Streamlit app, or a custom front end.

## Extending Vanna
Vanna is designed to connect to any database, LLM, and vector database. There's a [VannaBase](https://github.com/vanna-ai/vanna/blob/main/src/vanna/base/base.py) abstract base class that defines some basic functionality. The package provides implementations for use with OpenAI and ChromaDB. You can easily extend Vanna to use your own LLM or vector database. See the [documentation](https://vanna.ai/docs/) for more details.

## Vanna in 100 Seconds
https://github.com/vanna-ai/vanna/assets/7146154/eb90ee1e-aa05-4740-891a-4fc10e611cab

## More resources
 - [Full Documentation](https://vanna.ai/docs/) 
 - [Website](https://vanna.ai) 
 - [Discord group for support](https://discord.gg/qUZYKHremx)
