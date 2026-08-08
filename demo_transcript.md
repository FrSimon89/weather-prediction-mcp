# Agent Bricks demonstration cases

These are the three acceptance-test prompts to run after registering the deployed MCP with Agent Bricks. The tool traces below describe the required call sequence; capture the actual Agent Bricks trace/final answer after deployment.

## 1. Rain tomorrow

**User:** Will it rain in Chicago tomorrow?

**Required tool flow:** `get_forecast("Chicago", 2)` → inspect the row for tomorrow.

**Expected answer shape:** State tomorrow's precipitation probability and conditions, then answer yes/no based on the returned forecast. Do not invent a value.

## 2. Jacket recommendation

**User:** Should I bring a jacket to Austin this weekend?

**Required tool flow:** `get_forecast("Austin", 4)` (or the minimum range covering both weekend dates) → inspect both relevant dates. For a date-specific judgment, `get_weather_recommendation("Austin", "YYYY-MM-DD")` may be called for each weekend day.

**Expected answer shape:** Summarize the relevant highs/lows and explain whether a jacket is recommended under the tool's stated thresholds.

## 3. Current conditions

**User:** What's the weather like in Seattle right now?

**Required tool flow:** `get_current_weather("Seattle")`.

**Expected answer shape:** Give current temperature, conditions, humidity, wind, and observation time/timezone when available.

## Failure guardrail

**User:** What's the weather in Atlantis tomorrow?

**Required behavior:** The MCP should return a location-resolution error. The agent must say it could not retrieve weather for that location rather than guessing.
