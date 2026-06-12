import logging
from pathlib import Path
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from app.core.config import settings

logger = logging.getLogger(__name__)

conf = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_FROM_NAME=settings.MAIL_FROM_NAME,
    MAIL_STARTTLS=settings.MAIL_STARTTLS,
    MAIL_SSL_TLS=settings.MAIL_SSL_TLS,
    USE_CREDENTIALS=settings.USE_CREDENTIALS,
    VALIDATE_CERTS=settings.VALIDATE_CERTS,
    TEMPLATE_FOLDER=Path(__file__).parent.parent / 'templates' / 'email'
)

fast_mail = FastMail(conf)

class EmailService:
    @staticmethod
    async def send_otp_email(email: str, otp: str):
        message = MessageSchema(
            subject="Your OTP Code - Grabber",
            recipients=[email],
            template_body={"otp": otp, "subject": "Verify Your Email"},
            subtype=MessageType.html
        )
        try:
            await fast_mail.send_message(message, template_name="otp_verification.html")
            logger.info(f"OTP email sent to {email}")
        except Exception as e:
            logger.error(f"Error sending OTP email: {e}")

    @staticmethod
    async def send_welcome_email(email: str):
        message = MessageSchema(
            subject="Welcome to Grabber!",
            recipients=[email],
            template_body={"subject": "Welcome to Grabber!"},
            subtype=MessageType.html
        )
        try:
            await fast_mail.send_message(message, template_name="welcome.html")
            logger.info(f"Welcome email sent to {email}")
        except Exception as e:
            logger.error(f"Error sending welcome email: {e}")

    @staticmethod
    async def send_password_reset_email(email: str, reset_url: str):
        message = MessageSchema(
            subject="Password Reset Request - Grabber",
            recipients=[email],
            template_body={"reset_url": reset_url, "subject": "Password Reset Request"},
            subtype=MessageType.html
        )
        try:
            await fast_mail.send_message(message, template_name="forgot_password.html")
            logger.info(f"Password reset email sent to {email}")
        except Exception as e:
            logger.error(f"Error sending password reset email: {e}")
            
    @staticmethod
    async def send_password_reset_success_email(email: str):
        message = MessageSchema(
            subject="Password Reset Successfully - Grabber",
            recipients=[email],
            template_body={"subject": "Password Reset Successfully"},
            subtype=MessageType.html
        )
        try:
            await fast_mail.send_message(message, template_name="password_reset_success.html")
            logger.info(f"Password reset success email sent to {email}")
        except Exception as e:
            logger.error(f"Error sending password reset success email: {e}")
            
    @staticmethod
    async def send_login_attempt_email(email: str, time: str, ip_address: str, user_agent: str):
        message = MessageSchema(
            subject="New Login Alert - Grabber",
            recipients=[email],
            template_body={
                "subject": "New Login Alert",
                "time": time,
                "ip_address": ip_address,
                "user_agent": user_agent
            },
            subtype=MessageType.html
        )
        try:
            await fast_mail.send_message(message, template_name="login_attempt.html")
            logger.info(f"Login attempt alert email sent to {email}")
        except Exception as e:
            logger.error(f"Error sending login attempt email: {e}")

