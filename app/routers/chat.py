import datetime
from typing import Dict, List
from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from uuid import UUID

from ..database import get_db, SessionLocal
from ..models import Message, Order, User, Notification
from ..schemas import MessageCreate, MessageOut
from ..utils.deps import get_current_user
from ..utils.pagination import paginate, PagedResponse
from ..utils.security import decode_token
from ..utils.logger import get_logger

router = APIRouter()
log = get_logger("chat")


class ConnectionManager:
    """Real-time WebSocket connections per order room."""

    def __init__(self):
        self._rooms: Dict[str, List[WebSocket]] = {}

    async def connect(self, ws: WebSocket, order_id: str):
        await ws.accept()
        self._rooms.setdefault(order_id, []).append(ws)
        log.info(f"WS connect: order={order_id}")

    def disconnect(self, ws: WebSocket, order_id: str):
        room = self._rooms.get(order_id, [])
        if ws in room:
            room.remove(ws)
        log.info(f"WS disconnect: order={order_id}")

    async def broadcast(self, order_id: str, data: dict):
        for ws in list(self._rooms.get(order_id, [])):
            try:
                await ws.send_json(data)
            except Exception:
                pass


manager = ConnectionManager()


def _get_order_or_403(order_id: UUID, user: User, db: Session) -> Order:
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(404, "Buyurtma topilmadi")
    if order.buyer_id != user.id and order.seller_id != user.id and not user.is_admin:
        raise HTTPException(403, "Ruxsat yo'q")
    return order


# ── REST endpoints ──────────────────────────────────────────────

@router.get("/{order_id}/messages", response_model=PagedResponse[MessageOut])
def get_messages(
    order_id: UUID,
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=200),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _get_order_or_403(order_id, user, db)
    q = db.query(Message).filter(Message.order_id == order_id).order_by(Message.created_at.asc())

    # O'qilmagan xabarlarni o'qilgan deb belgilaymiz
    db.query(Message).filter(
        Message.order_id == order_id,
        Message.sender_id != user.id,
        Message.is_read == False,
    ).update({"is_read": True})
    db.commit()

    items, total, pages = paginate(q, page, size)
    return {"items": items, "total": total, "page": page, "size": size, "pages": pages}


@router.post("/{order_id}/messages", response_model=MessageOut, status_code=201)
def send_message(
    order_id: UUID,
    payload: MessageCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    order = _get_order_or_403(order_id, user, db)
    if order.status in ("COMPLETED", "CANCELLED"):
        raise HTTPException(400, "Yopilgan buyurtmaga xabar yubora olmaysiz")

    msg = Message(
        order_id=order_id,
        sender_id=user.id,
        content=payload.content,
        message_type=payload.message_type,
        file_url=payload.file_url,
    )
    db.add(msg)

    # Boshqa tomonni xabardor qilish
    recipient = order.seller_id if user.id == order.buyer_id else order.buyer_id
    n = Notification(
        user_id=recipient,
        title="Yangi xabar",
        message=f"{user.username}: {(payload.content or '')[:60]}",
        link=f"/orders/{order_id}",
    )
    db.add(n)
    db.commit()
    db.refresh(msg)
    return msg


# ── WebSocket endpoint ──────────────────────────────────────────

@router.websocket("/{order_id}/ws")
async def websocket_chat(order_id: UUID, ws: WebSocket, token: str = Query(...)):
    """
    ws://host/api/v1/chat/{order_id}/ws?token=<JWT>

    Sends JSON: {type, sender_id, content, file_url, created_at}
    """
    payload = decode_token(token)
    if not payload:
        await ws.close(code=4001, reason="Token yaroqsiz")
        return

    db: Session = SessionLocal()
    try:
        user = db.query(User).filter(User.id == payload["sub"]).first()
        if not user:
            await ws.close(code=4001, reason="Foydalanuvchi topilmadi")
            return

        order = db.query(Order).filter(Order.id == order_id).first()
        if not order or (order.buyer_id != user.id and order.seller_id != user.id and not user.is_admin):
            await ws.close(code=4003, reason="Ruxsat yo'q")
            return

        room_key = str(order_id)
        await manager.connect(ws, room_key)

        try:
            while True:
                data = await ws.receive_json()
                content = data.get("content", "").strip()
                file_url = data.get("file_url")
                msg_type = data.get("message_type", "TEXT")

                if not content and not file_url:
                    continue

                msg = Message(
                    order_id=order_id,
                    sender_id=user.id,
                    content=content or None,
                    message_type=msg_type,
                    file_url=file_url,
                )
                db.add(msg)
                db.commit()
                db.refresh(msg)

                out = {
                    "id": str(msg.id),
                    "order_id": str(msg.order_id),
                    "sender_id": str(msg.sender_id),
                    "content": msg.content,
                    "message_type": msg.message_type,
                    "file_url": msg.file_url,
                    "is_read": msg.is_read,
                    "created_at": msg.created_at.isoformat(),
                }
                await manager.broadcast(room_key, out)

        except WebSocketDisconnect:
            manager.disconnect(ws, room_key)
    finally:
        db.close()
