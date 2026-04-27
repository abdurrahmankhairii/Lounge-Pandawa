"""
Booking Service — Anti-Collision Distributed Lock
Arjuna Smart Lounge App
"""
import uuid
import json
from contextlib import asynccontextmanager
from datetime import datetime, date, time, timezone, timedelta
from typing import Optional, List

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
import redis.asyncio as aioredis

from app.models.models import Booking, TimeSlot, QueueTicket
from app.schemas.schemas import BookingCreate, WalkInBookingCreate
from app.core.config import settings


class BookingService:
    """Handles all booking operations with anti-collision distributed locking."""

    LOCK_TIMEOUT = 10  # seconds

    def __init__(self, db: AsyncSession, redis_client: aioredis.Redis):
        self.db = db
        self.redis = redis_client

    # ============================================================
    # Distributed Lock
    # ============================================================
    @asynccontextmanager
    async def slot_lock(self, slot_id: int):
        """Acquire a distributed lock for a specific booking slot.
        Uses Redis SETNX with unique value for ownership verification."""
        lock_key = f"slot_lock:{slot_id}"
        lock_value = str(uuid.uuid4())

        acquired = await self.redis.set(
            lock_key, lock_value,
            nx=True,
            ex=self.LOCK_TIMEOUT,
        )

        if not acquired:
            raise HTTPException(
                status_code=409,
                detail="Slot sedang diproses oleh pengguna lain, silakan coba lagi dalam beberapa detik"
            )

        try:
            yield
        finally:
            # Release lock only if we own it (Lua script for atomicity)
            lua_script = """
                if redis.call('get', KEYS[1]) == ARGV[1] then
                    return redis.call('del', KEYS[1])
                else
                    return 0
                end
            """
            await self.redis.eval(lua_script, 1, lock_key, lock_value)

    # ============================================================
    # Generate Booking Code
    # ============================================================
    async def generate_booking_code(self) -> str:
        """Generate unique booking code: ARJ-YYYYMMDD-NNNN"""
        today = datetime.now(timezone.utc).strftime("%Y%m%d")
        counter_key = f"booking_counter:{today}"
        count = await self.redis.incr(counter_key)
        await self.redis.expire(counter_key, 86400 * 2)  # 2 days
        return f"ARJ-{today}-{count:04d}"

    # ============================================================
    # Slot Management
    # ============================================================
    async def get_available_slots(
        self,
        target_date: date,
        use_cache: bool = True
    ) -> List[TimeSlot]:
        """Get available time slots for a given date. Cached in Redis for 30s."""
        cache_key = f"slots:{target_date.isoformat()}"

        if use_cache:
            cached = await self.redis.get(cache_key)
            if cached:
                return json.loads(cached)

        result = await self.db.execute(
            select(TimeSlot)
            .where(
                and_(
                    TimeSlot.slot_date == target_date,
                    TimeSlot.is_active == True,
                )
            )
            .order_by(TimeSlot.start_time)
        )
        slots = result.scalars().all()

        slot_data = []
        for slot in slots:
            slot_dict = {
                "id": slot.id,
                "slot_date": slot.slot_date.isoformat(),
                "start_time": slot.start_time.isoformat(),
                "end_time": slot.end_time.isoformat(),
                "capacity": slot.capacity,
                "booked_count": slot.booked_count,
                "is_active": slot.is_active,
                "available": max(0, slot.capacity - slot.booked_count),
            }
            slot_data.append(slot_dict)

        await self.redis.setex(cache_key, 30, json.dumps(slot_data))
        return slot_data

    async def ensure_slots_exist(self, target_date: date):
        """Auto-generate time slots for a date if they don't exist."""
        existing = await self.db.execute(
            select(func.count()).where(TimeSlot.slot_date == target_date)
        )
        count = existing.scalar()
        if count > 0:
            return

        # Generate slots from 07:00 to 20:00, each 1 hour
        start_hour = 7
        end_hour = 20
        for hour in range(start_hour, end_hour):
            slot = TimeSlot(
                slot_date=target_date,
                start_time=time(hour, 0),
                end_time=time(hour + 1, 0) if hour + 1 <= 23 else time(23, 59),
                capacity=settings.DEFAULT_SLOT_CAPACITY,
                booked_count=0,
                is_active=True,
            )
            self.db.add(slot)
        await self.db.commit()

    # ============================================================
    # Create Booking (with Anti-Collision)
    # ============================================================
    async def create_booking(
        self,
        data: BookingCreate,
        user_id: str,
    ) -> Booking:
        """Create a new booking with distributed lock protection."""
        async with self.slot_lock(data.slot_id):
            # 1. Re-check capacity (fresh from DB, bypass cache)
            result = await self.db.execute(
                select(TimeSlot).where(TimeSlot.id == data.slot_id)
            )
            slot = result.scalar_one_or_none()

            if not slot:
                raise HTTPException(404, "Slot waktu tidak ditemukan")
            if not slot.is_active:
                raise HTTPException(409, "Slot waktu sudah tidak aktif")
            if slot.booked_count >= slot.capacity:
                raise HTTPException(409, "Slot sudah penuh, silakan pilih slot lain")

            # 2. Check for duplicate booking
            existing = await self.db.execute(
                select(Booking).where(
                    and_(
                        Booking.user_id == user_id,
                        Booking.slot_id == data.slot_id,
                        Booking.status.in_(["pending", "confirmed", "checked_in"]),
                    )
                )
            )
            if existing.scalar_one_or_none():
                raise HTTPException(409, "Anda sudah memiliki booking aktif di slot ini")

            # 3. Create booking
            booking_code = await self.generate_booking_code()
            booking = Booking(
                booking_code=booking_code,
                user_id=user_id,
                slot_id=data.slot_id,
                guest_name=data.guest_name,
                guest_phone=data.guest_phone,
                guest_email=data.guest_email,
                guest_type=data.guest_type,
                airline=data.airline,
                notes=data.notes,
                status="confirmed",
                source="online",
            )
            slot.booked_count += 1

            self.db.add(booking)
            await self.db.commit()
            await self.db.refresh(booking)

            # 4. Invalidate slot cache
            cache_key = f"slots:{slot.slot_date.isoformat()}"
            await self.redis.delete(cache_key)

            return booking

    # ============================================================
    # Walk-in Booking (Staff)
    # ============================================================
    async def create_walkin_booking(
        self,
        data: WalkInBookingCreate,
        staff_id: str,
    ) -> Booking:
        """Create a walk-in booking for a guest who arrives without reservation."""
        today = datetime.now(timezone.utc).date()
        now = datetime.now(timezone.utc).time()

        # Find current active slot
        result = await self.db.execute(
            select(TimeSlot).where(
                and_(
                    TimeSlot.slot_date == today,
                    TimeSlot.start_time <= now,
                    TimeSlot.end_time > now,
                    TimeSlot.is_active == True,
                )
            )
        )
        slot = result.scalar_one_or_none()

        if not slot:
            # Try the next available slot
            result = await self.db.execute(
                select(TimeSlot).where(
                    and_(
                        TimeSlot.slot_date == today,
                        TimeSlot.start_time > now,
                        TimeSlot.is_active == True,
                    )
                ).order_by(TimeSlot.start_time).limit(1)
            )
            slot = result.scalar_one_or_none()

        if not slot:
            raise HTTPException(409, "Tidak ada slot tersedia hari ini")

        async with self.slot_lock(slot.id):
            # Re-check capacity
            await self.db.refresh(slot)
            if slot.booked_count >= slot.capacity:
                raise HTTPException(
                    409,
                    "Lounge sedang penuh. Tamu dapat masuk waiting list."
                )

            booking_code = await self.generate_booking_code()
            booking = Booking(
                booking_code=booking_code,
                slot_id=slot.id,
                guest_name=data.guest_name,
                guest_phone=data.guest_phone,
                guest_type=data.guest_type,
                airline=data.airline,
                notes=data.notes,
                status="checked_in",
                source="walk_in",
                created_by=staff_id,
                check_in_time=datetime.now(timezone.utc),
            )
            slot.booked_count += 1

            self.db.add(booking)
            await self.db.commit()
            await self.db.refresh(booking)

            # Invalidate cache
            cache_key = f"slots:{today.isoformat()}"
            await self.redis.delete(cache_key)

            return booking

    # ============================================================
    # Check-in
    # ============================================================
    async def checkin_booking(self, booking_id: str) -> Booking:
        """Check in a guest with an existing booking."""
        result = await self.db.execute(
            select(Booking).where(Booking.id == booking_id)
        )
        booking = result.scalar_one_or_none()

        if not booking:
            raise HTTPException(404, "Booking tidak ditemukan")
        if booking.status not in ["pending", "confirmed"]:
            raise HTTPException(409, f"Booking tidak dapat di-check-in (status: {booking.status})")

        booking.status = "checked_in"
        booking.check_in_time = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(booking)
        return booking

    # ============================================================
    # Cancel Booking
    # ============================================================
    async def cancel_booking(self, booking_id: str, user_id: str) -> Booking:
        """Cancel a booking and release the slot capacity."""
        result = await self.db.execute(
            select(Booking).where(Booking.id == booking_id)
        )
        booking = result.scalar_one_or_none()

        if not booking:
            raise HTTPException(404, "Booking tidak ditemukan")
        if str(booking.user_id) != user_id:
            raise HTTPException(403, "Anda tidak memiliki akses ke booking ini")
        if booking.status in ["completed", "cancelled"]:
            raise HTTPException(409, "Booking sudah selesai atau dibatalkan")

        booking.status = "cancelled"

        # Release slot capacity
        if booking.slot_id:
            slot_result = await self.db.execute(
                select(TimeSlot).where(TimeSlot.id == booking.slot_id)
            )
            slot = slot_result.scalar_one_or_none()
            if slot and slot.booked_count > 0:
                slot.booked_count -= 1

        await self.db.commit()
        await self.db.refresh(booking)
        return booking

    # ============================================================
    # Get Bookings
    # ============================================================
    async def get_user_bookings(self, user_id: str) -> List[Booking]:
        """Get all bookings for a specific user."""
        result = await self.db.execute(
            select(Booking)
            .where(Booking.user_id == user_id)
            .order_by(Booking.created_at.desc())
        )
        return result.scalars().all()

    async def get_booking_by_code(self, code: str) -> Optional[Booking]:
        """Get a booking by its code."""
        result = await self.db.execute(
            select(Booking).where(Booking.booking_code == code)
        )
        return result.scalar_one_or_none()

    async def get_today_bookings(self, status: Optional[str] = None) -> List[Booking]:
        """Get all bookings for today, optionally filtered by status."""
        today = datetime.now(timezone.utc).date()
        query = (
            select(Booking)
            .join(TimeSlot)
            .where(TimeSlot.slot_date == today)
        )
        if status:
            query = query.where(Booking.status == status)
        query = query.order_by(Booking.created_at)

        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_capacity_status(self) -> dict:
        """Get current lounge capacity status for today."""
        today = datetime.now(timezone.utc).date()
        now = datetime.now(timezone.utc).time()

        result = await self.db.execute(
            select(TimeSlot).where(
                and_(
                    TimeSlot.slot_date == today,
                    TimeSlot.start_time <= now,
                    TimeSlot.end_time > now,
                    TimeSlot.is_active == True,
                )
            )
        )
        current_slot = result.scalar_one_or_none()

        if not current_slot:
            return {
                "total_capacity": 0,
                "occupied": 0,
                "available": 0,
                "occupancy_rate": 0,
            }

        return {
            "total_capacity": current_slot.capacity,
            "occupied": current_slot.booked_count,
            "available": max(0, current_slot.capacity - current_slot.booked_count),
            "occupancy_rate": round(
                (current_slot.booked_count / current_slot.capacity) * 100, 1
            ) if current_slot.capacity > 0 else 0,
            "slot_time": f"{current_slot.start_time.isoformat()} - {current_slot.end_time.isoformat()}",
        }
