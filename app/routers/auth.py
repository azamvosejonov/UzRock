import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User
from ..schemas import UserCreate, UserLogin, UserOut, Token, UserUpdate
from ..utils.security import hash_password, verify_password, create_access_token
from ..utils.deps import get_current_user
from ..utils.logger import get_logger

router = APIRouter()
log = get_logger("auth")


@router.post("/register", response_model=Token, status_code=201)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(409, "Bu email allaqachon ro'yxatdan o'tgan")
    if db.query(User).filter(User.username == payload.username).first():
        raise HTTPException(409, "Bu username band")

    user = User(
        username=payload.username,
        email=payload.email,
        password_hash=hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    log.info(f"Yangi foydalanuvchi: {user.email}")
    return Token(access_token=create_access_token(str(user.id)))


@router.post("/login", response_model=Token)
def login(payload: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(401, "Email yoki parol noto'g'ri")

    user.last_online = datetime.datetime.utcnow()
    db.commit()
    log.info(f"Login: {user.email}")
    return Token(access_token=create_access_token(str(user.id)))


@router.get("/me", response_model=UserOut)
def get_me(user: User = Depends(get_current_user)):
    return user


@router.patch("/me", response_model=UserOut)
def update_me(
    payload: UserUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(user, field, value)
    db.commit()
    db.refresh(user)
    return user


@router.post("/me/become-seller", response_model=UserOut)
def become_seller(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if user.is_seller:
        raise HTTPException(400, "Siz allaqachon sotuvchisiz")
    user.is_seller = True
    db.commit()
    db.refresh(user)
    log.info(f"Yangi sotuvchi: {user.email}")
    return user
