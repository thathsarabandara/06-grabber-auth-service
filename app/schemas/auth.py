from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

class OTPVerify(BaseModel):
    email: EmailStr
    otp: str = Field(..., min_length=6, max_length=6)

class OTPResend(BaseModel):
    email: EmailStr

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    # refresh token will be set in HTTP-only cookie, not returned in body

class ForgotPassword(BaseModel):
    email: EmailStr

class ResetPassword(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8)

class ChangePassword(BaseModel):
    old_password: str
    new_password: str = Field(..., min_length=8)

class SessionResponse(BaseModel):
    id: str
    device_info: Optional[str]
    ip_address: Optional[str]
    expires_at: datetime
    is_revoked: bool
    created_at: datetime

    class Config:
        from_attributes = True
