import httpx
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import User
from app.core.config import settings
from app.core.redis_client import redis_client
from app.core import jwt as app_jwt
from app.models.user import UserRole, User


async def get_or_create_user(db: AsyncSession, phone: str) -> User:
    """Fetches an existing user by phone, or creates a new unverified user."""

    result = await db.execute(select(User).where(User.phone == phone))
    user = result.scalars().first()
    
    if not user:
        user = User(phone=phone, is_verified=False)
        db.add(user)
        await db.commit()
        await db.refresh(user)
        
    return user


async def send_otp_msg91(phone: str) -> str:
    """Generates a 6-digit OTP, enforces a 30s rate limit, saves in memory, and prints."""

    url = "https://api.msg91.com/api/v5/widget/sendOtp"
    payload = {
        "widgetId": settings.MSG_WIDGET_ID,
        "identifier": phone,
    }
    headers = {
        "content-type": "application/json",
        "authkey": settings.MSG_AUTH_KEY
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            redis_otp_key = f"otp:{phone}"
            await redis_client.set(
                redis_otp_key,
                data["message"],
                ex=300
            )

    except httpx.RequestError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Could not connect to the SMS gateway."
        )
    return data


async def resend_otp_msg91(phone: str) -> str:
    """Resends the OTP for the given phone number, enforcing a 30s rate limit and updating the in-memory store."""

    url = "https://api.msg91.com/api/v5/widget/retryOtp"

    redis_otp_key = f"otp:{phone}"
    req_id = await redis_client.get(redis_otp_key)

    if not req_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No existing OTP request found for this phone number."
        )
    
    payload = {
        "widgetId": settings.MSG_WIDGET_ID,
        "reqId": req_id
    }
    headers = {
        "content-type": "application/json",
        "authkey": settings.MSG_AUTH_KEY
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()

            await redis_client.set(
                redis_otp_key,
                data["message"],
                ex=300
            )

    except httpx.RequestError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Could not connect to the SMS gateway."
        )
    return data


async def verify_otp_msg91(phone: str, otp: str) -> bool:
    """Checks the provided OTP against the in-memory store."""
    
    url = "https://api.msg91.com/api/v5/widget/verifyOtp"

    redis_otp_key = f"otp:{phone}"
    redis_data = await redis_client.get(redis_otp_key)

    if not redis_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired otp"
        )

    payload = {
        "widgetId": settings.MSG_WIDGET_ID,
        "reqId": redis_data,
        "otp": otp
    }
    headers = {
        "content-type": "application/json",
        "authkey": settings.MSG_AUTH_KEY
    }
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            if data["type"] != "success":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid or expired OTP."
                )
            await redis_client.delete(redis_otp_key)
            print(redis_data)
            return True

    except httpx.RequestError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Could not connect to the SMS gateway."
        )


async def refresh_access_token(refresh_token: str, db: AsyncSession):
    """Validates the refresh token, checks user status, and issues a new access token."""
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Refresh token missing. Please log in."
        )
    
    user_id = app_jwt.verify_token(refresh_token, expected_type="refresh")
    

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()
    
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User no longer exists.")
    if user.is_blocked or not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User account is inactive or blocked.")
    
    new_access_token = app_jwt.create_access_token(subject=user.id)

    return new_access_token


async def get_admin(db: AsyncSession, email: str, password: str) -> User:
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalars().first()

    if not user or not user.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Invalid email or password."
        )

    if not app_jwt.verify_password(password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Invalid email or password."
        )
        
    if user.role not in [UserRole.ADMIN, UserRole.STAFF]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Access denied. Admin or Staff privileges required."
        )
        
    if not user.is_active or user.is_blocked:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account is inactive or blocked."
        )
    
    return user