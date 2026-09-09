from llm.model import client, SCHEMA_MODEL

print("Starting test...")

response = client.responses.create(
    model=SCHEMA_MODEL,
    input="Reply with exactly: API connection works"
)

print("Response received")
print(response.output_text)