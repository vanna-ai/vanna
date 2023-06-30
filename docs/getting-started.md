# Getting Started

## How do I import the Vanna.AI library?
```python
import vanna as vn
```

## How do I set my API key?
```python
vn.api_key = 'vanna-key-...'
```

## How do I set my organization name?
```python
vn.set_org('my_org')
```

## How do I train Vanna.AI on my data?
```python
vn.store_sql(
    question="Who are the top 10 customers by Sales?", 
    sql="SELECT customer_name, sales FROM customers ORDER BY sales DESC LIMIT 10"
)
```

## How do I ask questions about my data?
```python
my_question = 'What are the top 10 ABC by XYZ?'

sql = vn.generate_sql(question=my_question, error_msg=None)
# SELECT * FROM table_name WHERE column_name = 'value'
```

## Full Example
```python
import vanna as vn

vn.api_key = 'vanna-key-...' # Set your API key
vn.set_org('') # Set your organization name

# Train Vanna.AI on your data
vn.store_sql(
    question="Who are the top 10 customers by Sales?", 
    sql="SELECT customer_name, sales FROM customers ORDER BY sales DESC LIMIT 10"
)

# Ask questions about your data
my_question = 'What are the top 10 ABC by XYZ?'

# Generate SQL
sql = vn.generate_sql(question=my_question, error_msg=None) 

# Connect to your database
conn = snowflake.connector.connect(
        user='my_user',
        password='my_password',
        account='my_account',
        database='my_database',
    )

cs = conn.cursor()

# Get results
df = vn.get_results(
    cs=cs, 
    default_db=my_default_db, 
    sql=sql
    )

# Generate Plotly code
plotly_code = vn.generate_plotly_code(
    question=my_question, 
    sql=sql, 
    df=df
    )

# Get Plotly figure
fig = vn.get_plotly_figure(
    plotly_code=plotly_code, 
    df=df
    )

```