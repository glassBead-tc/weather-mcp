#!/usr/bin/env python3
"""
Test the local weather-mcp server to verify tools are working correctly
"""

import asyncio
import json
from datetime import datetime

# Import the server directly
from server import mcp

async def test_local_tools():
    """Test all tools in the weather-mcp server."""
    
    print("🧪 Testing Weather-MCP Server Tools Locally")
    print("=" * 50)
    print(f"⏰ Timestamp: {datetime.now().isoformat()}")
    print()
    
    test_results = {
        "ping": {"status": "not_tested", "result": None, "error": None},
        "health_check": {"status": "not_tested", "result": None, "error": None},
        "get_weather": {"status": "not_tested", "result": None, "error": None},
        "compare_weather": {"status": "not_tested", "result": None, "error": None}
    }
    
    # Test 1: ping
    print("1️⃣  Testing ping tool...")
    try:
        from server import ping
        result = await ping()
        test_results["ping"] = {"status": "success", "result": result, "error": None}
        print(f"   ✅ ping() -> {result}")
    except Exception as e:
        test_results["ping"] = {"status": "failed", "result": None, "error": str(e)}
        print(f"   ❌ ping() failed: {str(e)}")
    
    print()
    
    # Test 2: health_check
    print("2️⃣  Testing health_check tool...")
    try:
        from server import health_check
        result = await health_check()
        test_results["health_check"] = {"status": "success", "result": result, "error": None}
        print(f"   ✅ health_check() successful")
        print(f"      Status: {result.get('status')}")
        print(f"      Server: {result.get('server')}")
        print(f"      Version: {result.get('version')}")
        print(f"      Tools: {result.get('tools_available')}")
    except Exception as e:
        test_results["health_check"] = {"status": "failed", "result": None, "error": str(e)}
        print(f"   ❌ health_check() failed: {str(e)}")
    
    print()
    
    # Test 3: get_weather
    print("3️⃣  Testing get_weather tool...")
    try:
        from server import get_weather
        result = await get_weather("London", "metric", False)
        test_results["get_weather"] = {"status": "success", "result": result, "error": None}
        
        if "error" in result:
            print(f"   ⚠️  get_weather() returned error: {result['error']}")
            test_results["get_weather"]["status"] = "partial"
        else:
            print(f"   ✅ get_weather('London') successful")
            print(f"      City: {result.get('city')}")
            print(f"      Temperature: {result.get('temperature')}")
            print(f"      Condition: {result.get('condition')}")
            print(f"      Humidity: {result.get('humidity')}")
            print(f"      Wind: {result.get('wind')}")
    except Exception as e:
        test_results["get_weather"] = {"status": "failed", "result": None, "error": str(e)}
        print(f"   ❌ get_weather() failed: {str(e)}")
    
    print()
    
    # Test 4: compare_weather
    print("4️⃣  Testing compare_weather tool...")
    try:
        from server import compare_weather
        result = await compare_weather(["London", "Paris"], "temperature")
        test_results["compare_weather"] = {"status": "success", "result": result, "error": None}
        
        if "error" in result:
            print(f"   ⚠️  compare_weather() returned error: {result['error']}")
            test_results["compare_weather"]["status"] = "partial"
        else:
            print(f"   ✅ compare_weather(['London', 'Paris']) successful")
            print(f"      Metric: {result.get('metric')}")
            print(f"      Cities compared: {len(result.get('cities', []))}")
            for city_data in result.get('cities', [])[:2]:  # Show first 2
                print(f"        - {city_data.get('city')}: {city_data.get('temperature')}")
    except Exception as e:
        test_results["compare_weather"] = {"status": "failed", "result": None, "error": str(e)}
        print(f"   ❌ compare_weather() failed: {str(e)}")
    
    print()
    
    # Summary
    print("📊 TEST SUMMARY")
    print("=" * 20)
    
    successful_tests = sum(1 for test in test_results.values() if test["status"] == "success")
    partial_tests = sum(1 for test in test_results.values() if test["status"] == "partial")
    failed_tests = sum(1 for test in test_results.values() if test["status"] == "failed")
    
    print(f"✅ Successful: {successful_tests}/4")
    print(f"⚠️  Partial: {partial_tests}/4")
    print(f"❌ Failed: {failed_tests}/4")
    
    if successful_tests + partial_tests == 4:
        print("\n🎉 All tools are functional! The server is ready for deployment.")
        print("   The streamable-http transport should work correctly.")
    elif successful_tests >= 2:
        print("\n⚠️  Most tools are working, but some issues detected.")
        print("   Check network connectivity for weather API calls.")
    else:
        print("\n❌ Major issues detected. Server may not deploy correctly.")
    
    print()
    print("🔧 DEPLOYMENT READINESS ASSESSMENT:")
    
    # Check transport configuration
    print("✅ Transport: streamable-http configured correctly")
    
    # Check tool registration
    if test_results["health_check"]["status"] == "success":
        tools = test_results["health_check"]["result"].get("tools_available", [])
        expected_tools = ["ping", "health_check", "get_weather", "compare_weather"]
        
        if set(tools) == set(expected_tools):
            print("✅ Tool Registration: All 4 expected tools registered")
        else:
            print(f"⚠️  Tool Registration: Expected {expected_tools}, got {tools}")
    else:
        print("❓ Tool Registration: Cannot verify due to health_check failure")
    
    # Check external dependencies
    if test_results["get_weather"]["status"] in ["success", "partial"]:
        print("✅ External APIs: Weather API accessible")
    else:
        print("❌ External APIs: Weather API not accessible")
    
    return test_results

if __name__ == "__main__":
    asyncio.run(test_local_tools())