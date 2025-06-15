from typing import Dict, Any
import os

# Completely lazy loading approach - only import FastMCP when needed
def get_mcp():
    """Lazy-loaded FastMCP instance to avoid import-time dependencies."""
    from mcp.server.fastmcp import FastMCP
    return FastMCP("weather-server")

# Lazy loading: Only import when needed, not at module level
def get_http_client():
    """Lazy-loaded HTTP client to avoid import-time dependencies."""
    import httpx
    return httpx.AsyncClient(timeout=10.0)

def get_weather_api_url():
    """Lazy-loaded weather API URL."""
    return "https://wttr.in"

def setup_tools(mcp):
    """Setup tools on the MCP server instance."""
    
    @mcp.tool()
    async def ping() -> str:
        """Simple ping tool to test server responsiveness and prevent timeouts."""
        return "pong"

    @mcp.tool()
    async def health_check() -> Dict[str, Any]:
        """Health check to verify server connectivity and status."""
        from datetime import datetime
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "server": "weather-mcp",
            "version": "1.0.0",
            "tools_available": ["ping", "health_check", "get_weather", "compare_weather"]
        }

        @mcp.tool()
        async def get_weather(city: str, units: str = "metric", detailed: bool = False) -> Dict[str, Any]:
            """Get current weather for a city."""
            if not city:
                return {"error": "City name required"}
            
            try:
                # Lazy load dependencies
                from urllib.parse import quote
                
                async with get_http_client() as client:
                    response = await client.get(
                        f"{get_weather_api_url()}/{quote(city)}",
                        params={"format": "j1", "m": "" if units == "metric" else "f"}
                    )
                    response.raise_for_status()
                    
                data = response.json()
                current = data["current_condition"][0]
                
                result = {
                    "city": city,
                    "temperature": f"{current['temp_C']}°C" if units == "metric" else f"{current['temp_F']}°F",
                    "condition": current["weatherDesc"][0]["value"],
                    "humidity": f"{current['humidity']}%",
                    "wind": f"{current['windspeedKmph']} km/h" if units == "metric" else f"{current['windspeedMiles']} mph"
                }
                
                if detailed:
                    result["forecast"] = [
                        {
                            "date": day["date"],
                            "max": f"{day['maxtempC']}°C",
                            "min": f"{day['mintempC']}°C",
                            "condition": day["hourly"][4]["weatherDesc"][0]["value"]
                        }
                        for day in data["weather"][:3]
                    ]
                    
                return result
            except Exception as e:
                return {"error": str(e)}

        async def compare_weather(cities: list[str], metric: str = "temperature") -> Dict[str, Any]:
            """Compare weather between multiple cities."""
            if not cities or len(cities) > 5:
                return {"error": "Provide 1-5 cities"}
            
            comparisons = []
            for city in cities:
                weather = await get_weather(city)
                if "error" not in weather:
                    comparisons.append({
                        "city": city,
                        "temperature": weather["temperature"],
                        "humidity": weather["humidity"],
                        "wind": weather["wind"]
                    })
            
            # Sort by metric
            if metric in ["temperature", "humidity", "wind"]:
                comparisons.sort(
                    key=lambda x: float(x[metric].split()[0].replace("°C", "").replace("%", "")), 
                    reverse=True
                )
            
            return {"metric": metric, "cities": comparisons}

def main():
    """Main entry point for the weather MCP server."""
    # Lazy initialization - only create mcp instance when needed
    mcp = get_mcp()
    setup_tools(mcp)
    
    print("🌐 Starting weather MCP server")
    mcp.run()

if __name__ == "__main__":
    main()