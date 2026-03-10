"""Модели книги и экземпляра (каталог)."""

from sqlalchemy import Column, ForeignKey, Integer, String, Table, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

# Связь книг и тегов (many-to-many)
book_tags = Table(
    "book_tags",
    Base.metadata,
    Column("book_id", Integer, ForeignKey("books.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
)

# Связь книг и авторов (many-to-many)
book_authors = Table(
    "book_authors",
    Base.metadata,
    Column("book_id", Integer, ForeignKey("books.id", ondelete="CASCADE"), primary_key=True),
    Column("author_id", Integer, ForeignKey("authors.id", ondelete="RESTRICT"), primary_key=True),
)


class Book(Base):
    """Книга: связь с авторами (M2M), жанром, возрастом, языком и тегами."""

    __tablename__ = "books"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    cover_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    genre_id: Mapped[int | None] = mapped_column(
        ForeignKey("genres.id", ondelete="SET NULL"),
        nullable=True,
    )
    age_rating_id: Mapped[int] = mapped_column(
        ForeignKey("age_ratings.id", ondelete="RESTRICT"),
        nullable=False,
    )
    language_id: Mapped[int] = mapped_column(
        ForeignKey("languages.id", ondelete="RESTRICT"),
        nullable=False,
    )

    author_rels: Mapped[list["Author"]] = relationship(
        "Author",
        secondary=book_authors,
        back_populates="books",
        lazy="selectin",
        order_by="Author.name",
    )
    genre_rel: Mapped["Genre | None"] = relationship("Genre", back_populates="books")
    age_rating_rel: Mapped["AgeRating"] = relationship(
        "AgeRating", back_populates="books"
    )
    language_rel: Mapped["Language"] = relationship(
        "Language", back_populates="books"
    )
    tag_rels: Mapped[list["Tag"]] = relationship(
        "Tag",
        secondary=book_tags,
        back_populates="books",
        lazy="selectin",
    )

    copies: Mapped[list["BookCopy"]] = relationship(
        "BookCopy",
        back_populates="book",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"Book(id={self.id}, title={self.title!r})"


class BookCopy(Base):
    """Экземпляр книги: связь с книгой, уникальный номер из CSV, статус."""

    __tablename__ = "book_copies"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    book_id: Mapped[int] = mapped_column(
        ForeignKey("books.id", ondelete="CASCADE"), nullable=False
    )
    unique_number: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    status: Mapped[str] = mapped_column(String(200), nullable=False)
    cover_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    book: Mapped["Book"] = relationship("Book", back_populates="copies")

    def __repr__(self) -> str:
        return f"BookCopy(id={self.id}, unique_number={self.unique_number!r})"
