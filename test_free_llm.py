from openai import OpenAI

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key="REDACTED_EXPOSED_OPENROUTER_KEY"
)

response = client.chat.completions.create(
    model="openrouter/free",
    messages=[
        {
            "role": "user",
            "content": """
Reply only with:

{
  "status":"success"
}
"""
        }
    ]
)

print(response.choices[0].message.content)