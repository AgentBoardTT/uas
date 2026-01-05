"""Configuration endpoints."""

import logging

from fastapi import APIRouter, HTTPException

from ..config_loader import list_available_configs, load_config_by_id
from ..models import ConfigInfo

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/configs", tags=["configs"])


@router.get("", response_model=list[ConfigInfo])
async def list_configs():
    """List all available configurations."""
    return list_available_configs()


@router.get("/{config_id}")
async def get_config(config_id: str):
    """Get a specific configuration by ID."""
    try:
        config = load_config_by_id(config_id)
        return config
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Config not found: {config_id}")
