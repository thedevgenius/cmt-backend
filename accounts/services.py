import requests
from django.conf import settings
from django.core.cache import cache
from django.contrib.auth import get_user_model
from rest_framework import status

# This automatically gets your CustomUser model that we created earlier
User = get_user_model()

def send_and_store_otp(phone):
    """
    Checks/creates a user, sends an OTP via MSG91, and stores the response in memory.
    """

    user, created = User.objects.get_or_create(
        phone=phone,
        defaults={"is_active": False}
    )

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
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status() 
        response_data = response.json()
        
        message = response_data["message"]
        cache_key = f"otp_id_{phone}"
        cache.set(cache_key, message, timeout=300)

        return {
            "success": True,
            "user_created": created,
            "message": "OTP sent successfully",
            "data": message
        }

    except requests.exceptions.RequestException as e:
        # Handle network errors, invalid API keys, etc.
        return {
            "success": False,
            "error": str(e)
        }
    
def verify_otp_service(phone: str, otp: str) -> dict:
    """Handles the business logic for verifying an OTP."""
    cache_key = f"otp_id_{phone}"
    req_id = cache.get(cache_key)

    if not req_id:
        return {
            "success": False, 
            "error": "Expired OTP or no request found.", 
            "status": status.HTTP_400_BAD_REQUEST
        }

    url = "https://api.msg91.com/api/v5/widget/verifyOtp"
    payload = {
        "widgetId": settings.MSG_WIDGET_ID,
        "reqId": req_id,
        "otp": otp
    }
    headers = {
        "content-type": "application/json",
        "authkey": settings.MSG_AUTH_KEY
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()

        if data.get("type") != "success":
            return {
                "success": False, 
                "error": "Invalid or expired OTP.", 
                "status": status.HTTP_400_BAD_REQUEST
            }

        # Clear cache on success so OTP cannot be reused
        cache.delete(cache_key)
        
        return {"success": True, "status": status.HTTP_200_OK}

    except requests.exceptions.RequestException:
        return {
            "success": False, 
            "error": "Could not connect to the SMS gateway.", 
            "status": status.HTTP_503_SERVICE_UNAVAILABLE
        }