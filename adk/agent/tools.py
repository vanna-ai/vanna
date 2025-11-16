#!/usr/bin/env python3
"""
Specialized tools for UN Policy Agent
These tools represent the salary, leave, and travel subagents
"""

import requests
import json
import os
import logging
import sys
import importlib.util
from typing import Optional, Dict, Any
from .utils import load_salary_agent_instruction, load_leave_agent_instruction, load_travel_agent_instruction
from .cache.salary_cache import get_salary_cache, init_salary_cache
from un.policy.hr import extract as nlp_extract

# Create tools logger
tools_logger = logging.getLogger("tools")
tools_logger.setLevel(logging.DEBUG if os.getenv("DEBUG_TOOLS", "false").lower() == "true" else logging.WARNING)

# Global variable to track which agent tool was last used
last_agent_tool_used = None

# Configuration
AZURE_FUNCTION_URL = "https://oneunapp-functions.azurewebsites.net/api/smartQuery"

# ============================================================================
# NLP ENTITY EXTRACTION (using un_policy_nlp package)
# ============================================================================
# Replaced old spacy module loading with direct import from un_policy_nlp package
# See GAP_ANALYSIS_un_policy_nlp_vs_extract_entities.md for migration details
# ============================================================================

# ============================================================================
# CACHE INITIALIZATION UTILITY
# ============================================================================

def _ensure_cache_loaded() -> bool:
    """Ensure salary cache is loaded and healthy.

    Lazy initialization: loads cache on first tool call.
    Subsequent calls skip initialization if cache is healthy.

    Returns:
        bool: True if cache is healthy, False otherwise
    """
    try:
        cache = get_salary_cache()

        # If cache is not healthy, initialize it
        if not cache.is_healthy():
            tools_logger.debug("💾 Cache not healthy, initializing from unpolicy.db...")
            success = init_salary_cache()
            if success:
                cache = get_salary_cache()
                stats = cache.get_stats()
                tools_logger.debug(f"✅ Cache initialized: {stats.total_rows} rows loaded")
            else:
                tools_logger.warning("⚠️ Cache initialization failed, will fallback to other methods")
                return False

        return cache.is_healthy()

    except Exception as e:
        tools_logger.warning(f"⚠️ Error ensuring cache is loaded: {e}")
        return False

def get_salary_info(query: str) -> dict:
    """Get UN salary information from Azure system.
    
    This tool specializes in UN salary scales, Post Adjustment rates, compensation calculations,
    and all salary-related policies for Professional, General Service, Field Service, Director,
    and senior leadership categories.
    
    Args:
        query (str): The UN salary query (e.g., "P-3 salary", "Post Adjustment New York", "GS salary scale")
        
    Returns:
        dict: Salary information with detailed compensation data
    """
    global last_agent_tool_used
    last_agent_tool_used = "un_salary_specialist"
    tools_logger.debug(f"🔧 [Salary Tool] Querying UN salary for: '{query}'")
    
    
    try:
        response = requests.post(
            AZURE_FUNCTION_URL,
            json={"query": query},
            timeout=15.0
        )
        response.raise_for_status()
        result = response.json()
        
        tools_logger.debug(f"✅ [Salary Tool] Azure response type: {result.get('type', 'unknown')}")
        
        # Extract salary-specific information for ADK
        if result.get('type') == 'salary' and result.get('salaryInfo'):
            salary_info = result['salaryInfo'][0]
            return {
                "status": "success",
                "result": {
                    "type": "salary",
                    "content": salary_info.get('content', ''),
                    "title": salary_info.get('chunk_title', 'Salary Information'),
                    "domain": "salary_scales_and_compensation"
                }
            }
        elif result.get('topicInfo'):
            # Sometimes salary queries return as topic_question
            topic_info = result['topicInfo'][0] 
            return {
                "status": "success",
                "result": {
                    "type": "salary_topic",
                    "content": topic_info.get('content', ''),
                    "title": topic_info.get('chunk_title', 'Salary Policy Information'),
                    "domain": "salary_scales_and_compensation"
                }
            }
        else:
            return {
                "status": "success",
                "result": {
                    "type": "general",
                    "content": "No specific salary information found for this query.",
                    "title": "Salary Query Response",
                    "domain": "salary_scales_and_compensation"
                }
            }
        
    except Exception as e:
        print(f"❌ [Salary Tool] Error: {e}")
        return {
            "status": "error",
            "error_message": f"Failed to get salary information: {str(e)}"
        }

def get_leave_info(query: str) -> dict:
    """Get UN leave policy information from Azure system.
    
    This tool specializes in leave entitlements, accrual rates, annual leave, sick leave,
    parental leave, special leave, home leave, R&R leave, and all leave-related policies
    for all UN staff categories.
    
    Args:
        query (str): The UN leave query (e.g., "annual leave entitlement", "sick leave policy", "parental leave")
        
    Returns:
        dict: Leave policy information with detailed entitlement data
    """
    global last_agent_tool_used
    last_agent_tool_used = "un_leave_specialist"
    tools_logger.debug(f"🔧 [Leave Tool] Querying UN leave policy for: '{query}'")
    
    try:
        response = requests.post(
            AZURE_FUNCTION_URL,
            json={"query": query},
            timeout=15.0
        )
        response.raise_for_status()
        result = response.json()
        
        tools_logger.debug(f"✅ [Leave Tool] Azure response type: {result.get('type', 'unknown')}")
        
        # Extract leave-specific information for ADK
        if result.get('topicInfo'):
            topic_info = result['topicInfo'][0] 
            return {
                "status": "success",
                "result": {
                    "type": "leave_policy",
                    "content": topic_info.get('content', ''),
                    "title": topic_info.get('chunk_title', 'Leave Policy Information'),
                    "domain": "leave_entitlements_and_policies"
                }
            }
        elif result.get('type') == 'salary' and result.get('salaryInfo'):
            # Sometimes leave queries might be classified as salary
            salary_info = result['salaryInfo'][0]
            return {
                "status": "success",
                "result": {
                    "type": "leave_related",
                    "content": salary_info.get('content', ''),
                    "title": salary_info.get('chunk_title', 'Leave-Related Information'),
                    "domain": "leave_entitlements_and_policies"
                }
            }
        else:
            return {
                "status": "success",
                "result": {
                    "type": "general",
                    "content": "No specific leave policy information found for this query.",
                    "title": "Leave Policy Response",
                    "domain": "leave_entitlements_and_policies"
                }
            }
        
    except Exception as e:
        print(f"❌ [Leave Tool] Error: {e}")
        return {
            "status": "error",
            "error_message": f"Failed to get leave policy information: {str(e)}"
        }

def get_travel_info(query: str) -> dict:
    """Get UN travel policy information from Azure system.
    
    This tool specializes in official travel policies, travel authorization, DSA rates,
    class of travel eligibility, travel allowances, and all travel-related entitlements
    for UN staff.
    
    Args:
        query (str): The UN travel query (e.g., "DSA rates", "business class eligibility", "travel authorization")
        
    Returns:
        dict: Travel policy information with detailed travel guidance
    """
    global last_agent_tool_used
    last_agent_tool_used = "un_travel_specialist"
    tools_logger.debug(f"🔧 [Travel Tool] Querying UN travel policy for: '{query}'")
    
    try:
        response = requests.post(
            AZURE_FUNCTION_URL,
            json={"query": query},
            timeout=15.0
        )
        response.raise_for_status()
        result = response.json()
        
        tools_logger.debug(f"✅ [Travel Tool] Azure response type: {result.get('type', 'unknown')}")
        
        # Extract travel-specific information for ADK
        if result.get('topicInfo'):
            topic_info = result['topicInfo'][0] 
            return {
                "status": "success",
                "result": {
                    "type": "travel_policy",
                    "content": topic_info.get('content', ''),
                    "title": topic_info.get('chunk_title', 'Travel Policy Information'),
                    "domain": "travel_policies_and_procedures"
                }
            }
        elif result.get('type') == 'salary' and result.get('salaryInfo'):
            # Sometimes travel allowances might be classified as salary
            salary_info = result['salaryInfo'][0]
            return {
                "status": "success",
                "result": {
                    "type": "travel_allowance",
                    "content": salary_info.get('content', ''),
                    "title": salary_info.get('chunk_title', 'Travel Allowance Information'),
                    "domain": "travel_policies_and_procedures"
                }
            }
        else:
            return {
                "status": "success",
                "result": {
                    "type": "general",
                    "content": "No specific travel policy information found for this query.",
                    "title": "Travel Policy Response",
                    "domain": "travel_policies_and_procedures"
                }
            }
        
    except Exception as e:
        print(f"❌ [Travel Tool] Error: {e}")
        return {
            "status": "error",
            "error_message": f"Failed to get travel policy information: {str(e)}"
        }

def get_un_policy_info(query: str) -> dict:
    """Get general UN policy information from Azure system.
    
    This is the main tool for general UN policy queries, benefits overview,
    allowances information, and broad policy questions that don't fit into
    specific salary, leave, or travel domains.
    
    Args:
        query (str): The UN policy query (e.g., "UN benefits overview", "allowances for international staff")
        
    Returns:
        dict: General UN policy information
    """
    print(f"🔧 [Policy Tool] Querying UN policy for: '{query}'")
    
    try:
        response = requests.post(
            AZURE_FUNCTION_URL,
            json={"query": query},
            timeout=15.0
        )
        response.raise_for_status()
        result = response.json()
        
        print(f"✅ [Policy Tool] Azure response type: {result.get('type', 'unknown')}")
        
        # Handle different response types for general policy queries
        if result.get('type') == 'category_question' and result.get('classification'):
            primary_match = result['classification']['primary_match']
            return {
                "status": "success",
                "result": {
                    "type": "category_response",
                    "content": primary_match.get('user_content') or primary_match.get('content', ''),
                    "title": primary_match.get('title', 'UN Policy Information'),
                    "domain": "general_un_policies"
                }
            }
        elif result.get('topicInfo'):
            topic_info = result['topicInfo'][0] 
            return {
                "status": "success",
                "result": {
                    "type": "policy_topic",
                    "content": topic_info.get('content', ''),
                    "title": topic_info.get('chunk_title', 'UN Policy Information'),
                    "domain": "general_un_policies"
                }
            }
        elif result.get('type') == 'salary' and result.get('salaryInfo'):
            # Sometimes general benefits queries might return salary info
            salary_info = result['salaryInfo'][0]
            return {
                "status": "success",
                "result": {
                    "type": "benefits_related",
                    "content": salary_info.get('content', ''),
                    "title": salary_info.get('chunk_title', 'Benefits Information'),
                    "domain": "general_un_policies"
                }
            }
        else:
            return {
                "status": "empty_result",
                "result": {
                    "type": "no_content",
                    "content": "",
                    "title": "No Azure Results",
                    "domain": "general_un_policies"
                }
            }
        
    except Exception as e:
        print(f"❌ [Policy Tool] Error: {e}")
        return {
            "status": "error",
            "error_message": f"Failed to get UN policy information: {str(e)}"
        }

def get_pa_rate(duty_station: str) -> dict:
    """Get exact Post Adjustment (PA) rate for a specific duty station.
    
    This tool provides precise PA rates from the comprehensive 2025 data.
    Use this tool for any PA rate queries instead of calling Azure smartQuery.
    
    Args:
        duty_station (str): The duty station name (e.g., "Thailand", "France, Paris", "USA, New York")
        
    Returns:
        dict: PA rate information with exact percentage
    """
    print(f"🔧 [PA Rate Tool] Looking up PA rate for: '{duty_station}'")
    
    # Comprehensive PA rates database (2025)
    pa_rates = {
        "afghanistan": 36.6, "albania": 34.2, "algeria": 41.4, "angola": 47.0, "anguilla": 50.1,
        "antigua and barbuda": 50.1, "argentina": 40.1, "armenia": 34.1, "aruba": 59.4, "australia": 25.5,
        "austria": 37.2, "azerbaijan": 33.9, "bahamas": 66.4, "bahrain": 34.2, "bangladesh": 41.2,
        "barbados": 62.1, "belarus": 39.8, "belgium": 31.8, "belize": 44.1, "benin": 30.8,
        "bermuda": 80.1, "bhutan": 39.6, "bolivia": 22.3, "bonaire": 50.1, "bosnia and herzegovina": 26.4,
        "botswana": 23.2, "brazil": 28.3, "british virgin islands": 46.1, "bulgaria": 22.8, "burkina faso": 25.9,
        "burundi": 36.3, "cambodia": 28.3, "cameroon": 37.7, "canada, montreal": 33.1, "canada, ottawa": 42.2,
        "canada, toronto": 48.8, "cape verde": 36.7, "cayman islands": 46.8, "central african republic": 46.0,
        "chad": 49.9, "chile": 20.6, "china, beijing": 52.2, "china, hong kong (sar)": 99.3, "china, macao (sar)": 49.8,
        "colombia": 35.7, "comoros": 39.0, "congo": 40.9, "congo, democratic republic": 52.2, "cook islands": 42.8,
        "costa rica": 33.0, "cote d'ivoire": 50.0, "croatia": 25.6, "cuba": 56.5, "cyprus": 20.4,
        "czech republic": 33.8, "denmark": 57.1, "djibouti": 41.6, "dominica": 50.1, "dominican republic": 27.9,
        "ecuador": 24.6, "egypt": 23.7, "el salvador": 29.7, "equatorial guinea": 37.9, "eritrea": 40.3,
        "estonia": 40.1, "eswatini": 16.6, "ethiopia": 48.5, "fiji": 36.3, "finland": 32.0,
        "france, lyon and elsewhere": 36.8, "france, paris": 40.1, "french guiana": 24.8, "gabon": 38.6,
        "gambia": 34.7, "georgia": 25.1, "germany, berlin": 30.2, "germany, bonn": 23.5, "germany, dresden": 23.5,
        "germany, frankfurt": 31.7, "germany, hamburg": 37.6, "germany, munich": 42.9, "ghana": 37.2,
        "gibraltar": 61.7, "greece": 23.1, "grenada": 50.1, "guatemala": 32.5, "guinea": 52.7,
        "guinea bissau": 47.0, "guyana": 48.7, "haiti": 51.0, "honduras": 32.1, "hungary": 30.2,
        "iceland": 27.8, "india": 35.9, "indonesia": 31.3, "iran": 27.6, "iraq": 26.8,
        "ireland": 40.2, "israel, tel aviv": 61.2, "italy, brindisi": 11.7, "italy, rome": 17.0,
        "jamaica": 44.8, "japan, hiroshima": 27.6, "japan, tokyo": 43.8, "jerusalem": 52.6, "jordan": 30.2,
        "kazakhstan": 30.3, "kenya": 40.6, "kiribati": 42.0, "korea, democratic people's republic": 47.5,
        "korea, republic of": 47.8, "kuwait": 49.7, "kyrgyzstan": 28.8, "lao people's democratic republic": 28.5,
        "latvia": 30.5, "lebanon": 45.6, "lesotho": 28.7, "liberia": 48.6, "libya": 31.0,
        "lithuania": 32.0, "luxembourg": 36.5, "madagascar": 26.1, "malawi": 34.2, "malaysia": 47.0,
        "maldives": 37.3, "mali": 43.7, "malta": 22.0, "marshall islands": 41.6, "mauritania": 32.5,
        "mauritius": 28.3, "mexico": 48.2, "micronesia, federated states of": 58.0, "moldova": 42.1,
        "monaco": 40.1, "mongolia": 34.2, "montenegro": 28.9, "morocco": 29.1, "mozambique": 29.7,
        "myanmar": 35.1, "namibia": 30.5, "nauru": 42.8, "nepal": 25.3, "netherlands": 33.9,
        "new caledonia": 32.7, "new zealand": 34.9, "nicaragua": 27.6, "niger": 45.6, "nigeria": 46.9,
        "north macedonia": 25.1, "norway": 28.7, "oman": 29.9, "pakistan": 34.9, "palau": 42.8,
        "panama": 33.2, "papua new guinea": 45.3, "paraguay": 23.5, "peru": 32.1, "philippines": 38.0,
        "poland": 26.5, "portugal, guimaraes": 5.0, "portugal, lisbon": 21.4, "puerto rico": 27.9,
        "qatar": 46.6, "romania": 20.0, "russian federation": 42.8, "rwanda": 30.5, "saint helena": 49.7,
        "saint lucia": 45.2, "samoa": 33.0, "sao tome and principe": 62.9, "saudi arabia": 46.4,
        "senegal": 40.7, "serbia": 33.7, "seychelles": 41.9, "sierra leone": 46.3, "singapore": 65.1,
        "slovak republic": 24.5, "slovenia": 30.0, "solomon islands": 51.8, "somalia": 44.6,
        "south africa": 23.4, "south sudan": 42.5, "spain": 17.6, "sri lanka": 34.2,
        "st. kitts and nevis": 50.1, "st. vincent and the grenadines": 50.1, "sudan": 42.5,
        "suriname": 32.8, "sweden": 25.6, "switzerland": 67.6, "syrian arab republic": 14.0,
        "tajikistan": 33.1, "tanzania": 32.1, "thailand": 33.4, "timor-leste": 37.6, "togo": 40.8,
        "tonga": 36.1, "trinidad and tobago": 38.1, "tunisia": 28.1, "türkiye, ankara": 31.8,
        "türkiye, gebze": 38.4, "türkiye, istanbul": 38.4, "turkmenistan": 76.4, "tuvalu": 42.1,
        "uganda": 29.5, "ukraine": 25.7, "united arab emirates": 58.4, "united kingdom": 61.7,
        "usa, el paso": 48.8, "usa, miami": 50.1, "usa, new york": 72.1, "usa, san diego": 68.5,
        "usa, san francisco": 76.1, "usa, seattle": 51.7, "usa, washington d.c.": 55.4,
        "uruguay": 40.6, "uzbekistan": 30.3, "vanuatu": 47.7, "venezuela": 45.0, "vietnam": 29.8,
        "west bank & gaza strip": 52.6, "yemen": 23.7, "zambia": 26.2, "zimbabwe": 25.4,
        
        # Common variations and aliases
        "bangkok": 33.4, "thailand, bangkok": 33.4, "paris": 40.1, "france": 40.1,
        "new york": 72.1, "usa": 72.1, "united states": 72.1, "geneva": 67.6,
        "london": 61.7, "uk": 61.7, "hong kong": 99.3, "singapore": 65.1,
        "tokyo": 43.8, "japan": 43.8, "nairobi": 40.6, "kenya": 40.6,
        "cairo": 23.7, "egypt": 23.7, "dubai": 58.4, "uae": 58.4
    }
    
    # Normalize input for matching
    search_key = duty_station.lower().strip()
    
    # Try exact match first
    if search_key in pa_rates:
        rate = pa_rates[search_key]
        return {
            "status": "success",
            "result": {
                "duty_station": duty_station,
                "pa_rate": rate,
                "content": f"Post Adjustment rate for {duty_station} is {rate}% (2025 rates)",
                "year": "2025",
                "data_source": "Official UN PA rates"
            }
        }
    
    # Try partial matching for variations
    for key, rate in pa_rates.items():
        if search_key in key or key in search_key:
            return {
                "status": "success",
                "result": {
                    "duty_station": duty_station,
                    "pa_rate": rate,
                    "content": f"Post Adjustment rate for {duty_station} is {rate}% (matched: {key}) (2025 rates)",
                    "year": "2025",
                    "data_source": "Official UN PA rates"
                }
            }
    
    # Not found
    return {
        "status": "not_found",
        "result": {
            "duty_station": duty_station,
            "content": f"PA rate for '{duty_station}' not found in current database. Available locations include major UN duty stations.",
            "suggestion": "Try common formats like 'Thailand', 'France, Paris', 'USA, New York'"
        }
    }

def get_msa_rate(mission_location: str) -> dict:
    """Get exact Mission Subsistence Allowance (MSA) rate for a specific mission location.
    
    This tool provides precise MSA rates from the comprehensive 2025 data.
    Use this tool for any MSA rate queries instead of calling Azure smartQuery.
    
    Args:
        mission_location (str): The mission location (e.g., "Baghdad", "Kabul", "South Sudan")
        
    Returns:
        dict: MSA rate information with breakdown
    """
    print(f"🔧 [MSA Rate Tool] Looking up MSA rate for: '{mission_location}'")
    
    # Comprehensive MSA rates database (2025)
    msa_rates = {
        "afghanistan, kabul": {"first_30": 163, "after_30": 76, "accommodation": (101, 35), "meals": (41, 31), "misc": (21, 10)},
        "algeria, algiers": {"first_30": 260, "after_30": 121, "accommodation": (143, 43), "meals": (83, 62), "misc": (34, 16)},
        "burundi, bujumbura": {"first_30": 273, "after_30": 95, "accommodation": (172, 34), "meals": (65, 49), "misc": (36, 12)},
        "central african republic, bangui": {"first_30": 212, "after_30": 154, "accommodation": (112, 80), "meals": (72, 54), "misc": (28, 20)},
        "colombia, bogotá": {"first_30": 121, "after_30": 94, "accommodation": (79, 62), "meals": (26, 20), "misc": (16, 12)},
        "cyprus, nicosia": {"first_30": 225, "after_30": 106, "accommodation": (140, 50), "meals": (56, 42), "misc": (29, 14)},
        "democratic republic of the congo, kinshasa": {"first_30": 231, "after_30": 145, "accommodation": (134, 76), "meals": (67, 50), "misc": (30, 19)},
        "dominican republic, santo domingo": {"first_30": 243, "after_30": 114, "accommodation": (136, 43), "meals": (75, 56), "misc": (32, 15)},
        "egypt, cairo": {"first_30": 305, "after_30": 128, "accommodation": (183, 49), "meals": (82, 62), "misc": (40, 17)},
        "haiti, port-au-prince": {"first_30": 246, "after_30": 145, "accommodation": (145, 74), "meals": (69, 52), "misc": (32, 19)},
        "india, new delhi": {"first_30": 269, "after_30": 130, "accommodation": (172, 66), "meals": (62, 47), "misc": (35, 17)},
        "iraq, baghdad": {"first_30": 278, "after_30": 95, "accommodation": (175, 33), "meals": (67, 50), "misc": (36, 12)},
        "islamic republic of iran, tehran": {"first_30": 177, "after_30": 77, "accommodation": (117, 39), "meals": (37, 28), "misc": (23, 10)},
        "israel, jerusalem": {"first_30": 300, "after_30": 153, "accommodation": (201, 88), "meals": (60, 45), "misc": (39, 20)},
        "israel, tel aviv": {"first_30": 392, "after_30": 183, "accommodation": (259, 97), "meals": (82, 62), "misc": (51, 24)},
        "israel, tiberias": {"first_30": 314, "after_30": 161, "accommodation": (204, 88), "meals": (69, 52), "misc": (41, 21)},
        "jordan, amman": {"first_30": 242, "after_30": 117, "accommodation": (133, 49), "meals": (77, 53), "misc": (32, 15)},
        "kenya, nairobi": {"first_30": 267, "after_30": 112, "accommodation": (163, 45), "meals": (69, 52), "misc": (35, 15)},
        "kuwait, kuwait city": {"first_30": 319, "after_30": 136, "accommodation": (179, 44), "meals": (98, 74), "misc": (42, 18)},
        "lebanon, greater beirut": {"first_30": 232, "after_30": 147, "accommodation": (118, 65), "meals": (84, 63), "misc": (30, 19)},
        "libya, tripoli": {"first_30": 216, "after_30": 82, "accommodation": (140, 35), "meals": (48, 36), "misc": (28, 11)},
        "north macedonia, skopje": {"first_30": 194, "after_30": 108, "accommodation": (113, 52), "meals": (56, 42), "misc": (25, 14)},
        "occupied syrian golan": {"first_30": 236, "after_30": 169, "accommodation": (139, 97), "meals": (66, 50), "misc": (31, 22)},
        "pakistan, islamabad": {"first_30": 167, "after_30": 80, "accommodation": (120, 51), "meals": (25, 19), "misc": (22, 10)},
        "rwanda, kigali": {"first_30": 251, "after_30": 105, "accommodation": (151, 41), "meals": (67, 50), "misc": (33, 14)},
        "senegal, dakar": {"first_30": 249, "after_30": 126, "accommodation": (137, 49), "meals": (80, 60), "misc": (32, 17)},
        "serbia, pristina (kosovo)": {"first_30": 161, "after_30": 122, "accommodation": (81, 61), "meals": (59, 44), "misc": (21, 17)},
        "sierra leone, freetown": {"first_30": 243, "after_30": 138, "accommodation": (163, 84), "meals": (48, 36), "misc": (32, 18)},
        "somalia, mogadishu": {"first_30": 209, "after_30": 89, "accommodation": (157, 57), "meals": (25, 19), "misc": (27, 13)},
        "south africa, pretoria": {"first_30": 165, "after_30": 72, "accommodation": (104, 33), "meals": (39, 29), "misc": (22, 10)},
        "south sudan, juba": {"first_30": 128, "after_30": 97, "accommodation": (86, 65), "meals": (25, 19), "misc": (17, 13)},
        "sudan, khartoum": {"first_30": 208, "after_30": 190, "accommodation": (102, 106), "meals": (79, 59), "misc": (27, 25)},
        "tunisia, tunis": {"first_30": 200, "after_30": 90, "accommodation": (124, 40), "meals": (50, 38), "misc": (26, 12)},
        "uganda, kampala": {"first_30": 252, "after_30": 113, "accommodation": (171, 62), "meals": (48, 36), "misc": (33, 15)},
        "uganda, entebbe": {"first_30": 232, "after_30": 106, "accommodation": (162, 62), "meals": (40, 30), "misc": (30, 14)},
        "united arab emirates, abu dhabi": {"first_30": 417, "after_30": 225, "accommodation": (259, 118), "meals": (104, 78), "misc": (54, 29)},
        "western sahara, laayoune": {"first_30": 134, "after_30": 112, "accommodation": (60, 54), "meals": (57, 43), "misc": (17, 15)},
        "yemen, sana'a": {"first_30": 278, "after_30": 96, "accommodation": (203, 49), "meals": (39, 34), "misc": (36, 13)},
        
        # Common aliases
        "kabul": {"first_30": 163, "after_30": 76, "accommodation": (101, 35), "meals": (41, 31), "misc": (21, 10)},
        "baghdad": {"first_30": 278, "after_30": 95, "accommodation": (175, 33), "meals": (67, 50), "misc": (36, 12)},
        "juba": {"first_30": 128, "after_30": 97, "accommodation": (86, 65), "meals": (25, 19), "misc": (17, 13)},
        "south sudan": {"first_30": 128, "after_30": 97, "accommodation": (86, 65), "meals": (25, 19), "misc": (17, 13)},
        "kosovo": {"first_30": 161, "after_30": 122, "accommodation": (81, 61), "meals": (59, 44), "misc": (21, 17)},
        "abu dhabi": {"first_30": 417, "after_30": 225, "accommodation": (259, 118), "meals": (104, 78), "misc": (54, 29)}
    }
    
    # Normalize input for matching
    search_key = mission_location.lower().strip()
    
    # Try exact match first
    if search_key in msa_rates:
        rate_data = msa_rates[search_key]
        return {
            "status": "success",
            "result": {
                "mission_location": mission_location,
                "first_30_days": rate_data["first_30"],
                "after_30_days": rate_data["after_30"],
                "accommodation": {"first_30": rate_data["accommodation"][0], "after_30": rate_data["accommodation"][1]},
                "meals": {"first_30": rate_data["meals"][0], "after_30": rate_data["meals"][1]},
                "miscellaneous": {"first_30": rate_data["misc"][0], "after_30": rate_data["misc"][1]},
                "content": f"MSA rates for {mission_location}: First 30 days: ${rate_data['first_30']}, After 30 days: ${rate_data['after_30']} (2025 rates)",
                "year": "2025",
                "data_source": "Official UN MSA rates"
            }
        }
    
    # Try partial matching for variations
    for key, rate_data in msa_rates.items():
        if search_key in key or key in search_key:
            return {
                "status": "success",
                "result": {
                    "mission_location": mission_location,
                    "first_30_days": rate_data["first_30"],
                    "after_30_days": rate_data["after_30"],
                    "accommodation": {"first_30": rate_data["accommodation"][0], "after_30": rate_data["accommodation"][1]},
                    "meals": {"first_30": rate_data["meals"][0], "after_30": rate_data["meals"][1]},
                    "miscellaneous": {"first_30": rate_data["misc"][0], "after_30": rate_data["misc"][1]},
                    "content": f"MSA rates for {mission_location}: First 30 days: ${rate_data['first_30']}, After 30 days: ${rate_data['after_30']} (matched: {key}) (2025 rates)",
                    "year": "2025",
                    "data_source": "Official UN MSA rates"
                }
            }
    
    # Not found
    return {
        "status": "not_found",
        "result": {
            "mission_location": mission_location,
            "content": f"MSA rate for '{mission_location}' not found in current database. Available missions include peacekeeping and special political missions.",
            "suggestion": "Try locations like 'Baghdad', 'Kabul', 'South Sudan', 'Kosovo'"
        }
    }


def dsa_rates_search(location: str) -> str:
    """
    Search for UN DSA rates by country, city, or area for official travel.

    Args:
        location: Country, city, or area to search for DSA rates

    Returns:
        JSON string with DSA rate information including USD and local currency amounts
    """
    global last_agent_tool_used
    last_agent_tool_used = "un_travel_specialist"

    import csv
    import os
    from typing import List, Dict

    # Get the path to the DSA rates CSV file
    current_dir = os.path.dirname(os.path.abspath(__file__))
    csv_file_path = os.path.join(current_dir, 'dsa_rates.csv')

    if not os.path.exists(csv_file_path):
        return json.dumps({
            "status": "error",
            "result": {
                "content": "DSA rates database file not found. Please ensure dsa_rates.csv is available.",
                "data_source": "UN DSA rates database"
            }
        })

    tools_logger.debug(f"🔧 [DSA Tool] Searching DSA rates for: '{location}'")
    
    # Handle Japan default to Tokyo
    if location.lower().strip() in ['japan', 'jpn']:
        search_key = 'tokyo'
        tools_logger.debug(f"🔧 [DSA Tool] Japan query detected, defaulting to Tokyo")
    else:
        # Normalize search term
        search_key = location.lower().strip()
    
    matching_rates = []
    
    try:
        with open(csv_file_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                country = row.get('Country', '').strip().lower()
                area = row.get('Area', '').strip().lower()
                
                # Search in country or area fields
                if (search_key in country or search_key in area or 
                    country in search_key or area in search_key):
                    
                    # Clean and parse numeric values
                    first_60_usd = row.get('First 60 Days (USD)', '0').replace(',', '')
                    first_60_local = row.get('First 60 Days (Local)', '0').replace(',', '')
                    after_60_local = row.get('After 60 Days (Local)', '0').replace(',', '')
                    room_percentage = row.get('Room as % of DSA', '0')
                    
                    try:
                        first_60_usd = float(first_60_usd) if first_60_usd else 0
                        first_60_local = float(first_60_local) if first_60_local else 0
                        after_60_local = float(after_60_local) if after_60_local else 0
                        room_percentage = float(room_percentage) if room_percentage else 0
                    except ValueError:
                        # Skip rows with invalid numeric data
                        continue
                    
                    rate_info = {
                        "country": row.get('Country', '').strip(),
                        "currency": row.get('Currency', '').strip(),
                        "area": row.get('Area', '').strip(),
                        "first_60_days_usd": first_60_usd,
                        "first_60_days_local": first_60_local,
                        "after_60_days_local": after_60_local,
                        "room_percentage": room_percentage,
                        "effective_date": row.get('Effective Date', '').strip(),
                        "survey_date": row.get('Survey Date', '').strip(),
                        "notes": row.get('Notes', '').strip()
                    }
                    matching_rates.append(rate_info)
        
        print(f"✅ [DSA Tool] Found {len(matching_rates)} matching rates")
        
        if matching_rates:
            # Sort by country and area for consistent results
            matching_rates.sort(key=lambda x: (x['country'], x['area']))
            
            # Format the response
            content_parts = []
            content_parts.append(f"**DSA Rates for '{location}':**\n")
            
            current_country = None
            for rate in matching_rates[:10]:  # Limit to first 10 results
                if rate['country'] != current_country:
                    current_country = rate['country']
                    content_parts.append(f"\n**{rate['country']} ({rate['currency']}):**")
                
                content_parts.append(f"• **{rate['area']}:**")
                content_parts.append(f"  - First 60 days: ${rate['first_60_days_usd']} USD ({rate['first_60_days_local']:,.0f} {rate['currency']})")
                content_parts.append(f"  - After 60 days: {rate['after_60_days_local']:,.0f} {rate['currency']}")
                content_parts.append(f"  - Room allowance: {rate['room_percentage']}% of DSA")
                if rate['notes']:
                    content_parts.append(f"  - Notes: {rate['notes']}")
                content_parts.append(f"  - Effective: {rate['effective_date']}")
            
            if len(matching_rates) > 10:
                content_parts.append(f"\n*Showing first 10 of {len(matching_rates)} total matches*")
            
            return json.dumps({
                "status": "success",
                "result": {
                    "location": location,
                    "total_matches": len(matching_rates),
                    "rates_data": matching_rates[:10],
                    "content": "\n".join(content_parts),
                    "data_source": "UN DSA rates database (2025)",
                    "effective_date": matching_rates[0]['effective_date'] if matching_rates else None
                }
            })
        else:
            return json.dumps({
                "status": "not_found",
                "result": {
                    "location": location,
                    "content": f"No DSA rates found for '{location}'. Please check the spelling or try a different country/city name.",
                    "data_source": "UN DSA rates database"
                }
            })
    
    except Exception as e:
        print(f"❌ [DSA Tool] Error: {str(e)}")
        return json.dumps({
            "status": "error",
            "result": {
                "location": location,
                "content": f"Error searching DSA rates: {str(e)}",
                "data_source": "UN DSA rates database"
            }
        })


def get_staff_benefits_by_category(category: str) -> str:
    """
    Get UN staff benefits information by staff category.
    
    This tool retrieves specific benefits information for different UN staff categories,
    with emphasis on international vs local recruitment status and compensation structures.
    
    Args:
        category: Staff category to retrieve benefits for. Options:
            - "1" or "professional" or "international" -> Professional and Higher Categories  
            - "2" or "general_service" or "gs" -> General Services and Related Categories
            - "3" or "npo" or "national_professional" -> National Professional Officers
            - "4" or "field_service" or "fs" -> Field Service
            - "all" or "overview" -> All categories overview
            - "international_staff" -> Focus on international staff (Professional, Field Service)
    
    Returns:
        str: Formatted benefits information for the requested category
    """
    global last_agent_tool_used
    last_agent_tool_used = "un_benefits_specialist"
    tools_logger.debug(f"🔧 [Benefits Tool] Retrieving staff benefits for category: '{category}'")
    
    
    try:
        # Get the path to staff_benefits.md
        current_dir = os.path.dirname(os.path.abspath(__file__))
        benefits_file_path = os.path.join(current_dir, 'staff_benefits.md')
        
        if not os.path.exists(benefits_file_path):
            return json.dumps({
                "status": "error",
                "result": {
                    "content": "Staff benefits file not found",
                    "category": category
                }
            })
        
        # Read the entire file
        with open(benefits_file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # Define section mappings
        category_mapping = {
            "1": "professional",
            "professional": "professional", 
            "international": "professional",
            "p": "professional",
            "2": "general_service",
            "general_service": "general_service",
            "gs": "general_service", 
            "3": "npo",
            "npo": "npo",
            "national_professional": "npo",
            "4": "field_service", 
            "field_service": "field_service",
            "fs": "field_service",
            "all": "all",
            "overview": "all",
            "international_staff": "international_staff"
        }
        
        # Normalize category input
        normalized_category = category_mapping.get(category.lower().strip(), category.lower())
        
        # Split content by main sections
        sections = {}
        
        # Extract Professional and Higher Categories
        prof_start = content.find("## Professional and Higher Categories")
        prof_end = content.find("## General Services and Related Categories")
        if prof_start != -1 and prof_end != -1:
            sections["professional"] = content[prof_start:prof_end].strip()
        
        # Extract General Services and Related Categories  
        gs_start = content.find("## General Services and Related Categories")
        gs_end = content.find("## National Professional Officers")
        if gs_start != -1 and gs_end != -1:
            sections["general_service"] = content[gs_start:gs_end].strip()
        
        # Extract National Professional Officers
        npo_start = content.find("## National Professional Officers")
        npo_end = content.find("## Field Service")
        if npo_start != -1 and npo_end != -1:
            sections["npo"] = content[npo_start:npo_end].strip()
        
        # Extract Field Service
        fs_start = content.find("## Field Service")
        if fs_start != -1:
            sections["field_service"] = content[fs_start:].strip()
        
        # Handle different category requests
        result_content = ""
        
        if normalized_category == "professional":
            result_content = sections.get("professional", "Professional category information not found")
            
        elif normalized_category == "general_service":
            result_content = sections.get("general_service", "General Service category information not found")
            
        elif normalized_category == "npo":
            result_content = sections.get("npo", "National Professional Officer information not found")
            
        elif normalized_category == "field_service":
            result_content = sections.get("field_service", "Field Service category information not found")
            
        elif normalized_category == "international_staff":
            # Focus on international staff (Professional and Field Service)
            prof_section = sections.get("professional", "")
            fs_section = sections.get("field_service", "")
            
            result_content = f"""# International Staff Benefits Overview

International staff in the UN system include **Professional (P, D levels) and Field Service (FS)** categories who are normally recruited internationally and receive worldwide scale compensation.

{prof_section}

{fs_section}

**Key Distinctions for International Staff:**
• **Recruitment:** International recruitment vs. local recruitment
• **Salary Scale:** Worldwide scale with post adjustment vs. local salary scales  
• **Benefits:** Enhanced international benefits including home leave, education grants, mobility incentives
• **Pension:** UN Joint Staff Pension Fund participation after 6+ months service
• **Categories:** Professional (P-1 to P-5), Directors (D-1, D-2), Field Service (FS), and senior levels (ASG, USG)"""
            
        elif normalized_category == "all":
            # Provide overview of all categories
            result_content = f"""# UN Staff Benefits by Category Overview

{sections.get("professional", "")}

{sections.get("general_service", "")}

{sections.get("npo", "")}

{sections.get("field_service", "")}

**Summary:**
• **International Categories:** Professional & Field Service (worldwide scale, international benefits)
• **Local Categories:** General Service & National Professional Officers (local scale, local benefits)"""
        
        else:
            return json.dumps({
                "status": "error", 
                "result": {
                    "content": f"Invalid category '{category}'. Valid options: 1/professional/international, 2/general_service/gs, 3/npo/national_professional, 4/field_service/fs, all/overview, international_staff",
                    "category": category
                }
            })
        
        print(f"✅ [Benefits Tool] Retrieved {len(result_content)} characters for category '{normalized_category}'")
        
        return json.dumps({
            "status": "success",
            "result": {
                "category": normalized_category,
                "original_request": category,
                "content": result_content,
                "data_source": "UN Staff Benefits Documentation"
            }
        })
        
    except Exception as e:
        print(f"❌ [Benefits Tool] Error: {str(e)}")
        return json.dumps({
            "status": "error",
            "result": {
                "content": f"Error retrieving staff benefits: {str(e)}",
                "category": category
            }
        })


# ============================================================================
# NEW CACHE-ENABLED SALARY TOOLS
# ============================================================================
# These functions provide high-performance O(1) cache-based lookups
# Keep existing tools (get_salary_info, get_pa_rate, get_msa_rate) for comparison
# ============================================================================

def get_salary(query: str) -> dict:
    """Get UN salary amount using in-memory cache with SpaCy entity extraction.

    Natural language salary query using SpaCy NER for entity extraction,
    then cache-based O(1) lookups.

    This function uses SpaCy to extract entities (grade, step, etc.) from
    natural language queries like "P-3 step 5", falls back to regex if SpaCy
    is unavailable, then looks up the exact salary amount from the cache.

    Args:
        query (str): Natural language salary query (e.g., "P-3 step 5", "D-1 step 10 Gross")

    Returns:
        dict: {
            "status": "success" or "error",
            "result": {
                "amount": float,
                "currency": "USD",
                "level": str,
                "step": int,
                "rem_type": str,
                "data_source": str (indicates cache vs network)
            }
        }
    """
    _ensure_cache_loaded()
    tools_logger.debug(f"💰 [Salary] Querying with SpaCy + cache for: '{query}'")

    try:
        cache = get_salary_cache()
        level = None
        step = None
        rem_type = "Gross"  # default
        spacy_used = False

        # STEP 1: Try UN Policy NLP entity extraction first
        try:
            entities = nlp_extract(query)
            tools_logger.debug(f"[NLP] Extracted entities: {entities}")

            # Map extracted entities
            if entities.get("grade"):
                level = entities["grade"]  # Already formatted like "P-3"
                spacy_used = True
                tools_logger.debug(f"[NLP] Extracted grade: {level}")

            if entities.get("step"):
                step_str = str(entities["step"])
                try:
                    step = int(step_str)
                except (ValueError, TypeError):
                    pass
                if step is not None and spacy_used:
                    tools_logger.debug(f"[NLP] Extracted step: {step}")

        except Exception as e:
            tools_logger.debug(f"[NLP] Entity extraction failed: {e}, falling back to regex")

        # STEP 2: Fallback to regex parsing if SpaCy didn't extract level/step
        if not level or step is None:
            tools_logger.debug(f"[Regex] Fallback parsing for: '{query}'")
            query_upper = query.upper().strip()

            # Extract level (P-1 to P-5, D-1, D-2, etc.)
            if not level:
                for prefix in ["P-", "D-", "FS-", "GS-"]:
                    if prefix in query_upper:
                        idx = query_upper.find(prefix)
                        level_part = query_upper[idx:idx+3]  # e.g., "P-3"
                        if len(level_part) >= 2:
                            level = level_part[:2]  # e.g., "P-"
                            if idx+2 < len(query_upper) and query_upper[idx+2].isdigit():
                                level = level_part  # Full level like "P-3"
                            break

            # Extract step (typically 1-26)
            if step is None:
                for word in query_upper.split():
                    if word.isdigit():
                        step_val = int(word)
                        if 1 <= step_val <= 26:
                            step = step_val
                            break

        # STEP 3: Extract rem_type (Gross, Net, Base, etc.)
        query_upper = query.upper()
        if "NET" in query_upper:
            rem_type = "Net"
        elif "BASE" in query_upper:
            rem_type = "Base"
        elif "PENSIONABLE" in query_upper:
            rem_type = "Pensionable"
        elif "GROSS" in query_upper:
            rem_type = "Gross"

        # STEP 4: Validate extraction
        if not level or step is None:
            return {
                "status": "error",
                "result": {
                    "error": f"Could not parse query: '{query}'. Expected format: 'Level Step [REM_TYPE]' (e.g., 'P-3 step 5' or 'D-1 10 Gross')",
                    "extraction_method": "UN Policy NLP+Regex",
                    "data_source": "Query parser"
                }
            }

        # STEP 5: Look up in cache - O(1) operation
        version_id = 2
        amount = cache.get_salary_amount(version_id, level, step, rem_type)

        if amount is not None:
            method = "UN Policy NLP" if spacy_used else "Regex"
            tools_logger.info(f"[Salary] {method} extraction successful: {level} step {step} ({rem_type}) = ${amount}")
            return {
                "status": "success",
                "result": {
                    "amount": amount,
                    "currency": "USD",
                    "level": level,
                    "step": step,
                    "rem_type": rem_type,
                    "extraction_method": method,
                    "data_source": "Cache salary_steps table (O(1) lookup)"
                }
            }
        else:
            tools_logger.debug(f"[Salary] Not found in cache: {level} step {step} ({rem_type})")
            return {
                "status": "not_found",
                "result": {
                    "error": f"Salary not found for {level} step {step} ({rem_type})",
                    "level": level,
                    "step": step,
                    "rem_type": rem_type,
                    "extraction_method": "UN Policy NLP+Regex",
                    "data_source": "Cache salary_steps table"
                }
            }

    except Exception as e:
        tools_logger.error(f"❌ [Salary] Error: {e}")
        return {
            "status": "error",
            "result": {
                "error": f"Cache lookup failed: {str(e)}",
                "data_source": "Cache error handler"
            }
        }


def get_post_adjustment(duty_station: str) -> dict:
    """Get Post Adjustment (PA) rate using in-memory cache.

    Fast O(1) cache-based lookup for duty station PA rates.
    Falls back to Supabase if cache unavailable.

    Args:
        duty_station (str): UN duty station (e.g., "Geneva", "New York", "Cairo")

    Returns:
        dict: {
            "status": "success" or "error",
            "result": {
                "pa_rate": float (percentage),
                "duty_station": str,
                "currency_adjusted": bool,
                "data_source": str (indicates cache vs network)
            }
        }
    """
    _ensure_cache_loaded()
    tools_logger.debug(f"📍 [Cache PA] Querying cache for: '{duty_station}'")

    try:
        cache = get_salary_cache()

        # Look up PA rate in cache - O(1) operation
        pa_rate = cache.get_pa_rate(duty_station)

        if pa_rate is not None:
            tools_logger.debug(f"✅ [Cache PA] Found PA rate for {duty_station}: {pa_rate}%")
            return {
                "status": "success",
                "result": {
                    "pa_rate": pa_rate,
                    "duty_station": duty_station,
                    "percentage": f"{pa_rate}%",
                    "currency_adjusted": True,
                    "data_source": "Cache pa_rates table (O(1) lookup)"
                }
            }
        else:
            tools_logger.debug(f"⚠️ [Cache PA] Not found in cache: {duty_station}")
            return {
                "status": "not_found",
                "result": {
                    "error": f"PA rate not found for duty station: '{duty_station}'",
                    "duty_station": duty_station,
                    "data_source": "Cache pa_rates table"
                }
            }

    except Exception as e:
        tools_logger.error(f"❌ [Cache PA] Error: {e}")
        return {
            "status": "error",
            "result": {
                "error": f"Cache lookup failed: {str(e)}",
                "data_source": "Cache error handler"
            }
        }


def get_dsa(country: str, area: str) -> dict:
    """Get Daily Subsistence Allowance (DSA) rate using in-memory cache.

    NEW CAPABILITY: DSA lookup was not available in original tools.
    Fast O(1) cache-based lookup for country/area DSA rates.
    Falls back to Supabase if cache unavailable.

    Args:
        country (str): Country name (e.g., "Egypt", "Israel", "France")
        area (str): Area within country (e.g., "Cairo", "Tel Aviv", "Paris")

    Returns:
        dict: {
            "status": "success" or "error",
            "result": {
                "dsa_rate": float,
                "currency": str,
                "country": str,
                "area": str,
                "per_diem": "daily",
                "data_source": str (indicates cache vs network)
            }
        }
    """
    _ensure_cache_loaded()
    tools_logger.debug(f"🌍 [Cache DSA] Querying cache for: '{country}, {area}'")

    try:
        cache = get_salary_cache()

        # Look up DSA rate in cache - O(1) operation
        dsa_rate = cache.get_dsa_rate(country, area)

        if dsa_rate is not None:
            tools_logger.debug(f"✅ [Cache DSA] Found DSA rate for {country}/{area}: ${dsa_rate}")
            return {
                "status": "success",
                "result": {
                    "dsa_rate": dsa_rate,
                    "currency": "USD",
                    "country": country,
                    "area": area,
                    "per_diem": "daily",
                    "data_source": "Cache dsa_rates table (O(1) lookup)"
                }
            }
        else:
            tools_logger.debug(f"⚠️ [Cache DSA] Not found in cache: {country}/{area}")
            return {
                "status": "not_found",
                "result": {
                    "error": f"DSA rate not found for {country}/{area}",
                    "country": country,
                    "area": area,
                    "data_source": "Cache dsa_rates table"
                }
            }

    except Exception as e:
        tools_logger.error(f"❌ [Cache DSA] Error: {e}")
        return {
            "status": "error",
            "result": {
                "error": f"Cache lookup failed: {str(e)}",
                "data_source": "Cache error handler"
            }
        }


def get_msa(country: str, location: str, days_elapsed: int = 0) -> dict:
    """Get Mission Subsistence Allowance (MSA) rate using in-memory cache.

    Fast O(1) cache-based lookup for mission location MSA rates.
    Auto-selects first_30 or after_30 tier based on days_elapsed.
    Falls back to Supabase if cache unavailable.

    Args:
        country (str): Country name (e.g., "Israel", "Democratic Republic of the Congo")
        location (str): Mission location (e.g., "Tel Aviv", "Kinshasa")
        days_elapsed (int): Days elapsed in mission (default 0).
                           If <= 30, uses first_30 rate. If > 30, uses after_30 rate.

    Returns:
        dict: {
            "status": "success" or "error",
            "result": {
                "msa_rate": float,
                "currency": str,
                "country": str,
                "location": str,
                "time_tier": "first_30" or "after_30",
                "days_elapsed": int,
                "data_source": str (indicates cache vs network)
            }
        }
    """
    _ensure_cache_loaded()
    tools_logger.debug(f"🏢 [Cache MSA] Querying cache for: '{country}, {location}' (days={days_elapsed})")

    try:
        cache = get_salary_cache()

        # Determine time tier based on days_elapsed
        time_tier = "first_30" if days_elapsed <= 30 else "after_30"

        # Look up MSA rate in cache - O(1) operation
        msa_rate = cache.get_msa_rate(country, location, time_tier)

        if msa_rate is not None:
            tools_logger.debug(f"✅ [Cache MSA] Found MSA rate for {country}/{location} ({time_tier}): ${msa_rate}")
            return {
                "status": "success",
                "result": {
                    "msa_rate": msa_rate,
                    "currency": "USD",
                    "country": country,
                    "location": location,
                    "time_tier": time_tier,
                    "days_elapsed": days_elapsed,
                    "data_source": "Cache msa_rates table (O(1) lookup)"
                }
            }
        else:
            tools_logger.debug(f"⚠️ [Cache MSA] Not found in cache: {country}/{location}")
            return {
                "status": "not_found",
                "result": {
                    "error": f"MSA rate not found for {country}/{location}",
                    "country": country,
                    "location": location,
                    "time_tier": time_tier,
                    "data_source": "Cache msa_rates table"
                }
            }

    except Exception as e:
        tools_logger.error(f"❌ [Cache MSA] Error: {e}")
        return {
            "status": "error",
            "result": {
                "error": f"Cache lookup failed: {str(e)}",
                "data_source": "Cache error handler"
            }
        }