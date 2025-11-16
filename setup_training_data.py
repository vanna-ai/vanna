#!/usr/bin/env python3
"""
Helper script to pre-populate agent memory with training data.

This shows how to create context and add training data (business rules,
SQL examples) to agent memory before running the console app.

Usage:
    python setup_training_data.py
"""

import asyncio
import uuid
from vanna.core.tool import ToolContext
from vanna.core.user import User
from vanna.capabilities.agent_memory import InMemoryAgentMemory


async def create_training_context(agent_memory: InMemoryAgentMemory) -> ToolContext:
    """
    Create a ToolContext for training data setup.

    This context represents the "system" user performing initial setup.
    """
    return ToolContext(
        user=User(
            id="system",
            username="System",
            group_memberships=["admin"]  # Admin privileges for setup
        ),
        conversation_id="training-session",
        request_id=str(uuid.uuid4()),
        agent_memory=agent_memory
    )


async def setup_staffing_training_data():
    """
    Set up training data for staffing_table queries.

    This adds business rules and SQL examples to agent memory.
    """
    print("🔧 Setting up training data for staffing database...")

    # 1. Create agent memory
    agent_memory = InMemoryAgentMemory()

    # 2. Create context for training
    context = await create_training_context(agent_memory)

    # 3. Add business rules
    print("📝 Adding business rules...")

    await agent_memory.save_text_memory(
        content="""
        Business Rule: Active Employees
        - An employee is considered "active" if:
          * status = 'active'
          * deleted_at IS NULL
        - Exclude test employees (email LIKE '%test%')
        """,
        context=context
    )

    await agent_memory.save_text_memory(
        content="""
        Business Rule: Salary Analysis
        - For salary calculations:
          * Exclude NULL values
          * Exclude 0 values
          * Round to 2 decimal places
        - Format as currency: $XX,XXX.XX
        """,
        context=context
    )

    await agent_memory.save_text_memory(
        content="""
        Business Rule: Headcount Queries
        - Default to active employees only
        - Group by department for organizational views
        - Filter by hire_date for tenure analysis
        """,
        context=context
    )

    # 4. Add SQL examples
    print("💡 Adding SQL examples...")

    await agent_memory.save_tool_usage(
        question="Show all active employees",
        tool_name="run_sql",
        args={
            "sql": """
                SELECT employee_name, department, hire_date
                FROM staffing_table
                WHERE status = 'active'
                  AND deleted_at IS NULL
                ORDER BY hire_date DESC
            """
        },
        context=context,
        success=True,
        metadata={"category": "basic_query"}
    )

    await agent_memory.save_tool_usage(
        question="What is the average salary by department?",
        tool_name="run_sql",
        args={
            "sql": """
                SELECT
                    department,
                    ROUND(AVG(salary), 2) as avg_salary,
                    COUNT(*) as employee_count
                FROM staffing_table
                WHERE status = 'active'
                  AND salary IS NOT NULL
                  AND salary > 0
                GROUP BY department
                ORDER BY avg_salary DESC
            """
        },
        context=context,
        success=True,
        metadata={"category": "aggregation"}
    )

    await agent_memory.save_tool_usage(
        question="Show top 10 highest paid employees",
        tool_name="run_sql",
        args={
            "sql": """
                SELECT
                    employee_name,
                    department,
                    salary
                FROM staffing_table
                WHERE status = 'active'
                  AND salary IS NOT NULL
                ORDER BY salary DESC
                LIMIT 10
            """
        },
        context=context,
        success=True,
        metadata={"category": "ranking"}
    )

    await agent_memory.save_tool_usage(
        question="How many employees were hired each year?",
        tool_name="run_sql",
        args={
            "sql": """
                SELECT
                    strftime('%Y', hire_date) as year,
                    COUNT(*) as hires
                FROM staffing_table
                WHERE status = 'active'
                GROUP BY year
                ORDER BY year DESC
            """
        },
        context=context,
        success=True,
        metadata={"category": "time_series"}
    )

    print("✅ Training data setup complete!")
    print(f"   - Business rules: 3")
    print(f"   - SQL examples: 4")

    return agent_memory


async def demonstrate_context_usage():
    """
    Demonstrate different context scenarios.
    """
    print("\n" + "=" * 70)
    print("CONTEXT USAGE EXAMPLES")
    print("=" * 70 + "\n")

    agent_memory = InMemoryAgentMemory()

    # Example 1: System context (for setup)
    print("1️⃣  System Context (for initial setup)")
    system_context = ToolContext(
        user=User(id="system", group_memberships=["admin"]),
        conversation_id="setup",
        request_id=str(uuid.uuid4()),
        agent_memory=agent_memory
    )
    print(f"   User ID: {system_context.user.id}")
    print(f"   Groups: {system_context.user.group_memberships}")
    print()

    # Example 2: Regular user context
    print("2️⃣  Regular User Context")
    user_context = ToolContext(
        user=User(
            id="alice@company.com",
            username="Alice",
            email="alice@company.com",
            group_memberships=["analyst"],
            metadata={"department": "Engineering"}
        ),
        conversation_id="conv-123",
        request_id=str(uuid.uuid4()),
        agent_memory=agent_memory
    )
    print(f"   User ID: {user_context.user.id}")
    print(f"   Username: {user_context.user.username}")
    print(f"   Groups: {user_context.user.group_memberships}")
    print(f"   Department: {user_context.user.metadata.get('department')}")
    print()

    # Example 3: Admin context
    print("3️⃣  Admin User Context")
    admin_context = ToolContext(
        user=User(
            id="admin@company.com",
            username="Admin",
            group_memberships=["admin", "analyst"],
            permissions=["read_db", "write_db", "delete_db"]
        ),
        conversation_id="conv-456",
        request_id=str(uuid.uuid4()),
        agent_memory=agent_memory
    )
    print(f"   User ID: {admin_context.user.id}")
    print(f"   Groups: {admin_context.user.group_memberships}")
    print(f"   Permissions: {admin_context.user.permissions}")
    print()

    # Save data with different contexts
    print("4️⃣  Saving Data with Different Contexts")

    await agent_memory.save_text_memory(
        content="System-level rule: All dates in ISO format",
        context=system_context
    )
    print("   ✓ Saved system-level rule")

    await agent_memory.save_text_memory(
        content="Alice's note: Focus on Engineering department",
        context=user_context
    )
    print("   ✓ Saved Alice's user-specific note")

    await agent_memory.save_text_memory(
        content="Admin note: Quarterly review in progress",
        context=admin_context
    )
    print("   ✓ Saved admin-specific note")

    print("\n   Each piece of data is tagged with:")
    print("   - User ID (who saved it)")
    print("   - Timestamp (when)")
    print("   - Conversation ID (context)")


async def main():
    """Main demonstration."""

    # Setup training data
    agent_memory = await setup_staffing_training_data()

    # Demonstrate context usage
    await demonstrate_context_usage()

    print("\n" + "=" * 70)
    print("Now you can use this agent_memory with your Agent!")
    print("=" * 70)
    print("""
Example:

    agent = Agent(
        llm_service=llm,
        tool_registry=tool_registry,
        user_resolver=user_resolver,
        agent_memory=agent_memory  # ← Pre-populated with training data
    )
    """)


if __name__ == "__main__":
    asyncio.run(main())
