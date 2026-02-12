"""add farm_id and tags to conversations

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-02-12

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "d4e5f6a7b8c9"
down_revision: Union[str, None] = "c3d4e5f6a7b8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "conversations",
        sa.Column("farm_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "conversations",
        sa.Column("tags", postgresql.JSONB(), server_default="[]", nullable=False),
    )
    op.create_foreign_key(
        "fk_conversations_farm_id",
        "conversations",
        "farms",
        ["farm_id"],
        ["id"],
    )
    op.create_index("idx_conversations_farm", "conversations", ["farm_id"])


def downgrade() -> None:
    op.drop_index("idx_conversations_farm", table_name="conversations")
    op.drop_constraint("fk_conversations_farm_id", "conversations", type_="foreignkey")
    op.drop_column("conversations", "tags")
    op.drop_column("conversations", "farm_id")
