# Week 8: Two-Factor Authentication System

A Django REST Framework API implementing Two-Factor Authentication with email OTP verification, role-based permissions, and account lockout.

## Features

- **Email OTP Login** — Login sends a 6-digit OTP to the user's email; must verify OTP to get a JWT token
- **Expiring OTPs** — OTPs expire after 5 minutes and are single-use
- **Role-Based Permissions** — Middleware enforces access based on user roles (admin / moderator / user)
- **Account Lockout** — Account locks after 5 consecutive failed login attempts
- **Password Hashing** — Passwords are hashed using Django's built-in PBKDF2 hasher

## Tech Stack

- Python 3 / Django 5.2 / Django REST Framework
- PyJWT (JSON Web Tokens)
- SQLite (development)

## Setup & Run

```bash
# Activate virtualenv
source ../week8/venv/bin/activate

# Run migrations
python manage.py makemigrations accounts
python manage.py migrate

# Start the server
python manage.py runserver
```

## API Endpoints

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register/` | Register a new user |
| POST | `/api/auth/login/` | Login → sends OTP to email |
| POST | `/api/auth/verify-otp/` | Verify OTP → returns JWT token |
| POST | `/api/auth/resend-otp/` | Resend a new OTP |

### Protected (require JWT in `Authorization: Bearer <token>` header)

| Method | Endpoint | Allowed Roles |
|--------|----------|---------------|
| GET | `/api/admin/dashboard/` | admin |
| GET | `/api/moderator/panel/` | admin, moderator |
| GET | `/api/user/profile/` | admin, moderator, user |

## Postman Collection

Import [postman_collection.json](./postman_collection.json) into Postman to test all endpoints.

The collection auto-saves the JWT token after OTP verification, so protected endpoints work automatically.

## Demo Flow

1. **Register** a user with a role (`admin`, `moderator`, or `user`)
2. **Login** with username and password → OTP is printed in the server terminal
3. **Verify OTP** using the 6-digit code → receive a JWT token
4. **Access protected endpoints** using the JWT token
5. **Test role restriction** — a `user` role trying `/api/admin/dashboard/` gets `403 Forbidden`
6. **Test lockout** — 5 wrong passwords locks the account

> **Note:** Emails are printed to the server terminal (console email backend) instead of being sent to a real inbox. This is standard for development.


