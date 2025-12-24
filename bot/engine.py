"""Chat engine orchestrating intents, memory, and persona."""
from __future__ import annotations

from dataclasses import dataclass

from .intents import IntentDetector, IntentResult
from .logger import ChatLogger
from .memory import SessionMemory
from .persona import AriyoPersona


@dataclass
class ChatEngine:
    """Coordinator for chat interactions."""

    detector: IntentDetector
    persona: AriyoPersona
    memory: SessionMemory
    logger: ChatLogger

    def handle_message(self, user_text: str) -> tuple[str, IntentResult]:
        """Handle a user message and return a response with intent info."""
        intent_result = self.detector.detect(user_text)

        if intent_result.intent == "reset_memory":
            self.memory.reset()

        response = self.persona.generate_response(
            intent=intent_result.intent,
            user_text=user_text,
            memory=self.memory,
            confidence=intent_result.confidence,
        )

        self.memory.add_user_message(user_text)
        self.memory.add_bot_message(response)

        self.logger.log_turn(
            user_text=user_text,
            intent=intent_result.intent,
            confidence=intent_result.confidence,
            response=response,
        )

        return response, intent_result
