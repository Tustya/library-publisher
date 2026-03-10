"""Хеширование паролей (Argon2), JWT и нормализация телефона."""

import re
from datetime import UTC, datetime, timedelta

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from jose import JWTError, jwt

from app.core.config import settings

ALGORITHM = "HS256"

_hasher = PasswordHasher()

# Единый формат хранения: 79XXXXXXXXX (11 цифр, без +)
PHONE_DIGITS_ONLY_PATTERN = re.compile(r"\D")
RUS_COUNTRY_CODE = "7"
RUS_PREFIX_10 = "9"  # после 7 идёт 9 для мобильных


def hash_password(password: str) -> str:
    """Хеширование пароля Argon2."""
    return _hasher.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Проверка пароля против хеша."""
    try:
        _hasher.verify(hashed_password, plain_password)
        return True
    except VerifyMismatchError:
        return False


def normalize_phone(raw: str) -> str:
    """
    Нормализация телефона в единый вид: 79XXXXXXXXX.
    Принимает +7, 8, 7 в начале, вставку из буфера, пробелы/скобки/тире.
    """
    digits = PHONE_DIGITS_ONLY_PATTERN.sub("", raw)
    if not digits:
        return ""
    if digits.startswith("8") and len(digits) >= 10:
        digits = RUS_COUNTRY_CODE + digits[1:]
    elif digits.startswith("7") and len(digits) == 11:
        pass
    elif len(digits) == 10 and digits.startswith(RUS_PREFIX_10):
        digits = RUS_COUNTRY_CODE + digits
    elif len(digits) == 10 and not digits.startswith(RUS_PREFIX_10):
        digits = RUS_COUNTRY_CODE + digits
    return digits[:11] if len(digits) >= 11 else digits


def create_access_token(subject: str) -> str:
    """Создать JWT с sub=phone."""
    expire = datetime.now(UTC) + timedelta(minutes=settings.access_token_expire_minutes)
    to_encode = {"sub": subject, "exp": expire}
    return jwt.encode(to_encode, settings.secret_key, algorithm=ALGORITHM)


def decode_access_token(token: str) -> str | None:
    """Декодировать JWT, вернуть sub (phone) или None."""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
        return payload.get("sub")
    except JWTError:
        return None
