# Single-Table Console Chat App - Quick Guide

Perfect for databases with many tables where you only need to query one or a few specific tables.

## 🎯 Why Use This Version?

**Problem:** Your database has 50 tables, but you only care about 1 table.

**Solution:** This version only extracts the schema for the table(s) you specify.

**Benefits:**
- 💰 **Minimal token usage** - only 1 table instead of 50
- ⚡ **Faster responses** - less schema for LLM to process
- 💵 **Lower API costs** - fewer tokens = less money
- 🎯 **Focused context** - more accurate queries

## ✅ Usage

### Single Table

```bash
python console_chat_app_single_table.py <database.db> <table_name>
```

**Example with your staffing_table:**
```bash
python console_chat_app_single_table.py myapp.db staffing_table
```

### Multiple Tables

If you need 2-3 related tables:

```bash
python console_chat_app_single_table.py <database.db> <table1> <table2> <table3>
```

**Example:**
```bash
python console_chat_app_single_table.py myapp.db staffing_table employees departments
```

## 📊 What You'll See

```
======================================================================
🤖 VANNA v2 CONSOLE CHAT - Single-Table SQL Assistant
======================================================================
Focused on table(s): staffing_table
Type your questions in natural language.
Commands: 'quit' or 'exit' to end, 'clear' to clear conversation
======================================================================

📊 Database: /home/user/myapp.db
🎯 Target table(s): staffing_table
🤖 Model: claude-sonnet-4-20250514

🔍 Extracting schema for 1 table(s)...
✅ Schema extracted successfully!

======================================================================
DATABASE SCHEMA (FILTERED)
======================================================================

Included Tables: 1 of 1 requested

-- Table: staffing_table
CREATE TABLE staffing_table (
  id INTEGER PRIMARY KEY,
  employee_name TEXT NOT NULL,
  department TEXT,
  hire_date DATE,
  salary REAL
)
-- Columns (5):
--   id: INTEGER [PRIMARY KEY]
--   employee_name: TEXT NOT NULL
--   department: TEXT
--   hire_date: DATE
--   salary: REAL
-- Rows: 1,234
-- Sample data (first 3 rows):
--   Row 1: {'id': 1, 'employee_name': 'John Doe', 'department': 'Engineering', 'hire_date': '2020-01-15', 'salary': 75000.0}
--   Row 2: {'id': 2, 'employee_name': 'Jane Smith', 'department': 'Sales', 'hire_date': '2021-03-20', 'salary': 68000.0}
--   Row 3: {'id': 3, 'employee_name': 'Bob Johnson', 'department': 'Engineering', 'hire_date': '2019-11-01', 'salary': 82000.0}

======================================================================

----------------------------------------------------------------------
✅ LLM has complete knowledge of your table(s)!
💰 Token usage optimized - only relevant tables included!
----------------------------------------------------------------------

💬 You: How many employees are in each department?

======================================================================
⏱️  [10:30:45.123] Query received
⏱️  [10:30:45.234] 🧠 AI is thinking...

⏱️  [10:30:46.567] 🔧 Tool called: run_sql

📝 Generated SQL Query:
----------------------------------------------------------------------
SELECT department, COUNT(*) as employee_count
FROM staffing_table
GROUP BY department
ORDER BY employee_count DESC;
----------------------------------------------------------------------
⏱️  [10:30:46.789] ⚡ Executing SQL...
⏱️  [10:30:46.892] ✅ Tool execution completed
📊 Query returned: 3 rows × 2 columns

📋 Query Results:
----------------------------------------------------------------------
     department  employee_count
    Engineering              450
          Sales              398
             HR              386
----------------------------------------------------------------------

🤖 Assistant: The staffing table shows employees distributed across 3 departments:
- Engineering has the most with 450 employees
- Sales has 398 employees
- HR has 386 employees

======================================================================
⏱️  Total time: 1.2s
🔧 Tools used: run_sql
======================================================================
```

## 💡 Example Queries for staffing_table

```
How many employees are in the staffing table?
Show me the top 10 highest paid employees
What's the average salary by department?
List all employees hired in 2023
How many employees were hired each year?
Show me employees in the Engineering department
What's the salary range in the Sales department?
List all unique departments
```

## 🔍 Features

### Automatic Table Validation

If you specify a table that doesn't exist, the app will:
- Warn you that the table wasn't found
- Show you all available tables in the database

```bash
python console_chat_app_single_table.py myapp.db wrong_table_name

# Output:
⚠️  WARNING: None of the specified tables were found!
Requested: wrong_table_name

Available tables:
  - staffing_table
  - users
  - logs
  - config
  ...
```

### Sample Data Preview

The schema includes the first 3 rows of data so the LLM understands:
- Data format
- Typical values
- Data types in practice

### Multiple Table Support

If you need to query across related tables:

```bash
# Query both staffing and departments
python console_chat_app_single_table.py myapp.db staffing_table departments

# Now you can ask:
💬 You: Join staffing with departments to show full department names
```

## 📊 Token Savings

### Comparison

**Full schema (50 tables):**
```
Estimated tokens: ~8,000 tokens
Cost per query: Higher
LLM processing: Slower
```

**Single table:**
```
Estimated tokens: ~200 tokens
Cost per query: Much lower (40x less!)
LLM processing: Faster
```

### Real Numbers

For a database with 50 tables averaging 10 columns each:
- **Full schema:** ~8,000 tokens
- **Single table:** ~200 tokens
- **Savings:** 97.5% token reduction!

## ⚙️ Advanced Usage

### Environment Variables

```bash
# Use a different model
export ANTHROPIC_MODEL="claude-haiku-4-20250301"
python console_chat_app_single_table.py myapp.db staffing_table

# Set API key
export ANTHROPIC_API_KEY="your-key-here"
```

### Multiple Sessions

Each session is independent:

```bash
# Terminal 1 - Query staffing
python console_chat_app_single_table.py myapp.db staffing_table

# Terminal 2 - Query logs
python console_chat_app_single_table.py myapp.db logs

# Terminal 3 - Query both
python console_chat_app_single_table.py myapp.db staffing_table logs
```

## 🆚 When to Use Each Version

| Your Situation | Recommended App |
|----------------|-----------------|
| 50 tables, need only 1 | ✅ **console_chat_app_single_table.py** |
| 50 tables, need 2-3 | ✅ **console_chat_app_single_table.py** |
| 10 tables, query all | console_chat_app_with_schema.py |
| Unknown schema | console_chat_app.py (basic) |
| Development/exploration | console_chat_app_with_schema.py |
| Production/focused queries | ✅ **console_chat_app_single_table.py** |

## 🚀 Quick Start for Your staffing_table

```bash
# 1. Set API key (if not already set)
export ANTHROPIC_API_KEY='your-key-here'

# 2. Run the app with your database and table
python console_chat_app_single_table.py /path/to/your/database.db staffing_table

# 3. Start asking questions!
💬 You: How many people work here?
💬 You: What's the average salary?
💬 You: Show me recent hires
```

## ❓ FAQ

**Q: Can I change tables during a session?**
A: No, restart the app with different table name(s).

**Q: What if I need to query a table not in the schema?**
A: The LLM will only know about tables you specified. Restart with additional tables.

**Q: How many tables can I specify?**
A: As many as you want, but 1-5 is optimal for token efficiency.

**Q: Does this work with other databases?**
A: Currently optimized for SQLite. For other databases, use the basic `console_chat_app.py`.

**Q: Can I save the schema to a file?**
A: Yes, redirect output: `python console_chat_app_single_table.py myapp.db staffing_table > schema.txt 2>&1`

## 🎯 Pro Tips

1. **Start with one table** - Add more only if needed for JOINs
2. **Use descriptive questions** - "Show me employees hired in 2023" vs "SELECT * FROM..."
3. **Check sample data** - The schema shows 3 sample rows to guide you
4. **Validate table names** - If unsure, run once with wrong name to see available tables

## 📖 See Also

- [QUICKSTART.md](QUICKSTART.md) - General getting started guide
- [SCHEMA_DISCOVERY_EXPLAINED.md](SCHEMA_DISCOVERY_EXPLAINED.md) - How schema discovery works
- [USING_YOUR_OWN_DATABASE.md](USING_YOUR_OWN_DATABASE.md) - Customization guide
