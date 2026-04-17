
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Response, HTTPException, status, Cookie
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas import auth as user_schemas
from app.services import auth as auth_service
from app.core.dependencies import get_db
from app.services.jwt import create_access_token, create_refresh_token, verify_token
from app.core.config import settings
from app.schemas import auth as auth_schemas
from app.models.user import User, UserRole


router = APIRouter()

@router.post("/otp/send")
async def send_otp(otp_request: user_schemas.OtpRequest, db: AsyncSession = Depends(get_db)):
    user = await auth_service.get_or_create_user(db, otp_request.phone_number)
    await auth_service.send_otp_msg91(otp_request.phone_number)
    return {"message": "OTP sent successfully"}


@router.post("/otp/verify", response_model=auth_schemas.TokenResponse)
async def verify_otp(response: Response, otp_verify_request: user_schemas.OtpVerifyRequest, db: AsyncSession = Depends(get_db)):
    is_valid = await auth_service.verify_otp_msg91(otp_verify_request.phone_number, otp_verify_request.otp)

    if not is_valid:
        return {"message": "Invalid OTP"}
    
    user = await auth_service.verify_user(otp_verify_request.phone_number, db)

    access_token = create_access_token(subject=user.id)
    refresh_token = create_refresh_token(subject=user.id)

    cookie_max_age = settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60 
    
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,   # CRITICAL: JavaScript cannot access this cookie
        secure=False,    # IMPORTANT: Set to True in production so it only sends over HTTPS
        samesite="lax",  # Protects against Cross-Site Request Forgery (CSRF)
        max_age=cookie_max_age,
        expires=cookie_max_age,
    )

    return {"message": "OTP verified successfully", "access_token": access_token}


@router.post("/otp/resend")
async def resend_otp(otp_resend_request: user_schemas.OtpRequest, db: AsyncSession = Depends(get_db)):
    user = await auth_service.get_or_create_user(db, otp_resend_request.phone_number)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    await auth_service.resend_otp_msg91(otp_resend_request.phone_number)

    return {"message": "OTP resent successfully"}


@router.post("/refresh", response_model=auth_schemas.TokenResponse)
async def refresh_access_token(refresh_token: str | None = Cookie(default=None), db: AsyncSession = Depends(get_db)):

    new_access_token = await auth_service.refresh_access_token(refresh_token, db)
    
    return {
        "access_token": new_access_token,
        "token_type": "access"
    }


@router.post("/admin/login", response_model=auth_schemas.TokenResponse)
async def admin_login(
    request: auth_schemas.AdminLoginRequest, 
    response: Response, # Needed to set the refresh cookie
    db: AsyncSession = Depends(get_db)
):
    """
    Direct Admin/Staff login: Verifies credentials and issues JWTs immediately.
    """
    user = await auth_service.get_admin(db, request.email, request.password)

    user.last_login = datetime.now(timezone.utc)
    await db.commit()

    access_token = create_access_token(subject=user.id)
    refresh_token = create_refresh_token(subject=user.id)
    
    cookie_max_age = settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60 
    
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,   
        secure=False,    # Change to True when deploying to production (HTTPS)
        samesite="lax",  
        max_age=cookie_max_age,
        expires=cookie_max_age,
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }