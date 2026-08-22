import os
import pytest

if __name__ != "__main__" and os.getenv("RUN_LIVE_PROVIDER_MANUAL_SMOKE", "0") != "1":
    pytest.skip("manual live smoke; enable RUN_LIVE_PROVIDER_MANUAL_SMOKE=1 to run", allow_module_level=True)


from src.llm.request_config import create_live_client

api_key = os.getenv("GROQ_API_KEY") or os.getenv("OPENROUTER_API_KEY", "")
base_url = os.getenv(
    "LLM_BASE_URL",
    "https://api.groq.com/openai/v1" if os.getenv("GROQ_API_KEY") else "https://openrouter.ai/api/v1",
)
model = os.getenv("LLM_MODEL", "openai/gpt-oss-20b" if os.getenv("GROQ_API_KEY") else "openrouter/free")

client = create_live_client(
    base_url=base_url,
    api_key=api_key,
)

response = client.chat.completions.create(
    model=model,
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
