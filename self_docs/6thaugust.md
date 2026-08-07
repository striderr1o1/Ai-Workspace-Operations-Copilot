# Threading one Supabase client per request through RunnableConfig

## Problem

Two things bothered me:

1. Every tool step created its own Supabase client. Each tool call hit `get_supabase_client_with_token()` and spun up a fresh client, so a single user request with several tool calls paid that cost over and over.
2. I couldn't test `get_namespacename_from_supabase()` without hitting the real Supabase API, because it built its client internally.

## Decision

Create the client **once per request** in `dependencies.py` (`run_inference` / `run_inference_with_stream`) using the user's access token, and thread it through `RunnableConfig` — the same channel I already use for `user_id`. Tools now pull it from config instead of constructing their own.

## Why

- **Testability** — when I write tests, I can hand a mock client straight into `get_namespacename_from_supabase()`. No patching of internals, no live API.
- **One client per request** — all tool calls in a request share a single authenticated client, which also matches how RLS sees one `auth.uid()` per request.

## What I changed

- `supabase_db_functions.py`: `get_namespacename_from_supabase(client, user_id)` now takes the client as a parameter.
- `dependencies.py`: both run functions build the client and pass it to the agent factories.
- `agent_config.py`: `get_kb_agent` / `get_booking_agent` accept the client and put it in `configurable` as `supabase_client`. Replaces `access_token` there — tools no longer need the raw token.
- `kb_tools.py` / `booking_tools.py`: tools read `config["configurable"]["supabase_client"]`.
- `routes/ingestion.py`: builds its own per-request client, since it sits outside the agent chain.

## Status

Refactor done. Tests for `get_namespacename_from_supabase()` with a mock client are still WIP.
