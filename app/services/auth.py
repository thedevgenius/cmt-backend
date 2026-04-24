import httpx
from fastapi import HTTPException, status
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import User, UserRole
from app.core.config import settings
from app.core.redis_client import redis_client
from app.core import jwt as app_jwt


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.otp_expiry = 300  # 5 minutes
        self.headers = {
            "content-type": "application/json",
            "authkey": settings.MSG_AUTH_KEY
        }

    # --- User Management ---

    async def get_or_create_user(self, phone: str) -> User:
        """Fetches an existing user by phone, or creates a new unverified user."""
        result = await self.db.execute(select(User).where(User.phone == phone))
        user = result.scalars().first()
        
        if not user:
            user = User(phone=phone, is_verified=False)
            self.db.add(user)
            await self.db.commit()
            await self.db.refresh(user)
            
        return user

    async def get_admin(self, email: str, password: str) -> User:
        """Validates admin/staff credentials and status."""
        result = await self.db.execute(select(User).where(User.email == email))
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

    # --- OTP / MSG91 Logic ---

    async def _call_msg91(self, url: str, payload: dict) -> dict:
        """Internal helper to handle Msg91 API requests."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(url, json=payload, headers=self.headers)
                response.raise_for_status()
                return response.json()
        except httpx.RequestError:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Could not connect to the SMS gateway."
            )

    async def send_otp(self, phone: str) -> dict:
        """Sends OTP via Msg91 and stores the request ID in Redis."""
        url = "https://api.msg91.com/api/v5/widget/sendOtp"
        payload = {
            "widgetId": settings.MSG_WIDGET_ID,
            "identifier": phone,
        }
        
        data = await self._call_msg91(url, payload)
        
        # Save request ID to Redis for verification/retry
        await redis_client.set(f"otp:{phone}", data["message"], ex=self.otp_expiry)
        return data

    async def resend_otp(self, phone: str) -> dict:
        """Resends OTP using the existing request ID from Redis."""
        req_id = await redis_client.get(f"otp:{phone}")

        if not req_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No existing OTP request found for this phone number."
            )
        
        url = "https://api.msg91.com/api/v5/widget/retryOtp"
        payload = {"widgetId": settings.MSG_WIDGET_ID, "reqId": req_id}
        
        data = await self._call_msg91(url, payload)
        await redis_client.set(f"otp:{phone}", data["message"], ex=self.otp_expiry)
        return data

    async def verify_otp(self, phone: str, otp: str) -> bool:
        """Verifies OTP against Msg91 and clears Redis on success."""
        redis_key = f"otp:{phone}"
        req_id = await redis_client.get(redis_key)

        if not req_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired OTP."
            )

        url = "https://api.msg91.com/api/v5/widget/verifyOtp"
        payload = {
            "widgetId": settings.MSG_WIDGET_ID,
            "reqId": req_id,
            "otp": otp
        }
        
        data = await self._call_msg91(url, payload)
        
        if data.get("type") != "success":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired OTP."
            )
            
        await redis_client.delete(redis_key)
        return True

    # --- Token Management ---

    async def refresh_access_token(self, refresh_token: Optional[str]) -> str:
        """Validates refresh token and issues a new access token."""
        if not refresh_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, 
                detail="Refresh token missing. Please log in."
            )
        
        user_id = app_jwt.verify_token(refresh_token, expected_type="refresh")
        
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalars().first()
        
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User no longer exists.")
        if user.is_blocked or not user.is_active:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User account is inactive or blocked.")
        
        return app_jwt.create_access_token(subject=user.id)