"""add conversation tables

Revision ID: a1b2c3d4e5f6
Revises:
Create Date: 2026-02-11

"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # conversations 表
    op.create_table(
        "conversations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("record_id", sa.Uuid(), nullable=True),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("state", sa.String(30), nullable=False, server_default="initializing"),
        sa.Column("collected_info", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("confidence_scores", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["record_id"], ["medical_records.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
    )
    op.create_index("idx_conversations_user", "conversations", ["user_id"])
    op.create_index("idx_conversations_record", "conversations", ["record_id"])
    op.create_index("idx_conversations_status", "conversations", ["status"])
    op.create_index("idx_conversations_created", "conversations", ["created_at"])

    # conversation_messages 表
    op.create_table(
        "conversation_messages",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("conversation_id", sa.Uuid(), nullable=False),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("audio_url", sa.Text(), nullable=True),
        sa.Column("extracted_info", postgresql.JSONB(), nullable=True),
        sa.Column("confidence_scores", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["conversation_id"], ["conversations.id"], ondelete="CASCADE"),
    )
    op.create_index("idx_conv_messages_conversation", "conversation_messages", ["conversation_id"])
    op.create_index("idx_conv_messages_created", "conversation_messages", ["created_at"])


def downgrade() -> None:
    op.drop_table("conversation_messages")
    op.drop_table("conversations")
