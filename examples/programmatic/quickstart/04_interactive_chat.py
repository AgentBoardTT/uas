#!/usr/bin/env python3
"""Interactive chat example - type your own questions."""

import asyncio

from universal_agent_sdk import (
    AssistantMessage,
    StreamEvent,
    TextBlock,
    UniversalAgentClient,
)

async def interactive_chat():
    """Run an interactive chat session."""
    print("=" * 60)
    print("Interactive Chat with Claude")
    print("=" * 60)
    print("Type your messages and press Enter.")
    print("Type 'quit', 'exit', or 'q' to end the conversation.")
    print("=" * 60)
    print()

    async with UniversalAgentClient() as client:
        while True:
            try:
                user_input = input("You: ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nGoodbye!")
                break

            if not user_input:
                continue

            if user_input.lower() in ("quit", "exit", "q"):
                print("Goodbye!")
                break

            await client.send(user_input)

            print("\nAssistant: ", end="", flush=True)

            async for msg in client.receive():
                if isinstance(msg, StreamEvent):
                    # Print streaming text as it arrives
                    if msg.delta and msg.delta.get("type") == "text_delta":
                        print(msg.delta.get("text", ""), end="", flush=True)
                elif isinstance(msg, AssistantMessage):
                    # If not streaming, print the full response
                    if not any(isinstance(m, StreamEvent) for m in [msg]):
                        text = "".join(
                            b.text for b in msg.content if isinstance(b, TextBlock)
                        )
                        print(text, end="")

            print("\n")


if __name__ == "__main__":
    asyncio.run(interactive_chat())
