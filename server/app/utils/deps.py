from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import User
from .security import decode_token

bearer = HTTPBearer()


def _resolve_user(
    creds: HTTPAuthorizationCredentials = Depends(bearer),
    db: Session = Depends(get_db),
) -> User:
    payload = decode_token(creds.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="Token yaroqsiz yoki muddati o'tgan")
    user = db.query(User).filter(User.id == payload["sub"]).first()
    if not user:
        raise HTTPException(status_code=401, detail="Foydalanuvchi topilmadi")
    return user


def get_current_user(user: User = Depends(_resolve_user)) -> User:
    return user


def require_seller(user: User = Depends(get_current_user)) -> User:
    if not user.is_seller:
        raise HTTPException(status_code=403, detail="Sotuvchi akkaunt talab qilinadi")
    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin huquqi talab qilinadi")
    return user


def optional_user(
    db: Session = Depends(get_db),
    creds: HTTPAuthorizationCredentials = Depends(HTTPBearer(auto_error=False)),
) -> User | None:
    """Returns user if token present and valid, else None."""
    if not creds:
        return None
    payload = decode_token(creds.credentials)
    if not payload:
        return None
    return db.query(User).filter(User.id == payload["sub"]).first()
