# Using **Vanna.AI** in a Jupyter Notebook
**Vanna.AI** can be used in a Jupyter Notebook to generate SQL from natural language questions.

## Installation
```bash
%pip install vanna
```

## Import
```python
import vanna as vn
```

## Set API Key
```python
vn.api_key = 'vanna-key-...'
```

## Set Organization Name
```python
vn.set_org('my_org')
```

## Train **Vanna.AI** on your data
```python
vn.store_sql(
    question="Who are the top 10 customers by Sales?", 
    sql="SELECT customer_name, sales FROM customers ORDER BY sales DESC LIMIT 10"
)
```

## Ask questions about your data
```python
my_question = 'What are the top 10 ABC by XYZ?'

# Generate SQL
sql = vn.generate_sql(question=my_question, error_msg=None)
# SELECT * FROM table_name WHERE column_name = 'value'
```

## Run SQL
Run your SQL as you normally would.