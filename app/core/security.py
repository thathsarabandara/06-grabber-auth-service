from datetime import datetime, timedelta
from typing import Any, Union, Optional
from jose import jwt
from passlib.context import CryptContext
import secrets
import string
import hashlib

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

_OTP_ALPHABET = string.digits
_TOKEN_ALPHABET = string.ascii_letters + string.digits


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(
    subject: Union[str, Any], expires_delta: Optional[timedelta] = None
) -> str:
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def generate_otp(length: int = 6) -> str:
    """Generate a cryptographically secure numeric OTP."""
    return ''.join(secrets.choice(_OTP_ALPHABET) for _ in range(length))


def get_otp_hash(otp: str) -> str:
    return hashlib.sha256(otp.encode()).hexdigest()


def generate_reset_token(length: int = 32) -> str:
    """Generate a cryptographically secure password reset token."""
    return ''.join(secrets.choice(_TOKEN_ALPHABET) for _ in range(length))


def get_reset_token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def generate_refresh_token(length: int = 64) -> str:
    """Generate a cryptographically secure refresh token."""
    return ''.join(secrets.choice(_TOKEN_ALPHABET) for _ in range(length))


def get_refresh_token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()
