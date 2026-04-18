from pydantic import BaseModel, Field, field_validator
import phonenumbers


class AuthRequest(BaseModel):
    country: str = Field(default="IN", description="ISO country code (IN, US, etc)")
    phone_number: str = Field(
        ...,
        description="National phone number (without country code)",
        example="9876543210"
    )

    @field_validator("phone_number")
    def validate_phone_number(cls, value):
        if not value.isdigit():
            raise ValueError("Phone number must contain only digits")
        return value

    @field_validator("country")
    def validate_country(cls, value):
        if len(value) != 2:
            raise ValueError("Country must be ISO code like IN, US")
        return value.upper()

    def get_e164(self) -> str:
        try:
            parsed = phonenumbers.parse(self.phone_number, self.country)

            if not phonenumbers.is_valid_number(parsed):
                raise ValueError("Invalid phone number")

            return phonenumbers.format_number(
                parsed,
                phonenumbers.PhoneNumberFormat.E164
            )
        except Exception:
            raise ValueError("Invalid phone number format")


class OtpRequest(AuthRequest):
    pass


class OtpVerifyRequest(AuthRequest):
    otp: str = Field(..., description="4-digit OTP", example="5689")

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


class AdminLoginRequest(BaseModel):
    email: str
    password: str