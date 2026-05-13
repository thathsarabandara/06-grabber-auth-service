# 🔐 Grabber Auth Service

> **Repository `06`** · Security-critical authentication service for the Grabber platform. Handles JWT issuance, session management, email verification, robot serial-key binding, and role-based access control.

[![Language](https://img.shields.io/badge/Language-Python-3776AB?logo=python)]()
[![Framework](https://img.shields.io/badge/Framework-FastAPI-009688?logo=fastapi)]()
[![Database](https://img.shields.io/badge/Database-PostgreSQL%20%2B%20Redis-blue)]()
[![Security](https://img.shields.io/badge/Security-JWT%20%7C%20RBAC%20%7C%20OTP-red)]()
[![Status](https://img.shields.io/badge/Status-Planned-yellow)]()

---

## 🧭 What Is This Repository?

This is the **dedicated authentication and authorization service** for the Grabber platform, implemented in **Python / FastAPI**. It is intentionally deployed as a **separate, isolated microservice** — authentication vulnerabilities must be patchable independently, and robot binding security cannot share a deployment unit with business logic.

---

## 📦 Module Structure

```
06-grabber-auth-service/
├── app/
│   ├── auth/              ← Register, login, logout, JWT issue/refresh/revoke
│   ├── verification/      ← Email OTP verification, password reset flow
│   ├── sessions/          ← HTTP-only cookies, session revocation, security alerts
│   ├── robot_binding/     ← Serial-key pairing, ownership transfer, device deregistration
│   ├── rbac/              ← Roles: owner, operator, viewer — permission matrix
│   └── models/            ← SQLAlchemy / SQLModel database definitions
├── migrations/            ← Alembic database migrations (PostgreSQL)
├── tests/                 ← Unit and integration tests
├── requirements.txt
└── README.md
```

---

## 🔑 API Endpoints

### Authentication
- `POST /auth/register` - Create new user
- `POST /auth/login` - Authenticate & get JWT
- `POST /auth/logout` - Revoke session
- `POST /auth/refresh` - Refresh access token

### Robot Binding
- `POST /robots/bind` - Pair a robot serial key to user account
- `DELETE /robots/{id}/unbind` - Deregister robot
- `GET /robots` - List owned robots

---

## 🛡️ Security Design

| Feature | Implementation |
|---|---|
| **Framework** | FastAPI (Asynchronous) |
| **Token Storage** | JWT in HTTP-only, Secure, SameSite cookies |
| **Revocation** | Token blacklist stored in Redis |
| **Password Hashing** | passlib (bcrypt) |
| **Email Verification** | FastAPI-Mail / SMTP |

---

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- PostgreSQL ≥ 14
- Redis ≥ 7

### Setup
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Run migrations
alembic upgrade head
# Start dev server
uvicorn app.main:app --reload
```

---

## 🔗 Related Repositories
| Repo | Role |
|---|---|
| [`01-grabber-architecture`](../01-grabber-architecture) | Security model and auth flow design |
| [`05-grabber-api-gateway`](../05-grabber-api-gateway) | Forwards JWT verification requests here |
| [`07-grabber-robot-service`](../07-grabber-robot-service) | Consumes ownership and role info |

---
<div align="center">
  <sub>Part of the <strong>Grabber</strong> AI-Powered Industrial Robotic Arm Platform</sub>
</div>
