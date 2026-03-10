"""books: many-to-many с авторами (book_authors), удаление author_id

Revision ID: 008
Revises: 007
Create Date: 2025-02-21

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "008"
down_revision: Union[str, Sequence[str], None] = "007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "book_authors",
        sa.Column("book_id", sa.Integer(), nullable=False),
        sa.Column("author_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["book_id"], ["books.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["author_id"], ["authors.id"], ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("book_id", "author_id"),
    )
    op.execute(
        """
        INSERT INTO book_authors (book_id, author_id)
        SELECT id, author_id FROM books WHERE author_id IS NOT NULL
        """
    )
    op.drop_index("ix_books_author_id_title", table_name="books")
    op.drop_constraint("fk_books_author_id", "books", type_="foreignkey")
    op.drop_column("books", "author_id")


def downgrade() -> None:
    op.add_column(
        "books",
        sa.Column("author_id", sa.Integer(), nullable=True),
    )
    op.execute(
        """
        UPDATE books SET author_id = (
            SELECT author_id FROM book_authors
            WHERE book_authors.book_id = books.id
            LIMIT 1
        )
        """
    )
    op.create_foreign_key(
        "fk_books_author_id",
        "books",
        "authors",
        ["author_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_index(
        "ix_books_author_id_title",
        "books",
        ["author_id", "title"],
        unique=True,
    )
    op.drop_table("book_authors")
