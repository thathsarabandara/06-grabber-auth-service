# 🔐 Grabber Auth Service

> **Repository `06`** · Security-critical identity and authentication service for the Grabber platform — built on Python 3.11 and FastAPI. Governs user registrations, JWT generation, secure session revocation auditing, multi-device tracking, SMTP-driven email OTP validations, and profile uploads.

[![Language](https://img.shields.io/badge/Language-Python%203.11-3776AB?logo=python&style=flat-square)]()
[![Framework](https://img.shields.io/badge/Framework-FastAPI-009688?logo=fastapi&style=flat-square)]()
[![ORM](https://img.shields.io/badge/ORM-SQLAlchemy%20v2-red.svg?style=flat-square)]()
[![Database](https://img.shields.io/badge/Database-MySQL-blue.svg?style=flat-square)]()
[![Security](https://img.shields.io/badge/Security-JWT%20%7C%20OTP-red.svg?style=flat-square)]()
[![Status](https://img.shields.io/badge/Status-Active-brightgreen.svg?style=flat-square)]()

---

## 🎥 Video Demonstration

<div align="center">
  <a href="https://youtu.be/iKOU6gbL75o?si=H0k2EhaDtzkgA7v9">
    <img src="https://img.youtube.com/vi/iKOU6gbL75o/maxresdefault.jpg" alt="Grabber Demo Video" width="70%">
  </a>
  <br/>
  <sub>Click the image above to watch the demonstration video on YouTube.</sub>
</div>

---

## 🧭 What Is This Repository?

This is the dedicated **Authentication and Session Management service** for the Grabber platform. Deployed as a secure, isolated microservice, it manages user credentials, issues cryptographic JSON Web Tokens (JWT), verifies operators via secure OTP codes, and monitors active logins across devices. 

By separating security operations from the API Gateway and Robot Control units, the Grabber architecture ensures that token validations, hashing, and email workflows scale independently and remain isolated from operational business logic.

---

## 📦 Project Structure

The codebase is built on clean architectural patterns separating SQLAlchemy schemas, Pydantic DTO parameters, execution routes, and helper services:

```
06-grabber-auth-service/
├── app/
│   ├── api/                 # Endpoint routers and dependency injection
│   │   ├── deps.py          # Database sessions, oauth2 handlers, current user validations
│   │   └── routes/          # Core routers (auth, profile, sessions, health)
│   ├── core/                # Database engines, security utils, and settings config
│   │   ├── config.py        # Pydantic Settings base config
│   │   ├── database.py      # SQLAlchemy connection engines and session base
│   │   └── security.py      # Passwords hashing, tokens, crypt hashes
│   ├── models/              # SQLAlchemy database tables (User, Session, OTP, Audit)
│   ├── schemas/             # Pydantic schema parameters validation models
│   ├── services/            # Custom logic services (Auth logic, SMTP mailer)
│   ├── templates/           # Email HTML files
│   └── main.py              # Application setup and static folder mounting
├── Dockerfile               # Slim Python multi-stage container setup
├── docker-compose.yml       # Development execution profile
├── requirements.txt         # Production library dependencies
└── README.md
```

### Module Code Index

Below is a detailed summary of key components within this codebase:

* **App Entry & Routers**:
  * [app/main.py](app/main.py): Sets up the FastAPI instance. Performs automatic metadata database table creation (`Base.metadata.create_all`), defines CORS middlewares, mounts static upload directories under `/uploads`, and registers core routes.
  * [app/api/deps.py](app/api/deps.py): Declares dependencies used across endpoint controllers, including the MySQL database session generator (`get_db`) and JWT token validator (`get_current_user`).

* **API Endpoint Routers**:
  * [app/api/routes/auth.py](app/api/routes/auth.py): Handles public endpoints for registration, OTP email verification, OTP resending, login processing (returns access tokens in the body and refresh tokens in HTTP-only cookies), logout cleanups, and password recovery.
  * [app/api/routes/profile.py](app/api/routes/profile.py): Governs profile interactions, allowing authenticated operators to query details, update names/phone settings, change passwords, and upload custom profile images.
  * [app/api/routes/sessions.py](app/api/routes/sessions.py): Lists active user sessions and allows operators to revoke specific device tokens.
  * [app/api/routes/health.py](app/api/routes/health.py): Basic health checks.

* **Core Configurations**:
  * [app/core/config.py](app/core/config.py): Core settings module reading variables from `.env`.
  * [app/core/security.py](app/core/security.py): Security utilities using `passlib` for password hashing, `python-jose` for JWT encoding/decoding, and SHA-256 for token hashing.
  * [app/core/database.py](app/core/database.py): Initializes the SQLAlchemy database engine with connection pooling (`pool_pre_ping=True`) and binds the session generator.

* **Database Models (SQLAlchemy)**:
  * [app/models/user.py](app/models/user.py): Defines the `users` table, storing UUID primary keys, user attributes, profile photo URLs, and status flags.
  * [app/models/session.py](app/models/session.py): Defines the `sessions` table tracking user refresh tokens, device info, IP addresses, expiration times, and revocation flags.
  * [app/models/email_verification.py](app/models/email_verification.py): Holds OTP hashes, verification counts, and expiration dates.
  * [app/models/password_reset.py](app/models/password_reset.py): Manages secure tokens used for password recovery.
  * [app/models/login_audit_log.py](app/models/login_audit_log.py): Logs successful and failed login attempts.

* **Validation Schemas (Pydantic)**:
  * [app/schemas/user.py](app/schemas/user.py): Defines schemas for registration, updates, and profile responses.
  * [app/schemas/auth.py](app/schemas/auth.py): Validates credentials, OTP requests, password updates, and session objects.

* **Services**:
  * [app/services/auth_service.py](app/services/auth_service.py): Core authentication logic, handling password hashing, OTP generation, user validation, and session lifecycle.
  * [app/services/email_service.py](app/services/email_service.py): Integrates with `fastapi-mail` to send HTML-formatted OTP codes and password reset links.

---

## 📊 Database Schema Specifications

The service connects to a MySQL database. On application startup, [app/main.py](app/main.py) automatically creates the following tables:

### 1. Users Table (`users`)
Stores user accounts and onboarding status flags.
* **Columns**:
  * `id`: `VARCHAR(36)` (Primary Key UUID)
  * `first_name`: `VARCHAR(100)`
  * `last_name`: `VARCHAR(100)`
  * `email`: `VARCHAR(255)` (Unique Indexed, Non-Nullable)
  * `password_hash`: `TEXT` (Bcrypt hash)
  * `phone`: `VARCHAR(20)`
  * `profile_image`: `TEXT` (Avatar url path)
  * `status`: `Enum('PENDING_VERIFICATION', 'ACTIVE', 'SUSPENDED', 'DELETED')`
  * `created_at` / `updated_at`: `DATETIME`

### 2. Sessions Table (`sessions`)
Tracks active logins and refresh tokens across user devices.
* **Columns**:
  * `id`: `VARCHAR(36)` (Primary Key UUID)
  * `user_id`: `VARCHAR(36)` (Foreign Key pointing to `users.id`)
  * `refresh_token_hash`: `TEXT` (SHA-256 hash of the refresh token)
  * `device_info`: `TEXT` (User-agent header description)
  * `ip_address`: `VARCHAR(45)`
  * `expires_at`: `DATETIME`
  * `is_revoked`: `BOOLEAN` (Defaults to `False`)
  * `created_at`: `DATETIME`

### 3. Email Verifications Table (`email_verifications`)
Stores temporary OTP verification codes.
* **Columns**:
  * `id`: `VARCHAR(36)` (Primary Key UUID)
  * `user_id`: `VARCHAR(36)` (Foreign Key pointing to `users.id`)
  * `otp_hash`: `TEXT` (SHA-256 hash of the 6-digit OTP code)
  * `expires_at`: `DATETIME` (Typically 10-minute expiry)
  * `attempts`: `INTEGER` (Counts failed input tries, max 3 attempts)
  * `is_used`: `BOOLEAN`
  * `created_at`: `DATETIME`

### 4. Password Resets Table (`password_resets`)
Tracks password reset tokens sent via email.
* **Columns**:
  * `id`: `VARCHAR(36)` (Primary Key UUID)
  * `user_id`: `VARCHAR(36)` (Foreign Key pointing to `users.id`)
  * `reset_token_hash`: `TEXT` (SHA-256 hash of the reset token)
  * `expires_at`: `DATETIME` (Typically 15-minute expiry)
  * `is_used`: `BOOLEAN`
  * `created_at`: `DATETIME`

### 5. Login Audit Logs Table (`login_audit_logs`)
Logs successful and failed authentication events.
* **Columns**:
  * `id`: `VARCHAR(36)` (Primary Key UUID)
  * `user_id`: `VARCHAR(36)` (Foreign Key pointing to `users.id`, nullable)
  * `action`: `Enum('LOGIN_SUCCESS', 'LOGIN_FAILED', 'LOGOUT', 'PASSWORD_RESET')`
  * `ip_address`: `VARCHAR(45)`
  * `user_agent`: `TEXT`
  * `created_at`: `DATETIME`

---

## ⚡ Key Workflows & API Specifications

### 1. Signup & Verification Flow
```
Client                      Auth Service                     SMTP Server
  |                              |                               |
  |--- POST /register ----------->|                               |
  |    (status: PENDING_VERIF)   |--- Send OTP email ----------->|
  |                              |                               |
  |--- POST /verify-otp -------->|                               |
  |    (status: ACTIVE)          |                               |
```
* **Register**: `POST /api/v1/auth/register`
  * Body: `{"first_name": "John", "last_name": "Doe", "email": "john@example.com", "password": "securepassword", "phone": "12345678"}`
  * Note: Registers the user with `PENDING_VERIFICATION` status and triggers an email with a 6-digit OTP code.
* **Verify OTP**: `POST /api/v1/auth/verify-otp`
  * Body: `{"email": "john@example.com", "otp": "123456"}`
  * Note: Validates the OTP hash and sets the user's status to `ACTIVE`.

### 2. Authentication Lifecycle
* **Login**: `POST /api/v1/auth/login`
  * Body: `{"email": "john@example.com", "password": "securepassword"}`
  * Response: `{"access_token": "...", "token_type": "bearer"}`
  * Cookie set: Sets `refresh_token` as an `HTTP-only` cookie.
* **Logout**: `POST /api/v1/auth/logout`
  * Note: Reads the `refresh_token` cookie, invalidates the session in the database, and clears the cookie.

### 3. Session Management
* **List Active Sessions**: `GET /api/v1/auth/sessions`
  * Response: A list of active sessions showing device info, IP address, and creation date.
* **Revoke Target Session**: `DELETE /api/v1/auth/sessions/{session_id}`
* **Revoke Other Sessions**: `POST /api/v1/auth/sessions/revoke-all`
  * Note: Invalidates all other active sessions for the user, except for the current session.

### 4. Profile Management
* **Get Current Profile**: `GET /api/v1/auth/me`
* **Update Profile Details**: `PATCH /api/v1/auth/me`
  * Body: `{"first_name": "Johnny", "last_name": "Doe", "phone": "98765432"}`
* **Upload Profile Photo**: `POST /api/v1/auth/me/image` (Multipart Form)
  * File: `file` (Binary Image File)
  * Note: Deletes the old profile photo from disk and saves the new image to `uploads/profile_images`.
* **Change Password**: `POST /api/v1/auth/me/change-password`
  * Body: `{"old_password": "old_secure_pwd", "new_password": "new_secure_pwd"}`

---

## 🚀 Getting Started

### 1. Environment Configurations
Create a `.env` configuration file in the project root:
```env
PROJECT_NAME="Grabber Auth Service"

# MySQL Database URI
DATABASE_URL="mysql+pymysql://thathsara:BandaPutha@db/grabber_auth"

# Cryptographic configurations
SECRET_KEY=Eiui9vAzU/yEexBweuDV9E/gDNvliTAoit1nKWTJDWQ=
ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=300
REFRESH_TOKEN_EXPIRE_DAYS=30

# SMTP Verification Mail configuration
MAIL_USERNAME="stormprojects47@gmail.com"
MAIL_PASSWORD="your-smtp-app-password"
MAIL_FROM="stormprojects47@gmail.com"
MAIL_PORT=587
MAIL_SERVER="smtp.gmail.com"
MAIL_FROM_NAME="Grabber"
MAIL_STARTTLS=True
MAIL_SSL_TLS=False
USE_CREDENTIALS=True
VALIDATE_CERTS=True
```

### 2. Local Virtual Environment Setup
Ensure you have Python 3.11+ and a MySQL instance running:
```bash
# Initialize and activate virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start FastAPI development server
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

### 3. Run via Docker Compose
Build and run the container locally:
```bash
# Starts the auth service container on port 8001
docker compose up -d --build
```

---

## 🔗 Related Grabber Repositories

| Repository | Purpose |
|---|---|
| [`01-grabber-architecture`](https://github.com/thathsarabandara/01-grabber-architecture) | System blueprints, MQTT schemas, and database designs |
| [`03-grabber-mobile-app`](https://github.com/thathsarabandara/03-grabber-mobile-app) | Flutter app remote teleoperation HUD |
| [`05-grabber-api-gateway`](https://github.com/thathsarabandara/05-grabber-api-gateway) | Inbound router proxying app REST & WebSocket requests |
| [`07-grabber-robot-service`](https://github.com/thathsarabandara/07-grabber-robot-service) | Service processing joint commands and homing schedules |
| [`08-grabber-telemetry-service`](https://github.com/thathsarabandara/08-grabber-telemetry-service) | Core service publishing live telemetry and webcam captures |
| [`09-grabber-ai-service`](https://github.com/thathsarabandara/09-grabber-ai-service) | Engine orchestrating autonomous sorting tasks and YOLO models |

---

<div align="center">
  <sub>Part of the <strong>Grabber</strong> AI-Powered Industrial Robotic Arm Platform</sub>
</div>
