# Training in Vanna v2 - Complete Guide

**Important:** The way "training" works has fundamentally changed from Vanna 0.x to Vanna 2.0+

## 🔄 Key Difference: v1 vs v2

### Vanna 0.x (Legacy) - Explicit Training

```python
# Old way - v0.x
vn = MyVanna(config={'model': 'gpt-4'})

# Train with DDL
vn.train(ddl="""
    CREATE TABLE customers (
        id INT PRIMARY KEY,
        name TEXT,
        email TEXT
    )
""")

# Train with documentation
vn.train(documentation="Our business defines revenue as...")

# Train with SQL examples
vn.train(question="Who are top customers?",
         sql="SELECT name, SUM(total) FROM customers...")
```

### Vanna 2.0+ (Current) - Agent Memory

**There is NO `train()` method in Vanna v2!**

Instead, you use **Agent Memory** for the same purpose:

```python
# New way - v2.0+
from vanna import Agent
from vanna.capabilities.agent_memory import InMemoryAgentMemory
from vanna.tools import SaveTextMemoryTool

# Create agent with memory
agent_memory = InMemoryAgentMemory()

agent = Agent(
    llm_service=llm,
    tool_registry=tool_registry,
    user_resolver=user_resolver,
    agent_memory=agent_memory  # ← Memory replaces training
)
```

## 📚 How to "Train" in Vanna v2

### Method 1: Pre-populate Text Memory (Recommended)

This is the equivalent of `vn.train(ddl=...)` and `vn.train(documentation=...)`:

```python
from vanna.capabilities.agent_memory import InMemoryAgentMemory
from vanna.core.tool import ToolContext
from vanna.core.user import User
import uuid

# Create memory instance
agent_memory = InMemoryAgentMemory()

# Create a tool context (required for memory operations)
context = ToolContext(
    user=User(id="system", group_memberships=["admin"]),
    conversation_id="training",
    request_id=str(uuid.uuid4()),
    agent_memory=agent_memory
)

# Add DDL (schema information)
await agent_memory.save_text_memory(
    content="""
    CREATE TABLE customers (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        email TEXT UNIQUE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """,
    context=context
)

await agent_memory.save_text_memory(
    content="""
    CREATE TABLE orders (
        id INTEGER PRIMARY KEY,
        customer_id INTEGER,
        total DECIMAL(10,2),
        order_date DATE,
        FOREIGN KEY (customer_id) REFERENCES customers(id)
    );
    """,
    context=context
)

# Add documentation (business context)
await agent_memory.save_text_memory(
    content="""
    Business Rule: Revenue is calculated as SUM(orders.total)
    where order_status = 'completed'
    """,
    context=context
)

await agent_memory.save_text_memory(
    content="""
    Data Convention: Active customers have deleted_at IS NULL
    and email NOT LIKE '%test%'
    """,
    context=context
)

# Add SQL examples
await agent_memory.save_tool_usage(
    question="Who are the top 10 customers by revenue?",
    tool_name="run_sql",
    args={
        "sql": """
        SELECT c.name, SUM(o.total) as revenue
        FROM customers c
        JOIN orders o ON c.id = o.customer_id
        WHERE o.order_status = 'completed'
        GROUP BY c.id, c.name
        ORDER BY revenue DESC
        LIMIT 10
        """
    },
    context=context,
    success=True
)
```

### Method 2: Use SaveTextMemoryTool (Interactive)

Add the save tool so users (or the LLM) can add documentation:

```python
from vanna.tools import SaveTextMemoryTool

# Register the save tool
save_tool = SaveTextMemoryTool(agent_memory=agent_memory)
tool_registry.register(save_tool)

# Now the LLM can save information to memory when needed
# Or users can explicitly ask: "Save this as documentation: Revenue = ..."
```

### Method 3: Use Custom Tool Description (For Schema)

**This is what the console apps already do!**

Instead of saving schema to memory, put it directly in the tool description:

```python
from vanna.tools import RunSqlTool

# Extract schema
schema = """
CREATE TABLE customers (id INT, name TEXT, email TEXT);
CREATE TABLE orders (id INT, customer_id INT, total DECIMAL);
"""

# Create tool with schema in description
custom_description = f"""Execute SQL queries.

DATABASE SCHEMA:
{schema}

Use the schema above to write accurate queries.
"""

sql_tool = RunSqlTool(
    sql_runner=sqlite_runner,
    custom_tool_description=custom_description  # ← Schema goes here
)
```

**This is the most efficient approach for schema!**

## 🎯 Which Approach to Use?

### For Schema (Table/Column Information)

✅ **Recommended: Custom Tool Description**
- Put schema directly in RunSqlTool description
- Always available to LLM
- Fast (no RAG search needed)
- This is what console_chat_app_with_schema.py does

```python
sql_tool = RunSqlTool(
    sql_runner=runner,
    custom_tool_description=f"Execute SQL. Schema:\n{schema}"
)
```

❌ **Not Recommended: Agent Memory**
- Slower (requires RAG search)
- More complex setup
- Only useful if schema changes frequently

### For Business Rules & Documentation

✅ **Recommended: Agent Memory**
- Dynamic (can update without restarting)
- Searchable (LLM finds relevant rules)
- User-specific (different rules for different users)

```python
await agent_memory.save_text_memory(
    content="Revenue = SUM(total) WHERE status='completed'",
    context=context
)
```

### For SQL Examples (Question/Answer Pairs)

✅ **Recommended: Agent Memory with Auto-Save**
- Automatically saves successful queries
- Learns from usage over time
- Use `save_question_tool_args` tool

```python
from vanna.tools import SaveQuestionToolArgsTool

# Register the auto-save tool
save_qa_tool = SaveQuestionToolArgsTool(agent_memory=agent_memory)
tool_registry.register(save_qa_tool)

# Now successful queries are automatically saved
```

## 📋 Complete Setup Example

Here's a complete example combining all approaches:

```python
import asyncio
from vanna import Agent, AgentConfig
from vanna.core.registry import ToolRegistry
from vanna.core.user import SimpleUserResolver, User
from vanna.core.tool import ToolContext
from vanna.capabilities.agent_memory import InMemoryAgentMemory
from vanna.integrations.anthropic import AnthropicLlmService
from vanna.integrations.sqlite import SqliteRunner
from vanna.tools import (
    RunSqlTool,
    SaveTextMemoryTool,
    SaveQuestionToolArgsTool,
    LocalFileSystem
)
import uuid

async def setup_agent_with_training():
    # 1. Create agent memory
    agent_memory = InMemoryAgentMemory()

    # 2. Pre-populate with "training data"
    context = ToolContext(
        user=User(id="system", group_memberships=["admin"]),
        conversation_id="training",
        request_id=str(uuid.uuid4()),
        agent_memory=agent_memory
    )

    # Add business rules
    await agent_memory.save_text_memory(
        content="Active customers: deleted_at IS NULL AND email NOT LIKE '%test%'",
        context=context
    )

    await agent_memory.save_text_memory(
        content="Revenue calculation: SUM(orders.total) WHERE status = 'completed'",
        context=context
    )

    # Add SQL examples
    await agent_memory.save_tool_usage(
        question="Show top customers by revenue",
        tool_name="run_sql",
        args={
            "sql": "SELECT c.name, SUM(o.total) as revenue FROM customers c JOIN orders o ON c.id = o.customer_id GROUP BY c.id ORDER BY revenue DESC LIMIT 10"
        },
        context=context,
        success=True
    )

    # 3. Extract schema for tool description
    schema = """
    CREATE TABLE customers (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        email TEXT UNIQUE
    );

    CREATE TABLE orders (
        id INTEGER PRIMARY KEY,
        customer_id INTEGER,
        total DECIMAL(10,2),
        status TEXT
    );
    """

    # 4. Create tools
    tool_registry = ToolRegistry()
    file_system = LocalFileSystem(working_directory="./data")

    # SQL tool with schema
    sql_tool = RunSqlTool(
        sql_runner=SqliteRunner(database_path="mydb.db"),
        file_system=file_system,
        custom_tool_description=f"""Execute SQL queries.

DATABASE SCHEMA:
{schema}

Use exact table/column names from schema above.
"""
    )
    tool_registry.register(sql_tool)

    # Memory tools (for adding more training data)
    save_text_tool = SaveTextMemoryTool(agent_memory=agent_memory)
    tool_registry.register(save_text_tool)

    save_qa_tool = SaveQuestionToolArgsTool(agent_memory=agent_memory)
    tool_registry.register(save_qa_tool)

    # 5. Create agent
    llm = AnthropicLlmService(model="claude-sonnet-4-20250514")
    user_resolver = SimpleUserResolver()

    agent = Agent(
        llm_service=llm,
        tool_registry=tool_registry,
        user_resolver=user_resolver,
        agent_memory=agent_memory,  # ← Memory provides "training"
        config=AgentConfig(stream_responses=True)
    )

    return agent

# Run it
agent = asyncio.run(setup_agent_with_training())
```

## 🔍 How It Works

When the LLM processes a question:

1. **System Prompt** includes memory instructions
2. **LLM decides** to search memory for relevant context
3. **RAG search** finds similar questions/documentation
4. **Context injected** into the system prompt
5. **SQL tool description** provides schema
6. **LLM generates** SQL using all available context

### Example Flow

```
User: "Show me top customers by revenue"

Step 1: LLM searches memory
  → Finds: "Revenue = SUM(orders.total) WHERE status='completed'"
  → Finds: Previous SQL example for "top customers"

Step 2: Context added to system prompt
  → System prompt now includes business rules
  → System prompt includes similar SQL examples

Step 3: LLM reads SQL tool description
  → Gets complete database schema
  → Understands available tables/columns

Step 4: LLM generates SQL
  → Uses schema from tool description
  → Applies business rules from memory
  → Follows pattern from similar examples

Step 5: Query executes successfully
  → Auto-saved to memory for future use
```

## 🆚 Comparison Table

| Aspect | Vanna 0.x | Vanna 2.0+ |
|--------|-----------|------------|
| **Schema** | `vn.train(ddl="...")` | Custom tool description or agent memory |
| **Documentation** | `vn.train(documentation="...")` | `agent_memory.save_text_memory()` |
| **SQL Examples** | `vn.train(question="...", sql="...")` | `agent_memory.save_tool_usage()` |
| **Storage** | Vector DB (ChromaDB, Pinecone, etc.) | AgentMemory implementations |
| **Retrieval** | Automatic during `generate_sql()` | Via RAG tools or context enhancer |
| **User-Specific** | No | Yes (per-user memories) |

## 💡 Best Practices

### 1. Start Simple

```python
# Just use schema in tool description
sql_tool = RunSqlTool(
    sql_runner=runner,
    custom_tool_description=f"Execute SQL.\n\nSchema:\n{schema}"
)
```

### 2. Add Memory for Complex Domains

```python
# Add business rules and conventions
await agent_memory.save_text_memory(
    content="Business rules and conventions here...",
    context=context
)
```

### 3. Enable Auto-Learning

```python
# Let the agent learn from successful queries
save_qa_tool = SaveQuestionToolArgsTool(agent_memory=agent_memory)
tool_registry.register(save_qa_tool)
```

## 🚀 Migration from v0.x

If you have existing v0.x training data:

### Option 1: Use Legacy Adapter

```python
from vanna.legacy.adapter import LegacyVannaAdapter

# Wrap your old vn object
vn = MyOldVanna(...)
vn.train(ddl="...")  # Your existing training

# Wrap it
tools = LegacyVannaAdapter(vn)

# Use with new agent
agent = Agent(llm_service=llm, tool_registry=tools, ...)
```

### Option 2: Migrate to Agent Memory

```python
# Get training data from v0.x
training_data = vn.get_training_data()

# Convert to v2.0+ format
for item in training_data:
    if item['training_data_type'] == 'ddl':
        await agent_memory.save_text_memory(
            content=item['content'],
            context=context
        )
    elif item['training_data_type'] == 'sql':
        await agent_memory.save_tool_usage(
            question=item['question'],
            tool_name="run_sql",
            args={"sql": item['sql']},
            context=context,
            success=True
        )
```

## ✅ Summary

**"Training" in Vanna v2 = Providing Context**

Three mechanisms:
1. **Tool Description** → Schema (fastest, recommended)
2. **Agent Memory** → Business rules, documentation (dynamic, searchable)
3. **Auto-Save** → Learn from usage (automatic improvement)

**For your staffing_table:**

```python
# Schema in tool description (what we already do)
sql_tool = RunSqlTool(..., custom_tool_description=f"Schema:\n{schema}")

# Optional: Add business rules to memory
await agent_memory.save_text_memory(
    content="For headcount, exclude terminated employees (status='active')",
    context=context
)

# Optional: Enable learning
tool_registry.register(SaveQuestionToolArgsTool(agent_memory=agent_memory))
```

That's it! The console apps already handle schema efficiently via tool descriptions. Agent memory is optional for advanced use cases.
