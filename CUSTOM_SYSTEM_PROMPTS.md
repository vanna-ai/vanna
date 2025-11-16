# Customizing System Prompts in Vanna v2

Guide to customizing system prompts to control how the LLM generates SQL queries.

## 🎯 What is a System Prompt?

The **system prompt** is instructions sent to the LLM that define its role, behavior, and guidelines. It controls:
- How the LLM interprets user questions
- SQL query generation style and standards
- Response format and tone
- Business rules and conventions

## 📊 Two Ways to Influence SQL Generation

Vanna v2 provides two mechanisms:

| Method | Purpose | When to Use |
|--------|---------|-------------|
| **Tool Description** | Schema + SQL syntax rules | Always (we already use this!) |
| **System Prompt** | Domain knowledge + behavior | Optional (for fine-tuning) |

### Current Setup (Tool Description)

The console apps already use **custom tool descriptions** to provide schema:

```python
def create_schema_aware_tool_description(schema: str) -> str:
    return f"""Execute SQL queries.

{schema}  # ← Schema goes here

Guidelines:
- Use exact table/column names
- SQLite-compatible syntax
"""
```

This works great! But you can add a **system prompt** for more control.

## ✅ Official Way to Add Custom System Prompts

Based on Vanna's official example (`src/vanna/examples/custom_system_prompt_example.py`):

### Step 1: Import the Correct Interface

```python
from vanna.core.interfaces import SystemPromptBuilder  # ← Official interface
from vanna.core.models import ToolSchema, User
from typing import List, Optional
```

### Step 2: Create Your Custom Builder

```python
class MySystemPromptBuilder(SystemPromptBuilder):
    """Custom system prompt for SQL generation."""

    async def build_system_prompt(
        self, user: User, tools: List[ToolSchema]
    ) -> Optional[str]:
        """
        This method is called once per conversation turn.
        Return your custom instructions here.
        """
        return """You are an expert SQL assistant.

Your responsibilities:
1. Write efficient SQL queries
2. Explain results clearly
3. Suggest follow-up questions

Guidelines:
- Validate syntax before execution
- Use JOINs appropriately
- Limit large result sets
"""
```

### Step 3: Pass to Agent

```python
from vanna import Agent

agent = Agent(
    llm_service=llm,
    tool_registry=tool_registry,
    user_resolver=user_resolver,
    system_prompt_builder=MySystemPromptBuilder(),  # ← Add this!
)
```

That's it! The LLM will now follow your custom instructions.

## 📝 Complete Example

I created `console_chat_app_custom_prompt.py` with two system prompt examples:

### Example 1: General SQL Expert

```python
class SQLExpertSystemPromptBuilder(SystemPromptBuilder):
    async def build_system_prompt(self, user: User, tools: List[ToolSchema]) -> Optional[str]:
        return """You are an expert SQL database assistant.

Your primary responsibilities:
1. Translate natural language into efficient SQL
2. Analyze and explain query results
3. Suggest optimizations

SQL Query Guidelines:
- Validate table/column names against schema
- Use appropriate JOINs (avoid Cartesian products)
- Limit results to 1000 rows by default
- Use explicit column names (not SELECT *)
- Format dates as YYYY-MM-DD

Response Format:
1. Explain your approach
2. Execute the query
3. Summarize results with insights
4. Suggest follow-up questions
"""
```

### Example 2: Domain-Specific (Staffing)

```python
class StaffingSystemPromptBuilder(SystemPromptBuilder):
    async def build_system_prompt(self, user: User, tools: List[ToolSchema]) -> Optional[str]:
        return """You are an expert HR analytics assistant.

DOMAIN: Employee Staffing and Human Resources

Your expertise:
- Headcount analysis (by dept, location, status)
- Compensation analysis (salary ranges, averages)
- Tenure analysis (retention, turnover, trends)

SQL Standards for Staffing Data:
- Exclude NULL/0 salaries in compensation queries
- Filter status='active' for headcount (unless specified)
- Default to last 12 months for date queries
- Group by department/location for aggregations

Formatting Rules:
- Salaries: $75,000 (currency with commas)
- Headcount: Whole numbers only
- Percentages: One decimal (15.3%)
- Dates: YYYY-MM-DD format

Data Privacy:
- No individual PII without aggregation
- Use employee_id instead of names

Response Style:
- Lead with key metric
- Provide context and trends
- Suggest actionable next steps
"""
```

## 🚀 How to Use

### Run the Custom Prompt Demo

```bash
python console_chat_app_custom_prompt.py myapp.db staffing_table
```

This version uses the **StaffingSystemPromptBuilder** by default.

### Customize for Your Needs

Edit `console_chat_app_custom_prompt.py` line 310-315:

```python
# Option 1: General SQL expert
custom_prompt_builder = SQLExpertSystemPromptBuilder(domain_context="my business")

# Option 2: Staffing-specific (default)
custom_prompt_builder = StaffingSystemPromptBuilder()

# Option 3: Your own custom builder
class MyCustomBuilder(SystemPromptBuilder):
    async def build_system_prompt(self, user, tools):
        return "Your custom instructions here..."

custom_prompt_builder = MyCustomBuilder()
```

## 🔍 What Goes Where?

### Tool Description (always include):
- **Database schema** (tables, columns, types)
- **SQL syntax rules** (SQLite-specific features)
- **Available operations** (SELECT, JOIN, etc.)

### System Prompt (optional, for fine-tuning):
- **Domain context** (what the database is for)
- **Business rules** (how to interpret data)
- **Response style** (tone, format, detail level)
- **Best practices** (performance, conventions)

## 💡 Examples by Use Case

### Use Case 1: Enforce Query Standards

```python
async def build_system_prompt(self, user, tools):
    return """SQL Query Standards:

REQUIRED:
- Every query must have a LIMIT clause (max 10,000)
- Use explicit column names (NO SELECT *)
- Always add WHERE clauses for large tables
- Include comments explaining complex logic

FORBIDDEN:
- DROP, DELETE, TRUNCATE commands
- Queries without LIMIT on production tables
- Cartesian products (missing JOIN conditions)
"""
```

### Use Case 2: Add Business Context

```python
async def build_system_prompt(self, user, tools):
    return """Business Context:

This is an e-commerce database:
- 'orders' table: Customer purchases
- 'products' table: Inventory catalog
- 'customers' table: User accounts

Common Business Rules:
- Revenue = SUM(order_items.price * quantity)
- Active products: status = 'active'
- Test data: exclude email LIKE '%test%'
- Fiscal year: July 1 - June 30

When users ask for "sales", they mean completed orders (status='shipped').
When users ask for "customers", they mean active accounts (deleted_at IS NULL).
"""
```

### Use Case 3: Response Formatting

```python
async def build_system_prompt(self, user, tools):
    return """Response Format:

For every query, provide:

1. **Quick Answer** (1 sentence)
   "There are 450 employees across 3 departments."

2. **Query Explanation** (brief)
   "I'll count employees grouped by department..."

3. **SQL Execution** (use run_sql tool)

4. **Insights** (2-3 bullet points)
   • Engineering has the most employees (45%)
   • Sales and HR are roughly equal
   • 15% increase from last quarter

5. **Follow-up Questions** (2-3 suggestions)
   "Would you like to see:
   - Salary breakdown by department?
   - Hiring trends over time?
   - Department headcount history?"
"""
```

### Use Case 4: User-Specific Prompts

```python
class RoleBasedPromptBuilder(SystemPromptBuilder):
    async def build_system_prompt(self, user, tools):
        # Different prompts based on user role
        if "admin" in user.permissions:
            return """You're assisting an admin user.

Access: Full database access
Focus: System health, data quality, performance
Show: Technical details, query plans, optimization tips
"""
        elif "analyst" in user.permissions:
            return """You're assisting a data analyst.

Access: Read-only on business tables
Focus: Insights, trends, visualizations
Show: Business metrics, comparisons, recommendations
"""
        else:
            return """You're assisting a standard user.

Access: Basic queries on public data
Focus: Simple questions and reports
Show: Easy-to-understand summaries
"""
```

## 🎯 Best Practices

### DO:
✅ Keep prompts focused and specific
✅ Include examples of good queries
✅ Define formatting standards clearly
✅ Add business context and rules
✅ Specify response structure

### DON'T:
❌ Make prompts too long (> 1000 words)
❌ Repeat information from tool descriptions
❌ Include schema details (put those in tool description)
❌ Use vague instructions like "be helpful"

## 📊 System Prompt vs Tool Description

```
┌─────────────────────────────────────────────┐
│ SYSTEM PROMPT                               │
│ ─────────────────────────────────────────── │
│ • Domain knowledge                          │
│ • Business rules                            │
│ • Response style                            │
│ • Best practices                            │
│ • Tone and format                           │
└─────────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────────┐
│ TOOL DESCRIPTION (run_sql)                  │
│ ─────────────────────────────────────────── │
│ • Database schema                           │
│ • Table/column details                      │
│ • SQL syntax rules                          │
│ • Available operations                      │
└─────────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────────┐
│ LLM GENERATES SQL                           │
└─────────────────────────────────────────────┘
```

## 🔧 Debugging Your System Prompt

Want to see what prompt the LLM receives? Add logging:

```python
class DebugPromptBuilder(SystemPromptBuilder):
    async def build_system_prompt(self, user, tools):
        prompt = """Your custom prompt here..."""

        # Log it
        print("=" * 70)
        print("SYSTEM PROMPT SENT TO LLM:")
        print("=" * 70)
        print(prompt)
        print("=" * 70)

        return prompt
```

## 📚 See Also

- **console_chat_app_custom_prompt.py** - Complete working example
- **src/vanna/examples/custom_system_prompt_example.py** - Official Vanna example
- **SCHEMA_DISCOVERY_EXPLAINED.md** - How schema is provided to LLM
- **Vanna README** - Section 6: LLM Context Enhancers

## 🚀 Quick Start

```bash
# 1. Try the custom prompt demo
python console_chat_app_custom_prompt.py myapp.db staffing_table

# 2. Edit the builder in the file (lines 120-180)

# 3. Run again to see the difference!
```

The custom prompt approach gives you fine-grained control over SQL generation behavior while keeping schema information in the tool description where it belongs.
