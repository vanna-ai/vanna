#!/usr/bin/env python3
"""
UN Policy Agent - Knowledge-based Implementation
Pure knowledge-based approach without any tools to avoid function calling errors
"""


import os
import sys

# Force ADK to use Google AI Studio (Gemini API) instead of Vertex AI.
# This must be done BEFORE any ADK modules are imported.
os.environ['GOOGLE_GENAI_USE_VERTEXAI'] = 'FALSE'


from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm
from .utils import (
    load_main_agent_instruction,
    load_salary_agent_instruction,
    load_leave_agent_instruction,
    load_travel_agent_instruction,
    load_staffing_agent_instruction
)

# Model configuration functions
def get_azure_openai_model():
    """Configure Azure OpenAI model through LiteLLM with deterministic settings"""
    # Set up LiteLLM environment variables for Azure OpenAI
    azure_api_key = os.getenv('AZURE_OPENAI_API_KEY')
    azure_endpoint = os.getenv('AZURE_OPENAI_ENDPOINT')
    azure_api_version = os.getenv('AZURE_OPENAI_API_VERSION', '2024-02-15-preview')
    deployment_name = os.getenv('AZURE_OPENAI_DEPLOYMENT_NAME', 'gpt-4o')
    
    if azure_api_key:
        os.environ['AZURE_API_KEY'] = azure_api_key
    if azure_endpoint:
        os.environ['AZURE_API_BASE'] = azure_endpoint
    os.environ['AZURE_API_VERSION'] = azure_api_version
    
    # LiteLLM format for Azure OpenAI: azure/{deployment_name}
    azure_model_id = f"azure/{deployment_name}"
    
    # LiteLLM model with deterministic parameters passed directly to constructor
    return LiteLlm(
        model=azure_model_id,
        temperature=0.0,      # Deterministic responses
        max_tokens=800,       # Reasonable limit (reduced from 1500 to avoid rate limits)
        seed=42               # Reproducible results
    )

def get_openai_model():
    """Configure regular OpenAI model through LiteLLM with deterministic settings"""
    # Set up LiteLLM environment variables for OpenAI
    openai_api_key = os.getenv('OPENAI_API_KEY')
    openai_model = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
    
    if openai_api_key:
        os.environ['OPENAI_API_KEY'] = openai_api_key
    
    # LiteLLM model with deterministic parameters passed directly to constructor
    return LiteLlm(
        model=openai_model,
        temperature=0.0,      # Deterministic responses
        max_tokens=800,       # Reasonable limit (reduced from 1500 to avoid rate limits)
        seed=42               # Reproducible results
    )

# Get model provider preference from environment
MODEL_PROVIDER = os.getenv('MODEL_PROVIDER', 'gemini').lower()
MODEL_NAME = os.getenv('ADK_MODEL', 'gemini-2.5-flash-lite')

# Legacy support for USE_AZURE_OPENAI
use_azure_legacy = os.getenv('USE_AZURE_OPENAI', 'false').lower() == 'true'
if use_azure_legacy and MODEL_PROVIDER == 'gemini':
    MODEL_PROVIDER = 'azure_openai'

# Choose model based on configuration
if MODEL_PROVIDER == 'azure_openai':
    model_config = get_azure_openai_model()
    print(f"Using Azure OpenAI model: {os.getenv('AZURE_OPENAI_DEPLOYMENT_NAME', 'gpt-4o')} (deterministic)")
elif MODEL_PROVIDER == 'openai':
    model_config = get_openai_model()
    print(f"Using OpenAI model: {os.getenv('OPENAI_MODEL', 'gpt-4o-mini')} (deterministic)")
else:  # Default to Gemini with deterministic settings
    from google.adk.models.lite_llm import LiteLlm
    model_config = LiteLlm(
        model=MODEL_NAME,
        temperature=0.0,      # Deterministic responses
        max_tokens=800        # Reasonable limit (reduced from 1500 to avoid rate limits)
    )
    print(f"Using Gemini model: {MODEL_NAME} (deterministic with temperature=0.0)")

# Create specialized sub-agents WITH tools (since sub-agents can have tools)
from .tools import get_salary_info, get_leave_info, get_travel_info, get_pa_rate, get_msa_rate, dsa_rates_search, get_staff_benefits_by_category
from .tools import get_salary, get_post_adjustment, get_msa, get_dsa, query_staffing_table

# Salary Sub-agent WITH Azure tool AND PA/MSA rate tools
salary_agent = Agent(
    name="un_salary_specialist",
    model=model_config,
    description=(
        "UN Salary Specialist that provides precise salary information using the Azure policy database "
        "and exact PA/MSA rates from comprehensive 2025 databases. Specializes in UN salary scales, "
        "Post Adjustment rates, Mission Subsistence Allowance rates, compensation calculations, and "
        "salary-related policies for all UN staff categories (P, GS, FS, D, ASG, USG)."
    ),
    instruction=load_salary_agent_instruction(),
    tools=[get_salary, get_post_adjustment, get_msa],  # Add all salary-related tools
)

# Leave Sub-agent WITH Azure tool
leave_agent = Agent(
    name="un_leave_specialist",
    model=model_config,
    description=(
        "UN Leave Policy Specialist that provides precise leave information using the Azure policy database. "
        "Specializes in leave entitlements, accrual rates, annual leave, sick leave, parental leave, "
        "home leave, R&R leave, and all leave-related policies."
    ),
    instruction=load_leave_agent_instruction(),
    tools=[get_leave_info],  # Add Azure leave tool to sub-agent
)

# Travel Sub-agent WITH Azure tool
travel_agent = Agent(
    name="un_travel_specialist", 
    model=model_config,
    description=(
        "UN Travel Policy Specialist that provides precise travel information using the Azure policy database. "
        "Specializes in official travel policies, travel authorization, DSA rates, class of travel "
        "eligibility, and travel-related procedures."
    ),
    instruction=load_travel_agent_instruction(),
    tools=[get_travel_info, dsa_rates_search],  # Add Azure travel tool and DSA rates tool to sub-agent
)

# Benefits & Allowances Sub-agent (moved from main agent)
benefits_agent = Agent(
    name="un_benefits_specialist",
    model=model_config,
    description=(
        "UN Benefits and Allowances Specialist that provides comprehensive information about UN staff benefits "
        "including education grants, rental subsidies, dependency allowances, security evacuations, "
        "health insurance, pension contributions, and other entitlements not covered by salary/leave/travel agents. "
        "Specializes in staff category distinctions between international and local staff."
    ),
    instruction=load_main_agent_instruction(),  # Use the existing benefits knowledge
    tools=[get_staff_benefits_by_category],  # Add staff benefits category tool
)

# Staffing Data Sub-agent WITH Vanna-powered SQL query tool
staffing_agent = Agent(
    name="un_staffing_specialist",
    model=model_config,
    description=(
        "UN Staffing Data Specialist that provides detailed staffing information from the staffing database "
        "using Vanna AI-powered SQL queries. Answers questions about employee counts, department sizes, "
        "salary distributions, hiring trends, tenure analysis, and organizational structure data. "
        "Converts natural language questions into SQL queries and presents results in a clear, actionable format."
    ),
    instruction=load_staffing_agent_instruction(),
    tools=[query_staffing_table],  # Add Vanna staffing query tool
)

# Enhanced main agent instructions for coordination
def create_main_agent_instructions():
    """Create instructions for the main routing coordinator agent"""
    
    coordination_instructions = """
# UN Policy Agent - Main Routing Coordinator

You are the main UN Policy Agent coordinator responsible for routing user queries to the most appropriate specialist sub-agent.

## Available Specialist Sub-agents

1. **Salary Sub-agent** (un_salary_specialist): Handles all salary, compensation, Post Adjustment rates, Mission Subsistence Allowance (MSA), and Personal Allowance (PA) queries
2. **Leave Sub-agent** (un_leave_specialist): Handles all leave entitlements, accrual, leave policies, and time-off procedures
3. **Travel Sub-agent** (un_travel_specialist): Handles all travel policies, DSA rates, travel authorization, and official travel procedures
4. **Benefits Sub-agent** (un_benefits_specialist): Handles general benefits, allowances, education grants, rental subsidies, and other entitlements. Has access to staff category-specific benefits tool for international vs local staff distinctions
5. **Staffing Sub-agent** (un_staffing_specialist): Handles all staffing database queries, employee counts, department data, hiring trends, and organizational structure using Vanna AI-powered SQL queries

## Routing Strategy - ALWAYS Route to Specialists

**ALWAYS route queries to the appropriate sub-agent. Do NOT answer directly.**

### Routing Rules:
- **Salary/Compensation queries** → Salary specialist
  - Examples: "P-3 salary with PA in Geneva", "FS4 salary in UNIFIL", "Post Adjustment", "salary scale", "compensation", "MSA rates", "PA rates"
- **Leave queries** → Leave specialist
  - Examples: "annual leave", "AL", "sick leave", "SL", "parental leave", "home leave", "R&R", "days off", "leave entitlement", "leave days", "ML", "maternity leave", "paternity leave"
- **Travel queries** → Travel specialist
  - Examples: "DSA rates", "travel authorization", "business class", "official travel", "per diem"
- **Benefits/Allowances queries** → Benefits specialist
  - Examples: "education grant", "rental subsidy", "health insurance", "dependency allowance", "benefits overview", "UN benefits", "international staff benefits"
- **Staffing/Database queries** → Staffing specialist
  - Examples: "How many employees in Engineering?", "department headcount", "average salary by department", "recent hires", "hiring trends", "employee count", "staffing levels", "show me employees in HR", "who was hired in 2024"

## Response Format

When routing, simply forward the user's question to the appropriate specialist. The sub-agents have:
- Access to Azure policy databases for current information
- Specialized knowledge in their domains  
- Tools for precise data retrieval

## Key Principle

Your primary role is **routing coordination**, not direct answering. Always delegate to specialists for accurate, tool-enhanced responses.

## Important Notes on Query Recognition

- **Pay attention to abbreviations**: "AL" = Annual Leave, "SL" = Sick Leave, "ML" = Maternity Leave  
- **Context matters**: "temp staff" refers to temporary staff, not temperature
- **Leave-related terms**: "days", "entitlement", "time off" in context of staff = Leave specialist
- **When in doubt**: Choose the most specific specialist based on the primary topic
"""
    
    return coordination_instructions

# Test with minimal single agent first to isolate the issue
def create_comprehensive_instructions():
    """Combine all domain knowledge into a single comprehensive instruction set"""
    
    main_instructions = load_main_agent_instruction()
    salary_instructions = load_salary_agent_instruction()
    leave_instructions = load_leave_agent_instruction()
    travel_instructions = load_travel_agent_instruction()
    
    comprehensive_instructions = f"""
# UN Policy Agent - Comprehensive Knowledge Base

You are an expert UN Policy Agent with comprehensive knowledge across all UN staff policy domains.

## Domain Knowledge Summary

**SALARY EXPERTISE:** {salary_instructions[:500]}...

**LEAVE EXPERTISE:** {leave_instructions[:500]}...

**TRAVEL EXPERTISE:** {travel_instructions[:500]}...

**BENEFITS EXPERTISE:** {main_instructions[:500]}...

## Response Guidelines

Always provide:
1. Staff category distinctions (International vs. Local)
2. Eligibility criteria and requirements  
3. Policy frameworks and calculation methods
4. Verification disclaimers for current rates
5. Official source guidance

Use your comprehensive embedded knowledge to provide expert guidance on all UN policy matters.
"""
    
    return comprehensive_instructions

# Main UN Policy Agent WITHOUT tools but WITH sub-agents that have tools
un_policy_agent = Agent(
    name="un_policy_main",
    model=model_config,
    description=(
        "Main UN Policy Agent coordinator that routes user queries to specialized sub-agents. "
        "Functions as a pure routing coordinator to ensure users get precise, tool-enhanced responses "
        "from domain specialists with access to Azure policy databases and staffing data."
    ),
    instruction=create_main_agent_instructions(),
    # Root agent has NO tools - pure routing coordinator
    sub_agents=[salary_agent, leave_agent, travel_agent, benefits_agent, staffing_agent],  # All specialists with tools/knowledge
)

# Export for ADK - Pure routing coordinator with specialized sub-agents
root_agent = un_policy_agent
agent = un_policy_agent

# Architecture Summary:
# - Main Agent: Pure routing coordinator (NO tools, NO domain knowledge)
# - Salary Agent: Salary/compensation specialist (WITH salary/PA/MSA tools)
# - Leave Agent: Leave policy specialist (WITH leave tools)
# - Travel Agent: Travel policy specialist (WITH travel/DSA tools)
# - Benefits Agent: Benefits/allowances specialist (WITH benefits knowledge)
# - Staffing Agent: Staffing database specialist (WITH Vanna-powered SQL query tool)