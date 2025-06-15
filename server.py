from typing import Dict, Any, List, Optional
import json
import re
import hashlib
import base64
from urllib.parse import urlparse, parse_qs
import asyncio
from datetime import datetime, timedelta
import httpx
import requests
from dateutil.parser import parse as date_parse
from dateutil.relativedelta import relativedelta
from bs4 import BeautifulSoup
from pydantic import BaseModel, ValidationError
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("complex-deps-server")

# Pydantic models for data validation
class WebPageData(BaseModel):
    url: str
    title: Optional[str] = None
    description: Optional[str] = None
    status_code: int
    content_type: str
    word_count: int
    links: List[str] = []

class DateRange(BaseModel):
    start_date: str
    end_date: str
    
    def validate_dates(self):
        try:
            start = date_parse(self.start_date)
            end = date_parse(self.end_date)
            return start, end
        except Exception as e:
            raise ValueError(f"Invalid date format: {e}")

@mcp.tool()
async def scrape_webpage(url: str, include_links: bool = False) -> Dict[str, Any]:
    """Scrape a webpage and extract structured information."""
    if not url:
        return {"error": "URL is required"}
    
    try:
        # Use both httpx and requests for demonstration
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url)
            response.raise_for_status()
        
        # Parse HTML with BeautifulSoup
        soup = BeautifulSoup(response.content, 'lxml')
        
        # Extract information
        title = soup.find('title')
        title_text = title.get_text(strip=True) if title else None
        
        description = soup.find('meta', attrs={'name': 'description'})
        description_text = description.get('content') if description else None
        
        # Get text content and word count
        text_content = soup.get_text(strip=True)
        word_count = len(text_content.split())
        
        # Extract links if requested
        links = []
        if include_links:
            link_tags = soup.find_all('a', href=True)
            links = [link['href'] for link in link_tags[:20]]  # Limit to first 20 links
        
        # Use Pydantic for validation
        try:
            webpage_data = WebPageData(
                url=url,
                title=title_text,
                description=description_text,
                status_code=response.status_code,
                content_type=response.headers.get('content-type', 'unknown'),
                word_count=word_count,
                links=links
            )
            
            return webpage_data.dict()
            
        except ValidationError as e:
            return {"error": f"Data validation failed: {e}"}
            
    except Exception as e:
        return {"error": f"Failed to scrape webpage: {str(e)}"}

@mcp.tool()
def advanced_date_calculations(date_range: Dict[str, str], operation: str = "difference") -> Dict[str, Any]:
    """Perform advanced date calculations using dateutil."""
    try:
        # Validate input with Pydantic
        range_data = DateRange(**date_range)
        start_date, end_date = range_data.validate_dates()
        
        operations = {
            "difference": lambda s, e: {
                "days": (e - s).days,
                "weeks": (e - s).days / 7,
                "months": relativedelta(e, s).months + relativedelta(e, s).years * 12,
                "years": relativedelta(e, s).years
            },
            "add_business_days": lambda s, e: {
                "result": s + timedelta(days=20),  # Example: add 20 business days
                "weekday": (s + timedelta(days=20)).strftime("%A")
            },
            "quarterly_breakdown": lambda s, e: {
                "quarters": [(s + relativedelta(months=i*3)).strftime("%Y-Q%q") 
                           for i in range(0, int((e.year - s.year) * 4) + 4)][:4]
            }
        }
        
        if operation not in operations:
            return {"error": f"Unknown operation: {operation}. Available: {list(operations.keys())}"}
        
        result = operations[operation](start_date, end_date)
        
        return {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "operation": operation,
            "result": result
        }
        
    except Exception as e:
        return {"error": f"Date calculation failed: {str(e)}"}

@mcp.tool()
async def multi_api_aggregator(urls: List[str], timeout: int = 5) -> Dict[str, Any]:
    """Make multiple API calls concurrently and aggregate results."""
    if not urls or len(urls) > 10:
        return {"error": "Provide 1-10 URLs"}
    
    async def fetch_url(session: httpx.AsyncClient, url: str) -> Dict[str, Any]:
        try:
            response = await session.get(url, timeout=timeout)
            return {
                "url": url,
                "status": response.status_code,
                "headers": dict(response.headers),
                "content_length": len(response.content),
                "response_time": response.elapsed.total_seconds() if hasattr(response, 'elapsed') else None
            }
        except Exception as e:
            return {
                "url": url,
                "error": str(e)
            }
    
    try:
        async with httpx.AsyncClient() as session:
            tasks = [fetch_url(session, url) for url in urls]
            results = await asyncio.gather(*tasks, return_exceptions=True)
        
        successful = [r for r in results if not isinstance(r, Exception) and "error" not in r]
        failed = [r for r in results if isinstance(r, Exception) or "error" in r]
        
        # Calculate aggregate metrics
        if successful:
            avg_response_time = sum(r.get("response_time", 0) for r in successful) / len(successful)
            total_content_length = sum(r.get("content_length", 0) for r in successful)
        else:
            avg_response_time = 0
            total_content_length = 0
        
        return {
            "total_urls": len(urls),
            "successful": len(successful),
            "failed": len(failed),
            "avg_response_time": round(avg_response_time, 3),
            "total_content_length": total_content_length,
            "results": results
        }
        
    except Exception as e:
        return {"error": f"Multi-API aggregation failed: {str(e)}"}

@mcp.tool()
def html_content_analysis(html: str) -> Dict[str, Any]:
    """Analyze HTML content for structure and metadata."""
    if not html:
        return {"error": "HTML content is required"}
    
    try:
        soup = BeautifulSoup(html, 'lxml')
        
        # Count different elements
        element_counts = {}
        for tag in soup.find_all():
            element_counts[tag.name] = element_counts.get(tag.name, 0) + 1
        
        # Extract metadata
        meta_tags = soup.find_all('meta')
        metadata = {}
        for meta in meta_tags:
            if meta.get('name'):
                metadata[meta['name']] = meta.get('content', '')
            elif meta.get('property'):
                metadata[meta['property']] = meta.get('content', '')
        
        # Find all links and images
        links = [a.get('href') for a in soup.find_all('a', href=True)]
        images = [img.get('src') for img in soup.find_all('img', src=True)]
        
        # Text analysis
        text_content = soup.get_text(strip=True)
        text_stats = {
            "character_count": len(text_content),
            "word_count": len(text_content.split()),
            "paragraph_count": len(soup.find_all('p')),
            "heading_count": len(soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']))
        }
        
        return {
            "element_counts": element_counts,
            "metadata": metadata,
            "links_count": len(links),
            "images_count": len(images),
            "text_stats": text_stats,
            "structure_depth": max(len(tag.find_parents()) for tag in soup.find_all()) if soup.find_all() else 0
        }
        
    except Exception as e:
        return {"error": f"HTML analysis failed: {str(e)}"}

@mcp.tool()
def validate_data_structure(data: Dict[str, Any], schema_type: str = "basic") -> Dict[str, Any]:
    """Validate data structures using Pydantic schemas."""
    
    # Define different validation schemas
    schemas = {
        "basic": BaseModel,
        "webpage": WebPageData,
        "date_range": DateRange
    }
    
    if schema_type not in schemas:
        return {"error": f"Unknown schema type: {schema_type}. Available: {list(schemas.keys())}"}
    
    try:
        schema_class = schemas[schema_type]
        
        if schema_type == "basic":
            # For basic validation, just check if it's a valid dict
            if not isinstance(data, dict):
                raise ValidationError("Data must be a dictionary", BaseModel)
            return {"valid": True, "schema": schema_type, "data": data}
        
        # For specific schemas, validate according to their rules
        validated = schema_class(**data)
        return {
            "valid": True,
            "schema": schema_type,
            "validated_data": validated.dict()
        }
        
    except ValidationError as e:
        return {
            "valid": False,
            "schema": schema_type,
            "errors": str(e)
        }
    except Exception as e:
        return {"error": f"Validation failed: {str(e)}"}

if __name__ == "__main__":
    mcp.run(transport="streamable-http")