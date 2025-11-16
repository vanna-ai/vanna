#!/usr/bin/env python3
"""
Example script demonstrating how to use the Vanna staffing agent integration.

This shows how to query staffing data using natural language through the
integrated Google ADK agent with Vanna-powered SQL generation.
"""

import os
import sys

# Set up environment
os.environ['GOOGLE_GENAI_USE_VERTEXAI'] = 'FALSE'

# Configure database (adjust these to your setup)
os.environ['STAFFING_DATABASE_PATH'] = './unpolicy.db'  # Your database path
os.environ['STAFFING_TABLE_NAME'] = 'staffing_table'    # Your table name

# Import the agent
from agent import un_policy_agent


def example_queries():
    """Run example staffing queries through the agent."""

    print("=" * 70)
    print("Vanna Staffing Agent - Example Queries")
    print("=" * 70)
    print()

    # Example queries to demonstrate capabilities
    queries = [
        "How many employees do we have in total?",
        "Show me headcount by department",
        "What's the average salary by department?",
        "How many people were hired in 2024?",
        "Show me the top 5 highest paid employees",
        "Which department has the most employees?",
    ]

    print("Example queries you can ask:")
    print()
    for i, query in enumerate(queries, 1):
        print(f"{i}. {query}")

    print()
    print("=" * 70)
    print()

    # Note: Actual query execution requires proper ADK runtime environment
    # This is a demonstration of the query types supported

    print("To run these queries:")
    print("1. Set up your database at:", os.getenv('STAFFING_DATABASE_PATH'))
    print("2. Ensure table exists:", os.getenv('STAFFING_TABLE_NAME'))
    print("3. Set ANTHROPIC_API_KEY environment variable")
    print("4. Run your ADK agent and ask these questions")
    print()
    print("The agent will automatically:")
    print("  - Route staffing questions to the staffing specialist")
    print("  - Generate SQL queries using Vanna")
    print("  - Execute queries against your database")
    print("  - Present results with insights")
    print()


def direct_tool_usage():
    """Example of using the staffing tool directly."""

    print("=" * 70)
    print("Direct Tool Usage Example")
    print("=" * 70)
    print()

    # Import the tool
    from tools import query_staffing_table

    # Example: Direct tool call
    question = "How many employees are in each department?"

    print(f"Question: {question}")
    print()
    print("Calling query_staffing_table...")
    print()

    try:
        result = query_staffing_table(question)

        if result["status"] == "success":
            print("✅ Success!")
            print()
            print(f"SQL Generated: {result['result']['sql']}")
            print(f"Row Count: {result['result'].get('row_count', 'N/A')}")
            print(f"Summary: {result['result']['summary']}")
            print()

            if result['result']['data']:
                print("Data:")
                for row in result['result']['data'][:5]:  # Show first 5 rows
                    print(f"  {row}")
                if len(result['result']['data']) > 5:
                    print(f"  ... and {len(result['result']['data']) - 5} more rows")
        else:
            print(f"❌ Error: {result.get('error', 'Unknown error')}")

    except Exception as e:
        print(f"❌ Exception: {e}")
        import traceback
        traceback.print_exc()

    print()


def check_setup():
    """Check if environment is properly configured."""

    print("=" * 70)
    print("Setup Check")
    print("=" * 70)
    print()

    # Check API key
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if api_key:
        print("✅ ANTHROPIC_API_KEY is set")
    else:
        print("❌ ANTHROPIC_API_KEY is NOT set")
        print("   Set it with: export ANTHROPIC_API_KEY='your-key-here'")

    # Check database
    db_path = os.getenv('STAFFING_DATABASE_PATH', './unpolicy.db')
    if os.path.exists(db_path):
        print(f"✅ Database found at: {db_path}")

        # Check table
        import sqlite3
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            table_name = os.getenv('STAFFING_TABLE_NAME', 'staffing_table')
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                (table_name,)
            )

            if cursor.fetchone():
                print(f"✅ Table '{table_name}' exists")

                # Get row count
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                print(f"   Rows: {count:,}")
            else:
                print(f"❌ Table '{table_name}' NOT found")
                print("   Available tables:")
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                for (table,) in cursor.fetchall():
                    print(f"     - {table}")

            conn.close()
        except Exception as e:
            print(f"❌ Error checking database: {e}")
    else:
        print(f"❌ Database NOT found at: {db_path}")
        print(f"   Set it with: export STAFFING_DATABASE_PATH='/path/to/your/database.db'")

    print()

    # Check Vanna
    try:
        from vanna.integrations.anthropic import AnthropicLlmService
        print("✅ Vanna package is installed")
    except ImportError:
        print("❌ Vanna package NOT installed")
        print("   Install with: pip install vanna")

    print()
    print("=" * 70)
    print()


if __name__ == "__main__":
    # Run setup check
    check_setup()

    # Show example queries
    example_queries()

    # Optional: Try direct tool usage
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        direct_tool_usage()
    else:
        print("Run with --test flag to try direct tool usage:")
        print("  python example_staffing_query.py --test")
        print()
