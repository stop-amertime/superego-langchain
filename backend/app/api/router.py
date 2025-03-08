"""Main API router that combines all sub-routers."""
from fastapi import APIRouter

from .constitutions import router as constitutions_router
from .sysprompts import router as sysprompts_router
from .flow_configs import router as flow_configs_router
from .flow_templates import router as flow_templates_router
from .flow_instances import router as flow_instances_router

# Create the main API router
api_router = APIRouter()

# Include all sub-routers
api_router.include_router(constitutions_router)
api_router.include_router(sysprompts_router)
api_router.include_router(flow_configs_router)
api_router.include_router(flow_templates_router)
api_router.include_router(flow_instances_router)
