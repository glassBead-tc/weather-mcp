#!/usr/bin/env python3
"""
Quick test of the weather server functionality
"""
import asyncio
import sys
import os
sys.path.append('src')

from weather_server import get_weather

async def test_weather():
    print("Testing weather server...")
    
    # Test basic weather lookup
    result = await get_weather("London")
    print(f"London weather: {result}")
    
    # Test with different units
    result = await get_weather("New York", units="imperial")
    print(f"New York weather (imperial): {result}")
    
    # Test detailed forecast
    result = await get_weather("Tokyo", detailed=True)
    print(f"Tokyo detailed: {result}")

if __name__ == "__main__":
    asyncio.run(test_weather())