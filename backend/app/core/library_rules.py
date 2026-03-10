"""Правила библиотеки: срок выдачи, лимиты, дедлайн заказа, пятницы доставки."""

from datetime import UTC, date, datetime, time, timedelta

# Книги на 1 неделю
LOAN_DAYS = 7

# Не более 3 книг в одном заказе (вариант B: 1 книга за раз, но макс 3 активных брони)
RESERVATION_LIMIT_PER_ORDER = 1
MAX_ACTIVE_RESERVATIONS_PER_USER = 3

# Доставка/возврат: пятница 17:00–18:00
# Заказ принимается до 12:00 пятницы
ORDER_DEADLINE_FRIDAY_HOUR = 12
ORDER_DEADLINE_FRIDAY_MINUTE = 0

# Пятница = weekday 4 (0 понедельник)
FRIDAY_WEEKDAY = 4


def _now_local() -> datetime:
    """Текущее время (серверное; для продакшена лучше задать timezone в config)."""
    return datetime.now(UTC)


def get_next_delivery_friday() -> date:
    """
    Ближайшая пятница доставки.
    Если сегодня пятница и ещё не 12:00 — эта пятница, иначе следующая.
    """
    now = _now_local()
    today = now.date()
    if today.weekday() == FRIDAY_WEEKDAY and now.time() < time(
        ORDER_DEADLINE_FRIDAY_HOUR, ORDER_DEADLINE_FRIDAY_MINUTE
    ):
        return today
    days_until_friday = (FRIDAY_WEEKDAY - today.weekday() + 7) % 7
    if days_until_friday == 0:
        days_until_friday = 7
    return today + timedelta(days=days_until_friday)


def get_due_return_date(delivery_date: date) -> date:
    """Дата возврата = пятница доставки + 7 дней."""
    return delivery_date + timedelta(days=LOAN_DAYS)


def can_order_for_next_friday() -> tuple[bool, str]:
    """
    Можно ли ещё оформить заказ на ближайшую пятницу.
    Возвращает (ok, message).
    """
    now = _now_local()
    today = now.date()
    if today.weekday() == FRIDAY_WEEKDAY and now.time() >= time(
        ORDER_DEADLINE_FRIDAY_HOUR, ORDER_DEADLINE_FRIDAY_MINUTE
    ):
        return False, "Приём заказов на эту пятницу закончен (после 12:00). Оформите заказ на следующую пятницу до 12:00."
    return True, ""
