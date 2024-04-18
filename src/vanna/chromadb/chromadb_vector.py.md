## 📖 ChromaDB VectorStore Documentation

### Table of Contents

- [Overview](#overview)
- [Initialization](#initialization)
- [Embedding Generation](#embedding-generation)
- [Adding Training Data](#adding-training-data)
  - [SQL Queries](#sql-queries)
  - [DDL Statements](#ddl-statements)
  - [Documentation](#documentation)
- [Retrieving Training Data](#retrieving-training-data)
- [Removing Training Data](#removing-training-data)
- [Removing Collections](#removing-collections)
- [Searching for Similar Training Data](#searching-for-similar-training-data)
  - [Similar SQL Queries](#similar-sql-queries)
  - [Related DDL Statements](#related-ddl-statements)
  - [Related Documentation](#related-documentation)
- [Example Usage](#example-usage)

### Overview

The `ChromaDB_VectorStore` class provides a vectorized interface to a ChromaDB datastore, allowing for efficient search and retrieval of similar training data. It supports adding and retrieving SQL queries, DDL statements, and documentation.

### Initialization

```python
from chromadb_vectorstore import ChromaDB_VectorStore

# Create a vector store
vector_store = ChromaDB_VectorStore()
```

### Embedding Generation

The vector store uses an embedding function to generate vector representations of training data. The default embedding function uses a neural network to learn vector representations that capture the semantic meaning of the data. You can customize the embedding function by passing a different function to the constructor.

### Adding Training Data

#### SQL Queries

```python
# Add a SQL query to the vector store
vector_store.add_question_sql(
    question="What is the average salary of employees in the sales department?",
    sql="SELECT AVG(salary) FROM employees WHERE department = 'Sales';",
)
```

#### DDL Statements

```python
# Add a DDL statement to the vector store
vector_store.add_ddl(
    ddl="CREATE TABLE employees (id INT, name TEXT, salary INT);",
)
```

#### Documentation

```python
# Add documentation to the vector store
vector_store.add_documentation(
    documentation="""
    The `employees` table stores information about employees, including their ID, name, and salary.
    """,
)
```

### Retrieving Training Data

```python
# Get all training data
training_data = vector_store.get_training_data()
```

### Removing Training Data

```python
# Remove a training data item by its ID
vector_store.remove_training_data(id="my-training-data-id")
```

### Removing Collections

```python
# Remove the "sql" collection
vector_store.remove_collection(collection_name="sql")
```

### Searching for Similar Training Data

#### Similar SQL Queries

```python
# Find similar SQL queries to "What is the average salary of employees in the sales department?"
similar_sql = vector_store.get_similar_question_sql(
    question="What is the average salary of employees in the sales department?"
)
```

#### Related DDL Statements

```python
# Find DDL statements related to "CREATE TABLE employees"
related_ddl = vector_store.get_related_ddl(question="CREATE TABLE employees")
```

#### Related Documentation

```python
# Find documentation related to "employees" table
related_documentation = vector_store.get_related_documentation(question="employees")
```

### Example Usage

```python
# Initialize the vector store
vector_store = ChromaDB_VectorStore()

# Add training data
vector_store.add_question_sql(
    question="What is the average salary of employees in the sales department?",
    sql="SELECT AVG(salary) FROM employees WHERE department = 'Sales';",
)
vector_store.add_ddl(
    ddl="CREATE TABLE employees (id INT, name TEXT, salary INT);",
)
vector_store.add_documentation(
    documentation="""
    The `employees` table stores information about employees, including their ID, name, and salary.
    """,
)

# Get similar training data
similar_sql = vector_store.get_similar_question_sql(
    question="What is the average salary of employees in the sales department?"
)
related_ddl = vector_store.get_related_ddl(question="CREATE TABLE employees")
related_documentation = vector_store.get_related_documentation(question="employees")

# Use the training data to improve your search or recommendation models
```