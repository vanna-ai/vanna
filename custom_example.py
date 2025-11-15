#!/usr/bin/env python3
"""
Example: Customized console app for a specific database

This shows how to customize the console app for your specific use case:
- Filter specific tables
- Add domain-specific instructions
- Customize schema extraction

Usage:
    python custom_example.py /path/to/your/database.db
"""

# Copy the entire console_chat_app_with_schema.py and make these changes:

# 1. Customize extract_sqlite_schema to filter tables
def extract_sqlite_schema(database_path: str) -> str:
    """Extract schema, excluding internal tables."""
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()

    # CUSTOMIZE: Only include specific tables
    cursor.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table'
        AND name IN ('products', 'customers', 'orders')  -- YOUR TABLES
        ORDER BY name
    """)

    # ... rest of extraction logic ...


# 2. Customize tool description with domain knowledge
def create_schema_aware_tool_description(schema: str) -> str:
    return f"""Execute SQL queries against the e-commerce database.

DATABASE SCHEMA:
{schema}

BUSINESS RULES:
- The 'products' table contains our inventory
- The 'orders' table has all customer purchases
- When calculating revenue, use orders.total_price
- When analyzing customers, join with orders via customer_id

IMPORTANT:
- Always filter out test orders (orders.is_test = 0)
- Product prices are in USD
- Use exact table and column names as shown above
"""


# Usage example:
if __name__ == "__main__":
    # Just change the table filter and descriptions above
    # Everything else works the same!
    pass
