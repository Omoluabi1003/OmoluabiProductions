"""Tests for session memory."""
import unittest

from bot.memory import SessionMemory


class TestSessionMemory(unittest.TestCase):
    def test_memory_max_length(self) -> None:
        memory = SessionMemory(max_messages=3)
        for i in range(5):
            memory.add_user_message(f"user-{i}")
            memory.add_bot_message(f"bot-{i}")

        self.assertEqual(len(memory.recent_user_messages()), 3)
        self.assertEqual(len(memory.recent_bot_messages()), 3)
        self.assertEqual(memory.recent_user_messages()[0], "user-2")
        self.assertEqual(memory.recent_bot_messages()[0], "bot-2")

    def test_reset_clears_memory(self) -> None:
        memory = SessionMemory(max_messages=3)
        memory.add_user_message("hello")
        memory.add_bot_message("hi")
        memory.reset()

        self.assertEqual(memory.recent_user_messages(), [])
        self.assertEqual(memory.recent_bot_messages(), [])


if __name__ == "__main__":
    unittest.main()
