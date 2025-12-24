# Ariyo-Style CLI Chatbot

A conversation-only chatbot with a warm, respectful tone and session memory.

## How to run

```bash
python main.py
```

## How to run tests

```bash
python -m unittest
```

## How to add a new intent and response rule

1. Add a new intent name and keyword rules in `bot/intents.py` inside `IntentDetector.intent_rules`.
2. Add a response template in `bot/persona.py` inside `AriyoPersona.responses`, or add special handling in
   `AriyoPersona.generate_response` if the intent needs dynamic content.
3. Add or update tests in `tests/test_intents.py` to cover the new intent.
