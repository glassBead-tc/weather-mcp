#!/usr/bin/env python3
"""
Direct deployment health check for weather-mcp server
Attempts to check the deployment directly using known patterns
"""

import asyncio
import httpx
import json
from datetime import datetime

async def check_deployment_health():
    """Check deployment health directly."""
    
    # Known deployment patterns for Smithery
    potential_urls = [
        "https://weather-mcp-glassbead-tc.smithery.ai",
        "https://glassbead-tc-weather-mcp.smithery.ai",
        "https://weather-mcp.glassbead-tc.smithery.ai",
        # Add more potential patterns
    ]
    
    print("🔍 Checking potential deployment URLs...")
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        for url in potential_urls:
            try:
                print(f"   Testing: {url}")
                response = await client.get(url)
                
                if response.status_code in [200, 401, 404]:
                    print(f"   ✅ Response from {url}: HTTP {response.status_code}")
                    
                    # Try to get some basic info
                    if response.status_code == 200:
                        try:
                            content = response.text[:500]  # First 500 chars
                            print(f"   📄 Content preview: {content[:100]}...")
                        except:
                            pass
                    
                    return {
                        "status": "found",
                        "url": url,
                        "status_code": response.status_code,
                        "response_time": round(response.elapsed.total_seconds() * 1000, 2)
                    }
                else:
                    print(f"   ⚠️  {url}: HTTP {response.status_code}")
                    
            except httpx.ConnectError:
                print(f"   ❌ Connection failed to {url}")
            except Exception as e:
                print(f"   ❌ Error testing {url}: {str(e)}")
    
    return {"status": "not_found", "message": "No accessible deployment URLs found"}

async def check_github_deployment_status():
    """Check GitHub deployment status via API."""
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            print("🔍 Checking GitHub deployments...")
            
            # Get deployments
            response = await client.get(
                "https://api.github.com/repos/glassBead-tc/weather-mcp/deployments",
                params={"per_page": 5}
            )
            
            if response.status_code == 200:
                deployments = response.json()
                print(f"📋 Found {len(deployments)} deployments")
                
                for i, deployment in enumerate(deployments[:3]):
                    print(f"\n🚀 Deployment #{i+1}:")
                    print(f"   ID: {deployment.get('id')}")
                    print(f"   Environment: {deployment.get('environment', 'N/A')}")
                    print(f"   Ref: {deployment.get('ref', 'N/A')}")
                    print(f"   Created: {deployment.get('created_at', 'N/A')}")
                    
                    # Get deployment status
                    status_response = await client.get(
                        f"https://api.github.com/repos/glassBead-tc/weather-mcp/deployments/{deployment['id']}/statuses"
                    )
                    
                    if status_response.status_code == 200:
                        statuses = status_response.json()
                        if statuses:
                            latest_status = statuses[0]
                            print(f"   Status: {latest_status.get('state', 'N/A')}")
                            print(f"   Description: {latest_status.get('description', 'N/A')}")
                            if latest_status.get('target_url'):
                                print(f"   Target URL: {latest_status.get('target_url')}")
                
                return {
                    "status": "success",
                    "deployments": deployments[:3]
                }
            else:
                print(f"⚠️  GitHub deployments API returned: {response.status_code}")
                return {"status": "limited", "message": f"HTTP {response.status_code}"}
                
    except Exception as e:
        print(f"❌ Error checking GitHub deployments: {str(e)}")
        return {"status": "error", "message": str(e)}

async def analyze_workflow_logs():
    """Analyze recent workflow runs for deployment clues."""
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            print("🔍 Analyzing recent workflow runs...")
            
            # Get workflow runs
            response = await client.get(
                "https://api.github.com/repos/glassBead-tc/weather-mcp/actions/runs",
                params={"per_page": 3, "status": "completed"}
            )
            
            if response.status_code == 200:
                data = response.json()
                runs = data.get("workflow_runs", [])
                
                analysis = {
                    "successful_runs": 0,
                    "failed_runs": 0,
                    "recent_success": False,
                    "transport_fix_tested": False
                }
                
                for run in runs:
                    if run.get("conclusion") == "success":
                        analysis["successful_runs"] += 1
                        if run.get("head_branch") == "fix-github-action-transport":
                            analysis["transport_fix_tested"] = True
                            if runs.index(run) == 0:  # Most recent
                                analysis["recent_success"] = True
                    else:
                        analysis["failed_runs"] += 1
                    
                    print(f"   📊 {run.get('name', 'Unknown')}: {run.get('conclusion', 'N/A')} ({run.get('head_branch', 'N/A')})")
                
                print(f"\n📈 Workflow Analysis:")
                print(f"   ✅ Successful runs: {analysis['successful_runs']}")
                print(f"   ❌ Failed runs: {analysis['failed_runs']}")
                print(f"   🔧 Transport fix tested: {analysis['transport_fix_tested']}")
                print(f"   🎯 Recent success: {analysis['recent_success']}")
                
                return analysis
                
    except Exception as e:
        print(f"❌ Error analyzing workflows: {str(e)}")
        return {"status": "error", "message": str(e)}

async def main():
    """Main function."""
    
    print("🌤️  Weather-MCP Direct Deployment Check")
    print("=" * 50)
    print(f"⏰ Timestamp: {datetime.now().isoformat()}")
    print()
    
    # Check GitHub workflows
    workflow_analysis = await analyze_workflow_logs()
    print()
    
    # Check GitHub deployments
    deployment_result = await check_github_deployment_status()
    print()
    
    # Check direct deployment health
    health_result = await check_deployment_health()
    print()
    
    # Final summary
    print("📋 COMPREHENSIVE DEPLOYMENT STATUS")
    print("=" * 40)
    
    # Transport fix assessment
    if isinstance(workflow_analysis, dict) and workflow_analysis.get("transport_fix_tested"):
        print("✅ Transport Fix: streamable-http transport has been tested")
        if workflow_analysis.get("recent_success"):
            print("✅ Latest Status: Recent workflow run succeeded")
        else:
            print("⚠️  Latest Status: Recent workflow had issues")
    else:
        print("❓ Transport Fix: Unable to determine test status")
    
    # Deployment health
    if health_result.get("status") == "found":
        print(f"✅ Deployment Health: Server accessible at {health_result['url']}")
        print(f"   Response time: {health_result['response_time']}ms")
        print(f"   HTTP Status: {health_result['status_code']}")
    else:
        print("❌ Deployment Health: No accessible deployment found")
    
    # Tool detection (would need API access to verify)
    print("❓ Tool Detection: Requires API access to verify 4 expected tools")
    print("   Expected tools: ping, health_check, get_weather, compare_weather")
    
    print()
    print("🔧 TROUBLESHOOTING RECOMMENDATIONS:")
    
    if not workflow_analysis.get("recent_success"):
        print("1. Check GitHub Actions for recent failures")
        
    if health_result.get("status") != "found":
        print("2. Verify Smithery deployment completed successfully")
        print("3. Check if deployment URL is correctly configured")
        
    print("4. Test MCP server locally to ensure tools are properly registered")
    print("5. Verify streamable-http transport is working correctly")
    
    print()
    print("🔗 Key Links:")
    print("   GitHub Actions: https://github.com/glassBead-tc/weather-mcp/actions")
    print("   Smithery Dashboard: https://smithery.ai/server/@glassBead-tc/weather-mcp/deployments")

if __name__ == "__main__":
    asyncio.run(main())