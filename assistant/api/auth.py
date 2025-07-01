"""
Authentication utilities for the API.
"""

import os
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from fastapi import HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from assistant.utils.logger import setup_logger

logger = setup_logger(__name__)

security = HTTPBearer()

def create_access_token(data: dict, secret_key: str, expires_delta: Optional[timedelta] = None):
    """Create a new access token."""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=24)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, secret_key, algorithm="HS256")
    return encoded_jwt

def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)):
    """Verify JWT token."""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = credentials.credentials
    
    # Simple token verification for development
    # In production, you'd want proper JWT verification
    api_token = os.getenv("API_TOKEN", "default_token_change_me")
    jwt_secret = os.getenv("JWT_SECRET", "default_jwt_secret_change_me")
    
    # First try simple token match
    if token == api_token:
        return {"sub": "api_user", "type": "simple"}
    
    # Then try JWT verification
    try:
        payload = jwt.decode(token, jwt_secret, algorithms=["HS256"])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

def create_user_token(username: str, config) -> str:
    """Create a token for a specific user."""
    token_data = {"sub": username, "type": "user"}
    access_token_expires = timedelta(hours=config.jwt_expiry_hours)
    
    access_token = create_access_token(
        data=token_data,
        secret_key=config.jwt_secret,
        expires_delta=access_token_expires
    )
    
    return access_token

def verify_api_key(api_key: str, config) -> bool:
    """Verify API key."""
    return api_key == config.api_token
