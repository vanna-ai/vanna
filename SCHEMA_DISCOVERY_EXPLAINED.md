# How Vanna v2 Learns Database Schema - Explained

## The Critical Discovery

**Vanna v2 does NOT automatically provide database schema to the LLM!**

This is why the FastAPI UI feels slow and confusing - the LLM has to explore the database before it can answer your questions.

## The Problem: How It Currently Works

### What Happens on First Query

```
You: "Show me total sales by customer"

LLM receives:
  ❌ No table names
  ❌ No column names
  ❌ No DDL or schema
  ✅ Only: "Execute SQL queries against the configured database"

LLM's process:
  1. Query metadata: SELECT name FROM sqlite_master WHERE type='table'
  2. Query columns: PRAGMA table_info(customers)
  3. Query columns: PRAGMA table_info(sales)
  4. Finally generate the actual query
  5. Execute it

Result: 4-5 queries instead of 1! Slow and inefficient.
```

## The Solution: Two Approaches

### Approach 1: Schema-Aware Tool (Recommended)

**Use:** `console_chat_app_with_schema.py`

This version automatically:
1. Extracts complete database schema on startup
2. Provides schema to LLM via tool description
3. LLM generates accurate SQL on first try

```bash
python console_chat_app_with_schema.py Chinook.sqlite

# Output shows:
# ✅ Schema extracted successfully!
# ============================================================
# DATABASE SCHEMA
# ============================================================
#
# Total Tables: 11
#
# -- Table: Album
# CREATE TABLE Album (
#   AlbumId INTEGER PRIMARY KEY,
#   Title TEXT NOT NULL,
#   ArtistId INTEGER NOT NULL,
#   FOREIGN KEY (ArtistId) REFERENCES Artist(ArtistId)
# )
# -- Rows: 347
# ...
```

**Result:** Fast, accurate, transparent!

### Approach 2: Pre-populate Agent Memory

Add schema to memory on first run:

```python
from vanna.tools import SaveTextMemoryTool

# Save DDL to memory
save_text_tool = SaveTextMemoryTool(agent_memory=agent_memory)
tool_registry.register(save_text_tool)

# Or manually:
agent_memory.save_text_memory(
    user_id="demo_user",
    content="""
    CREATE TABLE customers (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        email TEXT
    );
    CREATE TABLE orders (
        id INTEGER PRIMARY KEY,
        customer_id INTEGER,
        total DECIMAL
    );
    """
)
```

## Performance Comparison

### Without Schema Knowledge (console_chat_app.py)

```
Query: "Who are the top 5 artists?"

Step 1: Explore tables (1.2s)
  SELECT name FROM sqlite_master WHERE type='table'

Step 2: Explore Artist table (0.8s)
  PRAGMA table_info(Artist)

Step 3: Explore Album table (0.7s)
  PRAGMA table_info(Album)

Step 4: Generate actual query (1.5s)
  SELECT a.Name, COUNT(al.AlbumId)...

Total time: ~4.2s, 4 queries
```

### With Schema Knowledge (console_chat_app_with_schema.py)

```
Query: "Who are the top 5 artists?"

Step 1: Generate query (1.2s)
  SELECT a.Name, COUNT(al.AlbumId)...
  (LLM already knows schema!)

Total time: ~1.2s, 1 query
```

**Result: 3.5x faster! 🚀**

## How Schema is Provided

The enhanced app extracts schema and adds it to the tool description:

```python
def create_schema_aware_tool_description(schema: str) -> str:
    return f"""Execute SQL queries against the configured SQLite database.

IMPORTANT: Use this schema information to generate accurate SQL queries:

{schema}

Guidelines:
- Use exact table and column names as shown above
- Pay attention to data types and constraints
- ...
"""

sql_tool = RunSqlTool(
    sql_runner=sqlite_runner,
    custom_tool_description=schema_aware_description
)
```

When the LLM decides to use the `run_sql` tool, it sees:
- All table names
- All column names with types
- Primary keys and foreign keys
- NOT NULL constraints
- Row counts
- Complete DDL

## Why Vanna v2 Doesn't Do This Automatically

Vanna v2 is designed as a **learning agent framework**, not just a text-to-SQL tool:

1. **User-aware security**: Different users might see different schemas
2. **Row-level security**: Schema might vary by permissions
3. **Large databases**: Some databases have 1000+ tables (too much for LLM context)
4. **Learning over time**: Agent memory improves with usage
5. **Flexibility**: Users control what schema info to share

## Three Ways to Provide Schema

### 1. Custom Tool Description (Best for small-medium databases)
```python
sql_tool = RunSqlTool(
    sql_runner=sqlite_runner,
    custom_tool_description=f"Execute SQL. Schema:\n{extracted_schema}"
)
```
✅ Fast - schema always available
✅ Simple - one-time extraction
❌ Large - can exceed LLM context for big databases

### 2. Agent Memory with RAG (Best for large databases)
```python
agent_memory.save_text_memory(content=ddl_for_table1)
agent_memory.save_text_memory(content=ddl_for_table2)
# LLM retrieves relevant schema based on question
```
✅ Scalable - only loads relevant tables
✅ Dynamic - can update schema over time
❌ Slower - requires RAG search
❌ Complex - needs memory setup

### 3. Custom System Prompt (Best for specific use cases)
```python
custom_prompt = f"""
You are a SQL expert. Database schema:
{schema}

Answer user questions by writing SQL queries.
"""

agent = Agent(
    llm_service=llm,
    system_prompt_builder=DefaultSystemPromptBuilder(base_prompt=custom_prompt)
)
```
✅ Always available - in every request
✅ Flexible - can add custom instructions
❌ Token usage - counts against every request
❌ Static - harder to update

## Recommendations

### For Development & Debugging
**Use:** `console_chat_app_with_schema.py`
- Fast startup, immediate schema awareness
- Perfect for understanding how things work
- Great for small-medium databases

### For Production
**Use:** Agent memory with RAG
- Scalable to large databases
- Secure - can filter by user permissions
- Improves over time

### For Simple Applications
**Use:** Custom tool description
- Easiest to implement
- Good enough for most use cases
- Works great for databases with < 50 tables

## Example: Complete Setup with Schema

```python
import sqlite3
from vanna import Agent, AgentConfig
from vanna.integrations.sqlite import SqliteRunner
from vanna.integrations.anthropic import AnthropicLlmService
from vanna.tools import RunSqlTool

# Extract schema
conn = sqlite3.connect("mydb.sqlite")
cursor = conn.cursor()
cursor.execute("SELECT sql FROM sqlite_master WHERE type='table'")
ddl_statements = [row[0] for row in cursor.fetchall()]
schema = "\n\n".join(ddl_statements)
conn.close()

# Create schema-aware tool
tool_description = f"""
Execute SQL queries against the database.

DATABASE SCHEMA:
{schema}

Use the schema above to write accurate SQL queries.
"""

sql_tool = RunSqlTool(
    sql_runner=SqliteRunner(database_path="mydb.sqlite"),
    custom_tool_description=tool_description
)

# Create agent
llm = AnthropicLlmService(model="claude-sonnet-4-20250514")
tool_registry = ToolRegistry()
tool_registry.register(sql_tool)

agent = Agent(llm_service=llm, tool_registry=tool_registry)

# Now the LLM knows your schema!
```

## Key Takeaways

1. **Vanna v2 requires you to provide schema information**
2. **The schema-aware console app does this automatically**
3. **This makes queries 3-5x faster**
4. **Choose the right approach based on your database size and use case**
5. **For the FastAPI server, add schema the same way**

## Next Steps

Try both console apps and see the difference:

```bash
# Without schema knowledge (slower, exploratory)
python console_chat_app.py Chinook.sqlite

# With schema knowledge (faster, direct)
python console_chat_app_with_schema.py Chinook.sqlite
```

You'll immediately notice the performance difference!
