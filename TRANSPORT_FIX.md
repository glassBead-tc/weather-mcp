# Smithery Transport Configuration Fix

## Issue Analysis

**Problem**: Tool scanning timeout (MCP error -32001) on Smithery deployment

**Root Cause**: Transport configuration mismatch
- Smithery expects `streamable-http` transport for hosted servers
- Build process shows `sed -i 's/transport=\"shttp\"/transport=\"stdio\"/'` 
- This sed command changes our correct `streamable-http` to `stdio`
- `stdio` transport doesn't work for HTTP-based tool scanning

## Solution

**Fixed Configuration**:
```python
if __name__ == "__main__":
    # Smithery's build process will change "shttp" to "stdio" via sed
    # This ensures compatibility with Smithery's deployment process
    print("🌐 Starting weather MCP server")
    mcp.run(transport="shttp")
```

## Key Points

1. **Smithery Build Process**: Uses sed command to change `"shttp"` to `"stdio"` 
2. **Lazy Loading**: Already implemented to prevent timeout during tool scanning
3. **Transport Compatibility**: Code uses "shttp" which becomes "stdio" after sed

## Expected Outcome

With `stdio` transport (after sed) + lazy loading:
- ✅ Server uses stdio transport as expected by Smithery
- ✅ Tools load lazily to prevent timeouts  
- ✅ MCP protocol works correctly over stdio
- ✅ Tool scanning should complete successfully

## Testing

Deploy with this configuration to verify:
- Tool scanning completes without timeout
- All 4 tools detected (ping, health_check, get_weather, compare_weather)
- Server health checks pass