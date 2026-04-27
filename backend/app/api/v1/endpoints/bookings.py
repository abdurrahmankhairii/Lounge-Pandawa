"""
Booking Endpoints — Slot availability, Create, Cancel, Status
"""
from datetime import date, datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db, get_redis
from app.core.security import get_current_user, require_roles, Role
from app.services.booking_service import BookingService
from app.schemas.schemas import BookingCreate, BookingResponse, BookingStatusUpdate, MessageResponse

router = APIRouter(prefix="/bookings", tags=["Bookings"])


@router.get("/slots")
async def get_available_slots(
    target_date: date = Query(default=None),
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
):
    if not target_date:
        target_date = datetime.now(timezone.utc).date()
    svc = BookingService(db, redis)
    await svc.ensure_slots_exist(target_date)
    return await svc.get_available_slots(target_date)


@router.post("", response_model=BookingResponse)
async def create_booking(
    data: BookingCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
):
    svc = BookingService(db, redis)
    booking = await svc.create_booking(data, current_user["sub"])
    return booking


@router.get("/mine")
async def get_my_bookings(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
):
    svc = BookingService(db, redis)
    return await svc.get_user_bookings(current_user["sub"])


@router.get("/{code}")
async def get_booking_by_code(
    code: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
):
    svc = BookingService(db, redis)
    booking = await svc.get_booking_by_code(code)
    if not booking:
        from fastapi import HTTPException
        raise HTTPException(404, "Booking tidak ditemukan")
    return booking


@router.put("/{booking_id}/cancel", response_model=MessageResponse)
async def cancel_booking(
    booking_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
):
    svc = BookingService(db, redis)
    await svc.cancel_booking(booking_id, current_user["sub"])
    return {"message": "Booking berhasil dibatalkan"}


@router.get("/capacity/status")
async def get_capacity_status(
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
):
    svc = BookingService(db, redis)
    return await svc.get_capacity_status()
