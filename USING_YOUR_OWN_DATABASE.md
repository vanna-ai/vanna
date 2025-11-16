# Using the Console Chat App with Your Own Database

Quick guide to using the schema-aware console app with your own SQLite database.

## ✅ Basic Usage (No Code Changes Needed!)

Just pass your database path:

```bash
python console_chat_app_with_schema.py /path/to/your/database.db
```

**That's it!** The app automatically:
- Extracts schema from ALL tables
- Shows you the complete schema
- Provides it to the LLM
- Lets you query your data

## 📝 Example

```bash
# Database in current directory
python console_chat_app_with_schema.py myapp.db

# Database elsewhere
python console_chat_app_with_schema.py ~/projects/store.db

# Absolute path
python console_chat_app_with_schema.py /var/data/production.db
```

## 🎯 Common Customizations

### 1. Include Only Specific Tables

If your database has many tables but you only care about a few:

**Edit line 59 in `console_chat_app_with_schema.py`:**

```python
# BEFORE (gets all tables)
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")

# AFTER (gets only specific tables)
cursor.execute("""
    SELECT name FROM sqlite_master
    WHERE type='table'
    AND name IN ('xxx', 'users', 'products', 'orders')
    ORDER BY name
""")
```

### 2. Exclude Internal/System Tables

**Edit line 59:**

```python
cursor.execute("""
    SELECT name FROM sqlite_master
    WHERE type='table'
    AND name NOT LIKE 'sqlite_%'        -- Exclude SQLite internals
    AND name NOT LIKE 'django_%'         -- Exclude Django tables
    AND name NOT IN ('migrations', 'logs')  -- Exclude specific tables
    ORDER BY name
""")
```

### 3. Add Business Rules and Domain Knowledge

Help the LLM understand your specific domain by customizing the tool description.

**Edit the `create_schema_aware_tool_description()` function (around line 104):**

```python
def create_schema_aware_tool_description(schema: str) -> str:
    return f"""Execute SQL queries against the database.

{schema}

BUSINESS RULES FOR THIS DATABASE:
- Table 'xxx' contains [your explanation]
- When calculating totals, use field [field_name]
- Always filter by [common condition]
- [Any other domain-specific rules]

Guidelines:
- Use exact table and column names as shown above
- The database is SQLite, use SQLite-compatible syntax
- Do NOT use DROP, DELETE, UPDATE, or INSERT unless explicitly requested
"""
```

### 4. Show Sample Data in Schema

Help the LLM understand data format by including examples.

**Add after line 95 (after the row count line):**

```python
        # Get row count
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        row_count = cursor.fetchone()[0]
        schema_parts.append(f"-- Rows: {row_count:,}")

        # ADD THIS: Show sample data
        if row_count > 0:
            cursor.execute(f"SELECT * FROM {table_name} LIMIT 3")
            sample_rows = cursor.fetchall()
            schema_parts.append(f"-- Sample data (first 3 rows):")
            for row in sample_rows:
                schema_parts.append(f"--   {row}")
```

### 5. Limit Schema Size for Large Databases

If you have 100+ tables, provide a summary instead of full DDL.

**Replace the extraction logic (lines 64-95) with:**

```python
for (table_name,) in tables:
    # Get column info only (skip full DDL)
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()

    schema_parts.append(f"\n-- Table: {table_name}")
    schema_parts.append(f"--   Columns: {', '.join(col[1] for col in columns)}")

    # Get row count
    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    row_count = cursor.fetchone()[0]
    schema_parts.append(f"--   Rows: {row_count:,}")
```

## 🔧 Complete Customization Example

For a real-world e-commerce database:

```python
def extract_sqlite_schema(database_path: str) -> str:
    """Extract schema for e-commerce database."""
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()

    schema_parts = []
    schema_parts.append("E-COMMERCE DATABASE SCHEMA")
    schema_parts.append("=" * 70)

    # Only include business tables
    cursor.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table'
        AND name IN ('products', 'customers', 'orders', 'order_items')
        ORDER BY name
    """)

    tables = cursor.fetchall()
    schema_parts.append(f"\nTotal Tables: {len(tables)}\n")

    for (table_name,) in tables:
        # Get DDL
        cursor.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name=?",
            (table_name,)
        )
        ddl = cursor.fetchone()[0]
        schema_parts.append(f"\n{ddl}")

        # Get row count and sample
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        schema_parts.append(f"-- Total rows: {count:,}")

        if count > 0:
            cursor.execute(f"SELECT * FROM {table_name} LIMIT 2")
            samples = cursor.fetchall()
            schema_parts.append("-- Examples:")
            for sample in samples:
                schema_parts.append(f"--   {sample}")

    conn.close()
    return "\n".join(schema_parts)


def create_schema_aware_tool_description(schema: str) -> str:
    return f"""Execute SQL queries against the e-commerce database.

{schema}

BUSINESS RULES:
- Products: Our inventory catalog with prices in USD
- Customers: User accounts and contact information
- Orders: Purchase records, join with customers via customer_id
- Order_items: Individual items in each order

COMMON QUERIES:
- Revenue: SUM(order_items.price * order_items.quantity)
- Top customers: GROUP BY customer_id, ORDER BY total DESC
- Popular products: GROUP BY product_id, COUNT(*) as sales

IMPORTANT:
- Always exclude test data: WHERE is_test = 0
- For active products only: WHERE status = 'active'
- Use exact table and column names as shown above
"""
```

## 🎨 Quick Customization Template

Save this as `my_custom_app.py`:

```python
#!/usr/bin/env python3
# Copy entire console_chat_app_with_schema.py here
# Then change these two functions:

def extract_sqlite_schema(database_path: str) -> str:
    # YOUR CUSTOM EXTRACTION HERE
    # Examples:
    # - Filter specific tables
    # - Exclude internal tables
    # - Add sample data
    # - Simplify for large databases
    pass

def create_schema_aware_tool_description(schema: str) -> str:
    return f"""
    YOUR CUSTOM DESCRIPTION HERE

    {schema}

    YOUR BUSINESS RULES HERE
    """

# Everything else stays the same!
```

## ⚡ Performance Tips

### For Small Databases (< 50 tables)
✅ Use full DDL extraction (default)
✅ Include all tables
✅ Show sample data

### For Medium Databases (50-200 tables)
✅ Filter to relevant tables only
✅ Use column summaries instead of full DDL
⚠️ Skip sample data

### For Large Databases (200+ tables)
✅ Definitely filter to specific tables
✅ Use minimal schema (table + column names only)
✅ Consider using Agent Memory with RAG instead

## 📊 Testing Your Customization

After customizing, test with these questions:

```
1. "What tables are in this database?"
   -> Should list your tables correctly

2. "Describe the xxx table"
   -> Should show accurate structure

3. "Show me 5 rows from xxx"
   -> Should generate correct SQL

4. "What is the relationship between table A and table B?"
   -> Should understand foreign keys if you included DDL
```

## ❓ Common Questions

**Q: Do I need to change the code?**
A: No! Just run: `python console_chat_app_with_schema.py your.db`

**Q: My database has 500 tables, is that okay?**
A: No, that's too much for LLM context. Filter to relevant tables only.

**Q: Can I use this with PostgreSQL or MySQL?**
A: The schema extraction is SQLite-specific, but you can adapt it. Or use the basic `console_chat_app.py` which works with any database via the SQL runner.

**Q: How do I know if the schema is too large?**
A: If the schema text is > 10,000 tokens (~40KB of text), consider filtering or simplifying.

**Q: Can I save the extracted schema to a file?**
A: Yes! Add this after line 171:
```python
with open("schema.txt", "w") as f:
    f.write(schema)
```

## 🚀 Quick Start Checklist

- [ ] Have your SQLite database file
- [ ] Set ANTHROPIC_API_KEY
- [ ] Run: `python console_chat_app_with_schema.py your.db`
- [ ] See schema extracted on startup
- [ ] Ask questions about your data!

That's it! No code changes needed for basic use.

## 📖 See Also

- [QUICKSTART.md](QUICKSTART.md) - Getting started guide
- [SCHEMA_DISCOVERY_EXPLAINED.md](SCHEMA_DISCOVERY_EXPLAINED.md) - How schema discovery works
- [CONSOLE_CHAT_README.md](CONSOLE_CHAT_README.md) - Full console app documentation
