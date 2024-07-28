import os
import sqlite3
from tempfile import TemporaryDirectory

import duckdb
from vanna.openai import OpenAI_Chat
from vanna.sqlite import SQLite_VectorStore
from vanna.sqlite.sqlite_vector import sqlite_information_schema
from vanna.duckdb import DuckDB_VectorStore


class MyVanna(SQLite_VectorStore, OpenAI_Chat):
    def __init__(self, config=None):
        SQLite_VectorStore.__init__(self, config=config)
        OpenAI_Chat.__init__(self, config=config)


with TemporaryDirectory() as temp_dir:
    database_path = os.path.join(temp_dir, "vanna.sqlite")
    vn = MyVanna(
        config={
            "api_key": os.environ["OPENAI_API_KEY"],
            "model": "gpt-4-turbo",
            "database": database_path,
        }
    )
    conn = sqlite3.connect(database_path)
    employee_ddl = """
    CREATE TABLE employee (
        employee_id INTEGER,
        name TEXT,
        occupation TEXT
    );
    """
    conn.execute(employee_ddl)
    conn.execute("""
    INSERT INTO employee VALUES
    (1, 'Alice Johnson', 'Software Engineer'),
    (2, 'Bob Smith', 'Data Scientist'),
    (3, 'Charlie Brown', 'Product Manager'),
    (4, 'Diana Prince', 'UX Designer'),
    (5, 'Ethan Hunt', 'DevOps Engineer');
    """)
    results = conn.execute("SELECT * FROM employee").fetchall()
    for row in results:
        print(row)
    conn.close()
    print(f"Temporary SQLite file created at: {database_path}")
    df_information_schema = sqlite_information_schema(database_path)
    print(df_information_schema)
    plan = vn.get_training_plan_generic(df_information_schema)
    print(plan)
    vn.train(plan=plan)
    vn.train(ddl=employee_ddl)
    training_data = vn.get_training_data()
    print(training_data)
    similar_query = vn.query_similar_embeddings("employee id", 3)
    print(similar_query)
    vn.ask(question="which employee is software engineer?")
    sql = vn.generate_sql(
        question="write a query to get all software engineers from the employees table",
        allow_llm_to_see_data=True,
    )
    print(sql)

################################


class MyVannaDuck(DuckDB_VectorStore, OpenAI_Chat):
    def __init__(self, config=None):
        DuckDB_VectorStore.__init__(self, config=config)
        OpenAI_Chat.__init__(self, config=config)


with TemporaryDirectory() as temp_dir:
    # Define the path for the DuckDB file within the temporary directory
    database_path = os.path.join(temp_dir, "vanna.duckdb")
    vn_duck = MyVannaDuck(
        config={
            "api_key": os.environ["OPENAI_API_KEY"],
            "model": "gpt-4-turbo",
            "database": database_path,
        }
    )
    # Connect to the DuckDB database file
    conn = duckdb.connect(database=database_path)
    # Create the employee table
    employee_ddl = """
    CREATE TABLE employee (
        employee_id INTEGER,
        name VARCHAR,
        occupation VARCHAR
    );
    """
    conn.execute(employee_ddl)
    conn.execute("""
    INSERT INTO employee VALUES
    (1, 'Alice Johnson', 'Software Engineer'),
    (2, 'Bob Smith', 'Data Scientist'),
    (3, 'Charlie Brown', 'Product Manager'),
    (4, 'Diana Prince', 'UX Designer'),
    (5, 'Ethan Hunt', 'DevOps Engineer');
    """)
    conn.commit()
    results = conn.execute("SELECT * FROM employee").fetchall()
    for row in results:
        print(row)
    # Close the connection
    conn.close()
    print(f"Temporary DuckDB file created at: {database_path}")
    vn_duck.connect_to_duckdb(database_path)
    df_information_schema = vn_duck.run_sql("SELECT * FROM INFORMATION_SCHEMA.COLUMNS")
    print(df_information_schema)
    plan = vn_duck.get_training_plan_generic(df_information_schema)
    print(plan)
    vn_duck.train(plan=plan)
    vn_duck.train(ddl=employee_ddl)
    training_data = vn_duck.get_training_data()
    print(training_data)
    similar_query = vn_duck.query_similar_embeddings("employee id", 3)
    print("similar query: ", similar_query)
    # vn_duck.ask(question="which employee is software engineer?")
    sql = vn_duck.generate_sql(
        question="write a query to get all software engineers from the employee table",
        allow_llm_to_see_data=True,
    )
    print(sql)
    df = vn_duck.run_sql(sql)
    print(df.name[0] == "Alice Johnson")
    print(df.name[0])
