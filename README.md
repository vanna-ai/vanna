![](https://img.vanna.ai/vanna-github.svg)

| GitHub | PyPI | Documentation |
| ------ | ---- | ------------- |
| [![GitHub](https://img.shields.io/badge/GitHub-vanna-blue?logo=github)](https://github.com/vanna-ai/vanna) | [![PyPI](https://img.shields.io/pypi/v/vanna?logo=pypi)](https://pypi.org/project/vanna/) | [![Documentation](https://img.shields.io/badge/Documentation-vanna-blue?logo=read-the-docs)](https://vanna.ai/docs/) |

# Vanna.AI - Personalized AI SQL Agent

https://github.com/vanna-ai/vanna/assets/7146154/1901f47a-515d-4982-af50-f12761a3b2ce

## How Vanna works
Vanna works in two easy steps - train a model on your data, and then ask questions.

1. **Train a model on your data**.
2. **Ask questions**.

When you ask a question, we utilize a custom model for your dataset to generate SQL, as seen below. Your model performance and accuracy depends on the quality and quantity of training data you use to train your model.
<img width="1725" alt="how-vanna-works" src="https://github.com/vanna-ai/vanna/assets/7146154/5e2e2179-ed7a-4df4-92a2-1c017923a675">

## Getting started
You can start by [automatically training Vanna (currently works for Snowflake)](https://vanna.ai/docs/vn-train.html) or add manual training data.

### Install Vanna
```
pip install vanna
```

Depending on the database you're using, you can also install the associated database drivers
```
pip install 'vanna[snowflake]'
```

### Import Vanna
```python
import vanna as vn
```

### Train with DDL Statements
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

### Train with Documentation
Sometimes you may want to add documentation about your business terminology or definitions.

```python
vn.train(documentation="Our business defines OTIF score as the percentage of orders that are delivered on time and in full")
```

### Train with SQL
You can also add SQL queries to your training data. This is useful if you have some queries already laying around. You can just copy and paste those from your editor to begin generating new SQL.

```python
vn.train(sql="SELECT * FROM my-table WHERE name = 'John Doe'")
```


## Asking questions
```python
vn.ask("What are the top 10 customers by sales?")
```

    SELECT c.c_name as customer_name,
           sum(l.l_extendedprice * (1 - l.l_discount)) as total_sales
    FROM   snowflake_sample_data.tpch_sf1.lineitem l join snowflake_sample_data.tpch_sf1.orders o
            ON l.l_orderkey = o.o_orderkey join snowflake_sample_data.tpch_sf1.customer c
            ON o.o_custkey = c.c_custkey
    GROUP BY customer_name
    ORDER BY total_sales desc limit 10;



<div>
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

## Why Vanna?

1. **High accuracy on complex datasets.**
    - Vanna’s capabilities are tied to the training data you give it
    - More training data means better accuracy for large and complex datasets
2. **Secure and private.**
    - Your database contents  are never sent to Vanna’s servers
    - We only see the bare minimum - schemas & queries.
3. **Isolated, custom model.**
    - You train a custom model specific to your database and your schema.
    - Nobody else can use your model or view your model’s training data unless you choose to add members to your model or make it public
    - We use a combination of third-party foundational models (OpenAI, Google) and our own LLM.
4. **Self learning.**
    - As you use Vanna more, your model continuously improves as we augment your training data
5. **Supports many databases.**
    - We have out-of-the-box support Snowflake, BigQuery, Postgres
    - You can easily make a connector for any [database](https://docs.vanna.ai/databases/)
6. **Pretrained models.**
    - If you’re a data provider you can publish your models for anyone to use
    - As part of our roadmap, we are in the process of pre-training models for common datasets (Google Ads, Facebook ads, etc)
7. **Choose your front end.**
    - Start in a Jupyter Notebook.
    - Expose to business users via Slackbot, web app, Streamlit app, or Excel plugin.
    - Even integrate in your web app for customers.

## More resources
 - [Full Documentation](https://vanna.ai/docs/)
 - [Website](https://vanna.ai)
 - [Slack channel for support](https://join.slack.com/t/vanna-ai/shared_invite/zt-1unu0ipog-iE33QCoimQiBDxf2o7h97w)
 - [LinkedIn](https://www.linkedin.com/company/vanna-ai/)
