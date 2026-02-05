"""
🧪 Test OVH Mistral integration with Vanna!

Run this to make sure everything works before using in production.
"""

import asyncio
import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

from vanna.integrations.ovh_mistral import OvhMistralLlmService
from vanna.core.llm import LlmRequest, LlmMessage
from vanna.core.user.models import User
async def main():
    print(" Testing OVH Mistral integration...")
    
    # Create the LLM service
    llm = OvhMistralLlmService(
        model="Mistral-Small-3.2-24B-Instruct-2506",  # Your working model
        api_key=os.getenv("MISTRAL_API_KEY"),
        base_url=os.getenv("MISTRAL_API_URL")
    )
    
    # Create a simple request
    request = LlmRequest(
        user=User(id="test_user"),
        messages=[
            LlmMessage(role="user", content="consider a student table in a database with columns id, name, age. Write a SQL query to select all students older than 20.")
        ],
        max_tokens=100,
        temperature=0.7
    )
    
    # Send it!
    print("Sending request to OVH Mistral...")
    response = await llm.send_request(request)
    
    print("\n Response from OVH Mistral:")
    print(response.content)
    print(f"\nTokens used: {response.usage}")

if __name__ == "__main__":
    asyncio.run(main())