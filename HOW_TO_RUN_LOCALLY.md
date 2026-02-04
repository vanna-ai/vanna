# How to Run Vanna Locally (Example)

This guide provides step-by-step instructions to run a basic Vanna example on your local machine. This example uses OpenAI for language model capabilities, ChromaDB as a vector store, and DuckDB as an in-memory SQL database.

## Prerequisites

1.  **Python:** Ensure you have Python 3.8 or newer installed. You can download it from [python.org](https://www.python.org/downloads/).
2.  **OpenAI API Key:** You need an API key from OpenAI.
    *   If you don't have one, sign up at [OpenAI](https://platform.openai.com/signup).
    *   Once you have an account, generate an API key from your [API keys page](https://platform.openai.com/api-keys).

## Setup Instructions

1.  **Create a Project Directory:**
    Open your terminal or command prompt and create a new directory for this project, then navigate into it:
    ```bash
    mkdir vanna-local-example
    cd vanna-local-example
    ```

2.  **Set up a Virtual Environment (Recommended):**
    Using a virtual environment keeps your project dependencies isolated.
    ```bash
    python -m venv .venv
    ```
    Activate the virtual environment:
    *   On macOS and Linux:
        ```bash
        source .venv/bin/activate
        ```
    *   On Windows:
        ```bash
        .venv\Scripts\activate
        ```
    Your terminal prompt should now indicate that you are in the virtual environment (e.g., `(.venv) your-prompt$`).

3.  **Install Vanna and Dependencies:**
    Install Vanna with the necessary extras for OpenAI, ChromaDB, and DuckDB:
    ```bash
    pip install "vanna[openai,chromadb,duckdb]"
    ```

4.  **Set OpenAI API Key:**
    You must set your OpenAI API key as an environment variable. Replace `"your-actual-api-key"` with your actual key.
    *   On macOS and Linux (for the current terminal session):
        ```bash
        export OPENAI_API_KEY="your-actual-api-key"
        ```
        To make it permanent, add this line to your shell's configuration file (e.g., `~/.bashrc`, `~/.zshrc`) and then source it (e.g., `source ~/.zshrc`).
    *   On Windows (for the current command prompt session):
        ```bash
        set OPENAI_API_KEY=your-actual-api-key
        ```
        To set it permanently, search for "environment variables" in the Windows search bar and add it to your user or system variables.

5.  **Create the Example Python Script:**
    Create a file named `run_vanna_example.py` in your `vanna-local-example` directory and paste the following code into it:

    ```python
    import os
    import pandas as pd
    from vanna.openai.openai_chat import OpenAI_Chat
    from vanna.chromadb.chromadb_vector import ChromaDB_VectorStore
    from vanna.base.base import VannaBase # For type hinting

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
        # If OPENAI_API_KEY is not in env and you don't want to set it as an env var,
        # you can pass it directly:
        # vn = MyVanna(config={'api_key': 'your-actual-api-key', 'model': 'gpt-3.5-turbo'})

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("Error: OPENAI_API_KEY environment variable not set.")
            print("Please set it before running the script.")
            print("e.g., export OPENAI_API_KEY='your-key'")
            return

        print("Initializing Vanna with OpenAI and ChromaDB...")
        # Using a common and generally available model. You can change if needed.
        vn: VannaBase = MyVanna(config={'model': 'gpt-3.5-turbo'})
        print("Vanna initialized.")

        # Connect to an in-memory DuckDB database
        print("\nConnecting to DuckDB (in-memory)...")
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
        training_id_ddl = vn.train(ddl=ddl)
        print(f"DDL training complete. Training ID: {training_id_ddl}")

        # Insert some sample data
        print("\nInserting sample data into DuckDB...")
        vn.run_sql("INSERT INTO employees (id, name, age, department) VALUES (1, 'Alice', 30, 'Engineering');")
        vn.run_sql("INSERT INTO employees (id, name, age, department) VALUES (2, 'Bob', 24, 'Marketing');")
        vn.run_sql("INSERT INTO employees (id, name, age, department) VALUES (3, 'Charlie', 35, 'Engineering');")
        vn.run_sql("INSERT INTO employees (id, name, age, department) VALUES (4, 'Diana', 28, 'Sales');")
        print("Sample data inserted.")

        # Verify data insertion
        df_verify = vn.run_sql("SELECT * FROM employees;")
        print("\nVerification: Current data in employees table:")
        print(df_verify.to_string()) # .to_string() for better console output

        # SQL query for training
        sql_example = "SELECT name, department FROM employees WHERE age > 30;"
        question_example = "Show me the names and departments of employees older than 30."
        print(f"\nTraining with SQL query:\nQuestion: {question_example}\nSQL: {sql_example}")
        training_id_sql = vn.train(question=question_example, sql=sql_example)
        print(f"SQL training complete. Training ID: {training_id_sql}")

        # Documentation for training
        documentation_example = "The employees table contains information about company staff, including their ID, name, age, and department. Engineering department focuses on product development."
        print(f"\nTraining with documentation: {documentation_example}")
        training_id_doc = vn.train(documentation=documentation_example)
        print(f"Documentation training complete. Training ID: {training_id_doc}")

        # Ask a question
        question = "What are the names of employees in the Engineering department?"
        print(f"\nAsking question (1): {question}")

        sql_generated, df_results, fig = vn.ask(
            question=question,
            print_results=False, # We'll print manually
            visualize=True,      # Attempt to generate a plot
            auto_train=True      # Add successful Q/A to training data
        )

        print("\n--- Results for question (1) ---")
        if sql_generated:
            print("\nGenerated SQL:")
            print(sql_generated)
        else:
            print("\nNo SQL generated.")

        if df_results is not None and not df_results.empty:
            print("\nQuery Results (DataFrame):")
            print(df_results.to_string())
        elif sql_generated:
            print("\nQuery Results: No data returned or error in execution.")

        if fig:
            print("\nPlotly Figure Generated. If in a Jupyter Notebook, it would display. In a script, you might need `fig.show()`.")
            # To view the plot if it's generated, you could uncomment:
            # fig.show() # This might open in a browser
        elif sql_generated and df_results is not None and not df_results.empty:
            print("\nNo Plotly Figure generated (or data not suitable for visualization).")

        # Ask another question that might benefit from the context or previous training
        question2 = "How many engineers are there?"
        print(f"\nAsking question (2): {question2}")
        sql_generated2, df_results2, fig2 = vn.ask(
            question=question2,
            print_results=False,
            visualize=True
        )

        print("\n--- Results for question (2) ---")
        if sql_generated2:
            print("\nGenerated SQL:")
            print(sql_generated2)
        else:
            print("\nNo SQL generated.")

        if df_results2 is not None and not df_results2.empty:
            print("\nQuery Results (DataFrame):")
            print(df_results2.to_string())
        elif sql_generated2:
            print("\nQuery Results: No data returned or error in execution.")

        if fig2:
            print("\nPlotly Figure Generated for question (2).")
            # fig2.show()
        elif sql_generated2 and df_results2 is not None and not df_results2.empty:
            print("\nNo Plotly Figure generated for question (2) (or data not suitable for visualization).")

        print("\nExample run finished. ChromaDB data is stored in the './chroma_db' directory.")

    if __name__ == "__main__":
        run_example()
    ```

## Running the Example

1.  **Ensure your virtual environment is active** and your `OPENAI_API_KEY` is set.
2.  **Run the script from your terminal:**
    ```bash
    python run_vanna_example.py
    ```

## Expected Output

The script will print output to the console, showing:
*   Connection messages.
*   DDL, SQL, and documentation used for training.
*   Verification of data inserted into the `employees` table.
*   The questions being asked.
*   The SQL query generated by Vanna in response to your questions.
*   The results of executing that SQL query (as a Pandas DataFrame).
*   Confirmation if a Plotly figure was generated.

You should see Vanna successfully generate SQL queries for the questions asked, based on the training data provided. For example, for "What are the names of employees in the Engineering department?", it should generate something like `SELECT name FROM employees WHERE department = 'Engineering';`.

A directory named `chroma_db` will be created in your `vanna-local-example` folder. This is where ChromaDB stores the vector embeddings of your training data.

## Troubleshooting

*   **`OPENAI_API_KEY not set` error:**
    Ensure you have correctly set the `OPENAI_API_KEY` environment variable (Step 4 in Setup). Double-check that there are no typos and that the key is valid. If you set it for the current session only, you'll need to set it again if you open a new terminal.
*   **`ModuleNotFoundError`:**
    Make sure your virtual environment is active and that you ran `pip install "vanna[openai,chromadb,duckdb]"` successfully within that environment.
*   **OpenAI API Errors (e.g., rate limits, authentication issues):**
    Check the error message from OpenAI. You might be exceeding your API quota, or there might be an issue with your key or billing. Visit your OpenAI account dashboard for more details.
*   **ChromaDB Issues:**
    If you encounter issues with ChromaDB, ensure you have write permissions in the directory where `run_vanna_example.py` is located, as it will try to create a `./chroma_db` subdirectory.
*   **Plotly visualization:**
    The script confirms if a Plotly figure object is created. To actually *see* the plot from a script, you might need to call `fig.show()`, which typically opens the plot in a web browser. This might require additional libraries or configurations depending on your OS and Python setup if it doesn't work out of the box. For interactive plotting, Jupyter Notebooks are often easier.

This example provides a basic Vanna workflow. You can expand on it by connecting to your own databases, using different LLMs, or exploring more advanced training techniques. Refer to the [official Vanna documentation](https://vanna.ai/docs/) for more information.
```
