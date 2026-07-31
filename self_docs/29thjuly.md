# Per-request user_id threading through agent → tools

## Problem

My `check_session_exists` dependency verifies the bearer token and returns `user["id"]`. I need that `user_id` to reach the booking tools so they only touch data linked to the authenticated user (multi-tenant isolation). My `dependencies.py` had `user_id` in `run_inference` but immediately dropped it — it never reached the tools.

## What I considered

1. **Put user_id in `graph_state`** — rejected. It's like adding a whole new dimension, just for a small thing

2. **Pass user_id in the LLM prompt** — rejected. Brittle glue. The LLM can drop it, hallucinate it, or echo it back to the user. Infrastructure concerns don't belong in prompts.

3. **Per-request tool classes with DI** — means fresh tool instances per request, which forces fresh `create_agent()` calls on every `/query`. Workable but unnecessary overhead.

4. **LangChain `RunnableConfig`** — chosen. Config is already threaded through LangGraph nodes → `create_agent` → tools automatically. Zero per-request cost, and user_id never touches the LLM.

## What I changed

- `dependencies.py`: moved graph/agent/client initialization **inside** `run_inference()` and `run_inference_with_stream()`. No more module-level singletons. `get_kb_agent(user_id)` and `get_booking_agent(user_id)` are called per-request.
- `agent_config.py`: both factory functions now accept `user_id` and return `agent.with_config({"configurable": {"user_id": user_id}})`.
- `booking_tools.py`: each `@tool` accepts `config: RunnableConfig`, extracts `user_id = config["configurable"]["user_id"]`. My existing query logic is untouched — `user_id` is just available for scoping now.

## Next

Add `.eq("user_id", user_id)` filters to my Supabase queries in the booking tools once the column exists.
