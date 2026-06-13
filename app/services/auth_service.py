from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from fastapi import HTTPException, status, BackgroundTasks
from typing import Tuple

from app.models.user import User, UserStatus
from app.models.email_verification import EmailVerification
from app.models.password_reset import PasswordReset
from app.models.session import Session as DbSession
from app.models.login_audit_log import LoginAuditLog, AuditAction
from app.schemas.user import UserCreate
from app.schemas.auth import LoginRequest, ForgotPassword, ResetPassword, ChangePassword
from app.core.security import (
    get_password_hash, verify_password, create_access_token,
    generate_otp, get_otp_hash, generate_reset_token, get_reset_token_hash,
    generate_refresh_token, get_refresh_token_hash
)
from app.services.email_service import EmailService
from app.core.config import settings

class AuthService:
    def __init__(self, db: Session):
        self.db = db

    def register_user(self, user_data: UserCreate, bg_tasks: BackgroundTasks) -> User:
        if self.db.query(User).filter(User.email == user_data.email).first():
            raise HTTPException(status_code=400, detail="Email already registered")
        
        db_user = User(
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            email=user_data.email,
            phone=user_data.phone,
            password_hash=get_password_hash(user_data.password),
            status=UserStatus.PENDING_VERIFICATION
        )
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)

        self._generate_and_send_otp(db_user, bg_tasks)
        return db_user

    def _generate_and_send_otp(self, user: User, bg_tasks: BackgroundTasks):
        otp = generate_otp()
        otp_hash = get_otp_hash(otp)
        expires_at = datetime.utcnow() + timedelta(minutes=15)

        # Invalidate previous unused OTPs
        self.db.query(EmailVerification).filter(
            EmailVerification.user_id == user.id,
            EmailVerification.is_used == False
        ).update({"is_used": True})

        verification = EmailVerification(
            user_id=user.id,
            otp_hash=otp_hash,
            expires_at=expires_at
        )
        self.db.add(verification)
        self.db.commit()

        bg_tasks.add_task(EmailService.send_otp_email, user.email, otp)

    def verify_otp(self, email: str, otp: str, bg_tasks: BackgroundTasks):
        user = self.db.query(User).filter(User.email == email).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        verification = self.db.query(EmailVerification).filter(
            EmailVerification.user_id == user.id,
            EmailVerification.is_used == False
        ).order_by(EmailVerification.created_at.desc()).first()

        if not verification:
            raise HTTPException(status_code=400, detail="No active OTP found")

        if verification.expires_at < datetime.utcnow():
            raise HTTPException(status_code=400, detail="OTP expired")

        if verification.attempts >= 3:
            raise HTTPException(status_code=400, detail="Too many attempts. Request a new OTP.")

        if verification.otp_hash != get_otp_hash(otp):
            verification.attempts += 1
            self.db.commit()
            raise HTTPException(status_code=400, detail="Invalid OTP")

        verification.is_used = True
        user.status = UserStatus.ACTIVE
        self.db.commit()

        bg_tasks.add_task(EmailService.send_welcome_email, user.email)

    def resend_otp(self, email: str, bg_tasks: BackgroundTasks):
        user = self.db.query(User).filter(User.email == email).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        self._generate_and_send_otp(user, bg_tasks)

    def login(self, login_data: LoginRequest, ip_address: str, user_agent: str, bg_tasks: BackgroundTasks) -> Tuple[str, str]:
        user = self.db.query(User).filter(User.email == login_data.email).first()
        if not user or not verify_password(login_data.password, user.password_hash):
            if user:
                self._log_audit(user.id, AuditAction.LOGIN_FAILED, ip_address, user_agent)
            raise HTTPException(status_code=401, detail="Invalid credentials")

        if user.status != UserStatus.ACTIVE:
            raise HTTPException(status_code=403, detail="Account is not active")

        access_token = create_access_token(subject=user.id)
        refresh_token = generate_refresh_token()
        
        expires_at = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        
        session = DbSession(
            user_id=user.id,
            refresh_token_hash=get_refresh_token_hash(refresh_token),
            device_info=user_agent,
            ip_address=ip_address,
            expires_at=expires_at
        )
        self.db.add(session)
        self._log_audit(user.id, AuditAction.LOGIN_SUCCESS, ip_address, user_agent)
        self.db.commit()
        
        bg_tasks.add_task(
            EmailService.send_login_attempt_email,
            user.email,
            datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
            ip_address,
            user_agent
        )

        return access_token, refresh_token

    def logout(self, refresh_token: str, user_id: str):
        token_hash = get_refresh_token_hash(refresh_token)
        session = self.db.query(DbSession).filter(
            DbSession.refresh_token_hash == token_hash,
            DbSession.user_id == user_id
        ).first()

        if session:
            session.is_revoked = True
            self._log_audit(user_id, AuditAction.LOGOUT, session.ip_address, session.device_info)
            self.db.commit()

    def forgot_password(self, email: str, bg_tasks: BackgroundTasks):
        user = self.db.query(User).filter(User.email == email).first()
        if not user:
            return

        reset_token = generate_reset_token()
        
        self.db.query(PasswordReset).filter(
            PasswordReset.user_id == user.id,
            PasswordReset.is_used == False
        ).update({"is_used": True})

        reset_entry = PasswordReset(
            user_id=user.id,
            reset_token_hash=get_reset_token_hash(reset_token),
            expires_at=datetime.utcnow() + timedelta(minutes=15)
        )
        self.db.add(reset_entry)
        self.db.commit()

        reset_url = f"http://localhost:5173/auth/reset-password?token={reset_token}"
        bg_tasks.add_task(EmailService.send_password_reset_email, user.email, reset_url)

    def reset_password(self, data: ResetPassword, bg_tasks: BackgroundTasks):
        token_hash = get_reset_token_hash(data.token)
        reset_entry = self.db.query(PasswordReset).filter(
            PasswordReset.reset_token_hash == token_hash,
            PasswordReset.is_used == False
        ).first()

        if not reset_entry or reset_entry.expires_at < datetime.utcnow():
            raise HTTPException(status_code=400, detail="Invalid or expired reset token")

        user = self.db.query(User).filter(User.id == reset_entry.user_id).first()
        user.password_hash = get_password_hash(data.new_password)
        reset_entry.is_used = True
        
        self.db.query(DbSession).filter(DbSession.user_id == user.id).update({"is_revoked": True})
        
        self._log_audit(user.id, AuditAction.PASSWORD_RESET, None, None)
        self.db.commit()
        
        bg_tasks.add_task(EmailService.send_password_reset_success_email, user.email)

    def change_password(self, user: User, data: ChangePassword):
        if not verify_password(data.old_password, user.password_hash):
            raise HTTPException(status_code=400, detail="Invalid previous password")

        user.password_hash = get_password_hash(data.new_password)
        
        # Optional: Revoke all other sessions when password changes
        self.db.query(DbSession).filter(DbSession.user_id == user.id).update({"is_revoked": True})
        
        self._log_audit(user.id, AuditAction.PASSWORD_RESET, None, None)
        self.db.commit()

    def _log_audit(self, user_id: str, action: AuditAction, ip_address: str, user_agent: str):
        log = LoginAuditLog(
            user_id=user_id,
            action=action,
            ip_address=ip_address,
            user_agent=user_agent
        )
        self.db.add(log)
