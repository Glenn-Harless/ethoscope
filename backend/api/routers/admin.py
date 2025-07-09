from typing import Any, Dict

from fastapi import APIRouter, Depends

from backend.api.dependencies import verify_request

router = APIRouter()


@router.get("/stats")
async def get_admin_stats(user_info: Dict[str, Any] = Depends(verify_request)):
    """Get admin statistics (requires admin permissions)"""
    # Check admin permissions
    if "admin" not in user_info.get("permissions", []):
        return {"error": "Admin access required"}

    return {
        "total_users": 100,  # Placeholder
        "total_requests": 50000,  # Placeholder
        "active_connections": 25,  # Placeholder
    }


@router.post("/clear-cache")
async def clear_cache(user_info: Dict[str, Any] = Depends(verify_request)):
    """Clear all caches (requires admin permissions)"""
    if "admin" not in user_info.get("permissions", []):
        return {"error": "Admin access required"}

    # TODO: Implement cache clearing
    return {"status": "Cache cleared"}
