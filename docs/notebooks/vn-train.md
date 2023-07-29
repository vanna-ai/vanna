![Vanna AI](https://img.vanna.ai/vanna-train.svg)

The following notebook goes through the process of training Vanna. 

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/vanna-ai/vanna-py/blob/main/notebooks/vn-train.ipynb)

[![Open in GitHub](https://img.vanna.ai/github.svg)](https://github.com/vanna-ai/vanna-py/blob/main/notebooks/vn-ask.ipynb)

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
```

# Login
Creating a login and getting an API key is as easy as entering your email (after you run this cell) and entering the code we send to you. Check your Spam folder if you don't see the code.


```python
api_key = vn.get_api_key('my-email@example.com')
vn.set_api_key(api_key)
```

# Set your Model
You need to choose a globally unique model name. Try using your company name or another unique string. All data from models are isolated - there's no leakage.


```python
vn.set_model('my-model') # Enter your model name here. This is a globally unique identifier for your model.
```

# Automatic Training
If you'd like to use automatic training, the Vanna package can crawl your database to fetch metadata to train your model. You can put in your Snowflake credentials here. These details are only referenced within your notebook. These database credentials are never sent to Vanna's severs.


```python
vn.connect_to_snowflake(account='my-account', username='my-username', password='my-password', database='my-database')
```


```python
training_plan = vn.get_training_plan_experimental(filter_databases=['SNOWFLAKE_SAMPLE_DATA'], filter_schemas=['TPCH_SF1'])
training_plan
```

    Trying query history
    Trying INFORMATION_SCHEMA.COLUMNS for SNOWFLAKE_SAMPLE_DATA





    Train on SQL:  What are the top 10 customers ranked by total sales?
    Train on SQL:  What are the top 10 customers in terms of total sales?
    Train on SQL:  What are the top two customers with the highest total sales for each region?
    Train on SQL:  What are the top 5 customers with the highest total sales?
    Train on SQL:  What is the total quantity of each product sold in each region, ordered by region name and total quantity in descending order?
    Train on SQL:  What is the number of orders for each week, starting from the most recent week?
    Train on SQL:  What countries are in the region 'EUROPE'?
    Train on Information Schema: SNOWFLAKE_SAMPLE_DATA.TPCH_SF1 SUPPLIER
    Train on Information Schema: SNOWFLAKE_SAMPLE_DATA.TPCH_SF1 LINEITEM
    Train on Information Schema: SNOWFLAKE_SAMPLE_DATA.TPCH_SF1 CUSTOMER
    Train on Information Schema: SNOWFLAKE_SAMPLE_DATA.TPCH_SF1 PARTSUPP
    Train on Information Schema: SNOWFLAKE_SAMPLE_DATA.TPCH_SF1 PART
    Train on Information Schema: SNOWFLAKE_SAMPLE_DATA.TPCH_SF1 ORDERS
    Train on Information Schema: SNOWFLAKE_SAMPLE_DATA.TPCH_SF1 REGION
    Train on Information Schema: SNOWFLAKE_SAMPLE_DATA.TPCH_SF1 NATION




```python
vn.train(plan=training_plan)
```

# Train with DDL Statements
If you prefer to manually train, you do not need to connect to a database. You can use the train function with other parmaeters like ddl


```python
vn.train(ddl="""
    CREATE TABLE IF NOT EXISTS my-table (
        id INT PRIMARY KEY,
        name VARCHAR(100),
        age INT
    )
""")
```

# Train with Documentation
Sometimes you may want to add documentation about your business terminology or definitions.


```python
vn.train(documentation="Our business defines OTIF score as the percentage of orders that are delivered on time and in full")
```

# Train with SQL
You can also add SQL queries to your training data. This is useful if you have some queries already laying around. You can just copy and paste those from your editor to begin generating new SQL.


```python
vn.train(sql="SELECT * FROM my-table WHERE name = 'John Doe'")
```

# View Training Data
At any time you can see what training data is in your model


```python
vn.get_training_data()
```




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
      <th>id</th>
      <th>training_data_type</th>
      <th>question</th>
      <th>content</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>15-doc</td>
      <td>documentation</td>
      <td>None</td>
      <td>This is a table in the PARTSUPP table.\n\nThe ...</td>
    </tr>
    <tr>
      <th>1</th>
      <td>11-doc</td>
      <td>documentation</td>
      <td>None</td>
      <td>This is a table in the CUSTOMER table.\n\nThe ...</td>
    </tr>
    <tr>
      <th>2</th>
      <td>14-doc</td>
      <td>documentation</td>
      <td>None</td>
      <td>This is a table in the ORDERS table.\n\nThe fo...</td>
    </tr>
    <tr>
      <th>3</th>
      <td>1244-sql</td>
      <td>sql</td>
      <td>What are the names of the top 10 customers?</td>
      <td>SELECT c.c_name as customer_name\nFROM   snowf...</td>
    </tr>
    <tr>
      <th>4</th>
      <td>1242-sql</td>
      <td>sql</td>
      <td>What are the top 5 customers in terms of total...</td>
      <td>SELECT c.c_name AS customer_name, SUM(l.l_quan...</td>
    </tr>
    <tr>
      <th>5</th>
      <td>17-doc</td>
      <td>documentation</td>
      <td>None</td>
      <td>This is a table in the REGION table.\n\nThe fo...</td>
    </tr>
    <tr>
      <th>6</th>
      <td>16-doc</td>
      <td>documentation</td>
      <td>None</td>
      <td>This is a table in the PART table.\n\nThe foll...</td>
    </tr>
    <tr>
      <th>7</th>
      <td>1243-sql</td>
      <td>sql</td>
      <td>What are the top 10 customers with the highest...</td>
      <td>SELECT c.c_name as customer_name,\n       sum(...</td>
    </tr>
    <tr>
      <th>8</th>
      <td>1239-sql</td>
      <td>sql</td>
      <td>What are the top 100 customers based on their ...</td>
      <td>SELECT c.c_name as customer_name,\n       sum(...</td>
    </tr>
    <tr>
      <th>9</th>
      <td>13-doc</td>
      <td>documentation</td>
      <td>None</td>
      <td>This is a table in the SUPPLIER table.\n\nThe ...</td>
    </tr>
    <tr>
      <th>10</th>
      <td>1241-sql</td>
      <td>sql</td>
      <td>What are the top 10 customers in terms of tota...</td>
      <td>SELECT c.c_name as customer_name,\n       sum(...</td>
    </tr>
    <tr>
      <th>11</th>
      <td>12-doc</td>
      <td>documentation</td>
      <td>None</td>
      <td>This is a table in the LINEITEM table.\n\nThe ...</td>
    </tr>
    <tr>
      <th>12</th>
      <td>18-doc</td>
      <td>documentation</td>
      <td>None</td>
      <td>This is a table in the NATION table.\n\nThe fo...</td>
    </tr>
    <tr>
      <th>13</th>
      <td>1248-sql</td>
      <td>sql</td>
      <td>How many customers are in each country?</td>
      <td>SELECT n.n_name as country,\n       count(*) a...</td>
    </tr>
    <tr>
      <th>14</th>
      <td>1240-sql</td>
      <td>sql</td>
      <td>What is the number of orders placed each week?</td>
      <td>SELECT date_trunc('week', o_orderdate) as week...</td>
    </tr>
  </tbody>
</table>
</div>



# Removing Training Data
If you added some training data by mistake, you can remove it. Model performance is directly linked to the quality of the training data.


```python
vn.remove_training_data(id='my-training-data-id')
```
