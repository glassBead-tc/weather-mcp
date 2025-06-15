from typing import Dict, Any, List
import json
import time
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("simple-server")

# Simple in-memory storage
notes_storage = []

@mcp.tool()
def add_note(title: str, content: str, tags: List[str] = None) -> Dict[str, Any]:
    """Add a new note with title, content, and optional tags."""
    if not title or not content:
        return {"error": "Title and content are required"}
    
    note = {
        "id": len(notes_storage) + 1,
        "title": title,
        "content": content,
        "tags": tags or [],
        "created_at": time.time()
    }
    notes_storage.append(note)
    return {"success": True, "note": note}

@mcp.tool()
def list_notes(tag_filter: str = None) -> Dict[str, Any]:
    """List all notes, optionally filtered by tag."""
    if tag_filter:
        filtered_notes = [note for note in notes_storage if tag_filter in note.get("tags", [])]
        return {"notes": filtered_notes, "count": len(filtered_notes), "filter": tag_filter}
    
    return {"notes": notes_storage, "count": len(notes_storage)}

@mcp.tool()
def search_notes(query: str) -> Dict[str, Any]:
    """Search notes by title or content."""
    if not query:
        return {"error": "Search query is required"}
    
    query_lower = query.lower()
    matching_notes = [
        note for note in notes_storage 
        if query_lower in note["title"].lower() or query_lower in note["content"].lower()
    ]
    
    return {"notes": matching_notes, "count": len(matching_notes), "query": query}

if __name__ == "__main__":
    mcp.run(transport="shttp")