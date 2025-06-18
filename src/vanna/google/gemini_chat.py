chat = GoogleGeminiChat(config={
    "model_name": "gemini-1.5-flash",
    "api_key": "your-key-here"
})

response = chat.submit_prompt("What's the capital of France?")
print(response)
