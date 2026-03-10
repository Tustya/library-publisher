"""Модель пользователя (читатель)."""

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base

USER_ROLE_READER = "reader"
USER_ROLE_ADMIN = "admin"


class User(Base):
    """Читатель: вход по телефону + пароль, имя/фамилия/отчество для профиля."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    phone: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    first_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    last_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    patronymic: Mapped[str | None] = mapped_column(String(100), nullable=True)
    delivery_address: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    role: Mapped[str] = mapped_column(String(50), nullable=False, default=USER_ROLE_READER)

    def __repr__(self) -> str:
        return f"User(id={self.id}, phone={self.phone!r})"
