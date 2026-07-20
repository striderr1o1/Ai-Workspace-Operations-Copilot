```
Orchestrator -> Campaign Designer (RAG over brand guidelines, past campaign performance, competitor intel, buyer personas)
-> Campaign Executor (creates content, creates campaigns, schedules posts, generates reports)
```

# Overview:
## Agents:
- Orchestrator
- Brand and Content Knowledge Agent
- Campaign Executor Agent

## Tasks:
- shift from supabase to simple postgresql
- create two mcp servers/one mcp server for both sub agents

## Phase 1:
- create the mcp server with tools and check what is being input and output, how it works, and check what data needs to be stored
- integrate postgresql, design schema
- unit testing

## Phase 2:
- connect the agentic workflow
- parallel execution of agents (asyncio)



