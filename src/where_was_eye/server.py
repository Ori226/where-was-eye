"""
HTTP Server for Where Was Eye

This module provides FastAPI-based HTTP servers for exposing timeline query functionality
as REST APIs and MCP (Model Context Protocol) servers.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any
import os
import logging

from .timeline_db import MyTimelineDB

logger = logging.getLogger(__name__)


class TimeRequest(BaseModel):
    """Request model for time-based location queries."""
    year: int
    month: int
    day: int
    hour: int
    minute: int


class LocationResponse(BaseModel):
    """Response model for location queries."""
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    success: bool = True
    error: Optional[str] = None


class ServerConfig:
    """Configuration for the HTTP server."""
    def __init__(
        self,
        timeline_db_path: Optional[str] = None,
        host: str = "0.0.0.0",
        port: int = 8000,
        cors_origins: list = ["*"],
        enable_mcp: bool = False
    ):
        self.timeline_db_path = timeline_db_path or os.environ.get("LOCATION_HISTORY_PATH")
        self.host = host
        self.port = port
        self.cors_origins = cors_origins
        self.enable_mcp = enable_mcp


def create_app(config: Optional[ServerConfig] = None) -> FastAPI:
    """
    Create and configure the FastAPI application.
    
    Args:
        config: Server configuration
        
    Returns:
        Configured FastAPI application
    """
    config = config or ServerConfig()
    
    if not config.timeline_db_path:
        raise ValueError("Timeline database path not provided in config or environment")
    
    app = FastAPI(
        title="Where Was Eye API",
        version="1.0.0",
        description="API for querying Google Timeline location history data",
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Initialize timeline database
    timeline_db = MyTimelineDB(config.timeline_db_path)
    
    @app.get("/")
    async def root():
        """Root endpoint with API information."""
        return {
            "name": "Where Was Eye API",
            "version": "1.0.0",
            "description": "API for querying Google Timeline location history",
            "endpoints": {
                "/get_location_at_time": "POST - Get location at specific time",
                "/health": "GET - Health check"
            }
        }
    
    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {"status": "healthy", "service": "where_was_eye"}
    
    @app.post("/get_location_at_time", response_model=LocationResponse)
    async def get_location_at_time(request: TimeRequest):
        """
        Get location at a specific time.
        
        Args:
            request: TimeRequest with year, month, day, hour, minute
            
        Returns:
            LocationResponse with latitude and longitude, or error
        """
        try:
            location = timeline_db.get_location_at_time(
                year=request.year,
                month=request.month,
                day=request.day,
                hour=request.hour,
                minute=request.minute
            )
            
            if location and "latitude" in location and "longitude" in location:
                return LocationResponse(
                    latitude=location.get("latitude"),
                    longitude=location.get("longitude")
                )
            else:
                return LocationResponse(
                    success=False,
                    error="Location not found for the specified time"
                )
                
        except Exception as e:
            logger.error(f"Error getting location: {e}")
            return LocationResponse(
                success=False,
                error=f"Internal server error: {str(e)}"
            )
    
    # MCP-specific endpoints if enabled
    if config.enable_mcp:
        _setup_mcp_endpoints(app, timeline_db)
    
    return app


def _setup_mcp_endpoints(app: FastAPI, timeline_db: MyTimelineDB):
    """Setup MCP (Model Context Protocol) specific endpoints."""
    
    class MCPTimeRequest(BaseModel):
        year: int
        month: int
        day: int
        hour: int
        minute: int
    
    @app.post("/mcp/get_location")
    async def mcp_get_location(request: MCPTimeRequest):
        """
        MCP-compatible endpoint for getting location.
        Returns data in MCP-friendly format.
        """
        try:
            location = timeline_db.get_location_at_time(
                year=request.year,
                month=request.month,
                day=request.day,
                hour=request.hour,
                minute=request.minute
            )
            
            return {
                "success": True,
                "data": location,
                "metadata": {
                    "source": "google_timeline",
                    "query_time": f"{request.year}-{request.month:02d}-{request.day:02d} {request.hour:02d}:{request.minute:02d}"
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "data": None
            }


# Simple standalone server runner
def run_server(
    timeline_db_path: Optional[str] = None,
    host: str = "0.0.0.0",
    port: int = 8000,
    reload: bool = False
):
    """
    Run the HTTP server standalone.
    
    Args:
        timeline_db_path: Path to timeline JSON file
        host: Server host address
        port: Server port
        reload: Enable auto-reload for development
    """
    import uvicorn
    
    config = ServerConfig(
        timeline_db_path=timeline_db_path,
        host=host,
        port=port
    )
    
    app = create_app(config)
    
    print(f"Starting Where Was Eye server on http://{host}:{port}")
    print(f"Timeline database: {config.timeline_db_path}")
    print("Available endpoints:")
    print("  GET  /          - API information")
    print("  GET  /health    - Health check")
    print("  POST /get_location_at_time - Get location at specific time")
    
    uvicorn.run(app, host=host, port=port, reload=reload)


if __name__ == "__main__":
    # Example: Run server with default configuration
    run_server()