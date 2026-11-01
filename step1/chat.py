import os
from dotenv import load_dotenv
from anthropic import Anthropic

load_dotenv()
client = Anthropic()

messages = []

while True:
    user_input = input("\nYou: ")
    if user_input in ("exit", "quit"):
        break

    messages.append({"role": "user", "content": user_input})

    response = client.messages.create(
        model=os.getenv("ANTHROPIC_MODEL", "claude-sonnet-5-5"),
        max_tokens=1000,
        system="You are a concise, helpful assistant.",
        messages=messages,
    )

    reply = response.content[0].text
    messages.append({"role": "assistant", "content": reply})

    print(f"\nAI: {reply}")
    print(f"[tokens in: {response.usage.input_tokens}, out: {response.usage.output_tokens}]")
