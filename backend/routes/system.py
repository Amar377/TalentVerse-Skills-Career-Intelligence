"""System status, AI provider health, and diagnostics."""
from fastapi import APIRouter
from backend.schemas import SystemStatusOut
from backend.ai_engine import get_provider_status

router = APIRouter(prefix="/system", tags=["System & Providers"])


@router.get("/status", response_model=SystemStatusOut)
def status_endpoint():
    status_data = get_provider_status()
    return SystemStatusOut.model_validate(status_data)
