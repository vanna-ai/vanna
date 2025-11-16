# ============================================================================
# VANNA STAFFING TABLE QUERY TOOL (WITH PERSISTENT LEARNING)
# ============================================================================

def query_staffing_table(question: str) -> dict:
    """Query the staffing table using Vanna AI-powered SQL generation with persistent learning.

    This tool uses a PERSISTENT Vanna agent that:
    - Learns from all successful queries across all users
    - Improves accuracy and speed over time
    - Retrieves and adapts proven query patterns
    - Shares knowledge across the entire organization

    The agent maintains a shared memory of successful SQL patterns, so each
    query helps improve the system for all future users.

    Args:
        question (str): Natural language question about staffing data
                       (e.g., "How many employees in Engineering?",
                        "What's the average salary by department?",
                        "Show recent hires in 2024")

    Returns:
        dict: {
            "status": "success" or "error",
            "result": {
                "question": str,
                "sql": str (generated SQL query),
                "data": list or dict (query results),
                "summary": str (human-readable summary),
                "query_number": int (how many queries processed),
                "data_source": "Staffing Database via Vanna (Learning Enabled)"
            }
        }
    """
    global last_agent_tool_used
    last_agent_tool_used = "un_staffing_specialist"
    tools_logger.debug(f"🔧 [Staffing Tool] Querying staffing table: '{question}'")

    try:
        import asyncio
        import os

        # Import the persistent manager
        try:
            from .vanna_agent_manager import get_vanna_manager
        except ImportError:
            # Fallback for direct imports
            import sys
            from pathlib import Path
            sys.path.insert(0, str(Path(__file__).parent))
            from vanna_agent_manager import get_vanna_manager

        # Get database path from environment
        database_path = os.getenv("STAFFING_DATABASE_PATH", "./unpolicy.db")
        table_name = os.getenv("STAFFING_TABLE_NAME", "staffing_table")

        if not os.path.exists(database_path):
            tools_logger.warning(f"⚠️ [Staffing Tool] Database not found: {database_path}")
            return {
                "status": "error",
                "result": {
                    "question": question,
                    "error": f"Staffing database not found at: {database_path}. Set STAFFING_DATABASE_PATH environment variable.",
                    "data_source": "Staffing Query Tool"
                }
            }

        # Get the persistent manager
        manager = get_vanna_manager()

        # Initialize agent if not already done
        # (This only happens once, then the agent persists!)
        try:
            if not manager.get_stats()["initialized"]:
                tools_logger.info("🚀 Initializing persistent Vanna agent (first time)...")
                manager.initialize_agent(
                    database_path=database_path,
                    table_name=table_name,
                    load_training_data=True  # Pre-populate with examples
                )
                tools_logger.info("✅ Agent initialized with shared memory and training data")
        except Exception as init_error:
            tools_logger.error(f"❌ Failed to initialize agent: {init_error}")
            return {
                "status": "error",
                "result": {
                    "question": question,
                    "error": f"Failed to initialize Vanna agent: {str(init_error)}",
                    "data_source": "Staffing Query Tool"
                }
            }

        # Execute query using the persistent agent
        # This agent LEARNS from this query and improves for future users!
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        result = loop.run_until_complete(
            manager.query(
                question=question,
                user_id="adk_user",  # Could be passed from ADK context
                metadata={"source": "adk_agent"}
            )
        )

        tools_logger.debug(f"✅ [Staffing Tool] Query completed via persistent agent")
        return result

    except Exception as e:
        tools_logger.error(f"❌ [Staffing Tool] Error: {e}")
        import traceback
        traceback.print_exc()
        return {
            "status": "error",
            "result": {
                "question": question,
                "error": f"Staffing query tool error: {str(e)}",
                "data_source": "Staffing Query Tool"
            }
        }
