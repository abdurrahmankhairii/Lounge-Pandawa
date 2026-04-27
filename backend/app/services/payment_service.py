"""
Payment Service — Midtrans Integration
"""
import hashlib
import uuid
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import Optional
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.models import Payment, Order, OrderItem, MenuItem
from app.schemas.schemas import PaymentCreate, OrderCreate
from app.core.config import settings


class PaymentService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_payment(self, order_id: str, user_id: str) -> dict:
        result = await self.db.execute(select(Order).where(Order.id == order_id))
        order = result.scalar_one_or_none()
        if not order:
            raise HTTPException(404, "Order tidak ditemukan")
        if str(order.user_id) != user_id:
            raise HTTPException(403, "Akses ditolak")
        if order.status == "cancelled":
            raise HTTPException(409, "Order sudah dibatalkan")

        payment_code = f"PAY-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"
        payment = Payment(
            order_id=order_id,
            payment_code=payment_code,
            amount=order.final_amount or order.total_amount,
            status="pending",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
        )
        self.db.add(payment)
        await self.db.commit()
        await self.db.refresh(payment)

        # In production, this would call Midtrans Core API
        snap_token = f"snap-{payment_code}"  # Placeholder

        return {
            "payment_id": str(payment.id),
            "payment_code": payment_code,
            "amount": float(payment.amount),
            "snap_token": snap_token,
            "redirect_url": f"{settings.APP_BASE_URL}/payment/{payment_code}",
        }

    async def handle_webhook(self, data: dict) -> dict:
        order_id = data.get("order_id", "")
        status = data.get("transaction_status", "")
        signature = data.get("signature_key", "")
        status_code = data.get("status_code", "")
        gross_amount = data.get("gross_amount", "")

        # Verify HMAC signature
        expected = hashlib.sha512(
            f"{order_id}{status_code}{gross_amount}{settings.MIDTRANS_SERVER_KEY}".encode()
        ).hexdigest()

        if signature != expected:
            raise HTTPException(400, "Invalid signature")

        result = await self.db.execute(
            select(Payment).where(Payment.payment_code == order_id)
        )
        payment = result.scalar_one_or_none()
        if not payment:
            raise HTTPException(404, "Payment tidak ditemukan")

        if payment.status == "settlement":
            return {"message": "Already processed"}

        status_map = {
            "settlement": "settlement",
            "capture": "settlement",
            "pending": "pending",
            "expire": "expire",
            "cancel": "cancel",
            "deny": "deny",
            "refund": "refund",
        }
        payment.status = status_map.get(status, status)
        payment.gateway_ref = data.get("transaction_id")
        payment.method = data.get("payment_type")

        if payment.status == "settlement":
            payment.paid_at = datetime.now(timezone.utc)
            order_result = await self.db.execute(select(Order).where(Order.id == payment.order_id))
            order = order_result.scalar_one_or_none()
            if order:
                order.status = "accepted"

        await self.db.commit()
        return {"message": "OK"}


class OrderService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_order(self, data: OrderCreate, user_id: str) -> Order:
        order_code = f"ORD-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"
        total = Decimal("0")
        order = Order(
            order_code=order_code,
            booking_id=str(data.booking_id) if data.booking_id else None,
            user_id=user_id,
            status="pending",
            notes=data.notes,
        )
        self.db.add(order)
        await self.db.flush()

        for item_data in data.items:
            menu_result = await self.db.execute(
                select(MenuItem).where(MenuItem.id == item_data.menu_item_id)
            )
            menu_item = menu_result.scalar_one_or_none()
            if not menu_item:
                raise HTTPException(404, f"Menu item {item_data.menu_item_id} tidak ditemukan")
            if not menu_item.is_available:
                raise HTTPException(409, f"Menu '{menu_item.name}' sedang tidak tersedia")

            subtotal = menu_item.price * item_data.quantity
            total += subtotal
            order_item = OrderItem(
                order_id=order.id,
                menu_item_id=menu_item.id,
                quantity=item_data.quantity,
                unit_price=menu_item.price,
                subtotal=subtotal,
                notes=item_data.notes,
            )
            self.db.add(order_item)

        order.total_amount = total
        order.final_amount = total - (order.discount or 0)
        await self.db.commit()
        await self.db.refresh(order)
        return order

    async def get_order(self, order_id: str) -> Optional[Order]:
        result = await self.db.execute(select(Order).where(Order.id == order_id))
        return result.scalar_one_or_none()

    async def update_order_status(self, order_id: str, status: str) -> Order:
        result = await self.db.execute(select(Order).where(Order.id == order_id))
        order = result.scalar_one_or_none()
        if not order:
            raise HTTPException(404, "Order tidak ditemukan")
        order.status = status
        order.updated_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(order)
        return order
