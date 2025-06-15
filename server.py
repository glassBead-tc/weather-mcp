from typing import Dict, Any, List
import json
import re
import hashlib
import base64
from urllib.parse import urlparse, parse_qs
import httpx
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("standard-deps-server")

@mcp.tool()
async def url_info(url: str) -> Dict[str, Any]:
    """Get information about a URL including parsing and basic HTTP check."""
    if not url:
        return {"error": "URL is required"}
    
    try:
        # Parse URL
        parsed = urlparse(url)
        url_info = {
            "original_url": url,
            "scheme": parsed.scheme,
            "hostname": parsed.hostname,
            "port": parsed.port,
            "path": parsed.path,
            "query_params": parse_qs(parsed.query),
            "fragment": parsed.fragment
        }
        
        # Try to get HTTP status
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.head(url)
                url_info["http_status"] = response.status_code
                url_info["content_type"] = response.headers.get("content-type", "unknown")
                url_info["server"] = response.headers.get("server", "unknown")
        except Exception as http_error:
            url_info["http_error"] = str(http_error)
        
        return url_info
        
    except Exception as e:
        return {"error": f"Failed to parse URL: {str(e)}"}

@mcp.tool()
def text_analysis(text: str) -> Dict[str, Any]:
    """Analyze text for various metrics and patterns."""
    if not text:
        return {"error": "Text is required"}
    
    # Basic metrics
    words = text.split()
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    
    # Character analysis
    char_count = len(text)
    char_count_no_spaces = len(text.replace(' ', ''))
    
    # Word analysis
    word_count = len(words)
    unique_words = len(set(word.lower() for word in words))
    avg_word_length = sum(len(word) for word in words) / word_count if word_count > 0 else 0
    
    # Find common words (excluding very short words)
    word_freq = {}
    for word in words:
        clean_word = re.sub(r'[^\w]', '', word.lower())
        if len(clean_word) > 2:  # Exclude very short words
            word_freq[clean_word] = word_freq.get(clean_word, 0) + 1
    
    most_common = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:5]
    
    return {
        "character_count": char_count,
        "character_count_no_spaces": char_count_no_spaces,
        "word_count": word_count,
        "sentence_count": len(sentences),
        "unique_words": unique_words,
        "avg_word_length": round(avg_word_length, 2),
        "most_common_words": most_common,
        "text_hash": hashlib.md5(text.encode()).hexdigest()
    }

@mcp.tool()
def encode_decode_text(text: str, operation: str = "encode", encoding: str = "base64") -> Dict[str, Any]:
    """Encode or decode text using various encodings."""
    if not text:
        return {"error": "Text is required"}
    
    if operation not in ["encode", "decode"]:
        return {"error": "Operation must be 'encode' or 'decode'"}
    
    try:
        if encoding == "base64":
            if operation == "encode":
                encoded = base64.b64encode(text.encode()).decode()
                return {"result": encoded, "operation": "base64_encode", "original_length": len(text)}
            else:  # decode
                decoded = base64.b64decode(text).decode()
                return {"result": decoded, "operation": "base64_decode", "result_length": len(decoded)}
        
        elif encoding == "url":
            from urllib.parse import quote, unquote
            if operation == "encode":
                encoded = quote(text)
                return {"result": encoded, "operation": "url_encode", "original_length": len(text)}
            else:  # decode
                decoded = unquote(text)
                return {"result": decoded, "operation": "url_decode", "result_length": len(decoded)}
        
        elif encoding == "hex":
            if operation == "encode":
                encoded = text.encode().hex()
                return {"result": encoded, "operation": "hex_encode", "original_length": len(text)}
            else:  # decode
                decoded = bytes.fromhex(text).decode()
                return {"result": decoded, "operation": "hex_decode", "result_length": len(decoded)}
        
        else:
            return {"error": f"Unsupported encoding: {encoding}. Supported: base64, url, hex"}
            
    except Exception as e:
        return {"error": f"Failed to {operation} text: {str(e)}"}

@mcp.tool()
def generate_hash(text: str, algorithm: str = "md5") -> Dict[str, Any]:
    """Generate hash of text using various algorithms."""
    if not text:
        return {"error": "Text is required"}
    
    algorithms = {
        "md5": hashlib.md5,
        "sha1": hashlib.sha1,
        "sha256": hashlib.sha256,
        "sha512": hashlib.sha512
    }
    
    if algorithm not in algorithms:
        return {"error": f"Unsupported algorithm: {algorithm}. Supported: {list(algorithms.keys())}"}
    
    try:
        hash_func = algorithms[algorithm]
        hash_value = hash_func(text.encode()).hexdigest()
        
        return {
            "text": text,
            "algorithm": algorithm,
            "hash": hash_value,
            "text_length": len(text)
        }
        
    except Exception as e:
        return {"error": f"Failed to generate hash: {str(e)}"}

if __name__ == "__main__":
    mcp.run(transport="streamable-http")