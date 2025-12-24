"""CLI entry point for the Ariyo-style chatbot."""
from __future__ import annotations

from bot.engine import ChatEngine
from bot.intents import IntentDetector
from bot.logger import ChatLogger
from bot.memory import SessionMemory
from bot.persona import AriyoPersona


def main() -> None:
    """Run the CLI chat loop."""
    engine = ChatEngine(
        detector=IntentDetector(),
        persona=AriyoPersona(),
        memory=SessionMemory(max_messages=20),
        logger=ChatLogger(),
    )

    print("Ariyo: Hello! I'm Ariyo, your chat companion.")
    print("Try: 'what time is it?', 'reset memory', or 'tell me about yourself'.")
    print("Type 'exit' or 'quit' to leave.\n")

    while True:
        user_text = input("You: ").strip()
        if not user_text:
            print("Ariyo: I'm listening. Share a thought or ask a question.")
            continue

        normalized = user_text.lower()
        if normalized in {"exit", "quit"}:
            print("Ariyo: Take care! If you need anything, I'm here.")
            break

        response, intent = engine.handle_message(user_text)
        print(f"Ariyo: {response}")

        if intent.intent == "goodbye":
            break


if __name__ == "__main__":
    main()
