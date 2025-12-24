"""File logging for chat turns."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass
class ChatLogger:
    """Simple file logger that appends chat turns with timestamps."""

    log_dir: Path = Path("logs")
    log_file: str = "chat.log"

    def __post_init__(self) -> None:
        self.log_dir.mkdir(parents=True, exist_ok=True)

    def log_turn(self, user_text: str, intent: str, confidence: float, response: str) -> None:
        """Log a single conversation turn."""
        timestamp = datetime.now().isoformat(timespec="seconds")
        log_path = self.log_dir / self.log_file
        line = (
            f"[{timestamp}] user={user_text!r} intent={intent} "
            f"confidence={confidence:.2f} bot={response!r}\n"
        )
        with log_path.open("a", encoding="utf-8") as handle:
            handle.write(line)
