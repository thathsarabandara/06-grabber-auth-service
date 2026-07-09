from fastapi import APIRouter, Depends, Response, Request, BackgroundTasks
from sqlalchemy.orm import Session
from app.api.deps import get_db
from app.schemas.user import UserCreate, UserResponse
from app.schemas.auth import LoginRequest, TokenResponse, OTPVerify, OTPResend, ForgotPassword, ResetPassword
from app.services.auth_service import AuthService
from app.core.config import settings

router = APIRouter()

@router.post("/register", response_model=UserResponse, status_code=201)
def register(user_in: UserCreate, bg_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    auth_service = AuthService(db)
    return auth_service.register_user(user_in, bg_tasks)

@router.post("/verify-otp")
def verify_otp(data: OTPVerify, bg_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    auth_service = AuthService(db)
    auth_service.verify_otp(data.email, data.otp, bg_tasks)
    return {"message": "Email verified successfully. Account is now active."}

@router.post("/resend-otp")
def resend_otp(data: OTPResend, bg_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    auth_service = AuthService(db)
    auth_service.resend_otp(data.email, bg_tasks)
    return {"message": "OTP resent successfully"}

@router.post("/login", response_model=TokenResponse)
def login(request: Request, response: Response, login_data: LoginRequest, bg_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    auth_service = AuthService(db)
    
    ip_address = request.client.host if request.client else "Unknown"
    user_agent = request.headers.get("user-agent", "Unknown")
    
    access_token, refresh_token = auth_service.login(login_data, ip_address, user_agent, bg_tasks)
    
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=False,  # Set to True in production with HTTPS
        samesite="lax",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
    )
    
    return {"access_token": access_token, "token_type": "bearer"}  # nosec B105 - 'bearer' is OAuth2 token_type, not a password

@router.post("/logout")
def logout(request: Request, response: Response, db: Session = Depends(get_db)):
    refresh_token = request.cookies.get("refresh_token")
    if refresh_token:
        from app.models.session import Session as DbSession
        from app.core.security import get_refresh_token_hash
        token_hash = get_refresh_token_hash(refresh_token)
        session = db.query(DbSession).filter(DbSession.refresh_token_hash == token_hash).first()
        if session:
            auth_service = AuthService(db)
            auth_service.logout(refresh_token, session.user_id)
            
    response.delete_cookie("refresh_token")
    return {"message": "Logged out successfully"}

@router.post("/forgot-password")
def forgot_password(data: ForgotPassword, bg_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    auth_service = AuthService(db)
    auth_service.forgot_password(data.email, bg_tasks)
    return {"message": "If the email is registered, a password reset link has been sent."}

@router.post("/reset-password")
def reset_password(data: ResetPassword, bg_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    auth_service = AuthService(db)
    auth_service.reset_password(data, bg_tasks)
    return {"message": "Password reset successfully. Please login with your new password."}
