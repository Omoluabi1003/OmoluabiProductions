"""Tests for intent detection."""
import unittest

from bot.intents import IntentDetector


class TestIntentDetector(unittest.TestCase):
    def setUp(self) -> None:
        self.detector = IntentDetector()

    def test_greeting_intent(self) -> None:
        result = self.detector.detect("Hello there")
        self.assertEqual(result.intent, "greetings")
        self.assertGreaterEqual(result.confidence, 0.5)

    def test_help_intent(self) -> None:
        result = self.detector.detect("Can you help me?")
        self.assertEqual(result.intent, "help")
        self.assertGreaterEqual(result.confidence, 0.5)

    def test_smalltalk_intent(self) -> None:
        result = self.detector.detect("How are you today?")
        self.assertEqual(result.intent, "smalltalk")
        self.assertGreaterEqual(result.confidence, 0.5)

    def test_time_intent(self) -> None:
        result = self.detector.detect("What time is it?")
        self.assertEqual(result.intent, "ask_time")
        self.assertGreaterEqual(result.confidence, 0.5)

    def test_date_intent(self) -> None:
        result = self.detector.detect("What's the date today?")
        self.assertEqual(result.intent, "ask_date")
        self.assertGreaterEqual(result.confidence, 0.5)

    def test_gratitude_intent(self) -> None:
        result = self.detector.detect("Thanks for the help")
        self.assertEqual(result.intent, "gratitude")
        self.assertGreaterEqual(result.confidence, 0.5)

    def test_goodbye_intent(self) -> None:
        result = self.detector.detect("Goodbye for now")
        self.assertEqual(result.intent, "goodbye")
        self.assertGreaterEqual(result.confidence, 0.5)

    def test_reset_memory_intent(self) -> None:
        result = self.detector.detect("reset memory")
        self.assertEqual(result.intent, "reset_memory")
        self.assertGreaterEqual(result.confidence, 0.5)

    def test_fallback_intent(self) -> None:
        result = self.detector.detect("abracadabra")
        self.assertEqual(result.intent, "fallback")


if __name__ == "__main__":
    unittest.main()
