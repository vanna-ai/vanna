# Vanna AI Base Class for Local or Server-Side Deployment 🤖

## Table of Contents 🔗
- [Introduction](#introduction)
- [Class Methods](#methods)
  - [Initialization](#initialization)
  - [Getting Information](#getting-information)
  - [Training](#training)
  - [Generating Content](#generating-content)
    - [Generate SQL](#generate-sql)
    - [Generate Followup Questions](#generate-followup-questions)
  - [Visualization](#visualization)
  - [Database Connectivity](#database-connectivity)
  - [Plotly Code](#plotly-code)
    - [Extract Python Code](#extract-python-code)
    - [Sanitize Plotly Code](#sanitize-plotly-code)
  - [Connecting to Databases](#connect-to-database)
  - [Training Plans](#training-plans)
  - [Creating Plotly Figures](#plotly-figures)

## Introduction 📚

The Vanna AI Base Class is the foundation for both local and server-side deployments of Vanna AI. It provides a consistent interface for interacting with the Vanna AI API, regardless of the deployment environment.

## Class Methods 📝

### Initialization 🔧
- `__init__(self, config=None)`: Initializes the Vanna AI Base Class with an optional configuration dictionary.

### Getting Information ℹ️
- `get_similar_question_sql(self, question: str, **kwargs) -> list`: Retrieves similar questions and their corresponding SQL statements.
- `get_related_ddl(self, question: str, **kwargs) -> list`: Retrieves related DDL statements to a question.
- `get_related_documentation(self, question: str, **kwargs) -> list`: Retrieves related documentation to a question.

### Training 🏋️
- `add_question_sql(self, question: str, sql: str, **kwargs) -> str`: Adds a question and its corresponding SQL query to the training data.
- `add_ddl(self, ddl: str, **kwargs) -> str`: Adds a DDL statement to the training data.
- `add_documentation(self, documentation: str, **kwargs) -> str`: Adds documentation to the training data.
- `get_training_data(self, **kwargs) -> pd.DataFrame`: Retrieves all the training data from the retrieval layer.
- `remove_training_data(id: str, **kwargs) -> bool`: Removes training data from the retrieval layer.
- `get_training_plan_generic(self, df) -> TrainingPlan`: Generates a training plan from an information schema dataframe.
- `get_training_plan_snowflake(self, filter_databases: Union[List[str], None] = None, filter_schemas: Union[List[str], None] = None, include_information_schema: bool = False, use_historical_queries: bool = True) -> TrainingPlan`: Generates a training plan by querying Snowflake's information schema and historical query data.

### Generating Content 📝
#### Generate SQL 💻
- `generate_sql(self, question: str, **kwargs) -> str`: Generates an SQL query that answers a question using an LLM.
- `generate_followup_questions(self, question: str, sql: str, df: pd.DataFrame, n_questions: int = 5, **kwargs) -> list`: Generates a list of followup questions that a user might ask about the results of an SQL query.
- `generate_questions(self, **kwargs) -> List[str]`: Generates a list of questions that a user might ask Vanna AI.
- `generate_summary(self, question: str, df: pd.DataFrame, **kwargs) -> str`: Generates a summary of the results of an SQL query.

#### Visualization 📊
- `generate_plotly_code(self, question: str = None, sql: str = None, df_metadata: str = None, **kwargs) -> str`: Generates Plotly code to visualize the results of an SQL query.
- `get_plotly_figure(self, plotly_code: str, df: pd.DataFrame, dark_mode: bool = True) -> plotly.graph_objs.Figure`: Retrieves a Plotly figure from a dataframe and Plotly code.

### Database Connectivity 🔌
- `connect_to_snowflake(self, account: str, username: str, password: str, database: str, role: Union[str, None] = None, warehouse: Union[str, None] = None)`: Connects to a Snowflake database.
- `connect_to_sqlite(self, url: str)`: Connects to a SQLite database.
- `connect_to_postgres(self, host: str = None, dbname: str = None, user: str = None, password: str = None, port: int = None)`: Connects to a Postgres database.
- `connect_to_mysql(self, host: str = None, dbname: str = None, user: str = None, password: str = None, port: int = None)`: Connects to a MySQL database.
- `connect_to_oracle(self, user: str = None, password: str = None, dsn: str = None)`: Connects to an Oracle database.
- `connect_to_bigquery(self, cred_file_path: str = None, project_id: str = None)`: Connects to a BigQuery database.
- `connect_to_duckdb(self, url: str, init_sql: str = None)`: Connects to a DuckDB database.
- `connect_to_mssql(self, odbc_conn_str: str)`: Connects to a Microsoft SQL Server database.

### Plotly Code 📊
#### Extract Python Code 🐍
- `_extract_python_code(self, markdown_string: str) -> str`: Extracts Python code from a markdown string.

#### Sanitize Plotly Code 🧹
- `_sanitize_plotly_code(self, raw_plotly_code: str) -> str`: Removes the fig.show() statement from the plotly code.

### Creating Plotly Figures 🖼️
- `get_plotly_figure(self, plotly_code: str, df: pd.DataFrame, dark_mode: bool = True) -> plotly.graph_objs.Figure`: Retrieves a Plotly figure from a dataframe and Plotly code.

### Example Usage 💻

```python
import vanna

# Initialize the Vanna AI Base Class
vn = vanna.VannaBase()

# Connect to a Snowflake database
vn.connect_to_snowflake(
    account="myaccount",
    username="myusername",
    password="mypassword",
    database="mydatabase",
)

# Ask Vanna AI a question
question = "What are the top 10 customers by sales?"
sql, df, fig = vn.ask(question, print_results=True)
```