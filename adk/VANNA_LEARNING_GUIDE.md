# Vanna Learning & Memory in Production

This guide explains how Vanna's learning system works in your multi-user UN HR application and the privacy/deployment considerations.

## Table of Contents

1. [How Vanna Learning Works](#how-vanna-learning-works)
2. [Current vs. New Implementation](#current-vs-new-implementation)
3. [Production Deployment Options](#production-deployment-options)
4. [Privacy & Security Considerations](#privacy--security-considerations)
5. [UN HR Use Case Scenarios](#un-hr-use-case-scenarios)
6. [Implementation Guide](#implementation-guide)

---

## How Vanna Learning Works

### The Learning Cycle

```
Query 1 (User A): "How many employees in Engineering?"
  ↓
  Vanna generates SQL: SELECT COUNT(*) FROM staffing_table WHERE department='Engineering'
  ↓
  Query executes successfully
  ↓
  ✅ Pattern stored in vector memory:
     Question pattern: "how many [entities] in [department]"
     SQL template: "SELECT COUNT(*) FROM ... WHERE department=..."
     Success: TRUE

Query 2 (User B): "How many people in Sales department?"
  ↓
  Vanna retrieves similar pattern from memory
  ↓
  Adapts the proven template
  ↓
  ⚡ Faster, more accurate SQL generation
  ↓
  ✅ Pattern reinforced and refined

Query 10 (User C): "Show me headcount by department"
  ↓
  Even better! Has seen many variations
  ↓
  Uses best practices from 9 previous queries
  ↓
  🚀 Optimal SQL generated instantly
```

### What Gets Stored in Memory

**Successful tool usage patterns:**
```json
{
  "question": "How many employees in Engineering?",
  "tool_name": "run_sql",
  "args": {
    "sql": "SELECT COUNT(*) FROM staffing_table WHERE department='Engineering'"
  },
  "success": true,
  "timestamp": "2025-11-16T10:30:00Z",
  "metadata": {"user": "hr_user_1", "source": "production"}
}
```

**Business rules:**
```json
{
  "content": "When counting employees, always filter for active status",
  "type": "business_rule",
  "timestamp": "2025-11-16T08:00:00Z"
}
```

**Vector embeddings:** Questions and SQL patterns are converted to vectors for semantic similarity search.

---

## Current vs. New Implementation

### Current Implementation ❌

**File:** `adk/agent/tools.py` (original)

```python
def query_staffing_table(question: str) -> dict:
    # Creates NEW agent for EVERY query
    vanna_agent = Agent(
        llm_service=llm,
        config=AgentConfig(...),
        tool_registry=tool_registry,
        # NO agent_memory parameter!
    )

    # Query executes
    # Agent is DISCARDED after query
    # Memory LOST
```

**Problems:**
- ❌ Each user starts from scratch
- ❌ No learning between queries
- ❌ Agent recreated 100+ times per day (wasteful)
- ❌ Can't improve over time
- ❌ Slower SQL generation

### New Implementation ✅

**File:** `adk/agent/vanna_agent_manager.py` (persistent)

```python
class VannaAgentManager:
    """Singleton manager with persistent memory."""

    def __init__(self):
        self._agent_memory = InMemoryAgentMemory()  # SHARED!

    def initialize_agent(self):
        self._agent = Agent(
            llm_service=llm,
            agent_memory=self._agent_memory,  # PERSISTENT MEMORY!
            # ...
        )

        # Pre-load training data
        self._load_training_data()

    async def query(self, question: str):
        # Uses SAME agent for ALL queries
        # Memory PERSISTS and GROWS
        # Agent LEARNS from every query
```

**Benefits:**
- ✅ Single agent instance (efficient)
- ✅ Learns from all queries
- ✅ Improves accuracy over time
- ✅ Faster responses (retrieves proven patterns)
- ✅ Shared knowledge across all users

---

## Production Deployment Options

### Option 1: Single Shared Agent (Recommended) ⭐

**Best for:** All UN HR users querying the same staffing database

**How it works:**
```
FastAPI Server (single instance)
  ↓
  VannaAgentManager (singleton)
    ↓
    Shared Agent Memory
      ↓
      All users benefit from all queries
```

**Setup:**
```python
# In your FastAPI startup
from adk.agent.vanna_agent_manager import get_vanna_manager

@app.on_event("startup")
async def startup():
    manager = get_vanna_manager()
    manager.initialize_agent(
        database_path="./unpolicy.db",
        table_name="staffing_table",
        load_training_data=True
    )
```

**Pros:**
- ✅ Maximum learning (all queries improve the system)
- ✅ Fastest response times (leverages all patterns)
- ✅ Simplest deployment
- ✅ Best for organization-wide tool

**Cons:**
- ⚠️ All users see patterns from all queries
- ⚠️ No isolation between departments/users

**Good for:**
- Public staffing data (headcount, averages)
- Organization-wide queries
- Non-sensitive HR analytics
- Internal tools where all users should have same access

### Option 2: Department-Isolated Agents

**Best for:** Different departments with separate data/privacy needs

**How it works:**
```python
class DepartmentVannaManager:
    def __init__(self):
        self._agents = {}  # dept_id -> agent instance

    def get_agent(self, department: str):
        if department not in self._agents:
            # Create agent with dept-specific memory
            memory = InMemoryAgentMemory()
            self._agents[department] = create_agent(memory)
        return self._agents[department]
```

**Pros:**
- ✅ Privacy isolation between departments
- ✅ Each department's queries improve their own agent
- ✅ Can have department-specific business rules

**Cons:**
- ⚠️ Less learning (smaller query pool per agent)
- ⚠️ More memory usage (multiple agents)

**Good for:**
- Departments with confidential data
- Different business rules per department
- Compliance requirements for data isolation

### Option 3: Stateless with Training Data Only

**Best for:** Maximum privacy, no cross-user learning

**How it works:**
```python
def query_staffing_table(question: str):
    # Create fresh agent with static training data
    memory = InMemoryAgentMemory()

    # Load static examples (same for all users)
    load_static_training_data(memory)

    # Create ephemeral agent
    agent = Agent(agent_memory=memory)

    # Query executes
    # Agent discarded (no learning from user queries)
```

**Pros:**
- ✅ Maximum privacy
- ✅ No cross-user learning
- ✅ Predictable behavior

**Cons:**
- ⚠️ No improvement over time
- ⚠️ Can't learn from user queries
- ⚠️ Slower (creates agent each time)

**Good for:**
- Highly regulated environments
- Paranoid privacy requirements
- Testing/development

---

## Privacy & Security Considerations

### What Information is Stored?

**With persistent memory:**
```
✅ Question text: "How many employees in Engineering?"
✅ Generated SQL: "SELECT COUNT(*) FROM ... WHERE department='Engineering'"
✅ Success/failure status
✅ Metadata: timestamp, user_id (optional)

❌ Actual query results (data rows)
❌ Sensitive employee information
❌ Personal identifiable information (PII)
```

**Key points:**
- ✅ **Questions and SQL patterns** are stored (for learning)
- ❌ **Query results** are NOT stored
- ❌ **Database data** is NOT stored in memory

### Privacy Options

#### 1. Anonymous Learning (Default)

```python
# Don't track which user asked which question
result = manager.query(
    question="How many employees?",
    user_id="anonymous",  # No user tracking
    metadata={"source": "production"}
)
```

#### 2. User-Tracked Learning

```python
# Track user for analytics (not isolation)
result = manager.query(
    question="How many employees?",
    user_id=request.user.email,  # Track who asked
    metadata={"department": "HR", "role": "analyst"}
)
```

#### 3. Department-Isolated Learning

```python
# Separate agent per department
manager = get_department_manager(user.department)
result = manager.query(question="...")
```

### Sensitive Queries

**Question:** What if someone asks "What is John Doe's salary?"

**Answer:**
1. Question pattern is stored: "What is [person]'s [field]?"
2. SQL template is stored: "SELECT [field] FROM ... WHERE name=..."
3. **Actual result (John's salary) is NOT stored**
4. Future queries can generate similar SQL, but data stays in database

**Mitigation options:**
- Add query filtering (block sensitive patterns)
- Use column-level permissions
- Audit sensitive queries
- Don't store questions with PII (filter before storing)

---

## UN HR Use Case Scenarios

### Scenario 1: Organization-Wide Tool

**Context:** All HR staff query same public staffing data

**Recommendation:** Single shared agent (Option 1)

**Why:**
- Non-sensitive data (headcount, averages, counts)
- All users should have same access
- Maximum learning benefit
- Fastest responses

**Implementation:**
```python
# Single manager for everyone
manager = get_vanna_manager()
manager.initialize_agent(
    database_path="./staffing.db",
    load_training_data=True
)

# All users use same agent
@app.post("/api/staffing/query")
async def staffing_query(question: str):
    result = await manager.query(question, user_id="hr_team")
    return result
```

**Learning benefits:**
- HR analyst asks "department headcount" → pattern stored
- Recruiter asks "hiring by department" → leverages similar pattern
- Manager asks "org structure" → even better (more examples)

### Scenario 2: Department-Specific Access

**Context:** Different departments have different data access

**Recommendation:** Department-isolated agents (Option 2)

**Why:**
- Each department has own data/rules
- Privacy between departments
- Department-specific learning

**Implementation:**
```python
class DepartmentManager:
    def __init__(self):
        self._agents = {}

    def get_agent(self, dept: str):
        if dept not in self._agents:
            # Create isolated agent for this department
            self._agents[dept] = VannaAgentManager()
            self._agents[dept].initialize_agent(
                database_path=f"./data/{dept}_staffing.db",
                load_training_data=True
            )
        return self._agents[dept]

dept_mgr = DepartmentManager()

@app.post("/api/staffing/query")
async def staffing_query(question: str, user: User):
    # Get department-specific agent
    manager = dept_mgr.get_agent(user.department)
    result = await manager.query(question, user_id=user.id)
    return result
```

### Scenario 3: Confidential HR Analytics

**Context:** Sensitive compensation/performance data

**Recommendation:** Stateless or minimal learning (Option 3)

**Why:**
- Can't risk exposing query patterns
- Compliance requirements
- Maximum privacy

**Implementation:**
```python
# Option A: Stateless (no learning from user queries)
def query_staffing_table(question: str):
    # Fresh agent each time
    manager = VannaAgentManager()
    manager.initialize_agent(load_training_data=True)
    result = await manager.query(question)
    # Manager discarded after query
    return result

# Option B: Filter sensitive queries
async def safe_query(question: str):
    # Check if question contains sensitive keywords
    if contains_pii(question):
        # Don't store pattern
        result = await execute_without_learning(question)
    else:
        # Normal learning
        result = await manager.query(question)
    return result
```

---

## Implementation Guide

### Step 1: Choose Your Deployment Option

Based on your privacy/learning needs:
- **Public data + max learning** → Option 1 (Single shared agent)
- **Department isolation** → Option 2 (Department agents)
- **Maximum privacy** → Option 3 (Stateless)

### Step 2: Update tools.py

Replace the current `query_staffing_table` function:

```python
# OLD (current) - No learning
def query_staffing_table(question: str) -> dict:
    # Creates new agent each time
    vanna_agent = Agent(...)  # No memory!
    # ...

# NEW - With persistent learning
def query_staffing_table(question: str) -> dict:
    from .vanna_agent_manager import get_vanna_manager

    manager = get_vanna_manager()

    # Initialize once (first call only)
    if not manager.get_stats()["initialized"]:
        manager.initialize_agent(
            database_path=os.getenv("STAFFING_DATABASE_PATH"),
            table_name=os.getenv("STAFFING_TABLE_NAME"),
            load_training_data=True
        )

    # Query using persistent agent
    loop = asyncio.get_event_loop()
    result = loop.run_until_complete(
        manager.query(question, user_id="un_hr_user")
    )

    return result
```

### Step 3: FastAPI Integration

```python
# main.py
from fastapi import FastAPI, Depends
from adk.agent.vanna_agent_manager import get_vanna_manager
import os

app = FastAPI()

@app.on_event("startup")
async def startup():
    """Initialize Vanna agent on server startup."""
    print("🚀 Initializing Vanna agent with persistent memory...")

    manager = get_vanna_manager()
    manager.initialize_agent(
        database_path=os.getenv("STAFFING_DATABASE_PATH", "./unpolicy.db"),
        table_name=os.getenv("STAFFING_TABLE_NAME", "staffing_table"),
        load_training_data=True
    )

    stats = manager.get_stats()
    print(f"✅ Vanna agent initialized: {stats}")

@app.get("/api/staffing/stats")
async def get_stats():
    """Get agent learning statistics."""
    manager = get_vanna_manager()
    return manager.get_stats()
```

### Step 4: Monitor Learning

```python
@app.get("/api/staffing/stats")
async def agent_stats():
    manager = get_vanna_manager()
    return {
        "initialized": manager.get_stats()["initialized"],
        "total_queries": manager.get_stats()["total_queries"],
        "memory_enabled": manager.get_stats()["memory_enabled"],
        "learning_active": True
    }
```

### Step 5: Test Learning

```python
# Test script
import asyncio
from adk.agent.vanna_agent_manager import get_vanna_manager

async def test_learning():
    manager = get_vanna_manager()
    manager.initialize_agent("./unpolicy.db", "staffing_table")

    # Query 1
    print("Query 1: First time asking...")
    result1 = await manager.query("How many employees?")
    print(f"  Took: {result1['execution_time']}ms")

    # Query 2 (similar)
    print("Query 2: Similar question...")
    result2 = await manager.query("How many people in total?")
    print(f"  Took: {result2['execution_time']}ms (should be faster!)")

    # Stats
    stats = manager.get_stats()
    print(f"\nTotal queries processed: {stats['total_queries']}")

asyncio.run(test_learning())
```

---

## Best Practices

### DO ✅

1. **Initialize once** at application startup
2. **Pre-load training data** with common query examples
3. **Monitor query patterns** for improvements
4. **Track statistics** (total queries, success rate)
5. **Use anonymous user_ids** if privacy is a concern
6. **Add business rules** to agent memory
7. **Test learning** in development first

### DON'T ❌

1. **Don't create new agents** for each query (defeats learning)
2. **Don't store PII** in questions if privacy required
3. **Don't share memory** across security boundaries
4. **Don't ignore failed queries** (they can teach too!)
5. **Don't forget to checkpoint** memory for restarts
6. **Don't expose sensitive patterns** in logs
7. **Don't skip training data** (gives agent a head start)

---

## Summary

**Current Implementation:**
- New agent per query
- No learning
- Slow and inefficient

**With Persistent Learning:**
- Single shared agent
- Learns from all queries
- Faster and smarter over time

**For UN HR:**
- **Option 1** (shared): Best for organization-wide public data
- **Option 2** (isolated): Best for department-specific needs
- **Option 3** (stateless): Best for maximum privacy

**Privacy:**
- Questions and SQL stored
- Results NOT stored
- PII can be filtered

**Benefits:**
- Improves accuracy
- Faster responses
- Learns organization terminology
- Better over time

**Next Steps:**
1. Choose deployment option
2. Update `query_staffing_table` to use manager
3. Initialize agent in FastAPI startup
4. Test learning behavior
5. Deploy and monitor

The agent gets smarter with every query your UN HR users ask!
