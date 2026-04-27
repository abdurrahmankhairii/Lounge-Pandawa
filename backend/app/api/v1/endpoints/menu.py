"""
Menu Endpoints — Public menu + Admin CRUD
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from app.core.database import get_db
from app.core.security import get_current_user, require_roles, Role
from app.models.models import MenuItem, MenuCategory, OrderItem, Order
from app.schemas.schemas import (
    MenuItemCreate, MenuItemUpdate, MenuItemResponse,
    MenuCategoryCreate, MenuCategoryUpdate, MenuCategoryResponse, MessageResponse
)

router = APIRouter(tags=["Menu"])


# PUBLIC ENDPOINTS
@router.get("/menu", response_model=list)
async def get_menu(
    category_id: Optional[int] = None,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    query = select(MenuItem).where(MenuItem.is_available == True)
    if category_id:
        query = query.where(MenuItem.category_id == category_id)
    if search:
        query = query.where(MenuItem.name.ilike(f"%{search}%"))
    query = query.order_by(MenuItem.sort_order, MenuItem.name)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/menu/categories")
async def get_categories(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(MenuCategory).where(MenuCategory.is_active == True)
        .order_by(MenuCategory.sort_order)
    )
    return result.scalars().all()


# ADMIN ENDPOINTS
@router.post("/admin/menu/categories")
async def create_category(
    data: MenuCategoryCreate,
    current_user: dict = Depends(require_roles(Role.MANAGER, Role.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    cat = MenuCategory(**data.model_dump(), created_by=current_user["sub"])
    db.add(cat)
    await db.commit()
    await db.refresh(cat)
    return cat


@router.put("/admin/menu/categories/{cat_id}")
async def update_category(
    cat_id: int, data: MenuCategoryUpdate,
    current_user: dict = Depends(require_roles(Role.MANAGER, Role.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(MenuCategory).where(MenuCategory.id == cat_id))
    cat = result.scalar_one_or_none()
    if not cat:
        raise HTTPException(404, "Kategori tidak ditemukan")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(cat, k, v)
    await db.commit()
    await db.refresh(cat)
    return cat


@router.delete("/admin/menu/categories/{cat_id}")
async def delete_category(
    cat_id: int,
    current_user: dict = Depends(require_roles(Role.MANAGER, Role.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(MenuCategory).where(MenuCategory.id == cat_id))
    cat = result.scalar_one_or_none()
    if not cat:
        raise HTTPException(404, "Kategori tidak ditemukan")
    items_count = await db.execute(
        select(func.count()).where(and_(MenuItem.category_id == cat_id, MenuItem.is_available == True))
    )
    if items_count.scalar() > 0:
        raise HTTPException(409, "Tidak bisa hapus kategori yang masih memiliki item aktif")
    cat.is_active = False
    await db.commit()
    return {"message": "Kategori berhasil dinonaktifkan"}


@router.post("/admin/menu/items")
async def create_menu_item(
    data: MenuItemCreate,
    current_user: dict = Depends(require_roles(Role.MANAGER, Role.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    item = MenuItem(**data.model_dump(), created_by=current_user["sub"])
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return item


@router.put("/admin/menu/items/{item_id}")
async def update_menu_item(
    item_id: int, data: MenuItemUpdate,
    current_user: dict = Depends(require_roles(Role.MANAGER, Role.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(MenuItem).where(MenuItem.id == item_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(404, "Menu item tidak ditemukan")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(item, k, v)
    item.updated_by = current_user["sub"]
    await db.commit()
    await db.refresh(item)
    return item


@router.delete("/admin/menu/items/{item_id}")
async def delete_menu_item(
    item_id: int,
    current_user: dict = Depends(require_roles(Role.MANAGER, Role.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(MenuItem).where(MenuItem.id == item_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(404, "Menu item tidak ditemukan")
    active_orders = await db.execute(
        select(func.count()).select_from(OrderItem).join(Order)
        .where(and_(OrderItem.menu_item_id == item_id, Order.status.notin_(["completed", "cancelled"])))
    )
    if active_orders.scalar() > 0:
        raise HTTPException(409, "Tidak bisa hapus item yang masih ada di order aktif")
    item.is_available = False
    await db.commit()
    return {"message": "Menu item berhasil dinonaktifkan"}


@router.patch("/staff/menu/items/{item_id}/toggle")
async def toggle_menu_availability(
    item_id: int,
    current_user: dict = Depends(require_roles(Role.KITCHEN, Role.STAFF, Role.MANAGER, Role.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(MenuItem).where(MenuItem.id == item_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(404, "Menu item tidak ditemukan")
    item.is_available = not item.is_available
    await db.commit()
    return {"message": f"Menu '{item.name}' {'tersedia' if item.is_available else 'tidak tersedia'}"}
