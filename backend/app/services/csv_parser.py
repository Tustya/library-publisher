"""Парсинг CSV-каталога по спецификации specs/csv-catalog-parsing.md."""

import csv
import re
from io import StringIO
from typing import Any

# Разделители для отсечения описания (издательство, год) от «автор + название»
DESC_SEP = re.compile(r"\s/\s|\.\s-\s")
# Точка с пробелом — разделитель автора и названия
AUTHOR_TITLE_SEP = re.compile(r"\.\s+")
# Возрастные метки
AGE_RATINGS = ("0+", "6+", "12+", "16+")
DEFAULT_AGE = "0+"
# Язык по ключевым словам
LANG_EN = re.compile(r"англ\.?\s*яз\.?", re.I)
# Теги
TAG_CLASSIC = re.compile(r"\bклассика\b", re.I)


def _parse_author_title(cell: str) -> tuple[str, str, str | None]:
    """
    Извлечь автора, название и опционально описание из ячейки «Автор. Наименование.».
    Возвращает (author, title, description).
    """
    cell = (cell or "").strip()
    if not cell:
        return ("", "", None)
    # Отсечь описание после « / » или «. - »
    match = DESC_SEP.search(cell)
    main_part = cell[: match.start()].strip() if match else cell
    rest = cell[match.end() :].strip() if match else None
    if not main_part:
        return ("", "", rest or None)
    # Автор и название: по первому «. » (точка и пробел)
    split = AUTHOR_TITLE_SEP.split(main_part, maxsplit=1)
    if len(split) == 2:
        author, title = split[0].strip(), split[1].strip()
    else:
        author, title = "", main_part.strip()
    return (author or "", title or "", rest)


def _parse_age_cell(cell: str) -> tuple[str, str, list[str]]:
    """
    Нормализовать колонку «Возраст»: возрастная метка, язык, теги.
    Возвращает (age_rating, language, tags).
    """
    cell = (cell or "").strip()
    age_rating = DEFAULT_AGE
    language = "русский"
    tags: list[str] = []
    if not cell:
        return (age_rating, language, tags)
    lower = cell.lower()
    if LANG_EN.search(cell):
        language = "английский"
    if TAG_CLASSIC.search(cell):
        tags.append("классика")
    for ar in AGE_RATINGS:
        if ar in cell or ar in lower:
            age_rating = ar
            break
    return (age_rating, language, tags)


def _normalize_unique_number(value: Any) -> str:
    """Уникальный номер — строка (в CSV может быть число)."""
    if value is None:
        return ""
    return str(value).strip()


def _find_column(row: list[str], possible_headers: list[str]) -> int | None:
    """Найти индекс колонки по возможным названиям заголовка."""
    for i, cell in enumerate(row):
        normalized = (cell or "").strip().lower().replace("\n", " ")
        for h in possible_headers:
            if h.lower() in normalized or normalized in h.lower():
                return i
    return None


def _detect_columns(headers: list[str]) -> dict[str, int]:
    """Определить индексы колонок по первой строке (возможен перенос в заголовке)."""
    row = [(h or "").strip() for h in headers]
    result: dict[str, int] = {}
    # Фото
    for i, h in enumerate(row):
        if "фото" in (h or "").lower():
            result["photo"] = i
            break
    # Автор. Наименование.
    for i, h in enumerate(row):
        if "автор" in (h or "").lower() and "наименование" in (h or "").lower():
            result["author_title"] = i
            break
    if "author_title" not in result:
        for i, h in enumerate(row):
            if "автор" in (h or "").lower():
                result["author_title"] = i
                break
    # Уникальный номер
    for i, h in enumerate(row):
        if "уникальн" in (h or "").lower() and "номер" in (h or "").lower():
            result["unique_number"] = i
            break
    if "unique_number" not in result:
        for i, h in enumerate(row):
            if "уникальн" in (h or "").lower() or "номер" in (h or "").lower():
                result["unique_number"] = i
                break
    # Жанр
    for i, h in enumerate(row):
        if (h or "").lower().strip() == "жанр":
            result["genre"] = i
            break
    # Возраст
    for i, h in enumerate(row):
        if (h or "").lower().strip() == "возраст":
            result["age"] = i
            break
    # Статус
    for i, h in enumerate(row):
        if (h or "").lower().strip() == "статус":
            result["status"] = i
            break
    return result


def parse_csv_rows(content: str) -> list[dict[str, Any]]:
    """
    Распарсить CSV (UTF-8, возможно BOM). Первая строка — заголовок.
    Возвращает список словарей с ключами: author, title, description, genre,
    age_rating, language, tags, photo, unique_number, status.
    Группировка по книге не делается — возвращаем по одной записи на строку (экземпляр).
    """
    if not content.strip():
        return []
    # Убрать BOM
    if content.startswith("\ufeff"):
        content = content[1:]
    reader = csv.reader(StringIO(content), delimiter=",", quotechar='"')
    rows = list(reader)
    if not rows:
        return []
    headers = rows[0]
    cols = _detect_columns(headers)
    result: list[dict[str, Any]] = []
    for r in rows[1:]:
        if not r:
            continue
        author, title, description = _parse_author_title(
            r[cols["author_title"]] if cols.get("author_title") is not None and cols["author_title"] < len(r)
            else ""
        )
        age_rating, language, tags = _parse_age_cell(
            r[cols["age"]] if cols.get("age") is not None and cols["age"] < len(r) else ""
        )
        unique_number = _normalize_unique_number(
            r[cols["unique_number"]] if cols.get("unique_number") is not None and cols["unique_number"] < len(r) else ""
        )
        if not unique_number and not author and not title:
            continue
        if not unique_number:
            unique_number = f"row_{len(result)}"
        photo = ""
        if cols.get("photo") is not None and cols["photo"] < len(r):
            photo = (r[cols["photo"]] or "").strip()
        genre = ""
        if cols.get("genre") is not None and cols["genre"] < len(r):
            genre = (r[cols["genre"]] or "").strip()
        status = ""
        if cols.get("status") is not None and cols["status"] < len(r):
            status = (r[cols["status"]] or "").strip()
        if not status:
            status = "Не указан"
        result.append({
            "author": author,
            "title": title,
            "description": description,
            "genre": genre or None,
            "age_rating": age_rating,
            "language": language,
            "tags": tags if tags else None,
            "photo": photo or None,
            "unique_number": unique_number,
            "status": status,
        })
    return result
