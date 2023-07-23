![Vanna AI](https://img.vanna.ai/vanna-training.svg)

This notebook will take you through how to use Vanna on your own data, including training an isolated model for your schema / organization. For more about Vanna, see our [intro blog post](https://medium.com/vanna-ai/intro-to-vanna-a-python-based-ai-sql-co-pilot-218c25b19c6a).

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/vanna-ai/vanna-py/blob/main/notebooks/vn-training.ipynb)

[![Open in GitHub](https://img.vanna.ai/github.svg)](https://github.com/vanna-ai/vanna-py/blob/main/notebooks/vn-training.ipynb)

# Install Vanna
First we install Vanna from [PyPI](https://pypi.org/project/vanna/) and import it.


```python
%pip install vanna
```


```python
import vanna as vn
```

# Login
Creating a login and getting an API key is as easy as entering your email (after you run this cell) and entering the code we send to you. Check your Spam folder if you don't see the code.


```python
api_key = vn.get_api_key('my-email@example.com')
vn.set_api_key(api_key)
```

# Set your Dataset
You need to choose a globally unique organization name. Try using your company name or another unique string. All data from datasets are isolated - there's no leakage. Datasets are private by default. You can add other users to your dataset later.


```python
vn.set_dataset('my-dataset') # Enter your dataset name here. This is a globally unique identifier for your dataset.
```

    Would you like to create dataset 'my-unique-dataset-name'? (y/n):  y
    What type of database would you like to use? (Snowflake, BigQuery, Postgres, etc.):  Postgres


# Training
Vanna needs to learn about your schema. Take some prior SQL queries and the questions associated with them and enter them below. The ones we've done reflect a fictitious dataset that you'll want to replace with your own queries and questions.


```python
vn.add_sql(
    question='What are the top 10 customers?',
    sql='SELECT customer_name, sales FROM customers ORDER BY sales desc LIMIT 10'
)
```




    True




```python
vn.add_sql(
    question='What are the top 10 customers in the US?',
    sql="SELECT customer_name, sales FROM customers WHERE country_name = 'UNITED STATES' ORDER BY sales desc LIMIT 10"
)
```




    True




```python
vn.add_sql(
    question='How many regions are there?',
    sql='SELECT DISTINCT region FROM customers'
)
```




    True



# Generate SQL
Ok, now we are ready to ask plain English questions and see whether Vanna can answer them! Once you get the SQL back, you can execute in Jupyter or on another interface.


```python
sql = vn.generate_sql('How many customers are there in each region?')
print(sql)
```

    SELECT region,
           count(distinct customer_id) as num_customers
    FROM   customers
    GROUP BY region


# Read the [Full Documentation Reference](https://docs.vanna.ai) for More Functionality

So that was cool, but there's more. Vanna can actually execute the SQL (in a privacy / security safe manner), generate explanations for what the SQL is doing, and even generate visualizations. [Click here](https://github.com/vanna-ai/vanna-py/blob/main/notebooks/vn-full.ipynb) for the next notebook that goes through this.
