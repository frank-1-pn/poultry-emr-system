"""add search_config table

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-02-11

"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b2c3d4e5f6a7"
down_revision: Union[str, None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "search_configs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("config_key", sa.String(100), nullable=False),
        sa.Column("config_value", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("updated_by", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("config_key"),
        sa.ForeignKeyConstraint(["updated_by"], ["users.id"]),
    )
    op.create_index("idx_search_config_key", "search_configs", ["config_key"])

    # 插入默认配置
    op.execute("""
        INSERT INTO search_configs (id, config_key, config_value, description)
        VALUES
        (gen_random_uuid(), 'search_weights',
         '{"primary_diagnosis": 3.0, "symptoms": 2.0, "poultry_type": 1.5, "breed": 1.0, "treatment": 1.0, "notes": 0.5}',
         '全文搜索字段权重配置'),
        (gen_random_uuid(), 'search_options',
         '{"max_results": 50, "min_score": 0.1, "enable_fuzzy": true, "fuzzy_distance": 2, "highlight_enabled": true}',
         '搜索行为选项'),
        (gen_random_uuid(), 'embedding_config',
         '{"model": "text-embedding-ada-002", "dimension": 1536, "batch_size": 100, "auto_embed": true}',
         '向量嵌入配置')
    """)


def downgrade() -> None:
    op.drop_table("search_configs")
