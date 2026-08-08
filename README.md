# Weather Prediction MCP + Agent Bricks

## Deliverable

This submission replaces the original Alpaca trading project with a weather-focused pipeline:

**Agent Bricks agent → external MCP (Databricks App) → FastMCP tools → `weather_broker.py` → Open-Meteo**

Open-Meteo is used because it requires no signup, API key, or credit card.

## MCP tools

- `get_current_weather(location)` — current temperature, apparent temperature, conditions, humidity, precipitation, and wind.
- `get_forecast(location, days)` — normalized daily high/low, precipitation probability, precipitation totals, conditions, and wind for 1–16 days.
- `get_weather_recommendation(location, date)` — derived umbrella/jacket recommendation using explicit thresholds rather than merely passing through API data.

All HTTP calls and response parsing are in `mcp_server/weather_broker.py`; the `@mcp.tool` functions contain no raw HTTP calls.

## Databricks App

`mcp_server/app.yaml` starts the FastMCP server using streamable HTTP. No secrets are required.

Deploy `mcp_server/` as its own Databricks App. Register the deployed app endpoint in the workspace as an **external MCP**, then add that MCP to a Databricks Agent Bricks agent.

## Agent system prompt

The recommended system prompt is in `agent_bricks/system_prompt.md`. It specifies tool selection, ordering, failure handling, and recommendation guardrails.

## Agent Bricks setup

1. Deploy `mcp_server/` as a Databricks App.
2. In the workspace's MCP/external-tool configuration, register the app's streamable-HTTP endpoint.
3. Grant the Agent Bricks agent permission to use the external MCP.
4. Create an Agent Bricks agent and add the registered MCP as its tool source.
5. Paste the contents of `agent_bricks/system_prompt.md` into the agent's system instructions.
6. Test with the three prompts in `agent_bricks/demo_transcript.md`.
7. Capture the Agent Bricks tool trace/final responses for submission evidence.

This repository does not pretend that an external Databricks workspace deployment was performed from source control; deployment and MCP registration are workspace-specific operations.

## Local test

```bash
cd mcp_server
pip install -r requirements.txt
python weather_mcp_server.py
```

The server listens on port 8000 by default and exposes the FastMCP streamable-HTTP endpoint.

## API/authentication

- Provider: Open-Meteo
- Authentication: none
- API key/Databricks secrets: not required

## Files

- `mcp_server/weather_mcp_server.py` — FastMCP server and three thin tools.
- `mcp_server/weather_broker.py` — Open-Meteo geocoding/forecast adapter and recommendation logic.
- `mcp_server/app.yaml` — Databricks App configuration.
- `mcp_server/requirements.txt` — runtime dependencies.
- `agent_bricks/system_prompt.md` — Agent Bricks system prompt.
- `agent_bricks/demo_transcript.md` — three natural-language test cases and expected tool flow.

Databricks App URLs
- MCP Server images: mcp_server_1, mcp_server_2 
