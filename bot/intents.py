"""Intent detection and scoring."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple


@dataclass(frozen=True)
class IntentResult:
    """Result of intent detection."""

    intent: str
    confidence: float


class IntentDetector:
    """Rule-based intent detector with lightweight scoring."""

    def __init__(self) -> None:
        self.intent_rules: Dict[str, List[Tuple[List[str], float]]] = {
            "greetings": [
                (["hello", "hi", "hey", "good morning", "good afternoon", "good evening"], 0.6),
                (["howdy", "yo"], 0.3),
            ],
            "gratitude": [
                (["thanks", "thank you", "appreciate", "grateful"], 0.8),
                (["cheers"], 0.3),
            ],
            "help": [
                (["help", "what can you do", "how do you work", "commands"], 0.8),
                (["guide", "assist", "support"], 0.4),
            ],
            "smalltalk": [
                (["how are you", "how's it going", "how are things"], 0.6),
                (["tell me about yourself", "who are you"], 0.5),
                (["what's up", "whats up", "sup"], 0.4),
            ],
            "ask_time": [
                (["time", "what time", "current time"], 0.7),
                (["clock"], 0.3),
            ],
            "ask_date": [
                (["date", "what date", "what day"], 0.7),
                (["day is it", "calendar"], 0.3),
            ],
            "goodbye": [
                (["bye", "goodbye", "see you", "later"], 0.7),
                (["exit", "quit", "farewell"], 0.6),
            ],
            "reset_memory": [
                (["reset memory", "clear memory", "forget this", "wipe memory"], 0.9),
            ],
        }

    def detect(self, text: str) -> IntentResult:
        """Detect the best intent for the given text."""
        normalized = " ".join(text.lower().strip().split())
        if not normalized:
            return IntentResult(intent="fallback", confidence=0.0)

        best_intent = "fallback"
        best_confidence = 0.0

        for intent, rules in self.intent_rules.items():
            score = 0.0
            max_weight = 0.0
            for phrases, weight in rules:
                max_weight = max(max_weight, weight)
                if any(phrase in normalized for phrase in phrases):
                    score += weight
            confidence = min(1.0, score / max_weight) if max_weight else 0.0
            if confidence > best_confidence:
                best_confidence = confidence
                best_intent = intent

        if best_confidence < 0.35:
            return IntentResult(intent="fallback", confidence=best_confidence)

        return IntentResult(intent=best_intent, confidence=round(best_confidence, 2))
