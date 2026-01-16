"""
Quickstart script to run Tecknoworks AI Agent locally
This script sets up a local server with OpenAI and the Urban Eats restaurant database
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from vanna import Agent, AgentConfig
from vanna.servers.fastapi import VannaFastAPIServer
from vanna.core.registry import ToolRegistry
from vanna.core.user import UserResolver, User, RequestContext
from vanna.integrations.foundry import AzureAIFoundryLlmService as FoundryLlmService
from vanna.tools import RunSqlTool, VisualizeDataTool
from vanna.integrations.sqlite import SqliteRunner
from vanna.tools.agent_memory import SaveQuestionToolArgsTool, SearchSavedCorrectToolUsesTool
from vanna.integrations.local.agent_memory import DemoAgentMemory
from vanna.core.system_prompt import DefaultSystemPromptBuilder

SCHEMA_DDL = """
-- Restaurant locations
CREATE TABLE restaurants (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    city TEXT NOT NULL,
    state TEXT,
    country TEXT DEFAULT 'USA',
    address TEXT,
    phone TEXT,
    manager_id INTEGER,
    opened_date DATE,
    seating_capacity INTEGER
);

-- Menu categories
CREATE TABLE categories (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT
);

-- Menu items
CREATE TABLE menu_items (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    category_id INTEGER,
    price DECIMAL(10,2) NOT NULL,
    cost DECIMAL(10,2),
    description TEXT,
    is_vegetarian BOOLEAN DEFAULT FALSE,
    is_available BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (category_id) REFERENCES categories(id)
);

-- Customers (loyalty program)
CREATE TABLE customers (
    id INTEGER PRIMARY KEY,
    first_name TEXT,
    last_name TEXT,
    email TEXT UNIQUE,
    phone TEXT,
    loyalty_points INTEGER DEFAULT 0,
    joined_date DATE,
    preferred_restaurant_id INTEGER,
    FOREIGN KEY (preferred_restaurant_id) REFERENCES restaurants(id)
);

-- Employees
CREATE TABLE employees (
    id INTEGER PRIMARY KEY,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    email TEXT,
    phone TEXT,
    role TEXT,
    restaurant_id INTEGER,
    hire_date DATE,
    hourly_rate DECIMAL(10,2),
    FOREIGN KEY (restaurant_id) REFERENCES restaurants(id)
);

-- Orders (sales transactions)
CREATE TABLE orders (
    id INTEGER PRIMARY KEY,
    restaurant_id INTEGER NOT NULL,
    customer_id INTEGER,
    employee_id INTEGER,
    order_date DATETIME NOT NULL,
    subtotal DECIMAL(10,2),
    tax DECIMAL(10,2),
    tip DECIMAL(10,2),
    total DECIMAL(10,2),
    payment_method TEXT,
    order_type TEXT,
    FOREIGN KEY (restaurant_id) REFERENCES restaurants(id),
    FOREIGN KEY (customer_id) REFERENCES customers(id),
    FOREIGN KEY (employee_id) REFERENCES employees(id)
);

-- Order line items
CREATE TABLE order_items (
    id INTEGER PRIMARY KEY,
    order_id INTEGER NOT NULL,
    menu_item_id INTEGER NOT NULL,
    quantity INTEGER DEFAULT 1,
    unit_price DECIMAL(10,2),
    notes TEXT,
    FOREIGN KEY (order_id) REFERENCES orders(id),
    FOREIGN KEY (menu_item_id) REFERENCES menu_items(id)
);

-- Suppliers
CREATE TABLE suppliers (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    contact_name TEXT,
    email TEXT,
    phone TEXT,
    address TEXT,
    category TEXT
);

-- Inventory items
CREATE TABLE inventory (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    supplier_id INTEGER,
    unit TEXT,
    unit_cost DECIMAL(10,2),
    reorder_level INTEGER,
    FOREIGN KEY (supplier_id) REFERENCES suppliers(id)
);

-- Inventory by restaurant
CREATE TABLE restaurant_inventory (
    id INTEGER PRIMARY KEY,
    restaurant_id INTEGER,
    inventory_id INTEGER,
    quantity DECIMAL(10,2),
    last_restocked DATE,
    FOREIGN KEY (restaurant_id) REFERENCES restaurants(id),
    FOREIGN KEY (inventory_id) REFERENCES inventory(id)
);
"""


class SimpleUserResolver(UserResolver):
    """Simple user resolver for demo purposes"""
    async def resolve_user(self, request_context: RequestContext) -> User:
        # For demo purposes, check for a cookie or default to admin
        user_email = request_context.get_cookie('vanna_email')

        if not user_email:
            # Default to admin user if no cookie is set
            user_email = "admin@example.com"

        print(f"User authenticated: {user_email}")

        if user_email == "admin@example.com":
            return User(id="admin1", email=user_email, group_memberships=['admin'])

        return User(id="user1", email=user_email, group_memberships=['user'])


def main():
    # Get Azure Foundry configuration from environment
    foundry_endpoint = os.getenv("AZURE_FOUNDRY_ENDPOINT") or os.getenv("AZURE_AI_FOUNDRY_ENDPOINT")
    foundry_model = os.getenv("AZURE_FOUNDRY_MODEL") or os.getenv("AZURE_AI_FOUNDRY_MODEL") or "gpt-4o"
    foundry_api_key = os.getenv("AZURE_FOUNDRY_API_KEY") or os.getenv("AZURE_AI_FOUNDRY_API_KEY")
    
    if not foundry_endpoint:
        raise ValueError("AZURE_FOUNDRY_ENDPOINT not found in .env file")

    if not foundry_api_key:
        print("Warning: AZURE_FOUNDRY_API_KEY not found. Assuming Entra ID authentication or environment variable set for SDK.")

    print("Setting up Tecknoworks AI Agent with Urban Eats restaurant database...")

    # Set up tools with access control
    tools = ToolRegistry()
    tools.register_local_tool(
        RunSqlTool(sql_runner=SqliteRunner(database_path="./demo-data/urban_eats.sqlite")),
        access_groups=['admin', 'user']
    )
    tools.register_local_tool(
        VisualizeDataTool(),
        access_groups=['admin', 'user']
    )

    # Set up agent memory
    agent_memory = DemoAgentMemory(max_items=1000)
    tools.register_local_tool(
        SaveQuestionToolArgsTool(),
        access_groups=['admin']
    )
    tools.register_local_tool(
        SearchSavedCorrectToolUsesTool(),
        access_groups=['admin', 'user']
    )

    # Set up LLM with Azure Foundry
    llm = FoundryLlmService(
        model=foundry_model,
        endpoint=foundry_endpoint,
        api_key=foundry_api_key
    )

    # Create agent
    agent = Agent(
        llm_service=llm,
        tool_registry=tools,
        user_resolver=SimpleUserResolver(),
        config=AgentConfig(),
        agent_memory=agent_memory,
        system_prompt_builder=DefaultSystemPromptBuilder(
            base_prompt=f"You are Vanna, an AI data analyst assistant. Here is the database schema:\n\n{SCHEMA_DDL}\n\nToday's date is 2026-01-16."
        )
    )

    # Create and run server
    print("\n" + "="*70)
    print("Starting Tecknoworks AI Agent Server...")
    print("="*70)
    print("\nServer will be available at:")
    print("  - Web UI: http://localhost:8000")
    print("  - API endpoint: http://localhost:8000/api/vanna/v2/chat_sse")
    print("\nDatabase: Urban Eats Restaurant Chain")
    print("  - 25 restaurant locations")
    print("  - 293K+ orders (6 months of data)")
    print("  - $16.4M+ in revenue data")
    print("\nPress Ctrl+C to stop the server")
    print("="*70 + "\n")

    server = VannaFastAPIServer(agent)
    server.run()


if __name__ == "__main__":
    main()
