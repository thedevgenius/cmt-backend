from pydantic import BaseModel, Field, field_validator

class AuthRequest(BaseModel):
    country: str = "IN" 
    phone_number: str = Field(..., description="Phone number to which OTP will be sent", example="919876543210")

    @field_validator("phone_number")
    def validate_phone_number(cls, value):
        if not value.isdigit():
            raise ValueError("Phone number must contain only digits")
        if len(value) < 10 or len(value) > 15:
            raise ValueError("Phone number must be between 10 and 15 digits")
        return value
    
    def __init__(self, **data):
        super().__init__(**data)
        first_digit = self.phone_number[0] if self.phone_number else None
        if self.country == "IN" and first_digit not in ["9", "8", "7", "6"]:
            raise ValueError("In India, phone numbers must start with 9, 8, 7, or 6")

        if self.country == "IN" and not self.phone_number.startswith("91"):
            self.phone_number = "91" + self.phone_number


class OtpRequest(AuthRequest):
    pass
    
   
class OtpVerifyRequest(AuthRequest):
    otp: str = Field(..., description="4-digit OTP sent to the user's phone", example="5689")

    @field_validator("otp")
    def validate_otp(cls, value):
        if not value.isdigit():
            raise ValueError("OTP must contain only digits")
        if len(value) != 4:
            raise ValueError("OTP must be exactly 4 digits")
        return value
    
class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"