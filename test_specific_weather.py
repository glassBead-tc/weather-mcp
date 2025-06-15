#!/usr/bin/env python3
import asyncio
import httpx

async def test_specific_locations():
    locations = [
        "San Francisco",
        "Paris,France", 
        "London,UK",
        "New York,NY",
        "tokyo"
    ]
    
    async with httpx.AsyncClient() as client:
        for location in locations:
            try:
                response = await client.get(f"https://wttr.in/{location}?format=j1&m=")
                print(f"\n{location}:")
                print(f"Status: {response.status_code}")
                content = response.text[:200]
                print(f"Content: {content}")
                
                if "current_condition" in content:
                    print("✅ Valid JSON response")
                else:
                    print("❌ Invalid response")
                    
            except Exception as e:
                print(f"Error for {location}: {e}")

if __name__ == "__main__":
    asyncio.run(test_specific_locations())