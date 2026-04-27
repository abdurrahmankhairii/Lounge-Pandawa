"""
SQLAlchemy ORM Models — All Database Tables
Arjuna Smart Lounge App
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Integer, Boolean, Text, Numeric, Date, Time,
    ForeignKey, DateTime, BigInteger, ARRAY, JSON, Index
)
from sqlalchemy.dialects.postgresql import UUID, INET, JSONB
from sqlalchemy.orm import relationship
from app.core.database import Base


def utcnow():
    return datetime.now(timezone.utc)


# ============================================================
# USERS, ROLES, & AUTHENTICATION
# ============================================================
class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    phone = Column(String(20), unique=True, nullable=True)
    full_name = Column(String(255), nullable=False)
    password_hash = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    totp_secret = Column(Text, nullable=True)
    failed_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime(timezone=True), nullable=True)
    last_login = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    # Relationships
    user_roles = relationship("UserRole", back_populates="user", cascade="all, delete-orphan")
    bookings = relationship("Booking", back_populates="user", foreign_keys="Booking.user_id")
    orders = relationship("Order", back_populates="user")


class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(Text, nullable=True)

    user_roles = relationship("UserRole", back_populates="role")


class UserRole(Base):
    __tablename__ = "user_roles"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    role_id = Column(Integer, ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True)

    user = relationship("User", back_populates="user_roles")
    role = relationship("Role", back_populates="user_roles")


# ============================================================
# BOOKINGS & TIME SLOTS
# ============================================================
class TimeSlot(Base):
    __tablename__ = "time_slots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    slot_date = Column(Date, nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    capacity = Column(Integer, default=20)
    booked_count = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)

    __table_args__ = (
        Index("idx_time_slots_date", "slot_date"),
        {"schema": None},
    )

    bookings = relationship("Booking", back_populates="slot")


class Booking(Base):
    __tablename__ = "bookings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    booking_code = Column(String(20), unique=True, nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    slot_id = Column(Integer, ForeignKey("time_slots.id"), nullable=True)
    guest_name = Column(String(255), nullable=False)
    guest_phone = Column(String(20), nullable=True)
    guest_email = Column(String(255), nullable=True)
    guest_type = Column(String(50), nullable=True)  # pilot, cabin_crew, medcheck, other
    airline = Column(String(100), nullable=True)
    status = Column(String(30), default="pending")
    # pending | confirmed | checked_in | completed | cancelled | no_show
    notes = Column(Text, nullable=True)
    check_in_time = Column(DateTime(timezone=True), nullable=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    source = Column(String(20), default="online")  # online | walk_in
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    __table_args__ = (
        Index("idx_bookings_slot", "slot_id"),
        Index("idx_bookings_user", "user_id"),
        Index("idx_bookings_status", "status"),
    )

    user = relationship("User", back_populates="bookings", foreign_keys=[user_id])
    slot = relationship("TimeSlot", back_populates="bookings")
    queue_ticket = relationship("QueueTicket", back_populates="booking", uselist=False)
    orders = relationship("Order", back_populates="booking")


# ============================================================
# QUEUE TICKETS
# ============================================================
class QueueTicket(Base):
    __tablename__ = "queue_tickets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    booking_id = Column(UUID(as_uuid=True), ForeignKey("bookings.id", ondelete="CASCADE"))
    ticket_number = Column(String(10), nullable=False)  # A-001, B-002, etc.
    prefix = Column(String(1), nullable=False)  # A=online, B=walk_in
    called_at = Column(DateTime(timezone=True), nullable=True)
    served_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(20), default="waiting")
    # waiting | called | serving | done | skip
    created_at = Column(DateTime(timezone=True), default=utcnow)

    booking = relationship("Booking", back_populates="queue_ticket")


# ============================================================
# MENU CATEGORIES & ITEMS
# ============================================================
class MenuCategory(Base):
    __tablename__ = "menu_categories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    name_en = Column(String(100), nullable=True)
    description = Column(Text, nullable=True)
    icon = Column(String(50), nullable=True)
    sort_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    items = relationship("MenuItem", back_populates="category")


class MenuItem(Base):
    __tablename__ = "menu_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    category_id = Column(Integer, ForeignKey("menu_categories.id"), nullable=True)
    name = Column(String(200), nullable=False)
    name_en = Column(String(200), nullable=True)
    description = Column(Text, nullable=True)
    price = Column(Numeric(12, 2), nullable=False)
    image_url = Column(Text, nullable=True)
    is_available = Column(Boolean, default=True)
    is_complimentary = Column(Boolean, default=False)
    prep_time_min = Column(Integer, default=5)
    allergens = Column(ARRAY(Text), default=[])
    tags = Column(ARRAY(Text), default=[])  # healthy, vegetarian, bestseller
    sort_order = Column(Integer, default=0)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    updated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    __table_args__ = (
        Index("idx_menu_items_cat", "category_id"),
    )

    category = relationship("MenuCategory", back_populates="items")
    order_items = relationship("OrderItem", back_populates="menu_item")


# ============================================================
# ORDERS & PAYMENTS
# ============================================================
class Order(Base):
    __tablename__ = "orders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_code = Column(String(20), unique=True, nullable=False, index=True)
    booking_id = Column(UUID(as_uuid=True), ForeignKey("bookings.id"), nullable=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    status = Column(String(30), default="pending")
    # pending | accepted | preparing | ready | delivered | cancelled
    total_amount = Column(Numeric(12, 2), nullable=True)
    discount = Column(Numeric(12, 2), default=0)
    final_amount = Column(Numeric(12, 2), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    booking = relationship("Booking", back_populates="orders")
    user = relationship("User", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    payment = relationship("Payment", back_populates="order", uselist=False)


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id", ondelete="CASCADE"))
    menu_item_id = Column(Integer, ForeignKey("menu_items.id"), nullable=True)
    quantity = Column(Integer, nullable=False, default=1)
    unit_price = Column(Numeric(12, 2), nullable=False)  # Snapshot harga saat order
    subtotal = Column(Numeric(12, 2), nullable=False)
    notes = Column(Text, nullable=True)

    order = relationship("Order", back_populates="items")
    menu_item = relationship("MenuItem", back_populates="order_items")


class Payment(Base):
    __tablename__ = "payments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id"), nullable=True)
    payment_code = Column(String(50), unique=True, nullable=False, index=True)
    method = Column(String(50), nullable=True)
    gateway_ref = Column(Text, nullable=True)  # Midtrans transaction ID
    amount = Column(Numeric(12, 2), nullable=False)
    status = Column(String(30), default="pending")
    # pending | settlement | expire | cancel | deny | refund
    paid_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    metadata_json = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)

    order = relationship("Order", back_populates="payment")


# ============================================================
# AUDIT LOG
# ============================================================
class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    action = Column(String(100), nullable=False)
    resource = Column(String(100), nullable=True)
    resource_id = Column(Text, nullable=True)
    old_values = Column(JSONB, nullable=True)
    new_values = Column(JSONB, nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)

    __table_args__ = (
        Index("idx_audit_user", "user_id"),
        Index("idx_audit_resource", "resource", "resource_id"),
    )


# ============================================================
# LOUNGE SETTINGS
# ============================================================
class LoungeSettings(Base):
    __tablename__ = "lounge_settings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String(100), unique=True, nullable=False)
    value = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    updated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
