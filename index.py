from typing import Dict, Any, List, Optional
import asyncio
import json
import time
from urllib.parse import quote
import httpx
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("complex-server")

# Configuration
WEATHER_API = "https://wttr.in"
GITHUB_API = "https://api.github.com"

# In-memory cache
cache = {}

@mcp.tool()
async def get_weather(city: str, units: str = "metric", detailed: bool = False) -> Dict[str, Any]:
    """Get current weather for a city with caching."""
    cache_key = f"weather:{city}:{units}:{detailed}"
    
    # Check cache (5 minute TTL)
    if cache_key in cache:
        cached_data, timestamp = cache[cache_key]
        if time.time() - timestamp < 300:  # 5 minutes
            return {**cached_data, "cached": True}
    
    if not city:
        return {"error": "City name required"}
    
    try:
        async with httpx.AsyncClient() as client:
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
            "wind": f"{current['windspeedKmph']} km/h" if units == "metric" else f"{current['windspeedMiles']} mph",
            "cached": False
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
        
        # Cache the result
        cache[cache_key] = (result, time.time())
        return result
        
    except Exception as e:
        return {"error": str(e)}

@mcp.tool()
async def batch_weather(cities: List[str], units: str = "metric") -> Dict[str, Any]:
    """Get weather for multiple cities concurrently."""
    if not cities or len(cities) > 10:
        return {"error": "Provide 1-10 cities"}
    
    # Use asyncio.gather for concurrent requests
    weather_tasks = [get_weather(city, units) for city in cities]
    results = await asyncio.gather(*weather_tasks, return_exceptions=True)
    
    weather_data = []
    errors = []
    
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            errors.append({"city": cities[i], "error": str(result)})
        elif "error" in result:
            errors.append({"city": cities[i], "error": result["error"]})
        else:
            weather_data.append(result)
    
    return {
        "weather_data": weather_data,
        "errors": errors,
        "total_cities": len(cities),
        "successful": len(weather_data)
    }

@mcp.tool()
async def github_user_info(username: str) -> Dict[str, Any]:
    """Get GitHub user information."""
    if not username:
        return {"error": "Username required"}
    
    cache_key = f"github:{username}"
    
    # Check cache (10 minute TTL)
    if cache_key in cache:
        cached_data, timestamp = cache[cache_key]
        if time.time() - timestamp < 600:  # 10 minutes
            return {**cached_data, "cached": True}
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{GITHUB_API}/users/{username}",
                headers={"Accept": "application/vnd.github.v3+json"}
            )
            response.raise_for_status()
            
        data = response.json()
        
        result = {
            "username": data["login"],
            "name": data.get("name"),
            "bio": data.get("bio"),
            "location": data.get("location"),
            "public_repos": data["public_repos"],
            "followers": data["followers"],
            "following": data["following"],
            "created_at": data["created_at"],
            "profile_url": data["html_url"],
            "cached": False
        }
        
        # Cache the result
        cache[cache_key] = (result, time.time())
        return result
        
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return {"error": f"User '{username}' not found"}
        return {"error": f"GitHub API error: {e.response.status_code}"}
    except Exception as e:
        return {"error": str(e)}

@mcp.tool()
async def weather_and_github_combo(city: str, username: str) -> Dict[str, Any]:
    """Get both weather and GitHub info concurrently for a location/user combo."""
    if not city or not username:
        return {"error": "Both city and username required"}
    
    # Concurrent requests
    weather_task = get_weather(city)
    github_task = github_user_info(username)
    
    weather_data, github_data = await asyncio.gather(weather_task, github_task, return_exceptions=True)
    
    result = {}
    
    if isinstance(weather_data, Exception):
        result["weather_error"] = str(weather_data)
    elif "error" in weather_data:
        result["weather_error"] = weather_data["error"]
    else:
        result["weather"] = weather_data
    
    if isinstance(github_data, Exception):
        result["github_error"] = str(github_data)
    elif "error" in github_data:
        result["github_error"] = github_data["error"]
    else:
        result["github"] = github_data
    
    return result

@mcp.tool()
def get_cache_stats() -> Dict[str, Any]:
    """Get cache statistics and status."""
    current_time = time.time()
    total_entries = len(cache)
    expired_entries = 0
    cache_types = {}
    
    for key, (data, timestamp) in cache.items():
        # Count expired entries (using 10 minute max TTL)
        if current_time - timestamp > 600:
            expired_entries += 1
        
        # Count by type
        cache_type = key.split(":")[0]
        cache_types[cache_type] = cache_types.get(cache_type, 0) + 1
    
    return {
        "total_entries": total_entries,
        "expired_entries": expired_entries,
        "active_entries": total_entries - expired_entries,
        "cache_types": cache_types,
        "cache_keys": list(cache.keys())
    }

@mcp.tool()
def clear_cache(cache_type: Optional[str] = None) -> Dict[str, Any]:
    """Clear cache entries, optionally by type."""
    global cache
    
    if cache_type:
        keys_to_remove = [key for key in cache.keys() if key.startswith(f"{cache_type}:")]
        for key in keys_to_remove:
            del cache[key]
        return {"cleared": len(keys_to_remove), "type": cache_type}
    else:
        cleared_count = len(cache)
        cache.clear()
        return {"cleared": cleared_count, "type": "all"}

if __name__ == "__main__":
    mcp.run(transport="shttp")