"""
Test konfiguratsiyasi:
- PostgreSQL UUID/JSONB → SQLite muvofiqlashtiriladi
- Har bir test uchun toza DB (drop_all + create_all)
- Umumiy fixture-lar: client, db, token-lar, domain ob'ektlar
"""
import os
import uuid
import hashlib
from decimal import Decimal

import pytest
from sqlalchemy import create_engine, types, String
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

# ═══════════════════════════════════════════════════════════════
# 1.  PostgreSQL tiplarini SQLite uchun patch qilish
#     (app modullaridan OLDIN bajarilishi kerak)
# ═══════════════════════════════════════════════════════════════

class _UUID(types.TypeDecorator):
    """postgresql.UUID  →  String(36) for SQLite."""
    impl = String(36)
    cache_ok = True

    def __init__(self, as_uuid=True, **kw):
        super().__init__(**kw)

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        try:
            return uuid.UUID(str(value))
        except (ValueError, AttributeError):
            return value


class _JSONB(types.TypeDecorator):
    """postgresql.JSONB  →  JSON for SQLite."""
    impl = types.JSON()
    cache_ok = True


import sqlalchemy.dialects.postgresql as _pg
_pg.UUID = _UUID
_pg.JSONB = _JSONB

# ═══════════════════════════════════════════════════════════════
# 2.  Test uchun SQLite engine yaratish
# ═══════════════════════════════════════════════════════════════

TEST_DB_URL = "sqlite://"
test_engine = create_engine(
    TEST_DB_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

# ═══════════════════════════════════════════════════════════════
# 3.  app.database modulini test engine bilan almashtirish
# ═══════════════════════════════════════════════════════════════
import app.database as _dbmod
_dbmod.engine = test_engine
_dbmod.SessionLocal = TestingSession

# ═══════════════════════════════════════════════════════════════
# 4.  Modellar va jadvallarni yaratish
# ═══════════════════════════════════════════════════════════════
from app.database import Base, get_db
from app import models  # noqa: E402 — modellarni ro'yxatga oladi

Base.metadata.create_all(bind=test_engine)

# ═══════════════════════════════════════════════════════════════
# 5.  To'lov env variable-larini test uchun belgilash
#     (app.main import qilishdan OLDIN — modul-level konstantalar)
# ═══════════════════════════════════════════════════════════════
os.environ.setdefault("CLICK_SECRET_KEY", "test_click_secret")
os.environ.setdefault("CLICK_SERVICE_ID", "12345")
os.environ.setdefault("CLICK_MERCHANT_ID", "67890")
os.environ.setdefault("PAYME_KEY", "test_payme_key")
os.environ.setdefault("PAYME_TEST_KEY", "test_payme_key")
os.environ.setdefault("PAYME_ID", "test_payme_id")

# ═══════════════════════════════════════════════════════════════
# 6.  FastAPI app va dependency override
# ═══════════════════════════════════════════════════════════════
from app.main import app  # noqa: E402 — lifespan create_all ham test engine ishlatadi

def _override_get_db():
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = _override_get_db


# ═══════════════════════════════════════════════════════════════
# 7.  Asosiy fixture-lar
# ═══════════════════════════════════════════════════════════════

@pytest.fixture(autouse=True)
def reset_db():
    """Har bir test uchun toza jadvallar."""
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    yield


@pytest.fixture
def db(reset_db):
    session = TestingSession()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(reset_db):
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c


# ─── Auth yordamchi funksiyalari ─────────────────────────────────

def register(client, username: str, email: str = None, password: str = "pass123!") -> str:
    """Foydalanuvchi ro'yxatdan o'tkazib, JWT token qaytaradi."""
    resp = client.post("/api/v1/auth/register", json={
        "username": username,
        "email": email or f"{username}@test.uz",
        "password": password,
    })
    assert resp.status_code == 201, resp.text
    return resp.json()["access_token"]


def auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def click_sign(trans_id, service_id, secret, merchant_id, amount, action, sign_time):
    raw = f"{trans_id}{service_id}{secret}{merchant_id}{amount}{action}{sign_time}"
    return hashlib.md5(raw.encode()).hexdigest()


# ─── Token fixture-lari ──────────────────────────────────────────

@pytest.fixture
def user_token(client):
    return register(client, "buyer1")


@pytest.fixture
def seller_token(client):
    token = register(client, "seller1")
    r = client.post("/api/v1/auth/me/become-seller", headers=auth(token))
    assert r.status_code == 200
    return token


@pytest.fixture
def admin_token(client, db):
    token = register(client, "admin1")
    user = db.query(models.User).filter(models.User.username == "admin1").first()
    user.is_admin = True
    db.commit()
    return token


@pytest.fixture
def funded_buyer(client, db):
    """100 so'm balansdagi xaridor."""
    token = register(client, "buyer_rich")
    user = db.query(models.User).filter(models.User.username == "buyer_rich").first()
    user.balance = Decimal("100.00")
    db.commit()
    return token


# ─── Domain fixture-lari ─────────────────────────────────────────

@pytest.fixture
def category(client, admin_token):
    r = client.post("/api/v1/categories/",
                    json={"name": "Games", "slug": "games"},
                    headers=auth(admin_token))
    assert r.status_code == 201
    return r.json()


@pytest.fixture
def game(client, admin_token, category):
    r = client.post("/api/v1/games/", json={
        "name": "Roblox", "slug": "roblox",
        "category_id": category["id"],
    }, headers=auth(admin_token))
    assert r.status_code == 201
    return r.json()


@pytest.fixture
def subcategory(client, admin_token, game):
    r = client.post("/api/v1/subcategories/", json={
        "name": "Robux", "slug": "robux",
        "game_id": game["id"],
    }, headers=auth(admin_token))
    assert r.status_code == 201
    return r.json()


@pytest.fixture
def product(client, seller_token, game, subcategory):
    r = client.post("/api/v1/products/", json={
        "title": "100 Robux", "price": "10.00",
        "game_id": game["id"],
        "subcategory_id": subcategory["id"],
        "is_auto_delivery": True,
    }, headers=auth(seller_token))
    assert r.status_code == 201, r.text
    return r.json()


@pytest.fixture
def order(client, funded_buyer, product):
    r = client.post("/api/v1/orders/",
                    json={"product_id": product["id"]},
                    headers=auth(funded_buyer))
    assert r.status_code == 201, r.text
    return r.json()


@pytest.fixture
def completed_order(client, funded_buyer, product, seller_token, order):
    """To'liq escrow flow: PAID_HELD → DELIVERED → COMPLETED."""
    oid = order["id"]
    r = client.post(f"/api/v1/orders/{oid}/deliver", headers=auth(seller_token))
    assert r.status_code == 200
    r = client.post(f"/api/v1/orders/{oid}/complete", headers=auth(funded_buyer))
    assert r.status_code == 200
    return r.json()
