"""Схемы для каталога книг."""

from datetime import date

from pydantic import BaseModel, Field


class RefItem(BaseModel):
    """Элемент справочника: id и отображаемое имя/код."""

    id: int
    name: str


class TagCreate(BaseModel):
    """Создание тега по имени (get-or-create)."""

    name: str = Field(..., min_length=1, max_length=200)


class BookCreate(BaseModel):
    """Создание книги (связи по id)."""

    author_ids: list[int] = Field(..., min_length=1, max_length=20)
    title: str = Field(..., min_length=1, max_length=500)
    description: str | None = Field(None, max_length=10000)
    cover_url: str | None = Field(None, max_length=1000)
    genre_id: int | None = Field(None, gt=0)
    age_rating_id: int = Field(..., gt=0)
    language_id: int = Field(..., gt=0)
    tag_ids: list[int] | None = Field(None, max_length=50)


class BookUpdate(BaseModel):
    """Обновление книги (связи по id)."""

    author_ids: list[int] | None = Field(None, min_length=1, max_length=20)
    title: str | None = Field(None, min_length=1, max_length=500)
    description: str | None = Field(None, max_length=10000)
    cover_url: str | None = Field(None, max_length=1000)
    genre_id: int | None = None
    age_rating_id: int | None = Field(None, gt=0)
    language_id: int | None = Field(None, gt=0)
    tag_ids: list[int] | None = Field(None, max_length=50)


class BookCopyCreate(BaseModel):
    """Создание экземпляра."""

    unique_number: str = Field(..., min_length=1, max_length=100)
    status: str = Field(..., min_length=1, max_length=200)
    cover_url: str | None = Field(None, max_length=1000)


class BookCopyUpdate(BaseModel):
    """Обновление экземпляра (статус и т.д.)."""

    unique_number: str | None = Field(None, min_length=1, max_length=100)
    status: str | None = Field(None, min_length=1, max_length=200)
    cover_url: str | None = Field(None, max_length=1000)


class BookCopyDetail(BaseModel):
    """Экземпляр для админки."""

    id: int
    book_id: int
    unique_number: str
    status: str
    cover_url: str | None

    model_config = {"from_attributes": True}


class BookListEntry(BaseModel):
    """Элемент списка книг (карточка)."""

    id: int
    author: str
    title: str
    cover_url: str | None
    genre: str | None
    age_rating: str
    language: str
    tags: list[str] | None
    available_count: int
    total_count: int


class BookDetail(BaseModel):
    """Карточка книги: полное описание и доступность."""

    id: int
    author: str
    title: str
    description: str | None
    cover_url: str | None
    genre: str | None
    age_rating: str
    language: str
    tags: list[str] | None
    available_count: int
    total_count: int
    earliest_return_date: date | None = None
    queue_count: int = 0
    current_user_has_book: bool = False
    queue_position: int | None = None
    queue_total: int = 0


class BookDetailWithCopies(BaseModel):
    """Карточка книги для админки с экземплярами (строки для отображения + id для формы)."""

    id: int
    author: str
    title: str
    description: str | None
    cover_url: str | None
    genre: str | None
    age_rating: str
    language: str
    tags: list[str] | None
    author_ids: list[int]
    genre_id: int | None
    age_rating_id: int
    language_id: int
    tag_ids: list[int]
    copies: list[BookCopyDetail]


class BookListResponse(BaseModel):
    """Список книг с пагинацией."""

    items: list[BookListEntry]
    total: int
    page: int
    size: int
    pages: int
