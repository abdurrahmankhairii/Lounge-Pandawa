"""
Pydantic Schemas — Request/Response Models
Arjuna Smart Lounge App
"""
from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, List
from datetime import date, time, datetime
from uuid import UUID
from decimal import Decimal


# ============================================================
# AUTH SCHEMAS
# ============================================================
class UserRegister(BaseModel):
    email: EmailStr
    phone: Optional[str] = Field(None, max_length=20)
    full_name: str = Field(..., min_length=2, max_length=255)
    password: str = Field(..., min_length=8)

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v):
        if v and not v.replace("+", "").replace("-", "").isdigit():
            raise ValueError("Nomor telepon tidak valid")
        return v


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: "UserResponse"


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class TwoFactorVerify(BaseModel):
    code: str = Field(..., min_length=6, max_length=6)


# ============================================================
# USER SCHEMAS
# ============================================================
class UserResponse(BaseModel):
    id: UUID
    email: str
    phone: Optional[str] = None
    full_name: str
    is_active: bool
    is_verified: bool
    roles: List[str] = []
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserCreate(BaseModel):
    email: EmailStr
    phone: Optional[str] = None
    full_name: str = Field(..., min_length=2, max_length=255)
    password: str = Field(..., min_length=8)
    roles: List[str] = ["GUEST"]


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    full_name: Optional[str] = None
    is_active: Optional[bool] = None
    roles: Optional[List[str]] = None


# ============================================================
# BOOKING SCHEMAS
# ============================================================
class TimeSlotResponse(BaseModel):
    id: int
    slot_date: date
    start_time: time
    end_time: time
    capacity: int
    booked_count: int
    is_active: bool
    available: int = 0

    class Config:
        from_attributes = True


class BookingCreate(BaseModel):
    slot_id: int
    guest_name: str = Field(..., min_length=2, max_length=255)
    guest_phone: Optional[str] = Field(None, max_length=20)
    guest_email: Optional[EmailStr] = None
    guest_type: Optional[str] = Field(None, pattern="^(pilot|cabin_crew|medcheck|other)$")
    airline: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = None


class WalkInBookingCreate(BaseModel):
    guest_name: str = Field(..., min_length=2, max_length=255)
    guest_phone: Optional[str] = None
    guest_type: Optional[str] = None
    airline: Optional[str] = None
    notes: Optional[str] = None


class BookingResponse(BaseModel):
    id: UUID
    booking_code: str
    user_id: Optional[UUID] = None
    slot_id: Optional[int] = None
    guest_name: str
    guest_phone: Optional[str] = None
    guest_email: Optional[str] = None
    guest_type: Optional[str] = None
    airline: Optional[str] = None
    status: str
    notes: Optional[str] = None
    check_in_time: Optional[datetime] = None
    source: str
    created_at: Optional[datetime] = None
    slot: Optional[TimeSlotResponse] = None
    queue_ticket: Optional["QueueTicketResponse"] = None

    class Config:
        from_attributes = True


class BookingStatusUpdate(BaseModel):
    status: str = Field(..., pattern="^(confirmed|checked_in|completed|cancelled|no_show)$")


# ============================================================
# QUEUE SCHEMAS
# ============================================================
class QueueTicketResponse(BaseModel):
    id: UUID
    booking_id: UUID
    ticket_number: str
    prefix: str
    status: str
    called_at: Optional[datetime] = None
    served_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class QueueStatusResponse(BaseModel):
    waiting_count: int
    serving_count: int
    current_ticket: Optional[str] = None
    next_tickets: List[str] = []


# ============================================================
# MENU SCHEMAS
# ============================================================
class MenuCategoryCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    name_en: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None
    sort_order: int = 0
    is_active: bool = True


class MenuCategoryUpdate(BaseModel):
    name: Optional[str] = None
    name_en: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None


class MenuCategoryResponse(BaseModel):
    id: int
    name: str
    name_en: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None
    sort_order: int
    is_active: bool
    items_count: int = 0
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class MenuItemCreate(BaseModel):
    category_id: int
    name: str = Field(..., min_length=1, max_length=200)
    name_en: Optional[str] = None
    description: Optional[str] = None
    price: Decimal = Field(..., gt=0)
    is_available: bool = True
    is_complimentary: bool = False
    prep_time_min: int = Field(5, ge=1)
    allergens: List[str] = []
    tags: List[str] = []
    sort_order: int = 0


class MenuItemUpdate(BaseModel):
    category_id: Optional[int] = None
    name: Optional[str] = None
    name_en: Optional[str] = None
    description: Optional[str] = None
    price: Optional[Decimal] = None
    is_available: Optional[bool] = None
    is_complimentary: Optional[bool] = None
    prep_time_min: Optional[int] = None
    allergens: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    sort_order: Optional[int] = None


class MenuItemResponse(BaseModel):
    id: int
    category_id: Optional[int] = None
    name: str
    name_en: Optional[str] = None
    description: Optional[str] = None
    price: Decimal
    image_url: Optional[str] = None
    is_available: bool
    is_complimentary: bool
    prep_time_min: int
    allergens: List[str] = []
    tags: List[str] = []
    sort_order: int
    category: Optional[MenuCategoryResponse] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ============================================================
# ORDER SCHEMAS
# ============================================================
class OrderItemCreate(BaseModel):
    menu_item_id: int
    quantity: int = Field(1, ge=1, le=20)
    notes: Optional[str] = None


class OrderCreate(BaseModel):
    booking_id: Optional[UUID] = None
    items: List[OrderItemCreate] = Field(..., min_length=1)
    notes: Optional[str] = None


class OrderItemResponse(BaseModel):
    id: UUID
    menu_item_id: Optional[int] = None
    quantity: int
    unit_price: Decimal
    subtotal: Decimal
    notes: Optional[str] = None
    menu_item: Optional[MenuItemResponse] = None

    class Config:
        from_attributes = True


class OrderResponse(BaseModel):
    id: UUID
    order_code: str
    booking_id: Optional[UUID] = None
    user_id: Optional[UUID] = None
    status: str
    total_amount: Optional[Decimal] = None
    discount: Optional[Decimal] = None
    final_amount: Optional[Decimal] = None
    notes: Optional[str] = None
    items: List[OrderItemResponse] = []
    payment: Optional["PaymentResponse"] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class OrderStatusUpdate(BaseModel):
    status: str = Field(..., pattern="^(accepted|preparing|ready|delivered|cancelled)$")


# ============================================================
# PAYMENT SCHEMAS
# ============================================================
class PaymentCreate(BaseModel):
    order_id: UUID
    method: Optional[str] = None  # qris, gopay, bank_transfer, credit_card


class PaymentResponse(BaseModel):
    id: UUID
    order_id: Optional[UUID] = None
    payment_code: str
    method: Optional[str] = None
    gateway_ref: Optional[str] = None
    amount: Decimal
    status: str
    paid_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    snap_token: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class MidtransWebhook(BaseModel):
    order_id: str
    transaction_status: str
    status_code: str
    gross_amount: str
    signature_key: str
    payment_type: Optional[str] = None
    transaction_id: Optional[str] = None


# ============================================================
# REPORT SCHEMAS
# ============================================================
class DailyReportResponse(BaseModel):
    date: date
    total_bookings: int
    checked_in: int
    no_shows: int
    cancelled: int
    total_orders: int
    total_revenue: Decimal
    avg_order_value: Decimal
    peak_hour: Optional[str] = None
    occupancy_rate: float


class RevenueReportResponse(BaseModel):
    period: str
    total_revenue: Decimal
    total_transactions: int
    payment_methods: dict = {}
    daily_breakdown: List[dict] = []


# ============================================================
# SETTINGS SCHEMAS
# ============================================================
class LoungeSettingsResponse(BaseModel):
    key: str
    value: Optional[str] = None
    description: Optional[str] = None


class LoungeSettingsUpdate(BaseModel):
    settings: dict = {}  # key: value pairs


# ============================================================
# AUDIT LOG SCHEMAS
# ============================================================
class AuditLogResponse(BaseModel):
    id: int
    user_id: Optional[UUID] = None
    action: str
    resource: Optional[str] = None
    resource_id: Optional[str] = None
    old_values: Optional[dict] = None
    new_values: Optional[dict] = None
    ip_address: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ============================================================
# COMMON SCHEMAS
# ============================================================
class PaginatedResponse(BaseModel):
    items: List = []
    total: int = 0
    page: int = 1
    per_page: int = 20
    pages: int = 1


class MessageResponse(BaseModel):
    message: str
    detail: Optional[str] = None
