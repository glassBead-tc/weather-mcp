# Weather MCP Server

A simple weather MCP server built with FastMCP that provides current weather data and city comparisons.

## Features

- Get current weather for any city
- Compare weather between multiple cities
- Support for metric and imperial units
- Optional detailed forecasts

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run locally:**
   ```bash
   python server.py
   ```

3. **Test with Claude Desktop/Code:**
   Add to your MCP configuration:
   ```json
   {
     "mcpServers": {
       "weather": {
         "command": "python",
         "args": ["/path/to/weather-mcp/server.py"]
       }
     }
   }
   ```

## Tools

### get_weather
Get current weather for a city.
- `city` (string): City name
- `units` (string, optional): "metric" or "imperial" (default: "metric")
- `detailed` (boolean, optional): Include 3-day forecast (default: false)

### compare_weather
Compare weather between multiple cities (max 5).
- `cities` (array): List of city names
- `metric` (string, optional): Sort by "temperature", "humidity", or "wind" (default: "temperature")

## Deploy to Smithery

1. Push to GitHub
2. Go to [smithery.ai/new](https://smithery.ai/new)
3. Connect your repository
4. Deploy\!

## Example Usage

```python
# Get weather for London
await get_weather("London")

# Get detailed weather with forecast
await get_weather("Tokyo", units="imperial", detailed=True)

# Compare temperatures across cities
await compare_weather(["New York", "Los Angeles", "Chicago"], metric="temperature")
```
