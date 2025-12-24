"""Session memory for the chatbot."""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Deque, List


@dataclass
class SessionMemory:
    """Bounded in-memory store for recent conversation turns."""

    max_messages: int = 20
    user_messages: Deque[str] = field(init=False)
    bot_messages: Deque[str] = field(init=False)

    def __post_init__(self) -> None:
        """Initialize deques with the configured max length."""
        self.user_messages = deque(maxlen=self.max_messages)
        self.bot_messages = deque(maxlen=self.max_messages)

    def add_user_message(self, message: str) -> None:
        """Add a user message to memory."""
        self.user_messages.append(message)

    def add_bot_message(self, message: str) -> None:
        """Add a bot message to memory."""
        self.bot_messages.append(message)

    def reset(self) -> None:
        """Clear all stored messages."""
        self.user_messages.clear()
        self.bot_messages.clear()

    def recent_user_messages(self) -> List[str]:
        """Return a list of recent user messages."""
        return list(self.user_messages)

    def recent_bot_messages(self) -> List[str]:
        """Return a list of recent bot messages."""
        return list(self.bot_messages)
