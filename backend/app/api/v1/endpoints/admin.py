"""
Admin Endpoints — User management, Settings, Audit logs, Reports
"""
from datetime import date, datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from app.core.database import get_db
from app.core.security import require_roles, Role, hash_password
from app.models.models import User, Role as RoleModel, UserRole, Booking, Order, Payment, AuditLog, LoungeSettings, TimeSlot
from app.schemas.schemas import UserCreate, UserUpdate, UserResponse, LoungeSettingsUpdate, MessageResponse

router = APIRouter(prefix="/admin", tags=["Admin Dashboard"])


# USER MANAGEMENT
@router.get("/users")
async def list_users(
    page: int = 1, per_page: int = 20,
    current_user: dict = Depends(require_roles(Role.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    offset = (page - 1) * per_page
    total = await db.execute(select(func.count()).select_from(User))
    result = await db.execute(select(User).offset(offset).limit(per_page).order_by(User.created_at.desc()))
    users = result.scalars().all()
    user_list = []
    for u in users:
        roles_r = await db.execute(select(RoleModel.name).join(UserRole).where(UserRole.user_id == u.id))
        roles = [r for r in roles_r.scalars().all()]
        user_list.append({
            "id": str(u.id), "email": u.email, "phone": u.phone,
            "full_name": u.full_name, "is_active": u.is_active,
            "is_verified": u.is_verified, "roles": roles,
            "last_login": u.last_login, "created_at": u.created_at,
        })
    return {"items": user_list, "total": total.scalar(), "page": page, "per_page": per_page}


@router.post("/users")
async def create_user(
    data: UserCreate,
    current_user: dict = Depends(require_roles(Role.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    existing = await db.execute(select(User).where(User.email == data.email))
    if existing.scalar_one_or_none():
        raise HTTPException(409, "Email sudah terdaftar")
    user = User(email=data.email, phone=data.phone, full_name=data.full_name, password_hash=hash_password(data.password), is_active=True, is_verified=True)
    db.add(user)
    await db.flush()
    for role_name in data.roles:
        role_r = await db.execute(select(RoleModel).where(RoleModel.name == role_name))
        role = role_r.scalar_one_or_none()
        if role:
            db.add(UserRole(user_id=user.id, role_id=role.id))
    await db.commit()
    return {"message": "User berhasil dibuat", "user_id": str(user.id)}


@router.put("/users/{user_id}")
async def update_user(
    user_id: str, data: UserUpdate,
    current_user: dict = Depends(require_roles(Role.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(404, "User tidak ditemukan")
    for k, v in data.model_dump(exclude_unset=True, exclude={"roles"}).items():
        setattr(user, k, v)
    if data.roles is not None:
        await db.execute(UserRole.__table__.delete().where(UserRole.user_id == user.id))
        for rn in data.roles:
            rr = await db.execute(select(RoleModel).where(RoleModel.name == rn))
            r = rr.scalar_one_or_none()
            if r:
                db.add(UserRole(user_id=user.id, role_id=r.id))
    await db.commit()
    return {"message": "User berhasil diupdate"}


@router.delete("/users/{user_id}")
async def deactivate_user(
    user_id: str,
    current_user: dict = Depends(require_roles(Role.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(404, "User tidak ditemukan")
    user.is_active = False
    await db.commit()
    return {"message": "User berhasil dinonaktifkan"}


# SETTINGS
@router.get("/settings")
async def get_settings(
    current_user: dict = Depends(require_roles(Role.MANAGER, Role.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(LoungeSettings))
    return result.scalars().all()


@router.put("/settings")
async def update_settings(
    data: LoungeSettingsUpdate,
    current_user: dict = Depends(require_roles(Role.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    for key, value in data.settings.items():
        result = await db.execute(select(LoungeSettings).where(LoungeSettings.key == key))
        setting = result.scalar_one_or_none()
        if setting:
            setting.value = str(value)
            setting.updated_by = current_user["sub"]
        else:
            db.add(LoungeSettings(key=key, value=str(value), updated_by=current_user["sub"]))
    await db.commit()
    return {"message": "Settings berhasil diupdate"}


# AUDIT LOGS
@router.get("/audit")
async def get_audit_logs(
    page: int = 1, per_page: int = 50,
    action: Optional[str] = None,
    current_user: dict = Depends(require_roles(Role.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    query = select(AuditLog).order_by(AuditLog.created_at.desc())
    if action:
        query = query.where(AuditLog.action == action)
    offset = (page - 1) * per_page
    query = query.offset(offset).limit(per_page)
    result = await db.execute(query)
    return result.scalars().all()


# REPORTS
@router.get("/reports/daily")
async def daily_report(
    report_date: Optional[date] = None,
    current_user: dict = Depends(require_roles(Role.MANAGER, Role.FINANCE, Role.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    if not report_date:
        report_date = datetime.now(timezone.utc).date()
    bookings = await db.execute(
        select(func.count(), Booking.status)
        .join(TimeSlot).where(TimeSlot.slot_date == report_date)
        .group_by(Booking.status)
    )
    booking_stats = {status: count for count, status in bookings.all()}
    revenue = await db.execute(
        select(func.coalesce(func.sum(Payment.amount), 0))
        .where(and_(func.date(Payment.paid_at) == report_date, Payment.status == "settlement"))
    )
    total_rev = revenue.scalar() or 0
    orders_count = await db.execute(
        select(func.count()).select_from(Order)
        .where(func.date(Order.created_at) == report_date)
    )
    total_orders = orders_count.scalar() or 0
    return {
        "date": report_date.isoformat(),
        "total_bookings": sum(booking_stats.values()),
        "checked_in": booking_stats.get("checked_in", 0),
        "no_shows": booking_stats.get("no_show", 0),
        "cancelled": booking_stats.get("cancelled", 0),
        "total_orders": total_orders,
        "total_revenue": float(total_rev),
        "booking_breakdown": booking_stats,
    }


@router.get("/reports/revenue")
async def revenue_report(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    current_user: dict = Depends(require_roles(Role.FINANCE, Role.MANAGER, Role.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    if not end_date:
        end_date = datetime.now(timezone.utc).date()
    if not start_date:
        from datetime import timedelta
        start_date = end_date - timedelta(days=30)
    revenue = await db.execute(
        select(
            func.date(Payment.paid_at).label("day"),
            func.sum(Payment.amount).label("total"),
            func.count().label("transactions"),
        )
        .where(and_(
            Payment.status == "settlement",
            func.date(Payment.paid_at) >= start_date,
            func.date(Payment.paid_at) <= end_date,
        ))
        .group_by(func.date(Payment.paid_at))
        .order_by(func.date(Payment.paid_at))
    )
    daily = [{"date": str(r.day), "revenue": float(r.total), "transactions": r.transactions} for r in revenue.all()]
    total = sum(d["revenue"] for d in daily)
    return {
        "period": f"{start_date} - {end_date}",
        "total_revenue": total,
        "total_transactions": sum(d["transactions"] for d in daily),
        "daily_breakdown": daily,
    }
