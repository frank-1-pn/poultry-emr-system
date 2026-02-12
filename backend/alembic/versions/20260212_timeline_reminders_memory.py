"""add timeline, reminders, memory tables

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-02-12

"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c3d4e5f6a7b8"
down_revision: Union[str, None] = "b2c3d4e5f6a7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. ALTER treatments: 增加 start_date, end_date, sort_order
    op.add_column("treatments", sa.Column("start_date", sa.Date(), nullable=True))
    op.add_column("treatments", sa.Column("end_date", sa.Date(), nullable=True))
    op.add_column("treatments", sa.Column("sort_order", sa.Integer(), nullable=True, server_default="0"))

    # 2. ALTER media_files: 增加 treatment_id FK
    op.add_column(
        "media_files",
        sa.Column("treatment_id", sa.Uuid(), nullable=True),
    )
    op.create_foreign_key(
        "fk_media_files_treatment_id",
        "media_files",
        "treatments",
        ["treatment_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("idx_media_treatment", "media_files", ["treatment_id"])

    # 3. ALTER conversations: 增加 session_number
    op.add_column(
        "conversations",
        sa.Column("session_number", sa.Integer(), nullable=True, server_default="1"),
    )

    # 4. CREATE reminders 表
    op.create_table(
        "reminders",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("record_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("reminder_date", sa.Date(), nullable=False),
        sa.Column("content", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column(
            "status",
            sa.String(20),
            nullable=False,
            server_default="pending",
        ),  # pending | confirmed | dismissed
        sa.Column("ai_generated", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["record_id"], ["medical_records.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("idx_reminders_user_date", "reminders", ["user_id", "reminder_date"])
    op.create_index("idx_reminders_record", "reminders", ["record_id"])
    op.create_index("idx_reminders_status", "reminders", ["status"])

    # 5. CREATE user_memories 表
    op.create_table(
        "user_memories",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("content", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("user_id", name="uq_user_memories_user_id"),
    )

    # 6. 数据回填: treatments.start_date = created_at::date
    op.execute("UPDATE treatments SET start_date = created_at::date WHERE start_date IS NULL")


def downgrade() -> None:
    op.drop_table("user_memories")
    op.drop_table("reminders")
    op.drop_column("conversations", "session_number")
    op.drop_index("idx_media_treatment", table_name="media_files")
    op.drop_constraint("fk_media_files_treatment_id", "media_files", type_="foreignkey")
    op.drop_column("media_files", "treatment_id")
    op.drop_column("treatments", "sort_order")
    op.drop_column("treatments", "end_date")
    op.drop_column("treatments", "start_date")
