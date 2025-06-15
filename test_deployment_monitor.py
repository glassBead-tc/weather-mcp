#!/usr/bin/env python3
"""Test script for the deployment monitor server"""

import asyncio
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

from deployment_monitor_server import github_api, smithery_api

async def test_apis():
    """Test both GitHub and Smithery APIs"""
    
    print("🧪 Testing GitHub API...")
    try:
        # Test with our weather-mcp repo
        runs = await github_api.get_workflow_runs("glassBead-tc", "weather-mcp", limit=3)
        print(f"✅ GitHub API: Found {len(runs)} workflow runs")
        if runs:
            latest = runs[0]
            print(f"   Latest run: {latest['status']} - {latest['conclusion']} ({latest['created_at']})")
    except Exception as e:
        print(f"❌ GitHub API error: {e}")
    
    print("\n🧪 Testing Smithery API...")
    try:
        # Test listing servers
        servers = await smithery_api.list_servers(owner="glassBead-tc", repo="weather-mcp")
        print(f"✅ Smithery API: Found {len(servers['servers'])} servers")
        
        for server in servers['servers']:
            print(f"   Server: {server['qualifiedName']} - Deployed: {server['isDeployed']}")
            
            # Test server details
            details = await smithery_api.get_server_details(server['qualifiedName'])
            deployment_url = details.get('deploymentUrl')
            if deployment_url:
                print(f"   Deployment URL: {deployment_url}")
                
                # Test health check
                health = await smithery_api.check_server_health(deployment_url)
                print(f"   Health: {health['status']} - {health.get('response_time_ms', 'N/A')}ms")
            
    except Exception as e:
        print(f"❌ Smithery API error: {e}")

if __name__ == "__main__":
    asyncio.run(test_apis())