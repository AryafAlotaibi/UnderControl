from llm.model import client, SCHEMA_MODEL

print("Starting test...")

response = client.chat.completions.create(
    model=SCHEMA_MODEL,
    messages=[
        {"role": "user", "content": "Reply with exactly: API connection works"}
    ],
)

print("Response received")
print(response.choices[0].message.content)
