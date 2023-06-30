---
marp: true
theme: gaia
_class: lead
paginate: true
backgroundColor: #111827
color: #fff
header: 'Updated: 2023-06-30'
---
<style>
  strong {
    font-family: 'Roboto Slab';
    color: transparent !important;
    background: linear-gradient(15deg, #009efd, #2af598);
    background-clip: text;
    -webkit-background-clip: text;
  }
  marp-pre {
    font-family: 'Fira Code Light';
    font-size: 0.75em;
    background: #000;
    border-radius: 30px;
  }
</style>

![bg left:40% 80%](https://ask.vanna.ai/static/img/vanna.svg)

# **Vanna.AI**
## Python Package

For Natural Language to SQL
(and associated functionality)

[Full Documentation Reference](https://vanna.ai)

[Slack]()

support@vanna.ai

---
# What can you do with **Vanna.AI**?

**Vanna.AI** has a Python package that allows you to convert natural language to SQL.

```python
import vanna as vn

vn.api_key = 'vanna-key-...' # Set your API key
vn.set_org('') # Set your organization name

my_question = 'What are the top 10 ABC by XYZ?'

sql = vn.generate_sql(question=my_question, error_msg=None) 
# SELECT * FROM table_name WHERE column_name = 'value'

(my_df, error_msg) = vn.run_sql(cs: snowflake.Cursor, sql=sql)

vn.generate_plotly_code(question=my_question, df=my_df)
# fig = px.bar(df, x='column_name', y='column_name')

vn.run_plotly_code(plotly_code=fig, df=my_df)

```

---

# Installation

## Global Installation
```bash
pip install vanna
```
or
```bash
pip3 install vanna
```

## Use a Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate
pip install vanna
```

---