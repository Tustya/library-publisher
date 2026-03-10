#!/usr/bin/env python3
"""CLI для управления приложением."""

import argparse
import asyncio
import sys

from sqlalchemy import select

from app.core.database import async_session_factory
from app.core.security import normalize_phone
from app.models.user import User, USER_ROLE_ADMIN


async def cmd_set_admin(phone: str) -> int:
    """Назначить пользователя администратором по номеру телефона."""
    normalized = normalize_phone(phone)
    if len(normalized) != 11 or not normalized.startswith("79"):
        print("Ошибка: укажите корректный номер телефона (+7 999 123-45-67)", file=sys.stderr)
        return 1
    async with async_session_factory() as session:
        result = await session.execute(select(User).where(User.phone == normalized))
        user = result.scalar_one_or_none()
        if not user:
            print(f"Ошибка: пользователь с номером {normalized} не найден", file=sys.stderr)
            return 1
        user.role = USER_ROLE_ADMIN
        await session.commit()
    print(f"Пользователь {normalized} назначен администратором")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Управление библиотекой Доброграда")
    subparsers = parser.add_subparsers(dest="command", required=True)

    set_admin = subparsers.add_parser("set-admin", help="Назначить администратора по телефону")
    set_admin.add_argument("phone", help="Номер телефона (например +7 999 123-45-67)")

    args = parser.parse_args()
    if args.command == "set-admin":
        return asyncio.run(cmd_set_admin(args.phone))
    return 0


if __name__ == "__main__":
    sys.exit(main())
