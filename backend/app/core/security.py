"""
Security Module — JWT, Password Hashing, RBAC, 2FA
Arjuna Smart Lounge App
"""
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import List, Optional, Set
from uuid import uuid4

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
import pyotp

from app.core.config import settings

# ============================================================
# Password Hashing (bcrypt)
# ============================================================
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)


def hash_password(password: str) -> str:
    """Hash a plain-text password using bcrypt with 12 rounds."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a bcrypt hash."""
    return pwd_context.verify(plain_password, hashed_password)


# ============================================================
# Role-Based Access Control (RBAC)
# ============================================================
class Role(str, Enum):
    GUEST = "GUEST"
    KITCHEN = "KITCHEN"
    STAFF = "STAFF"
    BLU_VIEWER = "BLU_VIEWER"
    FINANCE = "FINANCE"
    MANAGER = "MANAGER"
    SUPER_ADMIN = "SUPER_ADMIN"


ROLE_HIERARCHY = [
    Role.GUEST, Role.KITCHEN, Role.STAFF,
    Role.BLU_VIEWER, Role.FINANCE, Role.MANAGER, Role.SUPER_ADMIN
]


# ============================================================
# JWT Token Management
# ============================================================
security = HTTPBearer(auto_error=False)


def create_access_token(
    user_id: str,
    roles: List[str],
    extra_claims: dict = None
) -> str:
    """Create a JWT access token with user_id and roles in the payload."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "roles": roles,
        "jti": str(uuid4()),
        "iat": now,
        "exp": now + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES),
        "type": "access",
    }
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(user_id: str) -> str:
    """Create a JWT refresh token (longer-lived)."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "jti": str(uuid4()),
        "iat": now,
        "exp": now + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS),
        "type": "refresh",
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    """Decode and verify a JWT token. Raises HTTPException on failure."""
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token tidak valid atau sudah kadaluarsa",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
):
    """Dependency: extract and validate the current user from JWT."""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Autentikasi diperlukan",
            headers={"WWW-Authenticate": "Bearer"},
        )
    payload = decode_token(credentials.credentials)
    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tipe token tidak valid",
        )
    return payload


def require_roles(*allowed_roles: Role):
    """Dependency factory: restrict access to specific roles."""
    async def checker(current_user: dict = Depends(get_current_user)):
        user_roles: Set[str] = set(current_user.get("roles", []))
        allowed: Set[str] = {r.value for r in allowed_roles}
        if not user_roles.intersection(allowed):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Akses ditolak: role tidak memadai",
            )
        return current_user
    return checker


# ============================================================
# Two-Factor Authentication (TOTP)
# ============================================================
def generate_totp_secret() -> str:
    """Generate a new TOTP secret for 2FA setup."""
    return pyotp.random_base32()


def get_totp_uri(secret: str, email: str) -> str:
    """Generate a TOTP provisioning URI for QR code display."""
    totp = pyotp.TOTP(secret)
    return totp.provisioning_uri(name=email, issuer_name="Arjuna Lounge")


def verify_totp(secret: str, code: str) -> bool:
    """Verify a TOTP code against the secret."""
    totp = pyotp.TOTP(secret)
    return totp.verify(code, valid_window=1)


# ============================================================
# Rate Limiting Helper
# ============================================================
async def check_rate_limit(
    redis_client,
    key: str,
    max_attempts: int = 5,
    window_seconds: int = 900,  # 15 minutes
) -> bool:
    """Check and increment rate limit. Returns True if limit exceeded."""
    current = await redis_client.get(key)
    if current and int(current) >= max_attempts:
        return True
    pipe = redis_client.pipeline()
    pipe.incr(key)
    pipe.expire(key, window_seconds)
    await pipe.execute()
    return False


# ============================================================
# Password Policy Validation
# ============================================================
def validate_password_strength(password: str) -> Optional[str]:
    """Validate password meets minimum security requirements.
    Returns error message if invalid, None if valid."""
    if len(password) < 8:
        return "Password minimal 8 karakter"
    if not any(c.isupper() for c in password):
        return "Password harus mengandung huruf besar"
    if not any(c.islower() for c in password):
        return "Password harus mengandung huruf kecil"
    if not any(c.isdigit() for c in password):
        return "Password harus mengandung angka"
    if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
        return "Password harus mengandung simbol"
    return None
