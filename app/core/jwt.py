import jwt, hashlib
from passlib.context import CryptContext
from fastapi import HTTPException, status
from datetime import datetime, timedelta, timezone
from typing import Any
from app.core.config import settings

def create_access_token(subject: str | Any, expires_delta: timedelta | None = None) -> str:
    """Generates a short-lived Access Token."""
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # Standard JWT payload: 'exp' is expiration, 'sub' is the subject (usually user ID)
    to_encode = {"exp": expire, "sub": str(subject), "type": "access"}
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def create_refresh_token(subject: str | Any) -> str:
    """Generates a long-lived Refresh Token."""
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode = {"exp": expire, "sub": str(subject), "type": "refresh"}
    
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def verify_token(token: str, expected_type: str) -> str:
    """
    Decodes the JWT, verifies its signature and expiration, 
    and returns the user ID (subject).
    """
    try:
        # Decode the token using your secret key
        payload = jwt.decode(
            token, 
            settings.JWT_SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        
        # Ensure the token hasn't expired (PyJWT checks 'exp' automatically, but it's good practice to be explicit)
        token_type = payload.get("type")
        if token_type != expected_type:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token type. Expected {expected_type}.",
            )
            
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token is missing subject payload.",
            )

        return user_id
    
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired.",
        )
    

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

def get_password_hash(password: str) -> str:
    sha256_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()

    return pwd_context.hash(sha256_hash)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    sha256_hash = hashlib.sha256(plain_password.encode('utf-8')).hexdigest()
    
    print("VERIFY RAW LEN:", len(plain_password.encode()))
    print("VERIFY SHA256 LEN:", len(sha256_hash.encode()))

    return pwd_context.verify(sha256_hash, hashed_password)