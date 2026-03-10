"""Импорт каталога из распарсенных строк CSV: группировка по книге, создание/обновление записей."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.age_rating import AgeRating
from app.models.author import Author
from app.models.book import Book, BookCopy, book_authors
from app.models.genre import Genre
from app.models.language import Language
from app.models.tag import Tag
from app.services.csv_parser import parse_csv_rows


def _book_key(row: dict) -> tuple[str, str]:
    """Ключ группировки: (author, title)."""
    author = (row.get("author") or "").strip()
    title = (row.get("title") or "").strip()
    return (author or "Не указан", title or "Не указан")


async def _get_or_create_author(db: AsyncSession, name: str) -> Author:
    """Найти или создать автора."""
    result = await db.execute(select(Author).where(Author.name == name))
    author = result.scalar_one_or_none()
    if author:
        return author
    author = Author(name=name)
    db.add(author)
    await db.flush()
    return author


async def _get_or_create_genre(db: AsyncSession, name: str | None) -> Genre | None:
    """Найти или создать жанр. Если name пустой — вернуть None."""
    if not name or not name.strip():
        return None
    result = await db.execute(select(Genre).where(Genre.name == name.strip()))
    genre = result.scalar_one_or_none()
    if genre:
        return genre
    genre = Genre(name=name.strip())
    db.add(genre)
    await db.flush()
    return genre


async def _get_or_create_age_rating(db: AsyncSession, code: str) -> AgeRating:
    """Найти возрастной рейтинг по коду."""
    result = await db.execute(select(AgeRating).where(AgeRating.code == code))
    ar = result.scalar_one_or_none()
    if ar:
        return ar
    ar = AgeRating(code=code)
    db.add(ar)
    await db.flush()
    return ar


async def _get_or_create_language(db: AsyncSession, name: str) -> Language:
    """Найти или создать язык."""
    result = await db.execute(select(Language).where(Language.name == name))
    lang = result.scalar_one_or_none()
    if lang:
        return lang
    lang = Language(name=name)
    db.add(lang)
    await db.flush()
    return lang


async def _get_or_create_tags(
    db: AsyncSession, tag_names: list[str] | None
) -> list[Tag]:
    """Найти или создать теги по списку имён."""
    if not tag_names:
        return []
    result_tags: list[Tag] = []
    for name in tag_names:
        if not name or not str(name).strip():
            continue
        n = str(name).strip()
        result = await db.execute(select(Tag).where(Tag.name == n))
        tag = result.scalar_one_or_none()
        if not tag:
            tag = Tag(name=n)
            db.add(tag)
            await db.flush()
        result_tags.append(tag)
    return result_tags


async def import_from_csv_content(
    db: AsyncSession,
    content: str,
) -> tuple[int, int]:
    """
    Импортировать каталог из содержимого CSV.
    Группирует строки по книге (автор + название), создаёт/обновляет книги и экземпляры.
    Возвращает (количество книг, количество экземпляров).
    """
    rows = parse_csv_rows(content)
    if not rows:
        return (0, 0)
    groups: dict[tuple[str, str], list[dict]] = {}
    for r in rows:
        key = _book_key(r)
        groups.setdefault(key, []).append(r)
    books_created = 0
    copies_created = 0
    for (author_name, title), group_rows in groups.items():
        seen_numbers: set[str] = set()
        deduped_rows: list[dict] = []
        for r in group_rows:
            unum = (r.get("unique_number") or "").strip()
            if not unum or unum in seen_numbers:
                continue
            seen_numbers.add(unum)
            deduped_rows.append(r)
        if not deduped_rows:
            continue
        first = deduped_rows[0]
        author = await _get_or_create_author(db, author_name)
        genre = await _get_or_create_genre(db, first.get("genre"))
        age_rating = await _get_or_create_age_rating(
            db, first.get("age_rating") or "0+"
        )
        language = await _get_or_create_language(
            db, first.get("language") or "русский"
        )
        tag_list = await _get_or_create_tags(db, first.get("tags"))

        result = await db.execute(
            select(Book)
            .where(Book.title == title)
            .join(book_authors, Book.id == book_authors.c.book_id)
            .where(book_authors.c.author_id == author.id)
        )
        book = result.unique().scalars().first()
        if not book:
            book = Book(
                title=title,
                description=first.get("description"),
                cover_url=None,
                genre_id=genre.id if genre else None,
                age_rating_id=age_rating.id,
                language_id=language.id,
            )
            book.author_rels = [author]
            book.tag_rels = tag_list
            db.add(book)
            await db.flush()
            books_created += 1
        if not book.cover_url:
            for r in deduped_rows:
                if r.get("photo"):
                    book.cover_url = r["photo"]
                    break
        for r in deduped_rows:
            unum = (r.get("unique_number") or "").strip()
            if not unum:
                continue
            existing = await db.execute(
                select(BookCopy).where(BookCopy.unique_number == unum)
            )
            copy = existing.scalar_one_or_none()
            if copy:
                copy.status = r.get("status") or copy.status
                if r.get("photo"):
                    copy.cover_url = r["photo"]
                continue
            copy = BookCopy(
                book_id=book.id,
                unique_number=unum,
                status=r.get("status") or "Не указан",
                cover_url=r.get("photo"),
            )
            db.add(copy)
            copies_created += 1
    return (books_created, copies_created)