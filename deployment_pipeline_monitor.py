#!/usr/bin/env python3
"""
GitHub + Smithery Deployment Pipeline Monitor MCP Server

This server provides comprehensive monitoring of the entire deployment pipeline:
- GitHub repository status and workflow monitoring  
- Smithery deployment status and health checks
- Real-time pipeline monitoring with progress updates
- Integration tools for automated deployment workflows

Usage with environment variables:
export GITHUB_TOKEN=your_github_token
export SMITHERY_API_KEY=your_smithery_api_key
"""

import asyncio
import json
import httpx
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from urllib.parse import quote
from mcp.server.fastmcp import FastMCP

# Configuration from environment variables
import os
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
SMITHERY_API_KEY = os.getenv("SMITHERY_API_KEY", "")

mcp = FastMCP("deployment-pipeline-monitor")

@mcp.tool()
async def ping() -> str:
    """Simple ping tool to test server responsiveness."""
    return "pong"

@mcp.tool()
async def health_check() -> Dict[str, Any]:
    """Health check for the deployment monitor server."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "server": "deployment-pipeline-monitor",
        "github_configured": bool(GITHUB_TOKEN),
        "smithery_configured": bool(SMITHERY_API_KEY),
        "tools": [
            "ping",
            "health_check", 
            "check_github_repo_status",
            "check_smithery_deployment",
            "monitor_deployment_pipeline",
            "get_deployment_summary",
            "list_my_smithery_servers"
        ]
    }

@mcp.tool()
async def check_github_repo_status(
    owner: str,
    repo: str,
    branch: Optional[str] = None
) -> Dict[str, Any]:
    """Check GitHub repository status including recent workflow runs."""
    
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Get repository info
            repo_response = await client.get(
                f"https://api.github.com/repos/{owner}/{repo}",
                headers=headers
            )
            repo_data = repo_response.json()
            
            # Get recent workflow runs
            runs_response = await client.get(
                f"https://api.github.com/repos/{owner}/{repo}/actions/runs",
                headers=headers,
                params={"per_page": 5, "branch": branch} if branch else {"per_page": 5}
            )
            runs_data = runs_response.json()
            
            # Get branch info if specified
            branch_info = None
            if branch:
                try:
                    branch_response = await client.get(
                        f"https://api.github.com/repos/{owner}/{repo}/branches/{branch}",
                        headers=headers
                    )
                    branch_info = branch_response.json()
                except:
                    pass
            
            workflow_runs = []
            for run in runs_data.get("workflow_runs", []):
                workflow_runs.append({
                    "id": run["id"],
                    "name": run["name"],
                    "status": run["status"],
                    "conclusion": run["conclusion"],
                    "created_at": run["created_at"],
                    "updated_at": run["updated_at"],
                    "head_branch": run["head_branch"],
                    "event": run["event"],
                    "html_url": run["html_url"]
                })
            
            return {
                "repository": f"{owner}/{repo}",
                "default_branch": repo_data.get("default_branch"),
                "current_branch": branch,
                "branch_exists": branch_info is not None if branch else True,
                "latest_commit": branch_info.get("commit", {}).get("sha") if branch_info else None,
                "workflow_runs": workflow_runs,
                "total_runs": runs_data.get("total_count", 0),
                "repository_url": repo_data["html_url"]
            }
            
    except httpx.HTTPStatusError as e:
        return {"error": f"GitHub API error: {e.response.status_code} - {e.response.text}"}
    except Exception as e:
        return {"error": f"GitHub API error: {str(e)}"}

@mcp.tool() 
async def check_smithery_deployment(
    owner: str,
    repo: str
) -> Dict[str, Any]:
    """Check Smithery deployment status for a GitHub repository."""
    
    headers = {
        "Authorization": f"Bearer {SMITHERY_API_KEY}",
        "Content-Type": "application/json"
    }
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Search for servers from this repository
            response = await client.get(
                "https://registry.smithery.ai/servers",
                headers=headers,
                params={"q": f"owner:{owner} repo:{repo}"}
            )
            data = response.json()
            
            if not data.get("servers"):
                return {
                    "deployed": False,
                    "repository": f"{owner}/{repo}",
                    "message": "No servers found in Smithery registry"
                }
            
            servers = []
            for server in data["servers"]:
                # Get detailed server info
                detail_response = await client.get(
                    f"https://registry.smithery.ai/servers/{server['qualifiedName']}",
                    headers=headers
                )
                details = detail_response.json()
                
                # Health check if deployed
                health_status = {"status": "not_deployed", "healthy": False}
                deployment_url = details.get("deploymentUrl")
                
                if deployment_url:
                    try:
                        health_response = await client.get(deployment_url, timeout=5.0)
                        health_status = {
                            "status": "healthy" if health_response.status_code in [200, 401] else "unhealthy",
                            "healthy": health_response.status_code in [200, 401],  # 401 is OK (auth required)
                            "status_code": health_response.status_code,
                            "response_time_ms": round(health_response.elapsed.total_seconds() * 1000, 2)
                        }
                    except Exception as e:
                        health_status = {
                            "status": "error",
                            "healthy": False,
                            "error": str(e)
                        }
                
                servers.append({
                    "qualified_name": server["qualifiedName"],
                    "display_name": server["displayName"],
                    "description": server.get("description", ""),
                    "deployment_url": deployment_url,
                    "remote": details.get("remote", False),
                    "use_count": server.get("useCount", 0),
                    "tools_count": len(details.get("tools", [])) if details.get("tools") else 0,
                    "security_scan_passed": details.get("security", {}).get("scanPassed") if details.get("security") else None,
                    "health_status": health_status,
                    "homepage": server.get("homepage"),
                    "created_at": server.get("createdAt")
                })
            
            deployed_servers = [s for s in servers if s["deployment_url"]]
            healthy_servers = [s for s in servers if s["health_status"]["healthy"]]
            
            return {
                "deployed": len(deployed_servers) > 0,
                "repository": f"{owner}/{repo}",
                "servers": servers,
                "summary": {
                    "total_servers": len(servers),
                    "deployed_servers": len(deployed_servers),
                    "healthy_servers": len(healthy_servers),
                    "total_tools": sum(s["tools_count"] for s in servers),
                    "total_usage": sum(s["use_count"] for s in servers)
                }
            }
            
    except Exception as e:
        return {"error": f"Smithery API error: {str(e)}"}

@mcp.tool()
async def monitor_deployment_pipeline(
    owner: str,
    repo: str,
    branch: Optional[str] = None,
    check_interval_seconds: int = 30,
    max_duration_minutes: int = 60
) -> Dict[str, Any]:
    """Monitor the complete deployment pipeline from GitHub to Smithery with real-time updates."""
    
    start_time = datetime.now()
    max_duration = timedelta(minutes=max_duration_minutes)
    timeline = []
    
    def add_timeline_event(event_type: str, message: str, data: Dict = None):
        timeline.append({
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "message": message,
            "data": data or {}
        })
    
    add_timeline_event("start", f"Starting pipeline monitoring for {owner}/{repo}")
    
    while datetime.now() - start_time < max_duration:
        # Check GitHub status
        github_status = await check_github_repo_status(owner, repo, branch)
        
        # Check Smithery status
        smithery_status = await check_smithery_deployment(owner, repo)
        
        # Analyze current state
        current_state = {
            "github": {
                "has_recent_activity": len(github_status.get("workflow_runs", [])) > 0,
                "latest_run_status": None,
                "latest_run_conclusion": None
            },
            "smithery": {
                "deployed": smithery_status.get("deployed", False),
                "healthy_servers": smithery_status.get("summary", {}).get("healthy_servers", 0)
            }
        }
        
        # Check latest workflow run
        if github_status.get("workflow_runs"):
            latest_run = github_status["workflow_runs"][0]
            current_state["github"]["latest_run_status"] = latest_run["status"]
            current_state["github"]["latest_run_conclusion"] = latest_run["conclusion"]
            
            # Log workflow status changes
            if latest_run["status"] == "completed":
                if latest_run["conclusion"] == "success":
                    add_timeline_event("github_success", "GitHub workflow completed successfully", {
                        "run_id": latest_run["id"],
                        "url": latest_run["html_url"]
                    })
                else:
                    add_timeline_event("github_failure", f"GitHub workflow failed: {latest_run['conclusion']}", {
                        "run_id": latest_run["id"],
                        "url": latest_run["html_url"]
                    })
        
        # Log Smithery status
        if smithery_status.get("deployed"):
            healthy_count = current_state["smithery"]["healthy_servers"]
            add_timeline_event("smithery_status", f"Smithery: {healthy_count} healthy servers deployed")
        
        # Check for success condition
        if (current_state["github"]["latest_run_status"] == "completed" and
            current_state["github"]["latest_run_conclusion"] == "success" and
            current_state["smithery"]["deployed"] and
            current_state["smithery"]["healthy_servers"] > 0):
            
            add_timeline_event("pipeline_success", "✅ Complete pipeline success!")
            
            return {
                "status": "success",
                "message": "Pipeline monitoring completed successfully",
                "duration_minutes": round((datetime.now() - start_time).total_seconds() / 60, 2),
                "final_state": {
                    "github": github_status,
                    "smithery": smithery_status
                },
                "timeline": timeline
            }
        
        # Check for failure condition
        if (current_state["github"]["latest_run_status"] == "completed" and
            current_state["github"]["latest_run_conclusion"] not in ["success", None]):
            
            add_timeline_event("pipeline_failure", f"❌ Pipeline failed at GitHub: {current_state['github']['latest_run_conclusion']}")
            
            return {
                "status": "failed",
                "message": f"Pipeline failed: GitHub workflow {current_state['github']['latest_run_conclusion']}",
                "duration_minutes": round((datetime.now() - start_time).total_seconds() / 60, 2),
                "final_state": {
                    "github": github_status,
                    "smithery": smithery_status
                },
                "timeline": timeline
            }
        
        # Wait before next check
        await asyncio.sleep(check_interval_seconds)
    
    add_timeline_event("timeout", f"Monitoring timed out after {max_duration_minutes} minutes")
    
    return {
        "status": "timeout",
        "message": f"Pipeline monitoring timed out after {max_duration_minutes} minutes",
        "duration_minutes": max_duration_minutes,
        "final_state": {
            "github": github_status,
            "smithery": smithery_status
        },
        "timeline": timeline
    }

@mcp.tool()
async def get_deployment_summary(owner: str, repo: str) -> Dict[str, Any]:
    """Get a comprehensive deployment summary for a repository."""
    
    github_status = await check_github_repo_status(owner, repo)
    smithery_status = await check_smithery_deployment(owner, repo)
    
    # Overall health assessment
    pipeline_healthy = (
        len(github_status.get("workflow_runs", [])) > 0 and
        github_status.get("workflow_runs", [{}])[0].get("conclusion") == "success" and
        smithery_status.get("deployed", False) and
        smithery_status.get("summary", {}).get("healthy_servers", 0) > 0
    )
    
    return {
        "repository": f"{owner}/{repo}",
        "timestamp": datetime.now().isoformat(),
        "pipeline_healthy": pipeline_healthy,
        "github": github_status,
        "smithery": smithery_status,
        "recommendations": _generate_recommendations(github_status, smithery_status)
    }

@mcp.tool()
async def list_my_smithery_servers() -> Dict[str, Any]:
    """List all your servers in the Smithery registry."""
    
    headers = {
        "Authorization": f"Bearer {SMITHERY_API_KEY}",
        "Content-Type": "application/json"
    }
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                "https://registry.smithery.ai/servers",
                headers=headers,
                params={"pageSize": 50}  # Get more servers
            )
            data = response.json()
            
            servers = []
            for server in data.get("servers", []):
                # Get detailed info for each server
                detail_response = await client.get(
                    f"https://registry.smithery.ai/servers/{server['qualifiedName']}",
                    headers=headers
                )
                details = detail_response.json()
                
                servers.append({
                    "qualified_name": server["qualifiedName"],
                    "display_name": server["displayName"],
                    "description": server.get("description", ""),
                    "deployment_url": details.get("deploymentUrl"),
                    "remote": details.get("remote", False),
                    "use_count": server.get("useCount", 0),
                    "tools_count": len(details.get("tools", [])),
                    "homepage": server.get("homepage"),
                    "created_at": server.get("createdAt")
                })
            
            deployed_servers = [s for s in servers if s["deployment_url"]]
            
            return {
                "total_servers": len(servers),
                "deployed_servers": len(deployed_servers),
                "total_tools": sum(s["tools_count"] for s in servers),
                "total_usage": sum(s["use_count"] for s in servers),
                "servers": servers
            }
            
    except Exception as e:
        return {"error": f"Smithery API error: {str(e)}"}

def _generate_recommendations(github_status: Dict, smithery_status: Dict) -> List[str]:
    """Generate recommendations based on current deployment status."""
    recommendations = []
    
    # GitHub recommendations
    if not github_status.get("workflow_runs"):
        recommendations.append("Consider setting up GitHub Actions for automated testing and deployment")
    elif github_status.get("workflow_runs"):
        latest_run = github_status["workflow_runs"][0]
        if latest_run.get("conclusion") == "failure":
            recommendations.append(f"Fix failing GitHub workflow: {latest_run.get('html_url')}")
    
    # Smithery recommendations
    if not smithery_status.get("deployed"):
        recommendations.append("Deploy your server to Smithery for remote access")
    elif smithery_status.get("deployed"):
        summary = smithery_status.get("summary", {})
        if summary.get("healthy_servers", 0) == 0:
            recommendations.append("Check server health - no healthy servers detected")
        if summary.get("total_tools", 0) == 0:
            recommendations.append("Server deployed but no tools detected - check tool registration")
    
    return recommendations

if __name__ == "__main__":
    mcp.run(transport="streamable-http")