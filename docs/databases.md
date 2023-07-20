# How to use Vanna with various databases

You can use Vanna with any database that you can connect to via Python. Here are some examples of how to connect to various databases.

All you have to do is provide Vanna with a function that takes in a SQL query and returns a Pandas DataFrame. Here are some examples of how to do that.

**PostgreSQL**

```python
import pandas as pd
import psycopg2

conn_details = {...}  # fill this with your connection details
conn_postgres = psycopg2.connect(**conn_details)

def sql_to_df_postgres(sql: str) -> pd.DataFrame:
    df = pd.read_sql_query(sql, conn_postgres)
    return df

vn.sql_to_df = sql_to_df_postgres
```

**Snowflake**

```python
import pandas as pd
from snowflake.connector.pandas_tools import pd_read_sql
from snowflake.connector import connect

conn_details = {...}  # fill this with your connection details
conn_snowflake = connect(**conn_details)

def sql_to_df_snowflake(sql: str) -> pd.DataFrame:
    df = pd_read_sql(sql, conn_snowflake)
    return df

vn.sql_to_df = sql_to_df_snowflake
```

**Google BigQuery**

```python
from google.cloud import bigquery
import pandas as pd

project_id = 'your-project-id'  # replace with your Project ID
client_bigquery = bigquery.Client(project=project_id)

def sql_to_df_bigquery(sql: str) -> pd.DataFrame:
    df = client_bigquery.query(sql).to_dataframe()
    return df

vn.sql_to_df = sql_to_df_bigquery
```

**Amazon Athena**

```python
import pandas as pd
from pyathena import connect

conn_details = {...}  # fill this with your connection details
conn_athena = connect(**conn_details)

def sql_to_df_athena(sql: str) -> pd.DataFrame:
    df = pd.read_sql(sql, conn_athena)
    return df

vn.sql_to_df = sql_to_df_athena
```

**Amazon Redshift**

```python
import pandas as pd
import psycopg2

conn_details = {...}  # fill this with your connection details
conn_redshift = psycopg2.connect(**conn_details)

def sql_to_df_redshift(sql: str) -> pd.DataFrame:
    df = pd.read_sql_query(sql, conn_redshift)
    return df

vn.sql_to_df = sql_to_df_redshift
```

Sure, here is an example for Google Cloud SQL using the MySQL connector:

**Google Cloud SQL (MySQL)**

```python
import pandas as pd
import mysql.connector

conn_details = {...}  # fill this with your connection details
conn_google_cloud_sql = mysql.connector.connect(**conn_details)

def sql_to_df_google_cloud_sql(sql: str) -> pd.DataFrame:
    df = pd.read_sql(sql, conn_google_cloud_sql)
    return df
```

Note: Google Cloud SQL supports MySQL, PostgreSQL, and SQL Server. The above example uses MySQL. If you are using PostgreSQL or SQL Server, you should use the appropriate connector.

**SQLite**

```python
import sqlite3
import pandas as pd

db_path = 'path_to_your_db'  # replace with your SQLite DB path
conn_sqlite = sqlite3.connect(db_path)

def sql_to_df_sqlite(sql: str) -> pd.DataFrame:
    df = pd.read_sql_query(sql, conn_sqlite)
    return df

vn.sql_to_df = sql_to_df_sqlite
```

**Microsoft SQL Server**

```python
import pandas as pd
import pyodbc

conn_details = {...}  # fill this with your connection details
conn_sql_server = pyodbc.connect(**conn_details)

def sql_to_df_sql_server(sql: str) -> pd.DataFrame:
    df = pd.read_sql(sql, conn_sql_server)
    return df

vn.sql_to_df = sql_to_df_sql_server
```
