## Coding Style

- Prefers inline comments on code explaining what's happening, not just what the code does. Confidence: 0.9
- Prefers consolidating repeated logic into shared modules (DRY principle) rather than duplicating code across functions. Confidence: 0.9
- Prefers keeping implementations simple and avoiding premature abstraction (e.g., "keep it simple, dont create a reusable function if that's what youre doing"). Confidence: 0.9
- Prefers dependency injection over hardcoded imports — classes should accept dependencies (e.g., graph setup function) as constructor parameters rather than importing them directly. Confidence: 0.9
- Prefers consistent naming across the entire project (e.g., renaming `room_tools.py` to `booking_tools.py` everywhere). Confidence: 0.9
- Prefers minimal, precise code changes — only add/change what's strictly necessary for the task, no extra refactoring or additions. Confidence: 0.9

## Project Organization

- Prefers moving shared utilities and error handlers to a centralized `utils/` directory. Confidence: 0.8

## Communication & Feedback

- Values direct, honest, no-sugar assessment of their code quality and engineering skill level — wants to know where they stand and what to improve. Confidence: 0.6

## Workflow

- Prefers understanding the approach/plan first before writing code ("first tell me the approach...then we will see what to do"). Confidence: 1.0
- Prefers documenting architectural decisions in dated files within a `self_docs` directory for team/project reference. Confidence: 0.8
- Prefers self_docs entries written in **first person** ("my", "I") from their own perspective — the doc should read as them narrating their decision, not a third-party observer. Confidence: 0.9
- Prefers regular git commits with push to remote (multiple commit-and-push instructions throughout conversation). Confidence: 0.9
- Prefers updating documentation (e.g., README) before committing code changes. Confidence: 0.7
- Prefers moving global/singleton initializations (client, agents, graph) inside request handler functions for per-request instantiation rather than module-level singletons. Confidence: 1.0

## Architecture & Security

- Prefers user-scoped tool access — each user should only be able to access tools/resources linked to their own user ID (multi-tenant data isolation). Confidence: 0.85
- Prefers passing user identity context through the agent chain from the top-level layer down to tools, so tools can scope their operations to the requesting user. Confidence: 0.85
- Prefers establishing a reference implementation in one place (e.g., `fetch_room_data`), then replicating that same pattern consistently across all other related code — expects tools in the same family to follow the same table, filtering, and auth conventions. Confidence: 0.7
- Prefers using LangChain's RunnableConfig system (`.with_config({"configurable": {...}})` and `config["configurable"]["user_id"]`) to thread per-request user context to tools, rather than class-based DI or putting user_id in prompts. Confidence: 0.9
