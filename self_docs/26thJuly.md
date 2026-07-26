# Decisions made:

## Building Evaluations in @evals/evaluation_engine.py:
- created one function for both response_after_kb and response_after_booking because the logic was same
- Mode.JSON_SCHEMA to enforce JSON output based on Pydantic Base Model and add require parameters option in the chat completion so it doesnt route to some other router that doesn't support JSON.
