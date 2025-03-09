"""Main API router that combines all sub-routers."""
from fastapi import APIRouter

from .constitutions import router as constitutions_router
from .sysprompts import router as sysprompts_router
from .flow_definitions import router as flow_definitions_router
from .flow_instances_engine import router as flow_instances_router
from .messages import router as messages_router

# Create the main API router
api_router = APIRouter()

# Include all sub-routers
api_router.include_router(constitutions_router)
api_router.include_router(sysprompts_router)
api_router.include_router(flow_definitions_router)
api_router.include_router(flow_instances_router)
api_router.include_router(messages_router)
