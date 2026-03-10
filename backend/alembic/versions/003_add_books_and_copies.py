"""add books and book_copies tables

Revision ID: 003
Revises: 002
Create Date: 2025-02-19

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "003"
down_revision: Union[str, Sequence[str], None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "books",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("author", sa.String(500), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("cover_url", sa.String(1000), nullable=True),
        sa.Column("genre", sa.String(200), nullable=True),
        sa.Column("age_rating", sa.String(20), nullable=False, server_default="0+"),
        sa.Column("language", sa.String(50), nullable=False, server_default="русский"),
        sa.Column("tags", postgresql.ARRAY(sa.Text()), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_books_author_title",
        "books",
        ["author", "title"],
        unique=True,
    )
    op.create_table(
        "book_copies",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("book_id", sa.Integer(), nullable=False),
        sa.Column("unique_number", sa.String(100), nullable=False),
        sa.Column("status", sa.String(200), nullable=False),
        sa.Column("cover_url", sa.String(1000), nullable=True),
        sa.ForeignKeyConstraint(["book_id"], ["books.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_book_copies_unique_number"),
        "book_copies",
        ["unique_number"],
        unique=True,
    )
    op.create_index("ix_book_copies_book_id", "book_copies", ["book_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_book_copies_book_id", table_name="book_copies")
    op.drop_index(op.f("ix_book_copies_unique_number"), table_name="book_copies")
    op.drop_table("book_copies")
    op.drop_index("ix_books_author_title", table_name="books")
    op.drop_table("books")
