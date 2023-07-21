![Vanna AI](https://img.vanna.ai/vanna-full.svg)

This notebook will help you unleash the full potential of AI-powered data analysis at your organization. We'll go through how to "bulk train" Vanna and generate SQL, tables, charts, and explanations, all with minimal code and effort. For more about Vanna, see our [intro blog post](https://medium.com/vanna-ai/intro-to-vanna-a-python-based-ai-sql-co-pilot-218c25b19c6a).

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/vanna-ai/vanna-py/blob/main/notebooks/vn-full.ipynb)

[![Open in GitHub](https://img.vanna.ai/github.svg)](https://github.com/vanna-ai/vanna-py/blob/main/notebooks/vn-full.ipynb)

# Install Vanna
First we install Vanna from [PyPI](https://pypi.org/project/vanna/) and import it.
Here, we'll also install the Snowflake connector. If you're using a different database, you'll need to install the appropriate connector.


```python
%pip install vanna
%pip install snowflake-connector-python
```


```python
import vanna as vn
import snowflake.connector
import pandas as pd
```

# Login
Creating a login and getting an API key is as easy as entering your email (after you run this cell) and entering the code we send to you. Check your Spam folder if you don't see the code.


```python
api_key = vn.get_api_key('my-email@example.com')
vn.set_api_key(api_key)
```

# Set your Dataset
You need to choose a globally unique dataset name. Try using your company name or another unique string. All data from dataset are isolated - there's no leakage.


```python
vn.set_dataset('my-dataset') # Enter your dataset name here. This is a globally unique identifier for your dataset.
```

# Add Training Data
Instead of adding question / SQL pairs one by one, let's load a bunch in from a JSON, all at once. You'll make your own JSON that represents your data. You can see the [format here](https://github.com/vanna-ai/vanna-training-queries/blob/main/tpc-h/questions.json)


```python
training_json = "https://raw.githubusercontent.com/vanna-ai/vanna-training-queries/main/tpc-h/questions.json" #@param {type:"string"}

for _, row in pd.read_json(training_json).iterrows():
  vn.train(question=row.question, sql=row.sql)
```

# Set Database Connection
These details are only referenced within your notebook. These database credentials are never sent to Vanna's severs.


```python
vn.connect_to_snowflake(account='my-account', username='my-username', password='my-password', database='my-database')
```

# Get Results
This gets the SQL, gets the dataframe, and prints them both. Note that we use your connection string to execute the SQL on your warehouse from your local instance. Your connection nor your data gets sent to Vanna's servers. For more info on how Vanna works, [see this post](https://medium.com/vanna-ai/how-vanna-works-how-to-train-it-data-security-8d8f2008042).


```python
sql, df, fig = vn.ask()
```

    Enter a question:  Who are the top 10 customers by sales?


    SELECT c.c_name as customer_name,
           sum(l.l_extendedprice * (1 - l.l_discount)) as total_sales
    FROM   snowflake_sample_data.tpch_sf1.lineitem l join snowflake_sample_data.tpch_sf1.orders o
            ON l.l_orderkey = o.o_orderkey join snowflake_sample_data.tpch_sf1.customer c
            ON o.o_custkey = c.c_custkey
    GROUP BY customer_name
    ORDER BY total_sales desc limit 10;
    |    | CUSTOMER_NAME      |   TOTAL_SALES |
    |---:|:-------------------|--------------:|
    |  0 | Customer#000143500 |   6.75757e+06 |
    |  1 | Customer#000095257 |   6.29412e+06 |
    |  2 | Customer#000087115 |   6.18465e+06 |
    |  3 | Customer#000131113 |   6.08094e+06 |
    |  4 | Customer#000134380 |   6.07514e+06 |


# Improve Your Training Data
Did everything work well above? If so, improve your training data by adding the question / SQL pair to your organization's model's training data in one line of code.


```python
vn.store_sql(
    question=my_question,
    sql=sql,
)
```

# Run as a Web App
If you would like to use this functionality in a web app, you can deploy the Vanna Streamlit app and use your own secrets. See [this repo](https://github.com/vanna-ai/vanna-streamlit).
