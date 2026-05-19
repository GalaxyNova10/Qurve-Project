"""
Qurve AI - Authentication Health API
READ-ONLY endpoint for AWS credential system health monitoring.

Provides visibility into:
✅ credential validity
✅ source type
✅ region compliance
✅ expiration status
✅ auth telemetry
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import logging

from .aws_credentials_manager import get_aws_credentials_manager

logger = logging.getLogger(__name__)

# Create auth router
auth_router = APIRouter(prefix="/api/v1/cloud/auth", tags=["auth"])

@auth_router.get("/health", response_model=Dict[str, Any])
async def get_auth_health() -> Dict[str, Any]:
    """
    Get AWS authentication system health status.
    READ-ONLY endpoint for auth system monitoring.
    """
    try:
        credentials_manager = get_aws_credentials_manager()
        
        # Get health status for all regions
        regions = credentials_manager.get_allowed_regions()
        health_status = {}
        
        for region in regions:
            health_status[region] = await credentials_manager.get_auth_health()
        
        # Determine overall health
        overall_status = "healthy"
        if any(status["status"] != "healthy" for status in health_status.values()):
            overall_status = "degraded"
        if any(status["status"] in ["unavailable", "error"] for status in health_status.values()):
            overall_status = "unhealthy"
        
        return {
            "overall_status": overall_status,
            "regions": health_status,
            "primary_region": regions[0],  # First allowed region
            "allowed_regions": regions,
            "timestamp": health_status[regions[0]]["timestamp"] if health_status else None,
            "cache_status": {
                "has_cached_credentials": any(
                    status.get("cache_status", {}).get("cached", False) 
                    for status in health_status.values()
                ),
                "cache_valid": any(
                    status.get("cache_status", {}).get("valid", False) 
                    for status in health_status.values()
                )
            },
            "validation_cooldown": any(
                status.get("validation_cooldown", False) 
                for status in health_status.values()
            )
        }
        
    except Exception as e:
        logger.error("Failed to get auth health", error=str(e))
        raise HTTPException(status_code=500, detail="Auth health check failed")

@auth_router.get("/sources", response_model=Dict[str, Any])
async def get_credential_sources() -> Dict[str, Any]:
    """
    Get available credential sources and their status.
    READ-ONLY endpoint for credential source monitoring.
    """
    try:
        credentials_manager = get_aws_credentials_manager()
        regions = credentials_manager.get_allowed_regions()
        
        sources_status = {}
        for region in regions:
            health = await credentials_manager.get_auth_health()
            sources_status[region] = health.get("credential_sources", {})
        
        return {
            "sources": sources_status,
            "allowed_regions": regions,
            "priority_order": ["environment", "aws_profile", "iam_role"],
            "timestamp": sources_status.get(regions[0], {}).get("timestamp") if sources_status else None
        }
        
    except Exception as e:
        logger.error("Failed to get credential sources", error=str(e))
        raise HTTPException(status_code=500, detail="Credential sources check failed")

@auth_router.get("/regions", response_model=Dict[str, Any])
async def get_region_status() -> Dict[str, Any]:
    """
    Get AWS region compliance status.
    READ-ONLY endpoint for region monitoring.
    """
    try:
        credentials_manager = get_aws_credentials_manager()
        allowed_regions = credentials_manager.get_allowed_regions()
        
        region_status = {}
        for region in allowed_regions:
            health = await credentials_manager.get_auth_health()
            region_info = {
                "allowed": True,
                "status": health.get("status", "unknown"),
                "credential_source": health.get("credential_sources", {}).get("primary_source", "unknown")
            }
            region_status[region] = region_info
        
        return {
            "regions": region_status,
            "allowed_regions": allowed_regions,
            "compliance_status": "compliant",  # All regions are enforced
            "timestamp": region_status.get(allowed_regions[0], {}).get("timestamp") if region_status else None
        }
        
    except Exception as e:
        logger.error("Failed to get region status", error=str(e))
        raise HTTPException(status_code=500, detail="Region status check failed")

@auth_router.get("/validation-stats", response_model=Dict[str, Any])
async def get_validation_stats() -> Dict[str, Any]:
    """
    Get authentication validation statistics.
    READ-ONLY endpoint for auth performance monitoring.
    """
    try:
        credentials_manager = get_aws_credentials_manager()
        regions = credentials_manager.get_allowed_regions()
        
        validation_stats = {}
        total_validations = 0
        total_failures = 0
        total_cache_hits = 0
        total_cooldowns = 0
        
        for region in regions:
            health = await credentials_manager.get_auth_health()
            
            # Extract validation metrics
            if health.get("status") in ["valid", "invalid", "expiring", "expired"]:
                total_validations += 1
                if health.get("status") != "valid":
                    total_failures += 1
            
            # Check cache metrics
            cache_status = health.get("cache_status", {})
            if cache_status.get("cached", False):
                total_cache_hits += 1
            if not cache_status.get("valid", False):
                total_failures += 1
            
            # Check cooldown
            if health.get("validation_cooldown", False):
                total_cooldowns += 1
        
        return {
            "validation_stats": {
                "total_validations": total_validations,
                "total_failures": total_failures,
                "total_cache_hits": total_cache_hits,
                "total_cooldowns": total_cooldowns,
                "failure_rate": (total_failures / total_validations * 100) if total_validations > 0 else 0.0,
                "cache_hit_rate": (total_cache_hits / total_validations * 100) if total_validations > 0 else 0.0
            },
            "regions": regions,
            "timestamp": validation_stats.get("timestamp") if validation_stats else None
        }
        
    except Exception as e:
        logger.error("Failed to get validation stats", error=str(e))
        raise HTTPException(status_code=500, detail="Validation stats check failed")
