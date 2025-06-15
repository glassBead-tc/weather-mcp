"""
Weather MCP Server HTTP Transport
FastAPI wrapper for Smithery deployment with HTTP transport
"""
from fastapi import FastAPI, Request, Response
from fastapi.responses import StreamingResponse
import uvicorn
import json
import asyncio
from typing import Dict, Any
import sys
import os

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Import real weather tools
from weather_tools import get_weather, get_weather_alerts, compare_weather

# Create FastAPI app
app = FastAPI(
    title="Weather MCP Server",
    description="HTTP transport for Weather MCP Server",
    version="1.0.0"
)

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"status": "Weather MCP Server Running", "version": "1.0.0"}

@app.post("/mcp")
@app.get("/mcp")
async def mcp_endpoint(request: Request):
    """
    Streamable HTTP transport endpoint for MCP protocol.
    Handles both GET and POST requests as per 2025 MCP specification.
    """
    if request.method == "GET":
        # Handle Server-Sent Events for streaming
        async def event_stream():
            # SSE implementation for compatibility
            yield "data: {\"status\": \"connected\"}\n\n"
        
        return StreamingResponse(event_stream(), media_type="text/event-stream")
    
    elif request.method == "POST":
        # Handle JSON-RPC messages
        try:
            body = await request.body()
            json_data = json.loads(body)
            
            # Route to appropriate MCP handler based on method
            method = json_data.get("method", "")
            
            if method == "initialize":
                response = {
                    "jsonrpc": "2.0",
                    "id": json_data.get("id"),
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {
                            "tools": {}
                        },
                        "serverInfo": {
                            "name": "weather-server",
                            "version": "1.0.0"
                        }
                    }
                }
            elif method == "tools/list":
                response = {
                    "jsonrpc": "2.0",
                    "id": json_data.get("id"),
                    "result": {
                        "tools": [
                            {
                                "name": "get_weather",
                                "description": "Get current weather for a city",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {
                                        "city": {"type": "string"},
                                        "units": {"type": "string", "default": "metric"},
                                        "detailed": {"type": "boolean", "default": False}
                                    },
                                    "required": ["city"]
                                }
                            },
                            {
                                "name": "get_weather_alerts", 
                                "description": "Get weather alerts and warnings for a city",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {
                                        "city": {"type": "string"},
                                        "severity": {"type": "string", "default": "all"}
                                    },
                                    "required": ["city"]
                                }
                            },
                            {
                                "name": "compare_weather",
                                "description": "Compare weather between multiple cities", 
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {
                                        "cities": {"type": "array", "items": {"type": "string"}},
                                        "metric": {"type": "string", "default": "temperature"}
                                    },
                                    "required": ["cities"]
                                }
                            }
                        ]
                    }
                }
            elif method == "tools/call":
                # Handle tool calls
                tool_name = json_data.get("params", {}).get("name")
                arguments = json_data.get("params", {}).get("arguments", {})
                
                try:
                    if tool_name == "get_weather":
                        result = await get_weather(**arguments)
                    elif tool_name == "get_weather_alerts":
                        result = await get_weather_alerts(**arguments)
                    elif tool_name == "compare_weather":
                        result = await compare_weather(**arguments)
                    else:
                        raise ValueError(f"Unknown tool: {tool_name}")
                    
                    response = {
                        "jsonrpc": "2.0",
                        "id": json_data.get("id"),
                        "result": {
                            "content": [
                                {
                                    "type": "text",
                                    "text": json.dumps(result, indent=2)
                                }
                            ]
                        }
                    }
                except Exception as e:
                    response = {
                        "jsonrpc": "2.0",
                        "id": json_data.get("id"),
                        "error": {
                            "code": -32603,
                            "message": f"Tool execution error: {str(e)}"
                        }
                    }
            else:
                response = {
                    "jsonrpc": "2.0",
                    "id": json_data.get("id"),
                    "error": {
                        "code": -32601,
                        "message": f"Method not found: {method}"
                    }
                }
            
            return Response(
                content=json.dumps(response),
                media_type="application/json"
            )
            
        except Exception as e:
            error_response = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32700, "message": f"Parse error: {str(e)}"}
            }
            return Response(
                content=json.dumps(error_response),
                media_type="application/json",
                status_code=400
            )

# Entry point for the server
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)