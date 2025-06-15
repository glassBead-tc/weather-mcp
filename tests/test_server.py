#!/usr/bin/env python3
"""
Basic tests for the weather MCP server
"""

import pytest
import asyncio
from server import mcp

def test_server_initialization():
    """Test that the server initializes correctly"""
    assert mcp is not None
    assert mcp.name == "weather-server"

def test_server_has_tools():
    """Test that the server has the expected tools"""
    tools = getattr(mcp, '_tools', {})
    
    # Should have at least ping, health_check, and weather tools
    expected_tools = ['ping', 'health_check', 'get_weather', 'compare_weather']
    
    for tool in expected_tools:
        assert tool in tools, f"Missing expected tool: {tool}"

@pytest.mark.asyncio
async def test_ping_tool():
    """Test the ping tool"""
    from server import ping
    result = await ping()
    assert result == "pong"

@pytest.mark.asyncio  
async def test_health_check_tool():
    """Test the health check tool"""
    from server import health_check
    result = await health_check()
    
    assert result["status"] == "healthy"
    assert "timestamp" in result
    assert "server" in result
    assert "tools" in result

@pytest.mark.asyncio
async def test_get_weather_tool():
    """Test the get_weather tool with error handling"""
    from server import get_weather
    
    # Test with empty city (should return error)
    result = await get_weather("")
    assert "error" in result
    
    # Test with invalid city (should handle gracefully)
    result = await get_weather("NonexistentCity123")
    # Should either return valid data or an error, not crash
    assert isinstance(result, dict)

if __name__ == "__main__":
    pytest.main([__file__])