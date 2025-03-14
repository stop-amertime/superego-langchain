#!/usr/bin/env python3
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
import pathlib
from typing import Dict, Any

from app.api.routes import router
from app.flow.engine import initialize_engine

# Create FastAPI app
app = FastAPI(
    title="Superego Agent System",
    description="A research system investigating value-based monitoring agents",
    version="0.1.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router)

# Initialize the flow engine
base_dir = pathlib.Path(__file__).parent
constitutions_dir = base_dir / "data" / "constitutions"
flow_defs_dir = base_dir / "data" / "flow_definitions"

# Create data directories if they don't exist
for dir_path in [constitutions_dir, flow_defs_dir]:
    dir_path.mkdir(parents=True, exist_ok=True)

# Initialize the flow engine at startup
@app.on_event("startup")
async def startup_event():
    await initialize_engine(str(constitutions_dir), str(flow_defs_dir))

# Simple health check endpoint
@app.get("/health")
async def health_check() -> Dict[str, Any]:
    return {"status": "ok", "version": app.version}

if __name__ == "__main__":
    import uvicorn
    
    # Get port from environment or use default
    port = int(os.environ.get("PORT", 8000))
    
    # Run server
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=True)
