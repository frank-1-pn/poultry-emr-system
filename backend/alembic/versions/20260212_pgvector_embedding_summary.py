"""add pgvector embedding_vector to medical_records and summary to conversations

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-02-12

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "e5f6a7b8c9d0"
down_revision: Union[str, None] = "d4e5f6a7b8c9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 启用 pgvector 扩展
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # 添加 embedding_vector 列（1536 维）
    op.execute(
        "ALTER TABLE medical_records ADD COLUMN IF NOT EXISTS "
        "embedding_vector vector(1536)"
    )

    # 创建 IVFFlat 索引以加速近邻查询（需要数据后才有效，先用 HNSW）
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_records_embedding "
        "ON medical_records USING hnsw (embedding_vector vector_cosine_ops)"
    )

    # 添加 summary 列到 conversations
    op.add_column(
        "conversations",
        sa.Column("summary", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("conversations", "summary")
    op.execute("DROP INDEX IF EXISTS idx_records_embedding")
    op.execute("ALTER TABLE medical_records DROP COLUMN IF EXISTS embedding_vector")
