# Vanna Staffing Integration for Google ADK Agent

This guide explains how to use the Vanna-powered staffing query agent integrated into your Google ADK based UN HR Policy RAG application.

## Overview

The staffing agent is a specialized sub-agent that uses Vanna AI to convert natural language questions into SQL queries and execute them against your staffing database. It seamlessly integrates with your existing Google ADK agent architecture alongside salary, leave, travel, and benefits agents.

## Architecture

```
Main UN Policy Agent (Orchestrator)
├── Salary Agent (un_salary_specialist)
├── Leave Agent (un_leave_specialist)
├── Travel Agent (un_travel_specialist)
├── Benefits Agent (un_benefits_specialist)
└── Staffing Agent (un_staffing_specialist) ← NEW!
    └── query_staffing_table tool (Vanna-powered)
```

## Features

### What the Staffing Agent Can Do

- **Headcount Analysis**: Employee counts, department sizes, organizational structure
- **Salary Analytics**: Average/median salaries, compensation distributions, top earners
- **Hiring Trends**: New hires by period, tenure analysis, turnover insights
- **Department Queries**: Department-specific data, cross-department comparisons
- **Custom Queries**: Any question that can be answered from your staffing database

### How It Works

1. User asks a question in natural language
2. Main agent routes to staffing specialist
3. Staffing agent uses Vanna to:
   - Extract database schema
   - Generate SQL query
   - Execute query against database
   - Format results
4. Results displayed in chat with summary and insights

## Setup

### Prerequisites

1. **Vanna Package**: Ensure Vanna is installed
   ```bash
   pip install vanna
   ```

2. **Database**: Have your staffing database ready (SQLite format)

3. **Multi-User Configuration**: **IMPORTANT for FastAPI/production!**
   ```bash
   # Initialize database for concurrent access (run once)
   python adk/init_staffing_db.py ./unpolicy.db staffing_table
   ```
   This enables WAL mode and read-only connections for multi-user support.
   **See [CONCURRENCY_GUIDE.md](CONCURRENCY_GUIDE.md) for details.**

4. **Environment Variables**: Configure database location

### Configuration

Set these environment variables (or use defaults):

```bash
# Required: Anthropic API key for Vanna
export ANTHROPIC_API_KEY="your-anthropic-key-here"

# Optional: Database configuration
export STAFFING_DATABASE_PATH="./unpolicy.db"  # Default: ./unpolicy.db
export STAFFING_TABLE_NAME="staffing_table"     # Default: staffing_table

# Optional: Model selection
export ANTHROPIC_MODEL="claude-sonnet-4-20250514"  # Default model
```

### Database Schema

Your database should have a table (default name: `staffing_table`) with columns like:

```sql
CREATE TABLE staffing_table (
    id INTEGER PRIMARY KEY,
    employee_name TEXT,
    department TEXT,
    hire_date DATE,
    salary REAL,
    status TEXT,
    position TEXT,
    -- Add other columns as needed
);
```

The Vanna agent will automatically extract the schema, so it adapts to your specific table structure.

## Usage

### Starting the Agent

```bash
cd adk/agent
python -m google.adk.agents agent.py
```

Or if using a custom launcher:

```python
from adk.agent.agent import un_policy_agent

# The staffing agent is already integrated
# Just use the main agent as normal
```

### Example Queries

#### Basic Headcount

```
User: How many employees do we have?

Staffing Agent:
- Generates SQL: SELECT COUNT(*) FROM staffing_table
- Executes query
- Returns: "We have 1,234 employees in total"
```

#### Department Analysis

```
User: Show me headcount by department

Staffing Agent:
Department       | Employees
-----------------|----------
Engineering      | 450
Sales           | 398
HR              | 234
Finance         | 152

Key insights:
- Engineering is the largest department (36.5%)
- Total: 1,234 employees across 4 departments
```

#### Salary Analysis

```
User: What's the average salary by department?

Staffing Agent:
Department       | Avg Salary | Employee Count
-----------------|------------|---------------
Engineering      | $95,234    | 450
Finance         | $88,567    | 152
Sales           | $76,890    | 398
HR              | $68,234    | 234

Insights:
- Engineering has highest average salary
- Overall average: $82,231
```

#### Hiring Trends

```
User: How many people were hired in 2024?

Staffing Agent:
- 2024 hires: 89 employees
- Breakdown by quarter:
  Q1: 23 hires
  Q2: 31 hires
  Q3: 20 hires
  Q4: 15 hires
```

#### Complex Queries

```
User: Show me Engineering employees hired in the last year with salary above $100k

Staffing Agent:
Found 12 employees matching criteria:
[Employee list with details]
```

## Query Examples by Category

### Headcount Queries
- "How many employees are in each department?"
- "What is the total headcount?"
- "How many people work in Engineering?"
- "Show me department sizes"
- "Employee count by status"

### Salary Queries
- "What's the average salary by department?"
- "Who are the top 10 highest paid employees?"
- "What's the salary range in Sales?"
- "Show salary distribution"
- "Calculate median salary"

### Hiring & Tenure
- "How many employees were hired in 2024?"
- "Show hiring trends by year"
- "Who are the most recent hires?"
- "How many employees have been here more than 5 years?"
- "Tenure distribution"

### Department Analysis
- "List all departments"
- "Which department has the most employees?"
- "Show me Engineering department employees"
- "Compare department sizes"
- "Department growth trends"

### Custom Analytics
- "Show employees hired before 2020 by department"
- "Average tenure by department"
- "Salary quartiles across the organization"
- "Headcount trends over time"

## Integration with Other Agents

The staffing agent works seamlessly with other specialized agents:

### Combined Queries

```
User: What's the P-3 salary scale and how many P-3 employees do we have?

Response:
1. Salary Agent handles: P-3 salary scale information
2. Staffing Agent handles: Count of P-3 employees in database
```

### Context Switching

```
User: Show me Engineering headcount
[Staffing Agent responds]

User: What are their leave entitlements?
[Leave Agent responds with policy info]
```

## Technical Details

### Tool Implementation

The `query_staffing_table` tool (`adk/agent/tools.py`):

1. **Schema Extraction**: Automatically discovers table structure
2. **Vanna Integration**: Creates embedded Vanna agent
3. **SQL Generation**: Converts question to SQL using Vanna
4. **Query Execution**: Runs SQL against SQLite database
5. **Result Formatting**: Returns structured data with summary

### Agent Configuration

The staffing agent (`adk/agent/agent.py`):

```python
staffing_agent = Agent(
    name="un_staffing_specialist",
    model=model_config,
    description="UN Staffing Data Specialist...",
    instruction=load_staffing_agent_instruction(),
    tools=[query_staffing_table]
)
```

### Routing Logic

Main agent routing (`adk/agent/agent.py`):

- Detects staffing-related keywords
- Routes to staffing specialist
- Examples trigger words: "employees", "headcount", "department", "hired", "staffing levels"

## Customization

### Custom Database Tables

To use a different table name:

```bash
export STAFFING_TABLE_NAME="my_custom_employee_table"
```

### Custom Database Path

To use a different database:

```bash
export STAFFING_DATABASE_PATH="/path/to/my/database.db"
```

### Adding Training Data

For better query accuracy, you can add business rules and example queries:

```python
from setup_training_data import setup_staffing_training_data

# Add business rules for active employees, salary calculations, etc.
agent_memory = await setup_staffing_training_data()
```

## Troubleshooting

### Database Not Found

```
Error: Staffing database not found at: ./unpolicy.db
```

**Solution**: Set `STAFFING_DATABASE_PATH` to correct location

```bash
export STAFFING_DATABASE_PATH="/path/to/your/database.db"
```

### Table Not Found

```
Error: Table 'staffing_table' not found in database
```

**Solution**: Set `STAFFING_TABLE_NAME` to your actual table name

```bash
export STAFFING_TABLE_NAME="employees"  # or your table name
```

### Vanna Import Error

```
Error: Vanna integration not available
```

**Solution**: Install Vanna package

```bash
pip install vanna
pip install anthropic  # If not already installed
```

### Query Not Working

If queries aren't generating good results:

1. **Check Schema**: Ensure table has expected columns
2. **Add Training**: Use `setup_training_data.py` to add examples
3. **Rephrase Query**: Try more specific questions
4. **Check Logs**: Enable debug logging

```bash
export DEBUG_TOOLS="true"
```

## Performance Optimization

### Caching

Vanna internally caches schema information to avoid repeated extraction.

### Token Usage

- Schema extracted once per query
- Minimal overhead compared to full database scan
- Optimized for single-table queries

### Query Limits

Vanna uses sensible defaults:
- `max_tool_iterations=3`: Limits retry attempts
- Non-streaming for tool usage: Faster response
- Schema-aware: Only includes relevant table info

## Multi-User / Concurrency

### Designed for FastAPI + Next.js

The integration is optimized for multi-user web applications:

**Concurrent Access:**
- ✅ Multiple users can query simultaneously
- ✅ Read-only connections prevent locking
- ✅ WAL mode allows unlimited concurrent readers
- ✅ No blocking between simultaneous queries

**Performance:**
- 100-1000 concurrent users: **Fully supported**
- Average query time: **10-50ms** (depending on complexity)
- No connection pooling needed (connections created on-demand)

**Setup for Production:**
```bash
# One-time initialization for multi-user access
python adk/init_staffing_db.py ./unpolicy.db staffing_table
```

**See [CONCURRENCY_GUIDE.md](CONCURRENCY_GUIDE.md) for:**
- Detailed concurrency explanation
- Performance benchmarks
- Load testing examples
- Migration path to PostgreSQL if needed

## Security Considerations

### Read-Only Access

The staffing agent only performs SELECT queries:
- No INSERT, UPDATE, DELETE operations
- No table modifications
- Database opened in read-only mode: `file:path?mode=ro`
- Perfect for multi-user environments (no write conflicts)

### Data Privacy

- Only queries data from specified table
- No cross-database queries
- Respects database access permissions

### Query Validation

- SQL generated by Vanna
- Validated against schema
- Sandboxed execution environment

## Examples

### Example 1: Department Headcount

**User Query**: "How many employees in each department?"

**Agent Flow**:
1. Main agent routes to staffing specialist
2. Staffing agent calls `query_staffing_table("How many employees in each department?")`
3. Vanna generates SQL:
   ```sql
   SELECT department, COUNT(*) as employee_count
   FROM staffing_table
   GROUP BY department
   ORDER BY employee_count DESC
   ```
4. Query executes and returns results
5. Agent formats response with insights

### Example 2: Salary Analysis

**User Query**: "Show me average salary by department"

**SQL Generated**:
```sql
SELECT
    department,
    ROUND(AVG(salary), 2) as avg_salary,
    COUNT(*) as employee_count
FROM staffing_table
WHERE salary IS NOT NULL AND salary > 0
GROUP BY department
ORDER BY avg_salary DESC
```

**Response Includes**:
- Tabular data
- Summary statistics
- Key insights
- Data source attribution

## Advanced Usage

### Programmatic Access

```python
from adk.agent.tools import query_staffing_table

# Direct tool usage
result = query_staffing_table("How many employees hired in 2024?")

if result["status"] == "success":
    data = result["result"]["data"]
    summary = result["result"]["summary"]
    sql = result["result"]["sql"]

    print(f"SQL: {sql}")
    print(f"Summary: {summary}")
    print(f"Data: {data}")
```

### Custom Integrations

Integrate with dashboards, reports, or other systems:

```python
# Get data for dashboard
def get_department_stats():
    result = query_staffing_table("Department headcount and average salary")
    return result["result"]["data"]

# Export to CSV
def export_recent_hires():
    result = query_staffing_table("Employees hired in last 30 days")
    import pandas as pd
    df = pd.DataFrame(result["result"]["data"])
    df.to_csv("recent_hires.csv", index=False)
```

## Next Steps

1. **Set up your database**: Ensure staffing_table exists with data
2. **Configure environment**: Set STAFFING_DATABASE_PATH if needed
3. **Test queries**: Try example queries to verify integration
4. **Add training data**: Use setup_training_data.py for better accuracy
5. **Customize**: Adapt to your specific database schema and needs

## Support

For issues or questions:
- Check this documentation
- Review `adk/agent/tools.py` for tool implementation
- Review `adk/agent/agent.py` for agent configuration
- Enable debug logging with `DEBUG_TOOLS=true`

## Summary

The Vanna staffing integration provides:
- Natural language querying of staffing data
- Automatic SQL generation using AI
- Seamless integration with Google ADK agent architecture
- Comprehensive analytics and insights
- Easy setup and configuration

Ask questions in plain English, and the staffing agent will handle the rest!
