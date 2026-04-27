"""
Staff Endpoints — Check-in, Walk-in, Queue Management
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db, get_redis
from app.core.security import require_roles, Role
from app.services.booking_service import BookingService
from app.services.queue_service import QueueService
from app.schemas.schemas import WalkInBookingCreate, BookingStatusUpdate, MessageResponse

router = APIRouter(prefix="/staff", tags=["Staff Portal"])


@router.post("/bookings/walkin")
async def create_walkin_booking(
    data: WalkInBookingCreate,
    current_user: dict = Depends(require_roles(Role.STAFF, Role.MANAGER, Role.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
):
    svc = BookingService(db, redis)
    booking = await svc.create_walkin_booking(data, current_user["sub"])
    queue_svc = QueueService(db, redis)
    ticket = await queue_svc.join_queue(str(booking.id))
    return {"booking": booking, "queue_ticket": ticket}


@router.put("/bookings/{booking_id}/checkin")
async def checkin_booking(
    booking_id: str,
    current_user: dict = Depends(require_roles(Role.STAFF, Role.MANAGER, Role.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
):
    svc = BookingService(db, redis)
    booking = await svc.checkin_booking(booking_id)
    queue_svc = QueueService(db, redis)
    ticket = await queue_svc.join_queue(str(booking.id))
    return {"booking": booking, "queue_ticket": ticket}


@router.put("/bookings/{booking_id}/status")
async def update_booking_status(
    booking_id: str, data: BookingStatusUpdate,
    current_user: dict = Depends(require_roles(Role.STAFF, Role.MANAGER, Role.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
):
    from sqlalchemy import select
    from app.models.models import Booking
    result = await db.execute(select(Booking).where(Booking.id == booking_id))
    booking = result.scalar_one_or_none()
    if not booking:
        from fastapi import HTTPException
        raise HTTPException(404, "Booking tidak ditemukan")
    booking.status = data.status
    await db.commit()
    return {"message": f"Status diupdate ke {data.status}"}


@router.get("/bookings/today")
async def get_today_bookings(
    current_user: dict = Depends(require_roles(Role.STAFF, Role.MANAGER, Role.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
):
    svc = BookingService(db, redis)
    return await svc.get_today_bookings()


@router.get("/capacity")
async def get_capacity(
    current_user: dict = Depends(require_roles(Role.STAFF, Role.MANAGER, Role.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
):
    svc = BookingService(db, redis)
    return await svc.get_capacity_status()


@router.post("/queue/call")
async def call_next_queue(
    current_user: dict = Depends(require_roles(Role.STAFF, Role.MANAGER, Role.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
):
    svc = QueueService(db, redis)
    ticket = await svc.call_next()
    if not ticket:
        return {"message": "Tidak ada antrian yang menunggu"}
    return ticket


@router.put("/queue/{ticket_id}/done")
async def complete_queue(
    ticket_id: str,
    current_user: dict = Depends(require_roles(Role.STAFF, Role.MANAGER, Role.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
):
    svc = QueueService(db, redis)
    return await svc.complete_serving(ticket_id)


@router.put("/queue/{ticket_id}/skip")
async def skip_queue(
    ticket_id: str,
    current_user: dict = Depends(require_roles(Role.STAFF, Role.MANAGER, Role.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
):
    svc = QueueService(db, redis)
    return await svc.skip_ticket(ticket_id)
