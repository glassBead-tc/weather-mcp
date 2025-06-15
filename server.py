from typing import Dict, Any
import os
import datetime
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("minimal-deps-server")

@mcp.tool()
def get_system_info() -> Dict[str, Any]:
    """Get basic system information using only built-in modules."""
    return {
        "platform": os.name,
        "current_directory": os.getcwd(),
        "environment_variables": len(os.environ),
        "python_path": os.path.dirname(os.__file__) if hasattr(os, '__file__') else "unknown"
    }

@mcp.tool()
def get_timestamp(format_type: str = "iso") -> Dict[str, Any]:
    """Get current timestamp in various formats."""
    now = datetime.datetime.now()
    
    formats = {
        "iso": now.isoformat(),
        "readable": now.strftime("%Y-%m-%d %H:%M:%S"),
        "unix": int(now.timestamp()),
        "date_only": now.strftime("%Y-%m-%d"),
        "time_only": now.strftime("%H:%M:%S")
    }
    
    if format_type in formats:
        return {"timestamp": formats[format_type], "format": format_type}
    else:
        return {"error": f"Unknown format '{format_type}'. Available: {list(formats.keys())}"}

@mcp.tool()
def calculate_days_between(start_date: str, end_date: str) -> Dict[str, Any]:
    """Calculate days between two dates (YYYY-MM-DD format)."""
    try:
        start = datetime.datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.datetime.strptime(end_date, "%Y-%m-%d")
        
        difference = end - start
        days = difference.days
        
        return {
            "start_date": start_date,
            "end_date": end_date,
            "days_difference": days,
            "weeks": round(days / 7, 2),
            "is_future": days > 0
        }
    except ValueError as e:
        return {"error": f"Invalid date format. Use YYYY-MM-DD. Error: {str(e)}"}

if __name__ == "__main__":
    mcp.run(transport="shttp")