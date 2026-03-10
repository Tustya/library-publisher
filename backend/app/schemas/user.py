"""Схемы пользователя и auth."""

from pydantic import BaseModel, Field


class UserCreate(BaseModel):
    """Регистрация: только телефон и пароль."""

    phone: str = Field(..., min_length=10, max_length=20)
    password: str = Field(..., min_length=8, max_length=128)


class UserResponse(BaseModel):
    """Пользователь в ответах (без пароля)."""

    id: int
    phone: str
    first_name: str | None
    last_name: str | None
    patronymic: str | None
    delivery_address: str | None
    is_active: bool
    role: str

    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    """Обновление профиля: имя, фамилия, отчество, телефон, адрес доставки."""

    first_name: str | None = Field(None, max_length=100)
    last_name: str | None = Field(None, max_length=100)
    patronymic: str | None = Field(None, max_length=100)
    phone: str | None = Field(None, min_length=10, max_length=20)
    delivery_address: str | None = Field(None, max_length=500)


class Token(BaseModel):
    """Ответ логина."""

    access_token: str
    token_type: str = "bearer"
