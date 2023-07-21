![Vanna AI](https://img.vanna.ai/vanna-starter.svg)

This notebook takes you through the most simple example of using Vanna. For more about Vanna, see our [intro blog post](https://medium.com/vanna-ai/intro-to-vanna-a-python-based-ai-sql-co-pilot-218c25b19c6a).

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/vanna-ai/vanna-py/blob/main/notebooks/vn-starter.ipynb)

[![Open in GitHub](https://img.vanna.ai/github.svg)](https://github.com/vanna-ai/vanna-py/blob/main/notebooks/vn-starter.ipynb)

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

# Choose Datasets
We need to choose which datasets we want to use. In this example, we use a demo dataset that every user on Vanna has access to called `demo-tpc-h`. This is the [default TPC dataset](https://www.tpc.org/tpch/) that comes with every installation of Snowflake and represents a small business. [Details about this dataset are here](https://docs.snowflake.com/en/user-guide/sample-data-tpch). The training data for this dataset is [here](https://github.com/vanna-ai/vanna-training-queries/blob/main/tpc-h/questions.json)


```python
vn.set_dataset('demo-tpc-h')
```

# Ask a Question


```python
sql = vn.generate_sql(question='What are the top 10 customers by Sales?')
print(sql)
```

    SELECT c.c_name as customer_name,
           sum(l.l_extendedprice * (1 - l.l_discount)) as total_sales
    FROM   snowflake_sample_data.tpch_sf1.customer c join snowflake_sample_data.tpch_sf1.orders o
            ON c.c_custkey = o.o_custkey join snowflake_sample_data.tpch_sf1.lineitem l
            ON o.o_orderkey = l.l_orderkey
    GROUP BY customer_name
    ORDER BY total_sales desc limit 10;


# Want to use Vanna with your own data?

Get started with [this notebook](https://github.com/vanna-ai/vanna-notebooks/blob/main/vn-training.ipynb).
