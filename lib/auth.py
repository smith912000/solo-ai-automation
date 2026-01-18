"""
Simple auth helpers - supports both API key and password.
"""

import os
from typing import Optional

from fastapi import HTTPException


def require_auth(
    api_key: Optional[str] = None,
    password: Optional[str] = None,
    admin: bool = False
) -> None:
    """
    Validate authentication via API key OR password.
    
    Checks in order:
    1. API key (X-API-Key header)
    2. Password (X-Password header or query param)
    
    For admin endpoints, uses ADMIN_API_KEY/ADMIN_PASSWORD.
    """
    # Get expected values from env
    if admin:
        expected_key = os.getenv("ADMIN_API_KEY") or os.getenv("API_KEY")
        expected_password = os.getenv("ADMIN_PASSWORD") or os.getenv("PASSWORD")
    else:
        expected_key = os.getenv("API_KEY")
        expected_password = os.getenv("PASSWORD")
    
    # Check API key first
    if api_key and expected_key and api_key == expected_key:
        return  # Valid API key
    
    # Check password
    if password and expected_password and password == expected_password:
        return  # Valid password
    
    # If neither API key nor password is configured, allow access in dev mode
    if not expected_key and not expected_password:
        if os.getenv("ENV") == "development":
            return  # Dev mode, no auth required
        raise HTTPException(status_code=500, detail="No auth configured (API_KEY or PASSWORD)")
    
    # Auth failed
    raise HTTPException(status_code=401, detail="Invalid credentials")


def require_api_key(api_key: Optional[str], admin: bool = False) -> None:
    """
    Legacy function - validates API key from request headers.
    Now also checks PASSWORD as fallback.
    """
    # Get password from same header as fallback
    return require_auth(api_key=api_key, password=api_key, admin=admin)
