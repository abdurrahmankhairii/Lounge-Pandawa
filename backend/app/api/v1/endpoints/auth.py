"""
Auth Endpoints — Register, Login, Refresh, 2FA
"""
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db, get_redis
from app.core.security import (
    hash_password, verify_password, create_access_token,
    create_refresh_token, decode_token, get_current_user,
    validate_password_strength, check_rate_limit,
    generate_totp_secret, get_totp_uri, verify_totp
)
from app.models.models import User, Role, UserRole
from app.schemas.schemas import (
    UserRegister, UserLogin, TokenResponse, UserResponse,
    RefreshTokenRequest, TwoFactorVerify, MessageResponse
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=MessageResponse)
async def register(data: UserRegister, db: AsyncSession = Depends(get_db)):
    pw_err = validate_password_strength(data.password)
    if pw_err:
        raise HTTPException(400, pw_err)

    existing = await db.execute(select(User).where(User.email == data.email))
    if existing.scalar_one_or_none():
        raise HTTPException(409, "Email sudah terdaftar")

    if data.phone:
        phone_check = await db.execute(select(User).where(User.phone == data.phone))
        if phone_check.scalar_one_or_none():
            raise HTTPException(409, "Nomor telepon sudah terdaftar")

    user = User(
        email=data.email, phone=data.phone,
        full_name=data.full_name,
        password_hash=hash_password(data.password),
        is_active=True, is_verified=False,
    )
    db.add(user)
    await db.flush()

    guest_role = await db.execute(select(Role).where(Role.name == "GUEST"))
    role = guest_role.scalar_one_or_none()
    if role:
        db.add(UserRole(user_id=user.id, role_id=role.id))

    await db.commit()
    return {"message": "Registrasi berhasil. Silakan verifikasi email Anda."}


@router.post("/login", response_model=TokenResponse)
async def login(data: UserLogin, request: Request, db: AsyncSession = Depends(get_db), redis=Depends(get_redis)):
    ip = request.client.host if request.client else "unknown"
    rate_key = f"login_attempts:{ip}"
    if await check_rate_limit(redis, rate_key):
        raise HTTPException(429, "Terlalu banyak percobaan. Coba lagi dalam 15 menit.")

    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(401, "Email atau password salah")

    if not user.is_active:
        raise HTTPException(403, "Akun dinonaktifkan")

    if user.locked_until and user.locked_until > datetime.now(timezone.utc):
        raise HTTPException(423, "Akun terkunci sementara")

    roles_result = await db.execute(
        select(Role.name).join(UserRole).where(UserRole.user_id == user.id)
    )
    roles = [r for r in roles_result.scalars().all()]

    user.failed_attempts = 0
    user.last_login = datetime.now(timezone.utc)
    await db.commit()

    access_token = create_access_token(str(user.id), roles)
    refresh_token = create_refresh_token(str(user.id))

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": 1800,
        "user": UserResponse(
            id=user.id, email=user.email, phone=user.phone,
            full_name=user.full_name, is_active=user.is_active,
            is_verified=user.is_verified, roles=roles,
            created_at=user.created_at,
        ),
    }


@router.post("/refresh", response_model=dict)
async def refresh_token(data: RefreshTokenRequest):
    payload = decode_token(data.refresh_token)
    if payload.get("type") != "refresh":
        raise HTTPException(401, "Token bukan refresh token")
    new_access = create_access_token(payload["sub"], payload.get("roles", []))
    return {"access_token": new_access, "token_type": "bearer"}


@router.post("/logout", response_model=MessageResponse)
async def logout(current_user: dict = Depends(get_current_user)):
    return {"message": "Logout berhasil"}


@router.post("/setup-2fa", response_model=dict)
async def setup_2fa(current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.id == current_user["sub"]))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(404, "User tidak ditemukan")
    secret = generate_totp_secret()
    user.totp_secret = secret
    await db.commit()
    uri = get_totp_uri(secret, user.email)
    return {"secret": secret, "uri": uri}


@router.post("/verify-2fa", response_model=MessageResponse)
async def verify_2fa_code(data: TwoFactorVerify, current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.id == current_user["sub"]))
    user = result.scalar_one_or_none()
    if not user or not user.totp_secret:
        raise HTTPException(400, "2FA belum di-setup")
    if not verify_totp(user.totp_secret, data.code):
        raise HTTPException(401, "Kode 2FA tidak valid")
    return {"message": "Verifikasi 2FA berhasil"}
