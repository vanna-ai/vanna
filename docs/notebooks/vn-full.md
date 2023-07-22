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
sql, df, fig, followup_questions = vn.ask()
```

    Enter a question:  What are the top 10 customers by sales?


    SELECT c.c_name as customer_name,
           sum(l.l_extendedprice * (1 - l.l_discount)) as total_sales
    FROM   snowflake_sample_data.tpch_sf1.lineitem l join snowflake_sample_data.tpch_sf1.orders o
            ON l.l_orderkey = o.o_orderkey join snowflake_sample_data.tpch_sf1.customer c
            ON o.o_custkey = c.c_custkey
    GROUP BY customer_name
    ORDER BY total_sales desc limit 10;



<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }
</style>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>CUSTOMER_NAME</th>
      <th>TOTAL_SALES</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>Customer#000143500</td>
      <td>6757566.0218</td>
    </tr>
    <tr>
      <th>1</th>
      <td>Customer#000095257</td>
      <td>6294115.3340</td>
    </tr>
    <tr>
      <th>2</th>
      <td>Customer#000087115</td>
      <td>6184649.5176</td>
    </tr>
    <tr>
      <th>3</th>
      <td>Customer#000131113</td>
      <td>6080943.8305</td>
    </tr>
    <tr>
      <th>4</th>
      <td>Customer#000134380</td>
      <td>6075141.9635</td>
    </tr>
    <tr>
      <th>5</th>
      <td>Customer#000103834</td>
      <td>6059770.3232</td>
    </tr>
    <tr>
      <th>6</th>
      <td>Customer#000069682</td>
      <td>6057779.0348</td>
    </tr>
    <tr>
      <th>7</th>
      <td>Customer#000102022</td>
      <td>6039653.6335</td>
    </tr>
    <tr>
      <th>8</th>
      <td>Customer#000098587</td>
      <td>6027021.5855</td>
    </tr>
    <tr>
      <th>9</th>
      <td>Customer#000064660</td>
      <td>5905659.6159</td>
    </tr>
  </tbody>
</table>
</div>

    AI-generated follow-up questions:
    What is the total sales amount for each of the top 10 customers?
    Can you provide the details of the transactions for each of the top 10 customers?
    Which products did the top 10 customers purchase the most?
    What is the average sales amount for all customers?
    What is the distribution of sales amounts among all customers?
    How does the total sales of the top 10 customers compare to the total sales of the rest of the customers?
    Are there any seasonal patterns in the sales of the top 10 customers?
    Which regions do the top 10 customers belong to?
    What is the percentage contribution of each of the top 10 customers to the total sales?
    How have the sales of the top 10 customers changed over time?


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
