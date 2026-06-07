from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import engine, Base
from . import models

# Create all tables on startup
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="UzRock Marketplace API",
    description="Gaming marketplace with Escrow (Garant) system, real-time chat, and admin panel.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS — allow frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["Health"])
async def root():
    return {"status": "ok", "message": "UzRock Marketplace API is running!"}


@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "healthy"}


# ── Future routers ──────────────────────────────────────────
# from .routers import auth, games, products, orders, chat, admin
# app.include_router(auth.router,     prefix="/api/v1/auth",     tags=["Auth"])
# app.include_router(games.router,    prefix="/api/v1/games",    tags=["Games"])
# app.include_router(products.router, prefix="/api/v1/products", tags=["Products"])
# app.include_router(orders.router,   prefix="/api/v1/orders",   tags=["Orders"])
# app.include_router(chat.router,     prefix="/api/v1/chat",     tags=["Chat"])
# app.include_router(admin.router,    prefix="/api/v1/admin",    tags=["Admin"])
