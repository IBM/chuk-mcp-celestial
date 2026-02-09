# Examples

This directory contains example scripts demonstrating how to use the US Navy Celestial MCP Server.

## Running the Examples

Make sure you have the package installed:

```bash
# Install in development mode
pip install -e .

# Or install from PyPI
pip install chuk-mcp-celestial
```

Then run any example:

```bash
python examples/example_basic.py
python examples/eclipse_planner.py
```

## Available Examples

### `example_basic.py`
Basic usage examples of all celestial tools:
- Getting moon phases
- Sun and moon rise/set/transit times
- Solar eclipse local circumstances
- Finding all eclipses in a year
- Earth's seasonal events

### `eclipse_planner.py`
Advanced eclipse planning tool that:
- Finds all solar eclipses in the next N years
- Checks eclipse visibility from multiple locations
- Provides detailed local circumstances for each location

### `05_planet_position.py`
Planet position queries:
- Where is Mars tonight? (altitude, azimuth, magnitude, constellation)
- Survey all 8 planets at once
- Track a planet across the night (hourly positions)
- Same planet from different cities worldwide

### `06_planet_events.py`
Planet rise/set/transit times:
- When does Jupiter rise and set?
- Events in local time with timezone and DST
- All planets rise/set/transit for one day
- Venus as morning or evening star

### `07_artifact_storage.py`
Computation result storage via chuk-artifacts:
- Storage without backend (graceful degradation)
- Storage with mock backend (metadata, filenames)
- Error handling (store failures don't break tools)

## Using with MCP

To use this server with an MCP client (like Claude Desktop), you don't need to run these examples. Instead, configure the server in your MCP client settings:

```json
{
  "mcpServers": {
    "celestial": {
      "command": "chuk-mcp-celestial"
    }
  }
}
```

Then you can ask the AI assistant questions like:
- "When is the next full moon?"
- "What time does the sun rise in Seattle tomorrow?"
- "Are there any solar eclipses visible from New York in 2024?"
- "When are the equinoxes and solstices this year?"
- "Where is Mars in the sky tonight?"
- "What time does Jupiter rise tomorrow?"
- "Which planets are visible from London right now?"
