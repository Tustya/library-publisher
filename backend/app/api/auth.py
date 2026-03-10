"""Роуты регистрации и входа."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.core.security import (
    create_access_token,
    hash_password,
    normalize_phone,
    verify_password,
)
from app.models.user import User
from app.schemas.user import Token, UserCreate, UserResponse, UserUpdate

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse)
async def register(
    payload: UserCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """Регистрация: телефон + пароль. Телефон нормализуется в 79XXXXXXXXX."""
    phone = normalize_phone(payload.phone)
    if len(phone) != 11 or not phone.startswith("79"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Укажите корректный номер телефона (например +7 999 123-45-67)",
        )
    result = await db.execute(select(User).where(User.phone == phone))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь с таким номером уже зарегистрирован",
        )
    user = User(
        phone=phone,
        hashed_password=hash_password(payload.password),
        first_name=None,
        last_name=None,
        patronymic=None,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user


@router.post("/login", response_model=Token)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    """Вход по телефону (username) и паролю. Возвращает JWT."""
    phone = normalize_phone(form_data.username)
    if len(phone) != 11:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный номер телефона или пароль",
        )
    result = await db.execute(select(User).where(User.phone == phone))
    user = result.scalar_one_or_none()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный номер телефона или пароль",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Аккаунт деактивирован",
        )
    return {
        "access_token": create_access_token(user.phone),
        "token_type": "bearer",
    }


@router.get("/me", response_model=UserResponse)
async def me(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Текущий авторизованный пользователь."""
    return current_user


@router.patch("/me", response_model=UserResponse)
async def update_me(
    payload: UserUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """Обновление профиля: имя, фамилия, отчество, телефон, адрес доставки."""
    if payload.first_name is not None:
        current_user.first_name = payload.first_name or None
    if payload.last_name is not None:
        current_user.last_name = payload.last_name or None
    if payload.patronymic is not None:
        current_user.patronymic = payload.patronymic or None
    if payload.delivery_address is not None:
        current_user.delivery_address = payload.delivery_address or None
    if payload.phone is not None:
        phone = normalize_phone(payload.phone)
        if len(phone) != 11 or not phone.startswith("79"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Укажите корректный номер телефона",
            )
        if phone != current_user.phone:
            result = await db.execute(select(User).where(User.phone == phone))
            if result.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Пользователь с таким номером уже зарегистрирован",
                )
            current_user.phone = phone
    await db.flush()
    await db.refresh(current_user)
    return current_user
