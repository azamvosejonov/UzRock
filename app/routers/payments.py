"""
To'lov tizimi: Click va Payme (Uzbekistan)

Click flow:
  1. POST /payments/click/prepare  — Click to'lovdan oldin so'raydi (tekshirish)
  2. POST /payments/click/complete — Click to'lov tasdiqlangach so'raydi (bajarish)

Payme flow:
  1. POST /payments/payme          — JSON-RPC 2.0 endpoint (barcha metodlar bitta URL)

Foydalanuvchi balansini to'ldirish uchun:
  POST /payments/topup             — invoice yaratib, to'lov URL qaytaradi
"""

import hashlib
import hmac
import os
import base64
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from uuid import UUID

from ..database import get_db
from ..models import User, Transaction
from ..schemas import SuccessResponse, ClickPrepareRequest, ClickPrepareResponse, PaymeRequest
from ..utils.deps import get_current_user
from ..utils.logger import get_logger

router = APIRouter()
log = get_logger("payments")

CLICK_SECRET_KEY = os.getenv("CLICK_SECRET_KEY", "")
CLICK_SERVICE_ID = os.getenv("CLICK_SERVICE_ID", "")
CLICK_MERCHANT_ID = os.getenv("CLICK_MERCHANT_ID", "")

PAYME_KEY = os.getenv("PAYME_KEY", "")
PAYME_ID = os.getenv("PAYME_ID", "")
PAYME_TEST_KEY = os.getenv("PAYME_TEST_KEY", "")


def _add_balance(db: Session, user_id, amount: Decimal, desc: str, order_id=None):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return False
    user.balance += amount
    tx = Transaction(user_id=user_id, order_id=order_id, type="DEPOSIT", amount=amount, description=desc)
    db.add(tx)
    db.commit()
    log.info(f"Balance top-up: user={user_id} amount={amount}")
    return True


# ── Topup (create invoice) ──────────────────────────────────────

@router.post("/topup")
def create_topup(
    amount: Decimal,
    method: str,
    user: User = Depends(get_current_user),
):
    """
    Balansni to'ldirish uchun to'lov havolasini yaratadi.
    method: click | payme
    """
    if amount <= 0:
        raise HTTPException(400, "Summa 0 dan katta bo'lishi kerak")

    merchant_trans_id = f"topup_{user.id}_{int(amount)}"

    if method == "click":
        # Click invoice URL
        url = (
            f"https://my.click.uz/services/pay"
            f"?service_id={CLICK_SERVICE_ID}"
            f"&merchant_id={CLICK_MERCHANT_ID}"
            f"&amount={amount}"
            f"&transaction_param={merchant_trans_id}"
            f"&return_url=https://yoursite.uz/profile/balance"
        )
        return {"payment_url": url, "method": "click", "amount": amount}

    elif method == "payme":
        # Payme invoice URL
        params = f'm={PAYME_ID};ac.merchant_trans_id={merchant_trans_id};a={int(amount * 100)}'
        encoded = base64.b64encode(params.encode()).decode()
        url = f"https://checkout.paycom.uz/{encoded}"
        return {"payment_url": url, "method": "payme", "amount": amount}

    raise HTTPException(400, "Noma'lum to'lov usuli. click yoki payme kiriting")


# ── Click callbacks ─────────────────────────────────────────────

def _click_verify_sign(data: ClickPrepareRequest) -> bool:
    """Click imzosini tekshirish."""
    sign = hashlib.md5(
        f"{data.click_trans_id}{data.service_id}{CLICK_SECRET_KEY}"
        f"{data.merchant_trans_id}{data.amount}{data.action}{data.sign_time}".encode()
    ).hexdigest()
    return sign == data.sign_string


@router.post("/click/prepare", response_model=ClickPrepareResponse)
def click_prepare(data: ClickPrepareRequest, db: Session = Depends(get_db)):
    """Click Prepare — to'lovdan oldin tekshirish."""
    log.info(f"Click prepare: {data.merchant_trans_id} amount={data.amount}")

    if not _click_verify_sign(data):
        return ClickPrepareResponse(
            click_trans_id=data.click_trans_id,
            merchant_trans_id=data.merchant_trans_id,
            error=-1,
            error_note="SIGN CHECK FAILED",
        )

    if data.error != 0:
        return ClickPrepareResponse(
            click_trans_id=data.click_trans_id,
            merchant_trans_id=data.merchant_trans_id,
            error=data.error,
            error_note=data.error_note,
        )

    # merchant_trans_id formatini tekshirish (topup_{user_id}_{amount})
    parts = data.merchant_trans_id.split("_")
    if len(parts) < 3 or parts[0] != "topup":
        return ClickPrepareResponse(
            click_trans_id=data.click_trans_id,
            merchant_trans_id=data.merchant_trans_id,
            error=-5,
            error_note="USER NOT FOUND",
        )

    try:
        user_id = parts[1]
        user = db.query(User).filter(User.id == user_id).first()
    except Exception:
        user = None

    if not user:
        return ClickPrepareResponse(
            click_trans_id=data.click_trans_id,
            merchant_trans_id=data.merchant_trans_id,
            error=-5,
            error_note="USER NOT FOUND",
        )

    return ClickPrepareResponse(
        click_trans_id=data.click_trans_id,
        merchant_trans_id=data.merchant_trans_id,
        merchant_prepare_id=data.click_trans_id,
        error=0,
        error_note="Success",
    )


@router.post("/click/complete", response_model=ClickPrepareResponse)
def click_complete(data: ClickPrepareRequest, db: Session = Depends(get_db)):
    """Click Complete — to'lov amalga oshirilgach balansga qo'shish."""
    log.info(f"Click complete: {data.merchant_trans_id} amount={data.amount}")

    if not _click_verify_sign(data):
        return ClickPrepareResponse(
            click_trans_id=data.click_trans_id,
            merchant_trans_id=data.merchant_trans_id,
            error=-1,
            error_note="SIGN CHECK FAILED",
        )

    if data.error != 0:
        return ClickPrepareResponse(
            click_trans_id=data.click_trans_id,
            merchant_trans_id=data.merchant_trans_id,
            error=data.error,
            error_note=data.error_note,
        )

    parts = data.merchant_trans_id.split("_")
    if len(parts) < 3:
        return ClickPrepareResponse(
            click_trans_id=data.click_trans_id,
            merchant_trans_id=data.merchant_trans_id,
            error=-9,
            error_note="INVALID TRANSACTION",
        )

    user_id = parts[1]
    amount = Decimal(str(data.amount))

    ok = _add_balance(db, user_id, amount, f"Click to'lov: {data.click_trans_id}")
    if not ok:
        return ClickPrepareResponse(
            click_trans_id=data.click_trans_id,
            merchant_trans_id=data.merchant_trans_id,
            error=-5,
            error_note="USER NOT FOUND",
        )

    return ClickPrepareResponse(
        click_trans_id=data.click_trans_id,
        merchant_trans_id=data.merchant_trans_id,
        merchant_prepare_id=data.click_trans_id,
        error=0,
        error_note="Success",
    )


# ── Payme JSON-RPC ──────────────────────────────────────────────

def _payme_auth(request: Request) -> bool:
    """Payme Basic Auth tekshirish."""
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Basic "):
        return False
    try:
        decoded = base64.b64decode(auth[6:]).decode()
        _, key = decoded.split(":", 1)
        return key in (PAYME_KEY, PAYME_TEST_KEY)
    except Exception:
        return False


def _payme_error(code: int, message: str, req_id: int):
    return {"error": {"code": code, "message": message}, "id": req_id}


def _payme_ok(result: dict, req_id: int):
    return {"result": result, "id": req_id}


@router.post("/payme")
async def payme_endpoint(request: Request, db: Session = Depends(get_db)):
    """
    Payme JSON-RPC 2.0 endpoint.
    Metodlar: CheckPerformTransaction, CreateTransaction,
              PerformTransaction, CancelTransaction, CheckTransaction
    """
    if not _payme_auth(request):
        raise HTTPException(401, "Payme autentifikatsiya xatosi")

    body = await request.json()
    method = body.get("method")
    params = body.get("params", {})
    req_id = body.get("id", 1)

    log.info(f"Payme method: {method} | params: {params}")

    # merchant_trans_id dan user_id olish
    account = params.get("account", {})
    merchant_trans_id = account.get("merchant_trans_id", "")
    parts = merchant_trans_id.split("_") if merchant_trans_id else []
    user_id = parts[1] if len(parts) >= 3 else None
    amount_tiyin = params.get("amount", 0)
    amount = Decimal(str(amount_tiyin)) / 100  # tiyindan so'mga

    if method == "CheckPerformTransaction":
        if not user_id:
            return _payme_error(-31050, {"uz": "Foydalanuvchi topilmadi"}, req_id)
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return _payme_error(-31050, {"uz": "Foydalanuvchi topilmadi"}, req_id)
        if amount <= 0:
            return _payme_error(-31001, {"uz": "Noto'g'ri summa"}, req_id)
        return _payme_ok({"allow": True}, req_id)

    elif method == "CreateTransaction":
        trans_id = params.get("id")
        return _payme_ok({
            "create_time": int(__import__("time").time() * 1000),
            "transaction": trans_id,
            "state": 1,
        }, req_id)

    elif method == "PerformTransaction":
        trans_id = params.get("id")
        if user_id:
            _add_balance(db, user_id, amount, f"Payme to'lov: {trans_id}")
        return _payme_ok({
            "perform_time": int(__import__("time").time() * 1000),
            "transaction": trans_id,
            "state": 2,
        }, req_id)

    elif method == "CancelTransaction":
        trans_id = params.get("id")
        reason = params.get("reason", 0)
        return _payme_ok({
            "cancel_time": int(__import__("time").time() * 1000),
            "transaction": trans_id,
            "state": -1,
        }, req_id)

    elif method == "CheckTransaction":
        trans_id = params.get("id")
        return _payme_ok({
            "create_time": 0,
            "perform_time": 0,
            "cancel_time": 0,
            "transaction": trans_id,
            "state": 2,
            "reason": None,
        }, req_id)

    elif method == "GetStatement":
        return _payme_ok({"transactions": []}, req_id)

    return _payme_error(-32601, {"uz": "Noma'lum metod"}, req_id)
