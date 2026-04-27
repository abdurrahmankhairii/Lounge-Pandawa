"""
Queue Service — WAR Queue System
"""
import time as time_module
from datetime import datetime, timezone
from typing import Optional
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import redis.asyncio as aioredis
from app.models.models import QueueTicket, Booking
from app.core.config import settings


class QueueService:
    def __init__(self, db: AsyncSession, redis_client: aioredis.Redis):
        self.db = db
        self.redis = redis_client

    def _queue_key(self, lid: str, d: str) -> str:
        return f"queue:{lid}:{d}"

    def _serving_key(self, lid: str, d: str) -> str:
        return f"serving:{lid}:{d}"

    def _current_key(self, lid: str, d: str) -> str:
        return f"current:{lid}:{d}"

    async def generate_ticket_number(self, prefix: str) -> str:
        today = datetime.now(timezone.utc).strftime("%Y%m%d")
        key = f"queue_counter:{prefix}:{today}"
        count = await self.redis.incr(key)
        await self.redis.expire(key, 172800)
        return f"{prefix}-{count:03d}"

    async def join_queue(self, booking_id: str, lounge_id: str = None) -> QueueTicket:
        if not lounge_id:
            lounge_id = settings.LOUNGE_ID
        today = datetime.now(timezone.utc).strftime("%Y%m%d")
        result = await self.db.execute(select(Booking).where(Booking.id == booking_id))
        booking = result.scalar_one_or_none()
        if not booking:
            raise HTTPException(404, "Booking tidak ditemukan")
        if booking.status != "checked_in":
            raise HTTPException(409, "Booking belum di-check-in")
        existing = await self.db.execute(select(QueueTicket).where(QueueTicket.booking_id == booking_id))
        if existing.scalar_one_or_none():
            raise HTTPException(409, "Tamu sudah memiliki nomor antrian")
        prefix = "A" if booking.source == "online" else "B"
        ticket_number = await self.generate_ticket_number(prefix)
        ticket = QueueTicket(booking_id=booking_id, ticket_number=ticket_number, prefix=prefix, status="waiting")
        self.db.add(ticket)
        await self.db.commit()
        await self.db.refresh(ticket)
        score = time_module.time()
        queue_key = self._queue_key(lounge_id, today)
        await self.redis.zadd(queue_key, {str(ticket.id): score})
        await self.redis.expire(queue_key, 86400)
        return ticket

    async def call_next(self, lounge_id: str = None) -> Optional[QueueTicket]:
        if not lounge_id:
            lounge_id = settings.LOUNGE_ID
        today = datetime.now(timezone.utc).strftime("%Y%m%d")
        qk = self._queue_key(lounge_id, today)
        sk = self._serving_key(lounge_id, today)
        ck = self._current_key(lounge_id, today)
        lua = """
            local next_items = redis.call('ZPOPMIN', KEYS[1], 1)
            if #next_items == 0 then return nil end
            local tid = next_items[1]
            redis.call('SADD', KEYS[2], tid)
            redis.call('EXPIRE', KEYS[2], 86400)
            redis.call('SET', KEYS[3], tid)
            redis.call('EXPIRE', KEYS[3], 86400)
            return tid
        """
        ticket_id = await self.redis.eval(lua, 3, qk, sk, ck)
        if not ticket_id:
            return None
        result = await self.db.execute(select(QueueTicket).where(QueueTicket.id == ticket_id))
        ticket = result.scalar_one_or_none()
        if ticket:
            ticket.status = "called"
            ticket.called_at = datetime.now(timezone.utc)
            await self.db.commit()
            await self.db.refresh(ticket)
        return ticket

    async def complete_serving(self, ticket_id: str, lounge_id: str = None) -> QueueTicket:
        if not lounge_id:
            lounge_id = settings.LOUNGE_ID
        today = datetime.now(timezone.utc).strftime("%Y%m%d")
        await self.redis.srem(self._serving_key(lounge_id, today), ticket_id)
        result = await self.db.execute(select(QueueTicket).where(QueueTicket.id == ticket_id))
        ticket = result.scalar_one_or_none()
        if not ticket:
            raise HTTPException(404, "Ticket tidak ditemukan")
        ticket.status = "done"
        ticket.served_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(ticket)
        return ticket

    async def skip_ticket(self, ticket_id: str, lounge_id: str = None) -> QueueTicket:
        if not lounge_id:
            lounge_id = settings.LOUNGE_ID
        today = datetime.now(timezone.utc).strftime("%Y%m%d")
        await self.redis.zrem(self._queue_key(lounge_id, today), ticket_id)
        await self.redis.srem(self._serving_key(lounge_id, today), ticket_id)
        result = await self.db.execute(select(QueueTicket).where(QueueTicket.id == ticket_id))
        ticket = result.scalar_one_or_none()
        if not ticket:
            raise HTTPException(404, "Ticket tidak ditemukan")
        ticket.status = "skip"
        await self.db.commit()
        await self.db.refresh(ticket)
        return ticket

    async def get_queue_status(self, lounge_id: str = None) -> dict:
        if not lounge_id:
            lounge_id = settings.LOUNGE_ID
        today = datetime.now(timezone.utc).strftime("%Y%m%d")
        qk = self._queue_key(lounge_id, today)
        sk = self._serving_key(lounge_id, today)
        ck = self._current_key(lounge_id, today)
        waiting_count = await self.redis.zcard(qk)
        serving_count = await self.redis.scard(sk)
        current_id = await self.redis.get(ck)
        current_number = None
        if current_id:
            r = await self.db.execute(select(QueueTicket).where(QueueTicket.id == current_id))
            t = r.scalar_one_or_none()
            if t:
                current_number = t.ticket_number
        next_ids = await self.redis.zrange(qk, 0, 2)
        next_tickets = []
        for tid in next_ids:
            r = await self.db.execute(select(QueueTicket).where(QueueTicket.id == tid))
            t = r.scalar_one_or_none()
            if t:
                next_tickets.append(t.ticket_number)
        return {
            "waiting_count": waiting_count,
            "serving_count": serving_count,
            "current_ticket": current_number,
            "next_tickets": next_tickets,
        }
