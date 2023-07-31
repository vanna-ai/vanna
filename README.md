| GitHub | PyPI | Colab | Documentation |
| ------ | ---- | ----- | ------------- |
| [![GitHub](https://img.shields.io/badge/GitHub-vanna--py-blue?logo=github)](https://github.com/vanna-ai/vanna-py) | [![PyPI](https://img.shields.io/pypi/v/vanna?logo=pypi)](https://pypi.org/project/vanna/) | [![Colab](https://img.shields.io/badge/Colab-vanna--py-blue?logo=google-colab)](https://colab.research.google.com/github/vanna-ai/vanna-py/blob/main/notebooks/vn-starter.ipynb) | [![Documentation](https://img.shields.io/badge/Documentation-vanna--py-blue?logo=read-the-docs)](https://docs.vanna.ai) |

# Vanna.AI - Personalized AI SQL Agent

**Let Vanna.AI write your nasty SQL for you**. Vanna is a Python based AI SQL agent trained on your schema that writes complex SQL in seconds. `pip install vanna` to get started now.

## An example

A business user asks you **"who are the top 2 customers in each region?"** 

### The old way :rage: :tired_face: :hankey:
Simple question to ask, not so fun to answer. You spend over an hour a) finding the tables, b) figuring out out the joins, c) look up the syntax for ranking, d) putting this into a CTE, e) filtering by rank, and f) choosing the correct metrics. Finally, you come up with this ugly mess - 

```sql
with ranked_customers as (SELECT c.c_name as customer_name,
  r.r_name as region_name,
  row_number() OVER (PARTITION BY r.r_name
     ORDER BY sum(l.l_quantity * l.l_extendedprice) desc) as rank	
     FROM   snowflake_sample_data.tpch_sf1.customer c join snowflake_sample_data.tpch_sf1.orders o
         ON c.c_custkey = o.o_custkey join snowflake_sample_data.tpch_sf1.lineitem l
         ON o.o_orderkey = l.l_orderkey join snowflake_sample_data.tpch_sf1.nation n
         ON c.c_nationkey = n.n_nationkey join snowflake_sample_data.tpch_sf1.region r
         ON n.n_regionkey = r.r_regionkey
             GROUP BY customer_name, region_name)
SELECT region_name,
       customer_name
FROM   ranked_customers
WHERE  rank <= 2;
```

### The Vanna way :heart_eyes: :star2: :rocket:
With Vanna, you train up a custom model on your data warehouse, and simply enter this in your Jupyter Notebook - 

```python
import vanna as vn
vn.set_model('your-model')
vn.ask('who are the top 2 customers in each region?')
```

Vanna generates that nasty SQL above for you, runs it (locally & securely) and gives you back a Dataframe in seconds:

| customer_name | total_sales |
| ------------- | ----------- |
| Customer#000000001 |  68127.72 |
| Customer#000000002 |  65898.69 |

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
    - You can easily make a connector for any database https://docs.vanna.ai/databases/
6. **Pretrained models.**
    - If you’re a data provider you can publish your models for anyone to use
    - As part of our roadmap, we are in the process of pre-training models for common datasets (Google Ads, Facebook ads, etc)
7. **Choose your front end.**
    - Start in a Jupyter Notebook. 
    - Expose to business users via Slackbot, web app, Streamlit app, or Excel plugin. 
    - Even integrate in your web app for customers.

## Getting started
Training a model - link to vn-train notebook. Copy some code below

```python
%pip install vanna
import vanna as vn

vn.train(
    question="Which products have the highest sales?",
    sql="...",
)
```


## Asking questions
Show one question - returning chart, etc.

```python
adsfdaf
```

## More resources
 - [Full Documentation](https://docs.vanna.ai)
 - Website
 - Slack channel for support
 - LinkedIn
