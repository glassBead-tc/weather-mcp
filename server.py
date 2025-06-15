from typing import Dict, Any
from datetime import datetime
from urllib.parse import quote
import httpx
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("weather-server")
WEATHER_API = "https://wttr.in"

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
        "tools": ["ping", "health_check", "get_weather", "compare_weather"]
    }

@mcp.tool()
async def get_weather(city: str, units: str = "metric", detailed: bool = False) -> Dict[str, Any]:
    """Get current weather for a city."""
    if not city:
        return {"error": "City name required"}
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{WEATHER_API}/{quote(city)}",
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

@mcp.tool()
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

if __name__ == "__main__":
    mcp.run(transport="streamable-http")