"""books: author, genre, age_rating, language, tags as reference tables

Revision ID: 006
Revises: 005
Create Date: 2025-02-21

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "006"
down_revision: Union[str, Sequence[str], None] = "005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Справочники
    op.create_table(
        "authors",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(500), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_authors_name"), "authors", ["name"], unique=True)

    op.create_table(
        "genres",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_genres_name"), "genres", ["name"], unique=True)

    op.create_table(
        "age_ratings",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("code", sa.String(20), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_age_ratings_code"), "age_ratings", ["code"], unique=True
    )

    op.create_table(
        "languages",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(50), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_languages_name"), "languages", ["name"], unique=True
    )

    op.create_table(
        "tags",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_tags_name"), "tags", ["name"], unique=True)

    # 2. Связь книг и тегов
    op.create_table(
        "book_tags",
        sa.Column("book_id", sa.Integer(), nullable=False),
        sa.Column("tag_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["book_id"], ["books.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["tag_id"], ["tags.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("book_id", "tag_id"),
    )

    # 3. Новые колонки в books (пока nullable)
    op.add_column(
        "books",
        sa.Column("author_id", sa.Integer(), nullable=True),
    )
    op.add_column(
        "books",
        sa.Column("genre_id", sa.Integer(), nullable=True),
    )
    op.add_column(
        "books",
        sa.Column("age_rating_id", sa.Integer(), nullable=True),
    )
    op.add_column(
        "books",
        sa.Column("language_id", sa.Integer(), nullable=True),
    )

    # 4. Заполнить справочники возраст и язык по умолчанию
    op.execute(
        sa.text(
            "INSERT INTO age_ratings (code) VALUES ('0+'), ('6+'), ('12+'), ('16+'), ('18+')"
        )
    )
    op.execute(
        sa.text(
            "INSERT INTO languages (name) VALUES ('русский'), ('английский')"
        )
    )

    # 5. Перенос авторов
    op.execute(
        sa.text(
            "INSERT INTO authors (name) SELECT DISTINCT author FROM books WHERE author IS NOT NULL AND author != ''"
        )
    )
    # Книги с пустым автором — подставить "Не указан"
    op.execute(
        sa.text(
            "UPDATE books SET author = 'Не указан' WHERE author IS NULL OR author = ''"
        )
    )
    op.execute(
        sa.text(
            "INSERT INTO authors (name) SELECT 'Не указан' WHERE NOT EXISTS (SELECT 1 FROM authors WHERE name = 'Не указан')"
        )
    )
    op.execute(
        sa.text(
            "UPDATE books SET author_id = (SELECT id FROM authors WHERE authors.name = books.author)"
        )
    )

    # 6. Перенос жанров
    op.execute(
        sa.text(
            "INSERT INTO genres (name) SELECT DISTINCT genre FROM books WHERE genre IS NOT NULL AND genre != ''"
        )
    )
    op.execute(
        sa.text(
            "UPDATE books SET genre_id = (SELECT id FROM genres WHERE genres.name = books.genre) WHERE genre IS NOT NULL AND genre != ''"
        )
    )

    # 7. Перенос возрастного рейтинга
    op.execute(
        sa.text(
            "UPDATE books SET age_rating_id = (SELECT id FROM age_ratings WHERE age_ratings.code = books.age_rating)"
        )
    )
    # Если код не найден — ставим 0+
    op.execute(
        sa.text(
            "UPDATE books SET age_rating_id = (SELECT id FROM age_ratings WHERE code = '0+' LIMIT 1) WHERE age_rating_id IS NULL"
        )
    )

    # 8. Перенос языков (добавить недостающие)
    op.execute(
        sa.text(
            """
            INSERT INTO languages (name)
            SELECT DISTINCT language FROM books
            WHERE language IS NOT NULL AND language != ''
            ON CONFLICT (name) DO NOTHING
            """
        )
    )
    op.execute(
        sa.text(
            "UPDATE books SET language_id = (SELECT id FROM languages WHERE languages.name = books.language)"
        )
    )
    op.execute(
        sa.text(
            "UPDATE books SET language_id = (SELECT id FROM languages WHERE name = 'русский' LIMIT 1) WHERE language_id IS NULL"
        )
    )

    # 9. Перенос тегов (массив -> tags + book_tags)
    conn = op.get_bind()
    result = conn.execute(
        sa.text(
            "SELECT id, tags FROM books WHERE tags IS NOT NULL AND array_length(tags, 1) > 0"
        )
    )
    rows = result.fetchall()
    for book_id, tags_array in rows:
        if not tags_array:
            continue
        for tag_name in tags_array:
            if not tag_name or not str(tag_name).strip():
                continue
            name = str(tag_name).strip()
            conn.execute(
                sa.text(
                    "INSERT INTO tags (name) VALUES (:name) ON CONFLICT (name) DO NOTHING"
                ),
                {"name": name},
            )
            conn.execute(
                sa.text(
                    """
                    INSERT INTO book_tags (book_id, tag_id)
                    SELECT :book_id, id FROM tags WHERE name = :name
                    ON CONFLICT (book_id, tag_id) DO NOTHING
                    """
                ),
                {"book_id": book_id, "name": name},
            )

    # 10. NOT NULL для обязательных полей
    op.alter_column(
        "books",
        "author_id",
        existing_type=sa.Integer(),
        nullable=False,
    )
    op.alter_column(
        "books",
        "age_rating_id",
        existing_type=sa.Integer(),
        nullable=False,
    )
    op.alter_column(
        "books",
        "language_id",
        existing_type=sa.Integer(),
        nullable=False,
    )

    # 11. Внешние ключи
    op.create_foreign_key(
        "fk_books_author_id",
        "books",
        "authors",
        ["author_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_foreign_key(
        "fk_books_genre_id",
        "books",
        "genres",
        ["genre_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_books_age_rating_id",
        "books",
        "age_ratings",
        ["age_rating_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_foreign_key(
        "fk_books_language_id",
        "books",
        "languages",
        ["language_id"],
        ["id"],
        ondelete="RESTRICT",
    )

    # 12. Удалить старые колонки и индекс
    op.drop_index("ix_books_author_title", table_name="books")
    op.drop_column("books", "author")
    op.drop_column("books", "genre")
    op.drop_column("books", "age_rating")
    op.drop_column("books", "language")
    op.drop_column("books", "tags")

    # 13. Уникальность (author_id, title)
    op.create_index(
        "ix_books_author_id_title",
        "books",
        ["author_id", "title"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ix_books_author_id_title", table_name="books")

    op.add_column(
        "books",
        sa.Column("author", sa.String(500), nullable=True),
    )
    op.add_column(
        "books",
        sa.Column("genre", sa.String(200), nullable=True),
    )
    op.add_column(
        "books",
        sa.Column("age_rating", sa.String(20), nullable=True),
    )
    op.add_column(
        "books",
        sa.Column("language", sa.String(50), nullable=True),
    )
    op.add_column(
        "books",
        sa.Column("tags", postgresql.ARRAY(sa.Text()), nullable=True),
    )

    op.execute(
        sa.text(
            "UPDATE books SET author = (SELECT name FROM authors WHERE authors.id = books.author_id)"
        )
    )
    op.execute(
        sa.text(
            "UPDATE books SET genre = (SELECT name FROM genres WHERE genres.id = books.genre_id) WHERE genre_id IS NOT NULL"
        )
    )
    op.execute(
        sa.text(
            "UPDATE books SET age_rating = (SELECT code FROM age_ratings WHERE age_ratings.id = books.age_rating_id)"
        )
    )
    op.execute(
        sa.text(
            "UPDATE books SET language = (SELECT name FROM languages WHERE languages.id = books.language_id)"
        )
    )
    # Восстановление tags из book_tags в массив — подзапрос
    conn = op.get_bind()
    result = conn.execute(sa.text("SELECT id FROM books"))
    for (book_id,) in result:
        tag_names = conn.execute(
            sa.text(
                "SELECT t.name FROM book_tags bt JOIN tags t ON t.id = bt.tag_id WHERE bt.book_id = :bid"
            ),
            {"bid": book_id},
        ).fetchall()
        arr = [r[0] for r in tag_names] if tag_names else None
        conn.execute(
            sa.text("UPDATE books SET tags = :arr WHERE id = :bid"),
            {"arr": arr, "bid": book_id},
        )

    op.alter_column(
        "books",
        "author",
        existing_type=sa.String(500),
        nullable=False,
    )
    op.alter_column(
        "books",
        "age_rating",
        existing_type=sa.String(20),
        nullable=False,
        server_default="0+",
    )
    op.alter_column(
        "books",
        "language",
        existing_type=sa.String(50),
        nullable=False,
        server_default="русский",
    )

    op.drop_constraint("fk_books_language_id", "books", type_="foreignkey")
    op.drop_constraint("fk_books_age_rating_id", "books", type_="foreignkey")
    op.drop_constraint("fk_books_genre_id", "books", type_="foreignkey")
    op.drop_constraint("fk_books_author_id", "books", type_="foreignkey")
    op.drop_column("books", "author_id")
    op.drop_column("books", "genre_id")
    op.drop_column("books", "age_rating_id")
    op.drop_column("books", "language_id")

    op.create_index(
        "ix_books_author_title",
        "books",
        ["author", "title"],
        unique=True,
    )

    op.drop_table("book_tags")
    op.drop_index(op.f("ix_tags_name"), table_name="tags")
    op.drop_table("tags")
    op.drop_index(op.f("ix_languages_name"), table_name="languages")
    op.drop_table("languages")
    op.drop_index(op.f("ix_age_ratings_code"), table_name="age_ratings")
    op.drop_table("age_ratings")
    op.drop_index(op.f("ix_genres_name"), table_name="genres")
    op.drop_table("genres")
    op.drop_index(op.f("ix_authors_name"), table_name="authors")
    op.drop_table("authors")