"""
Queue Endpoints — WAR Queue System
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db, get_redis
from app.core.security import get_current_user, require_roles, Role
from app.services.queue_service import QueueService
from app.schemas.schemas import QueueTicketResponse, QueueStatusResponse, MessageResponse

router = APIRouter(prefix="/queue", tags=["Queue"])


@router.get("/current", response_model=QueueStatusResponse)
async def get_current_queue(
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
):
    svc = QueueService(db, redis)
    return await svc.get_queue_status()


@router.post("/join/{booking_id}")
async def join_queue(
    booking_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
):
    svc = QueueService(db, redis)
    ticket = await svc.join_queue(booking_id)
    return ticket
