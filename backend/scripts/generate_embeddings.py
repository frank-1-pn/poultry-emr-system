"""
批量生成病历 Embedding 脚本

用法:
    cd backend
    python -m scripts.generate_embeddings [--batch-size 20] [--limit 500]

需要先配置好 .env 中的 EMBEDDING_PROVIDER / EMBEDDING_API_KEY / EMBEDDING_MODEL
以及 DATABASE_URL。
"""

import argparse
import asyncio
import sys
from pathlib import Path

# 将 backend 加入 path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.config import get_settings  # noqa: E402
from app.core.database import AsyncSessionLocal  # noqa: E402
from app.services.embedding_service import batch_generate_embeddings  # noqa: E402


async def main(batch_size: int, limit: int):
    settings = get_settings()
    print(f"Embedding 提供商: {settings.EMBEDDING_PROVIDER}")
    print(f"Embedding 模型: {settings.EMBEDDING_MODEL}")
    print(f"批大小: {batch_size}, 上限: {limit}")
    print("-" * 40)

    async with AsyncSessionLocal() as db:
        result = await batch_generate_embeddings(
            db, batch_size=batch_size, limit=limit,
        )
        await db.commit()

    print(f"\n完成！")
    print(f"  处理: {result['processed']} 条")
    print(f"  成功: {result['success']} 条")
    print(f"  失败: {result['failed']} 条")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="批量生成病历 Embedding")
    parser.add_argument("--batch-size", type=int, default=20, help="每批处理数")
    parser.add_argument("--limit", type=int, default=500, help="最大处理数")
    args = parser.parse_args()

    asyncio.run(main(args.batch_size, args.limit))
