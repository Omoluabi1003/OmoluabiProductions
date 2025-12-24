"""Persona and response templates."""
from __future__ import annotations

from datetime import datetime
from typing import Dict

from .memory import SessionMemory


class AriyoPersona:
    """Ariyo-style response generator."""

    def __init__(self) -> None:
        self.responses: Dict[str, str] = {
            "greetings": "Hello! I'm Ariyo. How can I help today?",
            "help": (
                "I can chat, answer simple questions, tell you the time/date, "
                "and reset our session memory. Try: 'what time is it?' or 'reset memory'."
            ),
            "smalltalk": "I'm doing well, thanks for asking. How can I support you?",
            "gratitude": "You're welcome. Happy to help.",
            "goodbye": "Take care! If you need anything, I'm here.",
            "reset_memory": "All set. I've cleared our session memory.",
            "fallback": "I'm not fully sure I got that. Could you rephrase?",
        }

    def generate_response(
        self,
        intent: str,
        user_text: str,
        memory: SessionMemory,
        confidence: float,
        now: datetime | None = None,
    ) -> str:
        """Generate a response given an intent and context."""
        if intent == "ask_time":
            timestamp = (now or datetime.now()).strftime("%H:%M")
            return f"It's {timestamp} right now."
        if intent == "ask_date":
            date_str = (now or datetime.now()).strftime("%A, %B %d, %Y")
            return f"Today is {date_str}."
        if intent == "smalltalk" and "tell me more" in user_text.lower():
            return (
                "I'm Ariyo, your friendly chat companion. "
                "I keep things simple, respectful, and helpful."
            )
        if intent == "fallback" and confidence > 0.0:
            return "I might be a bit off. Can you say that another way?"

        return self.responses.get(intent, self.responses["fallback"])
