#!/usr/bin/env python3
"""
Quick deployment status checker for weather-mcp server
This script checks the Smithery deployment without requiring API keys for basic info
"""

import asyncio
import httpx
import json
from datetime import datetime

async def check_smithery_deployment_public():
    """Check public Smithery deployment info for weather-mcp server."""
    
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            # Try direct access to the known deployment
            print("🔍 Checking Smithery deployment status...")
            
            # Check the public registry for glassBead-tc servers
            response = await client.get(
                "https://registry.smithery.ai/servers",
                params={"q": "glassBead-tc"}
            )
            
            if response.status_code == 200:
                data = response.json()
                servers = data.get("servers", [])
                
                weather_servers = [s for s in servers if "weather" in s.get("displayName", "").lower() or "weather" in s.get("qualifiedName", "").lower()]
                
                print(f"📊 Found {len(servers)} servers for glassBead-tc")
                print(f"🌤️  Found {len(weather_servers)} weather-related servers")
                
                for server in weather_servers:
                    print(f"\n🌡️  Server: {server.get('qualifiedName', 'Unknown')}")
                    print(f"   Display Name: {server.get('displayName', 'N/A')}")
                    print(f"   Description: {server.get('description', 'N/A')}")
                    print(f"   Use Count: {server.get('useCount', 0)}")
                    print(f"   Created: {server.get('createdAt', 'N/A')}")
                    
                    # Try to get detailed info
                    try:
                        detail_response = await client.get(
                            f"https://registry.smithery.ai/servers/{server['qualifiedName']}"
                        )
                        if detail_response.status_code == 200:
                            details = detail_response.json()
                            deployment_url = details.get("deploymentUrl")
                            tools = details.get("tools", [])
                            
                            print(f"   Deployment URL: {deployment_url or 'Not deployed'}")
                            print(f"   Tools Count: {len(tools)}")
                            
                            if tools:
                                print("   Available Tools:")
                                for tool in tools:
                                    print(f"     - {tool.get('name', 'Unknown')}: {tool.get('description', 'No description')}")
                            
                            # Test deployment health if URL exists
                            if deployment_url:
                                print("   🔄 Testing deployment health...")
                                try:
                                    health_response = await client.get(deployment_url, timeout=10.0)
                                    status_code = health_response.status_code
                                    
                                    if status_code in [200, 401]:  # 401 is OK (auth required)
                                        print(f"   ✅ Deployment is healthy (HTTP {status_code})")
                                        print(f"   ⏱️  Response time: {round(health_response.elapsed.total_seconds() * 1000, 2)}ms")
                                    else:
                                        print(f"   ⚠️  Deployment responded with HTTP {status_code}")
                                        
                                except Exception as e:
                                    print(f"   ❌ Health check failed: {str(e)}")
                            else:
                                print("   ⚠️  No deployment URL found")
                        
                    except Exception as e:
                        print(f"   ❌ Failed to get detailed info: {str(e)}")
                
                return {
                    "status": "success",
                    "total_servers": len(servers),
                    "weather_servers": len(weather_servers),
                    "servers": weather_servers
                }
            else:
                print(f"❌ Registry API returned status code: {response.status_code}")
                return {"status": "error", "message": f"HTTP {response.status_code}"}
                
    except Exception as e:
        print(f"❌ Error checking deployment: {str(e)}")
        return {"status": "error", "message": str(e)}

async def check_github_workflows():
    """Check recent GitHub workflow status (public API)."""
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            print("🔍 Checking GitHub workflow status...")
            
            # Get recent workflow runs (public API)
            response = await client.get(
                "https://api.github.com/repos/glassBead-tc/weather-mcp/actions/runs",
                params={"per_page": 5}
            )
            
            if response.status_code == 200:
                data = response.json()
                runs = data.get("workflow_runs", [])
                
                print(f"📋 Found {len(runs)} recent workflow runs")
                
                for i, run in enumerate(runs[:3]):  # Show latest 3
                    print(f"\n🔄 Run #{i+1}:")
                    print(f"   Name: {run.get('name', 'Unknown')}")
                    print(f"   Status: {run.get('status', 'Unknown')}")
                    print(f"   Conclusion: {run.get('conclusion', 'N/A')}")
                    print(f"   Branch: {run.get('head_branch', 'Unknown')}")
                    print(f"   Created: {run.get('created_at', 'N/A')}")
                    print(f"   URL: {run.get('html_url', 'N/A')}")
                
                return {
                    "status": "success",
                    "total_runs": data.get("total_count", 0),
                    "recent_runs": runs[:5]
                }
            else:
                print(f"⚠️  GitHub API returned status code: {response.status_code}")
                if response.status_code == 403:
                    print("   This might be due to rate limiting or private repository")
                return {"status": "limited", "message": f"HTTP {response.status_code}"}
                
    except Exception as e:
        print(f"❌ Error checking GitHub: {str(e)}")
        return {"status": "error", "message": str(e)}

async def main():
    """Main deployment check function."""
    
    print("🚀 Weather-MCP Deployment Status Check")
    print("=" * 50)
    print(f"⏰ Timestamp: {datetime.now().isoformat()}")
    print()
    
    # Check GitHub workflows
    github_result = await check_github_workflows()
    print()
    
    # Check Smithery deployment  
    smithery_result = await check_smithery_deployment_public()
    print()
    
    # Summary
    print("📋 DEPLOYMENT SUMMARY")
    print("=" * 30)
    
    # GitHub summary
    if github_result["status"] == "success" and github_result["recent_runs"]:
        latest_run = github_result["recent_runs"][0]
        if latest_run["status"] == "completed" and latest_run["conclusion"] == "success":
            print("✅ GitHub: Latest workflow successful")
        else:
            print(f"⚠️  GitHub: Latest workflow {latest_run['status']} ({latest_run.get('conclusion', 'N/A')})")
    else:
        print("❓ GitHub: Status unclear (rate limited or error)")
    
    # Smithery summary
    if smithery_result["status"] == "success":
        weather_count = smithery_result["weather_servers"]
        if weather_count > 0:
            print(f"✅ Smithery: {weather_count} weather server(s) deployed")
            
            # Check for expected tools
            for server in smithery_result["servers"]:
                qualified_name = server.get("qualifiedName", "")
                if "weather" in qualified_name.lower():
                    print(f"   📡 Server: {qualified_name}")
                    break
        else:
            print("❌ Smithery: No weather servers found")
    else:
        print("❌ Smithery: Could not check deployment status")
    
    print()
    print("🔗 Direct Links:")
    print("   GitHub Repository: https://github.com/glassBead-tc/weather-mcp")
    print("   Smithery Registry: https://smithery.ai/server/@glassBead-tc/weather-mcp")
    print("   Deployment Dashboard: https://smithery.ai/server/@glassBead-tc/weather-mcp/deployments")

if __name__ == "__main__":
    asyncio.run(main())