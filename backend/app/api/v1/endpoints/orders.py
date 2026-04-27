"""
Order & Payment Endpoints
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.security import get_current_user, require_roles, Role
from app.services.payment_service import OrderService, PaymentService
from app.schemas.schemas import OrderCreate, OrderStatusUpdate, PaymentCreate, MidtransWebhook, MessageResponse

router = APIRouter(tags=["Orders & Payments"])


@router.post("/orders")
async def create_order(
    data: OrderCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = OrderService(db)
    return await svc.create_order(data, current_user["sub"])


@router.get("/orders/{order_id}")
async def get_order(
    order_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = OrderService(db)
    order = await svc.get_order(order_id)
    if not order:
        from fastapi import HTTPException
        raise HTTPException(404, "Order tidak ditemukan")
    return order


@router.put("/staff/orders/{order_id}/status")
async def update_order_status(
    order_id: str,
    data: OrderStatusUpdate,
    current_user: dict = Depends(require_roles(Role.STAFF, Role.KITCHEN, Role.MANAGER, Role.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    svc = OrderService(db)
    return await svc.update_order_status(order_id, data.status)


@router.post("/payments/create")
async def create_payment(
    data: PaymentCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = PaymentService(db)
    return await svc.create_payment(str(data.order_id), current_user["sub"])


@router.post("/payments/webhook")
async def midtrans_webhook(data: dict, db: AsyncSession = Depends(get_db)):
    svc = PaymentService(db)
    return await svc.handle_webhook(data)
