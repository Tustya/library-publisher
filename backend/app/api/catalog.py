"""API каталога книг: список, карточка, импорт из CSV."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_optional_user, require_admin
from app.models.book_queue import BookQueue
from app.models.user import User
from app.core.database import get_db
from app.helpers import format_authors_display
from app.models.age_rating import AgeRating
from app.models.author import Author
from app.models.book import Book, BookCopy, book_authors
from app.core.library_rules import get_due_return_date
from app.models.delivery import (
    RESERVATION_STATUS_CREATED,
    RESERVATION_STATUS_ISSUED,
    Delivery,
    Reservation,
)
from app.models.genre import Genre
from app.models.language import Language
from app.models.tag import Tag
from app.schemas.book import BookDetail, BookListEntry, BookListResponse, RefItem
from app.services.import_catalog import import_from_csv_content

router = APIRouter(prefix="/catalog", tags=["catalog"])


@router.get("/genres", response_model=list[RefItem])
async def list_genres(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[RefItem]:
    """Список жанров для фильтрации и форм."""
    result = await db.execute(select(Genre).order_by(Genre.name))
    return [RefItem(id=g.id, name=g.name) for g in result.scalars().all()]


@router.get("/authors", response_model=list[RefItem])
async def list_authors(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[RefItem]:
    """Список авторов для форм."""
    result = await db.execute(select(Author).order_by(Author.name))
    return [RefItem(id=a.id, name=a.name) for a in result.scalars().all()]


@router.get("/age-ratings", response_model=list[RefItem])
async def list_age_ratings(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[RefItem]:
    """Список возрастных рейтингов (0+, 6+, ...)."""
    result = await db.execute(select(AgeRating).order_by(AgeRating.id))
    return [RefItem(id=ar.id, name=ar.code) for ar in result.scalars().all()]


@router.get("/languages", response_model=list[RefItem])
async def list_languages(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[RefItem]:
    """Список языков для форм."""
    result = await db.execute(select(Language).order_by(Language.name))
    return [RefItem(id=lang.id, name=lang.name) for lang in result.scalars().all()]


@router.get("/tags", response_model=list[RefItem])
async def list_tags(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[RefItem]:
    """Список тегов для форм."""
    result = await db.execute(select(Tag).order_by(Tag.name))
    return [RefItem(id=t.id, name=t.name) for t in result.scalars().all()]

# Статусы, при которых экземпляр считается доступным
AVAILABLE_STATUS_PATTERN = "%доступно%"

# Экземпляр занят, если на него есть активная бронь
ACTIVE_RESERVATION_STATUSES = (RESERVATION_STATUS_CREATED, RESERVATION_STATUS_ISSUED)


def _available_count(
    copies: list[BookCopy],
    reserved_copy_ids: set[int] | None = None,
) -> int:
    """Число экземпляров с доступным статусом и без активной брони."""
    reserved = reserved_copy_ids or set()
    return sum(
        1
        for c in copies
        if c.status
        and "доступно" in c.status.lower()
        and c.id not in reserved
    )


async def _get_reserved_copy_ids(db: AsyncSession) -> set[int]:
    """ID экземпляров, занятых активными бронями."""
    stmt = select(Reservation.book_copy_id).where(
        Reservation.status.in_(ACTIVE_RESERVATION_STATUSES)
    )
    result = await db.execute(stmt)
    return set(result.scalars().all())


@router.get("/books", response_model=BookListResponse)
async def list_books(
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = 1,
    size: int = 20,
    search: str | None = None,
    genre: str | None = None,
    age_rating: str | None = None,
    language: str | None = None,
    available_only: bool = False,
) -> BookListResponse:
    """
    Список книг с пагинацией, поиском по названию/автору и фильтрами.
    """
    size = max(1, min(size, 100))
    page = max(1, page)
    offset = (page - 1) * size

    base = select(Book).options(
        selectinload(Book.author_rels),
        selectinload(Book.genre_rel),
        selectinload(Book.age_rating_rel),
        selectinload(Book.language_rel),
        selectinload(Book.tag_rels),
        selectinload(Book.copies),
    )
    count_stmt = select(func.count(Book.id))
    if search and search.strip():
        q = f"%{search.strip()}%"
        author_match = select(1).select_from(book_authors).join(
            Author, Author.id == book_authors.c.author_id
        ).where(
            book_authors.c.book_id == Book.id,
            Author.name.ilike(q),
        )
        search_cond = (Book.title.ilike(q)) | author_match.exists()
        base = base.where(search_cond)
        count_stmt = count_stmt.where(search_cond)
    if genre and genre.strip():
        base = base.join(Genre, Book.genre_id == Genre.id).where(
            Genre.name.ilike(f"%{genre.strip()}%")
        )
        count_stmt = count_stmt.join(Genre, Book.genre_id == Genre.id).where(
            Genre.name.ilike(f"%{genre.strip()}%")
        )
    if age_rating and age_rating.strip():
        base = base.join(AgeRating, Book.age_rating_id == AgeRating.id).where(
            AgeRating.code == age_rating.strip()
        )
        count_stmt = count_stmt.join(
            AgeRating, Book.age_rating_id == AgeRating.id
        ).where(AgeRating.code == age_rating.strip())
    if language and language.strip():
        base = base.join(Language, Book.language_id == Language.id).where(
            Language.name.ilike(f"%{language.strip()}%")
        )
        count_stmt = count_stmt.join(
            Language, Book.language_id == Language.id
        ).where(Language.name.ilike(f"%{language.strip()}%"))

    if available_only:
        # Подзапрос: книги, у которых есть хотя бы один свободный экземпляр
        # (статус "доступно" и не в активной брони — проверка по копиям в Python)
        available_subq = (
            select(BookCopy.book_id)
            .where(func.lower(BookCopy.status).like(AVAILABLE_STATUS_PATTERN))
            .distinct()
        )
        base = base.where(Book.id.in_(available_subq))
        count_stmt = count_stmt.where(Book.id.in_(available_subq))

    total_result = await db.execute(count_stmt)
    total = total_result.scalar() or 0
    base = base.order_by(Book.title).offset(offset).limit(size)
    result = await db.execute(base)
    books = list(result.scalars().all())

    reserved_ids = await _get_reserved_copy_ids(db)
    items: list[BookListEntry] = []
    for b in books:
        avail = _available_count(b.copies, reserved_ids)
        items.append(
            BookListEntry(
                id=b.id,
                author=format_authors_display(b.author_rels),
                title=b.title,
                cover_url=b.cover_url,
                genre=b.genre_rel.name if b.genre_rel else None,
                age_rating=b.age_rating_rel.code,
                language=b.language_rel.name,
                tags=[t.name for t in b.tag_rels] if b.tag_rels else None,
                available_count=avail,
                total_count=len(b.copies),
            )
        )

    pages = (total + size - 1) // size if total else 0
    return BookListResponse(
        items=items,
        total=total,
        page=page,
        size=size,
        pages=pages,
    )


async def _queue_count_for_book(db: AsyncSession, book_id: int) -> int:
    stmt = select(func.count(BookQueue.id)).where(BookQueue.book_id == book_id)
    result = await db.execute(stmt)
    return result.scalar() or 0


async def _user_has_book(
    db: AsyncSession, user_id: int, book_id: int
) -> bool:
    copy_ids_stmt = select(BookCopy.id).where(BookCopy.book_id == book_id)
    copy_result = await db.execute(copy_ids_stmt)
    copy_ids = list(copy_result.scalars().all())
    if not copy_ids:
        return False
    stmt = (
        select(Reservation.id)
        .join(Delivery, Reservation.delivery_id == Delivery.id)
        .where(
            Delivery.user_id == user_id,
            Reservation.book_copy_id.in_(copy_ids),
            Reservation.status.in_(ACTIVE_RESERVATION_STATUSES),
        )
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none() is not None


async def _user_queue_position(
    db: AsyncSession, book_id: int, user_id: int
) -> tuple[int | None, int]:
    stmt = (
        select(BookQueue.id, BookQueue.user_id)
        .where(BookQueue.book_id == book_id)
        .order_by(BookQueue.created_at.asc())
    )
    result = await db.execute(stmt)
    rows = list(result.all())
    total = len(rows)
    for position, (qid, uid) in enumerate(rows, start=1):
        if uid == user_id:
            return position, total
    return None, total


@router.get("/books/{book_id}", response_model=BookDetail)
async def get_book(
    book_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_optional_user)] = None,
) -> BookDetail:
    """Карточка книги: описание и доступность. При авторизации — данные очереди."""
    result = await db.execute(
        select(Book)
        .options(
            selectinload(Book.author_rels),
            selectinload(Book.genre_rel),
            selectinload(Book.age_rating_rel),
            selectinload(Book.language_rel),
            selectinload(Book.tag_rels),
            selectinload(Book.copies),
        )
        .where(Book.id == book_id)
    )
    book = result.scalar_one_or_none()
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Книга не найдена",
        )
    reserved_ids = await _get_reserved_copy_ids(db)
    avail = _available_count(book.copies, reserved_ids)
    earliest_return_date = None
    if avail == 0 and book.copies:
        copy_ids = [c.id for c in book.copies if c.id in reserved_ids]
        if copy_ids:
            stmt = (
                select(Delivery.delivery_date)
                .select_from(Reservation)
                .join(Delivery, Reservation.delivery_id == Delivery.id)
                .where(
                    Reservation.book_copy_id.in_(copy_ids),
                    Reservation.status.in_(ACTIVE_RESERVATION_STATUSES),
                )
            )
            result = await db.execute(stmt)
            delivery_dates = [row[0] for row in result.all()]
            if delivery_dates:
                earliest_return_date = min(
                    get_due_return_date(d) for d in delivery_dates
                )
    queue_count = await _queue_count_for_book(db, book_id)
    current_user_has_book = False
    queue_position: int | None = None
    queue_total = queue_count
    if current_user:
        current_user_has_book = await _user_has_book(
            db, current_user.id, book_id
        )
        pos, total = await _user_queue_position(db, book_id, current_user.id)
        queue_position = pos
        queue_total = total
    return BookDetail(
        id=book.id,
        author=format_authors_display(book.author_rels),
        title=book.title,
        description=book.description,
        cover_url=book.cover_url,
        genre=book.genre_rel.name if book.genre_rel else None,
        age_rating=book.age_rating_rel.code,
        language=book.language_rel.name,
        tags=[t.name for t in book.tag_rels] if book.tag_rels else None,
        available_count=avail,
        total_count=len(book.copies),
        earliest_return_date=earliest_return_date,
        queue_count=queue_count,
        current_user_has_book=current_user_has_book,
        queue_position=queue_position,
        queue_total=queue_total,
    )


@router.post("/import")
async def import_catalog(
    _admin: Annotated[object, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
    file: UploadFile | None = None,
) -> dict:
    """
    Импорт каталога из CSV. Только для администратора.
    Передать файл в multipart/form-data (ключ file).
    """
    content: str
    if file and file.filename:
        body = await file.read()
        try:
            content = body.decode("utf-8-sig")
        except UnicodeDecodeError:
            content = body.decode("cp1251", errors="replace")
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Загрузите CSV-файл",
        )
    books_count, copies_count = await import_from_csv_content(db, content)
    return {
        "books_created": books_count,
        "copies_created": copies_count,
        "message": f"Импортировано книг: {books_count}, экземпляров: {copies_count}",
    }
