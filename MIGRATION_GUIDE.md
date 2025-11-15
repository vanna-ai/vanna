# Migration Guide: Vanna 0.x to Vanna 2.0+

This guide will help you migrate from Vanna 0.x (legacy) to Vanna 2.0+, the new user-aware agent framework.

## Table of Contents
- [Overview of Changes](#overview-of-changes)
- [Quick Migration Path](#quick-migration-path)
- [Migration Strategies](#migration-strategies)
  - [Strategy 1: Using the Legacy Adapter (Recommended for Quick Migration)](#strategy-1-using-the-legacy-adapter-recommended-for-quick-migration)
  - [Strategy 2: Full Migration to New Architecture](#strategy-2-full-migration-to-new-architecture)
- [Key Architectural Differences](#key-architectural-differences)
- [API Mapping](#api-mapping)
- [Common Migration Scenarios](#common-migration-scenarios)
- [Breaking Changes](#breaking-changes)
- [FAQ](#faq)

---

## Overview of Changes

Vanna 2.0+ represents a fundamental architectural shift from a simple LLM wrapper to a full-fledged **user-aware agent framework**. Here are the major changes:

### What's New in 2.0+
- ✅ **User awareness** - Identity and permissions flow through every layer
- ✅ **Web component** - Pre-built UI with streaming responses
- ✅ **Tool registry** - Modular, extensible tool system
- ✅ **Rich UI components** - Tables, charts, status cards (not just text)
- ✅ **Streaming by default** - Progressive responses via SSE
- ✅ **Enterprise features** - Audit logs, rate limiting, observability
- ✅ **FastAPI/Flask servers** - Production-ready backends included

### What Changed from 0.x
- ❌ Direct method calls (`vn.ask()`) → Agent-based workflow
- ❌ Monolithic `VannaBase` class → Modular tool system
- ❌ No user context → User-aware at every layer
- ❌ Simple text responses → Rich streaming UI components

---

## Quick Migration Path

**Can't migrate immediately?** Use the Legacy Adapter to get started quickly:

```python
# Assume you already have a working vn object from your Vanna 0.x code:
# vn = MyVanna(config={"model": "gpt-4"})
# vn.connect_to_postgres(...)
# vn.train(ddl="...")

# NEW: Just add these imports and wrap your existing vn object
from vanna import Agent, AgentConfig
from vanna.servers.fastapi import VannaFastAPIServer
from vanna.core.user import UserResolver, User, RequestContext
from vanna.legacy.adapter import LegacyVannaAdapter
from vanna.integrations.anthropic import AnthropicLlmService

# Define simple user resolver
class SimpleUserResolver(UserResolver):
    async def resolve_user(self, request_context: RequestContext) -> User:
        user_email = request_context.get_cookie('vanna_email')
        return User(id=user_email, email=user_email, group_memberships=['user'])

# Wrap your existing vn with the adapter
tools = LegacyVannaAdapter(vn)

# Create agent with new LLM service
llm = AnthropicLlmService(model="claude-haiku-4-5")
agent = Agent(llm_service=llm, tool_registry=tools, user_resolver=SimpleUserResolver())

# Run server
server = VannaFastAPIServer(agent)
server.run(host='0.0.0.0', port=8000)

# Now it works with the new Agent framework!
# (See Strategy 1 below for complete example)
```

---

## Migration Strategies

### Strategy 1: Using the Legacy Adapter (Recommended for Quick Migration)

**Best for:** Teams that want to adopt Vanna 2.0+ gradually while maintaining existing code.

#### Step 1: Install Vanna 2.0+

```bash
pip install --force-reinstall --no-cache-dir 'vanna[flask,anthropic] @ git+https://github.com/vanna-ai/vanna.git@v2'
```

#### Step 2: Wrap Your Existing VannaBase Instance

```python
from vanna import Agent, AgentConfig
from vanna.servers.fastapi import VannaFastAPIServer
from vanna.core.user import UserResolver, User, RequestContext
from vanna.legacy.adapter import LegacyVannaAdapter
from vanna.integrations.anthropic import AnthropicLlmService

# Assume you already have a working vn object from your existing code:
# vn = MyVanna(config={'model': 'gpt-4', 'api_key': 'your-key'})
# vn.connect_to_postgres(...)
# vn.train(ddl="...")
# etc.

# NEW: Define user resolution (required in 2.0+)
class SimpleUserResolver(UserResolver):
    async def resolve_user(self, request_context: RequestContext) -> User:
        user_email = request_context.get_cookie('vanna_email')
        if not user_email:
            raise ValueError("Missing 'vanna_email' cookie")

        # Admin users get 'admin' group membership
        if user_email == "admin@example.com":
            return User(id="admin_user", email=user_email, group_memberships=['admin'])

        # Regular users get 'user' group membership
        return User(id=user_email, email=user_email, group_memberships=['user'])

# NEW: Wrap with legacy adapter
# This automatically registers run_sql and memory tools from your VannaBase instance
tools = LegacyVannaAdapter(vn)

# NEW: Set up LLM for the new Agent framework
llm = AnthropicLlmService(
    model="claude-haiku-4-5",
    api_key="YOUR_ANTHROPIC_API_KEY"
)

# NEW: Create agent with legacy adapter as tool registry
agent = Agent(
    llm_service=llm,
    tool_registry=tools,  # LegacyVannaAdapter is a ToolRegistry
    user_resolver=SimpleUserResolver(),
    config=AgentConfig()
)

# NEW: Create and run server
server = VannaFastAPIServer(agent)

if __name__ == "__main__":
    # Run with: python your_script.py
    # Or: uvicorn your_module:server --host 0.0.0.0 --port 8000
    server.run(host='0.0.0.0', port=8000)
```

**What the LegacyVannaAdapter does:**
- Automatically wraps `vn.run_sql()` as the `run_sql` tool (available to 'user' and 'admin' groups)
- Exposes training data from `vn.get_training_data()` as searchable memory (via `search_saved_correct_tool_uses` tool)
- Optionally allows saving new training data (via `save_question_tool_args` tool - admin only)
- Maintains your existing database connection and training data

**Pros:**
- ✅ Minimal code changes
- ✅ Preserve existing training data
- ✅ Gradual migration path
- ✅ Get new features (web UI, streaming) immediately

**Cons:**
- ⚠️ Limited user awareness (all requests use same VannaBase instance)
- ⚠️ Can't leverage row-level security
- ⚠️ Missing some advanced features

---

### Strategy 2: Full Migration to New Architecture

**Best for:** New projects or teams ready for a complete rewrite.

#### Before (Vanna 0.x)

```python
from vanna import VannaBase
from vanna.openai_chat import OpenAI_Chat
from vanna.chromadb import ChromaDB_VectorStore

class MyVanna(ChromaDB_VectorStore, OpenAI_Chat):
    def __init__(self, config=None):
        ChromaDB_VectorStore.__init__(self, config=config)
        OpenAI_Chat.__init__(self, config=config)

vn = MyVanna(config={'model': 'gpt-4', 'api_key': 'your-key'})
vn.connect_to_postgres(...)

# Train
vn.train(ddl="CREATE TABLE customers ...")
vn.train(question="Top customers?", sql="SELECT ...")

# Ask
sql = vn.generate_sql("Who are the top customers?")
df = vn.run_sql(sql)
print(df)
```

#### After (Vanna 2.0+)

```python
from vanna import Agent, AgentConfig
from vanna.servers.fastapi import VannaFastAPIServer
from vanna.core.registry import ToolRegistry
from vanna.core.user import UserResolver, User, RequestContext
from vanna.integrations.anthropic import AnthropicLlmService
from vanna.tools import RunSqlTool
from vanna.integrations.postgres import PostgresRunner

# 1. Define user resolution
class MyUserResolver(UserResolver):
    async def resolve_user(self, request_context: RequestContext) -> User:
        # Extract from your auth system (JWT, cookies, etc.)
        token = request_context.get_header('Authorization')
        user_data = await self.validate_token(token)

        return User(
            id=user_data['id'],
            email=user_data['email'],
            permissions=user_data['permissions'],
            metadata={'role': user_data['role']}
        )

# 2. Set up tools
tools = ToolRegistry()
postgres_runner = PostgresRunner(
    host="localhost",
    dbname="mydb",
    user="user",
    password="password",
    port=5432
)
tools.register_local_tool(
    RunSqlTool(sql_runner=postgres_runner),
    access_groups=['user', 'admin']
)

# 3. Create agent
llm = AnthropicLlmService(model="claude-sonnet-4-5")
agent = Agent(
    llm_service=llm,
    tool_registry=tools,
    user_resolver=MyUserResolver(),
    config=AgentConfig(stream_responses=True)
)

# 4. Create server
server = VannaFastAPIServer(agent)
app = server.create_app()

# Run with: uvicorn main:app --host 0.0.0.0 --port 8000
# Visit http://localhost:8000 for web UI
```

**Pros:**
- ✅ Full access to new features
- ✅ True user awareness
- ✅ Better security and permissions
- ✅ Production-ready architecture

**Cons:**
- ⚠️ Requires rewriting code
- ⚠️ Need to migrate training data approach
- ⚠️ Steeper learning curve

---

## Key Architectural Differences

| Feature | Vanna 0.x | Vanna 2.0+ |
|---------|-----------|------------|
| **User Context** | None | `User` object with permissions flows through entire system |
| **Interaction Model** | Direct method calls (`vn.ask()`) | Agent-based with streaming components |
| **Tools** | Monolithic methods | Modular `Tool` classes with schemas |
| **Responses** | Plain text/DataFrames | Rich UI components (tables, charts, code) |
| **Training** | `vn.train()` with vector DB | System prompts, context enrichers, RAG tools |
| **Database Connection** | `vn.connect_to_postgres()` | `SqlRunner` implementations as dependencies |
| **Web UI** | None (custom implementation) | Built-in web component + backend |
| **Streaming** | None | Server-Sent Events by default |
| **Permissions** | None | Group-based access control on tools |
| **Audit Logs** | None | Built-in audit logging system |

---

## Summary

| If you want to... | Use this strategy |
|-------------------|-------------------|
| Migrate quickly with minimal changes | **Strategy 1: Legacy Adapter** |
| Get full access to new features | **Strategy 2: Full Migration** |
| Support both legacy and new code | **Strategy 1** initially, then gradual migration |
| Start a new project | **Strategy 2: Full Migration** |

**Recommended Path:**
1. Start with Legacy Adapter for quick migration
2. Gradually rewrite critical paths to native 2.0+ architecture
3. Eventually remove Legacy Adapter once fully migrated

Good luck with your migration! 🚀
