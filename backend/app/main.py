"""
FastAPI Main Application — Arjuna Smart Lounge App
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import init_db, close_db
from app.api.v1.endpoints import auth, bookings, queue, menu, orders, staff, admin


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle: startup and shutdown."""
    await init_db()
    # Seed default roles
    from app.core.database import AsyncSessionLocal
    from app.models.models import Role
    from sqlalchemy import select
    async with AsyncSessionLocal() as db:
        for role_name in ["GUEST", "KITCHEN", "STAFF", "BLU_VIEWER", "FINANCE", "MANAGER", "SUPER_ADMIN"]:
            existing = await db.execute(select(Role).where(Role.name == role_name))
            if not existing.scalar_one_or_none():
                db.add(Role(name=role_name))
        await db.commit()

        # Create default super admin if none exists
        from app.models.models import User, UserRole
        from app.core.security import hash_password
        admin_check = await db.execute(
            select(User).join(UserRole).join(Role).where(Role.name == "SUPER_ADMIN")
        )
        if not admin_check.scalar_one_or_none():
            admin_user = User(
                email="admin@arjunalounge.id",
                full_name="Super Administrator",
                password_hash=hash_password("Admin@2025!"),
                is_active=True, is_verified=True,
            )
            db.add(admin_user)
            await db.flush()
            sa_role = await db.execute(select(Role).where(Role.name == "SUPER_ADMIN"))
            role = sa_role.scalar_one()
            db.add(UserRole(user_id=admin_user.id, role_id=role.id))
            await db.commit()

    yield
    await close_db()


app = FastAPI(
    title="Arjuna Smart Lounge API",
    description="Sistem Manajemen Lounge Terintegrasi — Balai Kesehatan Penerbangan",
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/v1")
app.include_router(bookings.router, prefix="/api/v1")
app.include_router(queue.router, prefix="/api/v1")
app.include_router(menu.router, prefix="/api/v1")
app.include_router(orders.router, prefix="/api/v1")
app.include_router(staff.router, prefix="/api/v1")
app.include_router(admin.router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    return {"status": "healthy", "app": settings.APP_NAME, "version": settings.APP_VERSION}


@app.get("/")
async def root():
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "status": "running",
    }
