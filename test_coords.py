#!/usr/bin/env python3
import asyncio
import httpx

async def test_coordinates():
    # Try with coordinates as suggested by the API
    coords = "51.5073219,-0.1276474"  # London
    
    async with httpx.AsyncClient() as client:
        response = await client.get(f"https://wttr.in/{coords}?format=j1&m=")
        print(f"Status: {response.status_code}")
        print(f"Content: {response.text[:500]}")

if __name__ == "__main__":
    asyncio.run(test_coordinates())