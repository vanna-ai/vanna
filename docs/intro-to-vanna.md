# Intro to Vanna: A Python-based AI SQL co-pilot

**TLDR**: We help data people that know Python write SQL faster using AI. [See our starter notebook here](notebooks/vn-starter.md).

## The deluge of data

We are bathing in an ocean of data, sitting in Snowflake or BigQuery, that is brimming with potential insights. Yet only a small fraction of people in an enterprise have the two skills required to harness the data —

1. A solid comprehension of advanced SQL, and
2. A comprehensive knowledge of the data structure & schema

## The burden of being data-savvy

Since you are reading this, chances are you are one of those fortunate few (data analysts, data scientists, data engineers, etc) with those abilities. It’s an invaluable skill, but you also get hit tons requests requiring you to write complex SQL queries. Annoying!

## Introducing Vanna, the SQL co-pilot

Vanna, at its core, is a co-pilot to Python & SQL savvy data people to to streamline the process of writing custom SQL on your company’s data warehouse using AI and LLMs. Most of our users use our Python package directly via Jupyter Notebooks ([starter notebook here](https://github.com/vanna-ai/vanna-notebooks/blob/main/vn-starter.ipynb)) —

```python
sql = vn.generate_sql(question='What are the top 10 customers by Sales?')
print(sql)
```

And here are the results —

```sql
SELECT customer_name,
       total_sales
FROM   (SELECT c.c_name as customer_name,
               sum(l.l_extendedprice * (1 - l.l_discount)) as total_sales,
               row_number() OVER (ORDER BY sum(l.l_extendedprice * (1 - l.l_discount)) desc) as rank
        FROM   snowflake_sample_data.tpch_sf1.lineitem l join snowflake_sample_data.tpch_sf1.orders o
                ON l.l_orderkey = o.o_orderkey join snowflake_sample_data.tpch_sf1.customer c
                ON o.o_custkey = c.c_custkey
        GROUP BY customer_name)
WHERE  rank <= 10;
```

## Getting started with Vanna in a Notebook

Vanna is super easy to get started with —

1. **Grab an API key** directly through the notebook
2. **Train a custom model** on some past queries from your data warehouse
3. **Ask questions in plain English** and get back SQL that you can run in your workflow

Check out the full starter notebook here.

Vanna is built with a privacy-first and security-first design — **your data never leaves your environment**.

## Using Vanna with a Streamlit front end

[Streamlit](https://streamlit.io/) is an open source pure Python front end. We have built an UI for Vanna on top of Streamlit, that you can either use directly (eg our hosted version), and that you can clone, download, optionally modify, and self host.

If you choose to self host it, you can run Vanna with a UI without any data leaving your environment.

![Image](https://miro.medium.com/v2/resize:fit:640/format:webp/1*PmScp647UWIaxUatib_4SQ.png)

[Check out the Streamlit UI here](https://github.com/vanna-ai/vanna-streamlit).

## Conclusion

Vanna is a powerful tool for data people that know Python to write SQL faster using AI. It's easy to get started with, and you can even use it with a Streamlit front end for a more interactive experience. Best of all, it's built with a privacy-first and security-first design, so your data never leaves your environment. Give it a try and see how it can streamline your SQL writing process.