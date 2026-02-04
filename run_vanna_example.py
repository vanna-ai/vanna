import os
import pandas as pd
from vanna.openai.openai_chat import OpenAI_Chat
from vanna.chromadb.chromadb_vector import ChromaDB_VectorStore
from vanna.base.base import VannaBase # For type hinting

# Ensure OPENAI_API_KEY is set as an environment variable
# For example:
# import os
# os.environ["OPENAI_API_KEY"] = "your-actual-api-key"
# Or set it in your shell before running the script

class MyVanna(ChromaDB_VectorStore, OpenAI_Chat):
    def __init__(self, config=None):
        # Default ChromaDB path if not in config
        if config is None:
            config = {}
        if 'path' not in config:
            # Define a path for ChromaDB to store its data
            # Using a local directory './chroma_db'
            config['path'] = './chroma_db'

        ChromaDB_VectorStore.__init__(self, config=config)
        OpenAI_Chat.__init__(self, config=config)

def run_example():
    # Instantiate MyVanna
    # The OPENAI_API_KEY will be picked up from the environment if not passed in config
    # You can specify a model, e.g., config={'model': 'gpt-3.5-turbo'}
    # If OPENAI_API_KEY is not in env, you must pass it:
    # vn = MyVanna(config={'api_key': 'sk-...', 'model': 'gpt-3.5-turbo'})
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY environment variable not set.")
        print("Please set it before running the script.")
        print("e.g., export OPENAI_API_KEY='your-key'")
        return

    vn: VannaBase = MyVanna(config={'model': 'gpt-3.5-turbo'}) # Using a common model

    # Connect to an in-memory DuckDB database
    print("Connecting to DuckDB (in-memory)...")
    vn.connect_to_duckdb(url=':memory:')
    print("Connected to DuckDB.")

    # DDL for training
    ddl = """
    CREATE TABLE IF NOT EXISTS employees (
        id INT PRIMARY KEY,
        name VARCHAR(100),
        age INT,
        department VARCHAR(50)
    );
    """
    print(f"\nTraining with DDL:\n{ddl}")
    vn.train(ddl=ddl)
    print("DDL training complete.")

    # Insert some sample data
    print("\nInserting sample data...")
    vn.run_sql("INSERT INTO employees (id, name, age, department) VALUES (1, 'Alice', 30, 'Engineering');")
    vn.run_sql("INSERT INTO employees (id, name, age, department) VALUES (2, 'Bob', 24, 'Marketing');")
    vn.run_sql("INSERT INTO employees (id, name, age, department) VALUES (3, 'Charlie', 35, 'Engineering');")
    vn.run_sql("INSERT INTO employees (id, name, age, department) VALUES (4, 'Diana', 28, 'Sales');")
    print("Sample data inserted.")

    # Verify data insertion
    df_verify = vn.run_sql("SELECT * FROM employees;")
    print("\nVerification: Current data in employees table:")
    print(df_verify)

    # SQL query for training
    sql_example = "SELECT name, department FROM employees WHERE age > 30;"
    question_example = "Show me the names and departments of employees older than 30."
    print(f"\nTraining with SQL query:\nQuestion: {question_example}\nSQL: {sql_example}")
    vn.train(question=question_example, sql=sql_example)
    print("SQL training complete.")

    # Documentation for training
    documentation_example = "The employees table contains information about company staff, including their ID, name, age, and department."
    print(f"\nTraining with documentation: {documentation_example}")
    vn.train(documentation=documentation_example)
    print("Documentation training complete.")

    # Ask a question
    question = "What are the names of employees in the Engineering department?"
    print(f"\nAsking question: {question}")

    # Set allow_llm_to_see_data to True if your question might require data introspection
    # For this specific question, it's unlikely to be needed, but good to be aware of.
    sql_generated, df_results, fig = vn.ask(question=question, print_results=False, visualize=True, auto_train=True, allow_llm_to_see_data=False)

    print("\n--- Results ---")
    if sql_generated:
        print("\nGenerated SQL:")
        print(sql_generated)
    else:
        print("\nNo SQL generated.")

    if df_results is not None and not df_results.empty:
        print("\nQuery Results (DataFrame):")
        print(df_results)
    elif sql_generated: # If SQL was generated but df is empty or None
        print("\nQuery Results: No data returned or error in execution.")

    if fig:
        print("\nPlotly Figure Generated. (Displaying depends on environment)")
        # In a script, fig.show() might open a browser window or require additional setup
        # For simplicity, we'll just confirm it's created.
        # fig.show()
    elif sql_generated and df_results is not None and not df_results.empty : # Figure might not be generated if data is not suitable
        print("\nNo Plotly Figure generated (or data not suitable for visualization).")

    # Ask another question that might benefit from the context
    question2 = "How many engineers are there?"
    print(f"\nAsking another question: {question2}")
    sql_generated2, df_results2, fig2 = vn.ask(question=question2, print_results=False, visualize=True)

    print("\n--- Results for second question ---")
    if sql_generated2:
        print("\nGenerated SQL:")
        print(sql_generated2)
    else:
        print("\nNo SQL generated.")

    if df_results2 is not None and not df_results2.empty:
        print("\nQuery Results (DataFrame):")
        print(df_results2)
    elif sql_generated2:
        print("\nQuery Results: No data returned or error in execution.")

    if fig2:
        print("\nPlotly Figure Generated for second question.")
    elif sql_generated2 and df_results2 is not None and not df_results2.empty:
        print("\nNo Plotly Figure generated for second question (or data not suitable for visualization).")


if __name__ == "__main__":
    run_example()
