# GitHub + Smithery Deployment Pipeline Monitor

A comprehensive MCP server for monitoring the entire deployment pipeline from GitHub Actions to Smithery deployment with real-time progress tracking.

## Features

- **GitHub Integration**: Monitor repository status and workflow runs
- **Smithery Integration**: Check deployment status and server health  
- **Real-time Monitoring**: Track pipeline progress with timeline events
- **Health Checks**: Test deployed servers with response time monitoring
- **Comprehensive Summaries**: Get actionable recommendations for deployment issues

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r deployment-monitor-requirements.txt
   ```

2. **Configure credentials:**
   ```bash
   cp .env.example .env
   # Edit .env with your actual tokens
   export GITHUB_TOKEN=your_github_token
   export SMITHERY_API_KEY=your_smithery_api_key
   ```

3. **Run the server:**
   ```bash
   python deployment_pipeline_monitor.py
   ```

## Tools

### `check_github_repo_status`
Monitor GitHub repository and recent workflow runs.
- `owner` (string): Repository owner
- `repo` (string): Repository name  
- `branch` (string, optional): Specific branch to check

### `check_smithery_deployment`
Check Smithery deployment status and server health.
- `owner` (string): Repository owner
- `repo` (string): Repository name

### `monitor_deployment_pipeline`
Real-time monitoring of the complete pipeline with timeline events.
- `owner` (string): Repository owner
- `repo` (string): Repository name
- `branch` (string, optional): Branch to monitor
- `check_interval_seconds` (int): How often to check (default: 30)
- `max_duration_minutes` (int): Maximum monitoring time (default: 60)

### `get_deployment_summary`
Comprehensive deployment status with recommendations.
- `owner` (string): Repository owner
- `repo` (string): Repository name

### `list_my_smithery_servers`
List all your servers in the Smithery registry.

## Example Usage

```python
# Monitor the weather-mcp deployment pipeline
await monitor_deployment_pipeline("glassBead-tc", "weather-mcp", branch="main")

# Get comprehensive status
await get_deployment_summary("glassBead-tc", "weather-mcp")

# Check specific aspects
await check_github_repo_status("glassBead-tc", "weather-mcp")
await check_smithery_deployment("glassBead-tc", "weather-mcp")
```

## Integration with Claude Desktop

Add to your MCP configuration:

```json
{
  "mcpServers": {
    "deployment-monitor": {
      "command": "python",
      "args": ["/path/to/deployment_pipeline_monitor.py"],
      "env": {
        "GITHUB_TOKEN": "your_github_token",
        "SMITHERY_API_KEY": "your_smithery_api_key"
      }
    }
  }
}
```

## What It Monitors

### GitHub
- Repository information and branches
- Workflow run status and conclusions
- Build logs and job details
- Recent activity and commit history

### Smithery  
- Server deployment status
- Health checks with response times
- Tool registration and counts
- Security scan results
- Usage analytics

### Pipeline Health
- End-to-end deployment success
- Failure detection and root cause analysis
- Timeline tracking with event history
- Actionable recommendations for fixes