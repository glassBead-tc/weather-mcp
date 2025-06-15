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
    # Smithery requires streamable-http transport for hosted servers
    print("🌐 Using streamable-http transport for Smithery deployment")
    mcp.run(transport="streamable-http")
```

## Key Points

1. **Smithery is opinionated**: Requires `streamable-http` for hosted servers
2. **Lazy Loading**: Already implemented to prevent timeout during tool scanning
3. **Build Process**: Smithery's sed command needs to be avoided or corrected

## Expected Outcome

With `streamable-http` transport + lazy loading:
- ✅ Server responds to HTTP requests for tool scanning
- ✅ Tools load lazily to prevent timeouts
- ✅ MCP protocol works correctly over HTTP
- ✅ Tool scanning should complete successfully

## Testing

Deploy with this configuration to verify:
- Tool scanning completes without timeout
- All 4 tools detected (ping, health_check, get_weather, compare_weather)
- Server health checks pass