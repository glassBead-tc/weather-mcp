#!/usr/bin/env python3
import asyncio
import httpx

async def debug_weather_api():
    async with httpx.AsyncClient() as client:
        response = await client.get("https://wttr.in/London?format=j1&m=")
        print(f"Status: {response.status_code}")
        print(f"Headers: {response.headers}")
        print(f"Content: {response.text[:500]}...")

if __name__ == "__main__":
    asyncio.run(debug_weather_api())