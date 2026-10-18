"""
Ollama field	           Meaning
prompt_eval_count	       Number of input/prompt tokens
eval_count	               Number of generated tokens
total_duration	           Total generation duration
load_duration	           Model loading time
eval_duration	           Time spent generating
"""

from backend.llm_client import generate

response = generate(
    """
Return this JSON exactly:

{
    "category": "general",
    "summary": "Test response."
}
"""
)


print("Response:")
print(response)

print()
print("Available fields:")

for key in response:
    print("-", key)

