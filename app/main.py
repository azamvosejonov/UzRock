import time
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from contextlib import asynccontextmanager
from .database import engine, Base
from . import models


@asynccontextmanager
async def lifespan(_app):
    models.Base.metadata.create_all(bind=engine)
    yield


# ── Ilovani sozlash ─────────────────────────────────────────────
app = FastAPI(
    lifespan=lifespan,
    title="UzRock Marketplace API",
    description=(
        "Gaming marketplace — Escrow/Garant tizimi, real-time chat, "
        "Click & Payme to'lovlar, admin panel.\n\n"
        "**Auth:** Barcha himoyalangan endpointlar uchun `Bearer <token>` header kerak."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS ────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],       # productionda domenlarni ko'rsating
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Request logging middleware ───────────────────────────────────
log = logging.getLogger("api")


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    ms = (time.perf_counter() - start) * 1000
    log.info(f"{request.method} {request.url.path} → {response.status_code} | {ms:.1f}ms")
    return response


# ── Global exception handler ─────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    log.exception(f"Kutilmagan xato: {exc}")
    return JSONResponse(status_code=500, content={"detail": "Ichki server xatosi"})


# ── Routerlarni ulash ────────────────────────────────────────────
from .routers import (
    auth, users, categories, games, subcategories,
    products, orders, chat, reviews, transactions,
    withdrawals, disputes, notifications, favorites,
    admin, payments,
)

PREFIX = "/api/v1"

app.include_router(auth.router,           prefix=f"{PREFIX}/auth",          tags=["Auth"])
app.include_router(users.router,          prefix=f"{PREFIX}/users",         tags=["Users"])
app.include_router(categories.router,     prefix=f"{PREFIX}/categories",    tags=["Categories"])
app.include_router(games.router,          prefix=f"{PREFIX}/games",         tags=["Games"])
app.include_router(subcategories.router,  prefix=f"{PREFIX}/subcategories", tags=["Subcategories"])
app.include_router(products.router,       prefix=f"{PREFIX}/products",      tags=["Products"])
app.include_router(orders.router,         prefix=f"{PREFIX}/orders",        tags=["Orders"])
app.include_router(chat.router,           prefix=f"{PREFIX}/chat",          tags=["Chat"])
app.include_router(reviews.router,        prefix=f"{PREFIX}/reviews",       tags=["Reviews"])
app.include_router(transactions.router,   prefix=f"{PREFIX}/transactions",  tags=["Transactions"])
app.include_router(withdrawals.router,    prefix=f"{PREFIX}/withdrawals",   tags=["Withdrawals"])
app.include_router(disputes.router,       prefix=f"{PREFIX}/disputes",      tags=["Disputes"])
app.include_router(notifications.router,  prefix=f"{PREFIX}/notifications", tags=["Notifications"])
app.include_router(favorites.router,      prefix=f"{PREFIX}/favorites",     tags=["Favorites"])
app.include_router(admin.router,          prefix=f"{PREFIX}/admin",         tags=["Admin"])
app.include_router(payments.router,       prefix=f"{PREFIX}/payments",      tags=["Payments"])


# ── Health check ─────────────────────────────────────────────────
@app.get("/", tags=["Health"])
async def root():
    return {"status": "ok", "message": "UzRock Marketplace API ishga tayyor!"}


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "healthy"}
