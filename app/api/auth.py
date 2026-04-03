from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from database import get_db
from models import AdminInfo

router = APIRouter(prefix="/admin", tags=["auth"])


class TokenOut(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshIn(BaseModel):
    refresh_token: str


class RegisterIn(BaseModel):
    username: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=6, max_length=255)


@router.post("/login", response_model=TokenOut)
def login(
    form: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """Đăng nhập — trả về access_token (30 phút) và refresh_token (7 ngày)."""
    admin = db.query(AdminInfo).filter(AdminInfo.username == form.username).first()
    if not admin or not verify_password(form.password, admin.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sai tên đăng nhập hoặc mật khẩu",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not admin.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tài khoản đã bị vô hiệu hoá",
        )
    return TokenOut(
        access_token=create_access_token(admin.username),
        refresh_token=create_refresh_token(admin.username),
    )


@router.post("/refresh", response_model=TokenOut)
def refresh_token(payload: RefreshIn, db: Session = Depends(get_db)):
    """Dùng refresh_token để lấy cặp token mới (access + refresh)."""
    username = decode_token(payload.refresh_token, expected_type="refresh")
    admin = (
        db.query(AdminInfo)
        .filter(AdminInfo.username == username, AdminInfo.is_active == True)
        .first()
    )
    if admin is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tài khoản không tồn tại hoặc đã bị vô hiệu hoá",
        )
    return TokenOut(
        access_token=create_access_token(admin.username),
        refresh_token=create_refresh_token(admin.username),
    )


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register_first_admin(payload: RegisterIn, db: Session = Depends(get_db)):
    """Tạo tài khoản admin đầu tiên. Bị khoá khi đã có admin trong hệ thống."""
    existing = db.query(AdminInfo).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Đã có admin. Liên hệ quản trị viên hiện tại để được cấp tài khoản.",
        )
    admin = AdminInfo(
        username=payload.username,
        password=hash_password(payload.password),
    )
    db.add(admin)
    db.commit()
    return {"message": f"Tạo tài khoản admin '{payload.username}' thành công."}
