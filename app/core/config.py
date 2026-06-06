from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "Grabber Auth Service"
    DATABASE_URL: str = "mysql+pymysql://user:password@localhost/dbname"
    SECRET_KEY: str = "super-secret-key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 300 # 5 hours
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30 # 30 days
    
    # Mail Config
    MAIL_USERNAME: str = "your-email@example.com"
    MAIL_PASSWORD: str = "your-app-password"
    MAIL_FROM: str = "your-email@example.com"
    MAIL_PORT: int = 587
    MAIL_SERVER: str = "smtp.gmail.com"
    MAIL_FROM_NAME: str = "Grabber"
    MAIL_STARTTLS: bool = True
    MAIL_SSL_TLS: bool = False
    USE_CREDENTIALS: bool = True
    VALIDATE_CERTS: bool = True
    
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
