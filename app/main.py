from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import health, auth, profile, sessions
from app.core.config import settings
from app.core.database import engine, Base
import app.models.user
import app.models.email_verification
import app.models.password_reset
import app.models.session
import app.models.login_audit_log

# Create DB tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.PROJECT_NAME)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api", tags=["health"])
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(profile.router, prefix="/api/v1/auth/me", tags=["profile"])
app.include_router(sessions.router, prefix="/api/v1/auth/sessions", tags=["sessions"])

@app.get("/")
def read_root():
    return {"message": f"Welcome to {settings.PROJECT_NAME}"}
