#!/usr/bin/env python3
"""
Utility functions for ADK UN Policy Agent
"""

import os
from pathlib import Path

def load_instruction_from_file(filename: str) -> str:
    """
    Load agent instructions from a markdown file.
    
    Args:
        filename (str): The markdown file name (e.g., 'un_benefits_and_allowances.md')
        
    Returns:
        str: The content of the file as a string for use in Agent instructions
        
    Raises:
        FileNotFoundError: If the instruction file doesn't exist
        IOError: If there's an error reading the file
    """
    try:
        # Get the directory where this utils.py file is located
        current_dir = Path(__file__).parent
        
        # Construct the full path to the instruction file
        instruction_file_path = current_dir / filename
        
        # Check if file exists
        if not instruction_file_path.exists():
            raise FileNotFoundError(f"Instruction file not found: {instruction_file_path}")
        
        # Read the file content
        with open(instruction_file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # Remove any leading/trailing whitespace
        content = content.strip()
        
        if not content:
            raise ValueError(f"Instruction file is empty: {instruction_file_path}")
        
        print(f"✅ Loaded instructions from: {filename} ({len(content)} characters)")
        return content
        
    except FileNotFoundError:
        print(f"❌ Instruction file not found: {filename}")
        raise
    except IOError as e:
        print(f"❌ Error reading instruction file {filename}: {e}")
        raise
    except Exception as e:
        print(f"❌ Unexpected error loading instructions from {filename}: {e}")
        raise

def load_main_agent_instruction() -> str:
    """
    Load the main UN Policy Agent instructions from the comprehensive benefits and allowances file.
    
    Returns:
        str: Complete agent instructions including domain knowledge and behavior guidelines
    """
    try:
        # Load the comprehensive benefits and allowances domain knowledge and behavioral guidelines
        return load_instruction_from_file('un_benefits_and_allowances.md')
        
    except Exception as e:
        print(f"❌ Error loading main agent instructions: {e}")
        # Fallback to basic instructions if file loading fails
        return """You are a helpful UN policy assistant that provides information about UN staff benefits, allowances, leave policies, salary information, and travel policies. Use the available tools to answer questions accurately and provide comprehensive guidance on UN HR policies."""

def load_salary_agent_instruction() -> str:
    """
    Load the salary agent instructions for the salary tool.
    
    Returns:
        str: Salary domain knowledge and behavioral guidelines
    """
    try:
        # Load from the local un_policy_agent directory
        return load_instruction_from_file('salary_agent_instructions.md')
        
    except Exception as e:
        print(f"❌ Error loading salary agent instructions: {e}")
        return """You are a specialized UN salary tool. Provide accurate salary information including scales, Post Adjustment rates, and compensation details for all UN staff categories."""

def load_leave_agent_instruction() -> str:
    """
    Load the leave agent instructions for the leave tool.
    
    Returns:
        str: Leave domain knowledge and behavioral guidelines
    """
    try:
        return load_instruction_from_file('leave_agent_instructions.md')
        
    except Exception as e:
        print(f"❌ Error loading leave agent instructions: {e}")
        return """You are a specialized UN leave policy tool. Provide accurate information about leave entitlements, accrual rates, and leave policies for all UN staff categories."""

def load_travel_agent_instruction() -> str:
    """
    Load the travel agent instructions for the travel tool.
    
    Returns:
        str: Travel domain knowledge and behavioral guidelines
    """
    try:
        return load_instruction_from_file('travel_agent_instructions.md')
        
    except Exception as e:
        print(f"❌ Error loading travel agent instructions: {e}")
        return """You are a specialized UN travel policy tool. Provide accurate information about official travel policies, DSA rates, travel authorization, and travel-related entitlements."""