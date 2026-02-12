"""Embedding 服务 — 生成 / 查询 / 批量处理 医疗记录向量"""

import logging
import uuid

from sqlalchemy import select, text, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.adapters.embedding_factory import EmbeddingAdapterFactory
from app.models.medical_record import MedicalRecord

logger = logging.getLogger(__name__)


def build_embedding_text(record: MedicalRecord) -> str:
    """将病历记录构建为适合 embedding 的纯文本"""
    parts: list[str] = []

    # 基本信息
    parts.append(f"禽类: {record.poultry_type}")
    if record.breed:
        parts.append(f"品种: {record.breed}")
    if record.age_days:
        parts.append(f"日龄: {record.age_days}天")
    if record.primary_diagnosis:
        parts.append(f"诊断: {record.primary_diagnosis}")
    if record.severity:
        parts.append(f"严重程度: {record.severity}")

    # 从 record_json 提取更多信息
    rj = record.record_json or {}

    symptoms = rj.get("symptoms")
    if symptoms:
        if isinstance(symptoms, list):
            parts.append(f"症状: {', '.join(str(s) for s in symptoms)}")
        else:
            parts.append(f"症状: {symptoms}")

    treatment = rj.get("treatment")
    if treatment:
        if isinstance(treatment, dict):
            items = []
            if treatment.get("drug"):
                items.append(treatment["drug"])
            if treatment.get("method"):
                items.append(treatment["method"])
            if treatment.get("dosage"):
                items.append(treatment["dosage"])
            parts.append(f"治疗: {' '.join(items)}")
        else:
            parts.append(f"治疗: {treatment}")

    for key in ("environment", "vaccination_history", "mortality", "notes"):
        val = rj.get(key)
        if val:
            parts.append(f"{key}: {val}")

    # markdown 摘要（截取前 500 字）
    if record.record_markdown:
        parts.append(record.record_markdown[:500])

    return "\n".join(parts)


def build_embedding_text_from_info(collected_info: dict) -> str:
    """将对话中的 collected_info 构建为 embedding 文本（用于相似病例检索）"""
    parts: list[str] = []

    if collected_info.get("poultry_type"):
        parts.append(f"禽类: {collected_info['poultry_type']}")
    if collected_info.get("breed"):
        parts.append(f"品种: {collected_info['breed']}")
    if collected_info.get("age_days"):
        parts.append(f"日龄: {collected_info['age_days']}天")
    if collected_info.get("primary_diagnosis"):
        parts.append(f"诊断: {collected_info['primary_diagnosis']}")
    if collected_info.get("severity"):
        parts.append(f"严重程度: {collected_info['severity']}")

    symptoms = collected_info.get("symptoms")
    if symptoms:
        if isinstance(symptoms, list):
            parts.append(f"症状: {', '.join(str(s) for s in symptoms)}")
        else:
            parts.append(f"症状: {symptoms}")

    treatment = collected_info.get("treatment")
    if treatment:
        if isinstance(treatment, dict):
            items = [v for v in treatment.values() if v]
            parts.append(f"治疗: {' '.join(str(i) for i in items)}")
        else:
            parts.append(f"治疗: {treatment}")

    return "\n".join(parts)


def _get_adapter() -> BaseEmbeddingAdapter:
    """获取默认 embedding 适配器"""
    return EmbeddingAdapterFactory.get_default_adapter()


async def generate_record_embedding(
    db: AsyncSession, record_id: uuid.UUID
) -> bool:
    """为单条病历生成 embedding 并存储"""
    result = await db.execute(
        select(MedicalRecord).where(MedicalRecord.id == record_id)
    )
    record = result.scalar_one_or_none()
    if not record:
        return False

    embedding_text = build_embedding_text(record)
    if not embedding_text.strip():
        logger.warning("病历 %s 无可用文本，跳过 embedding 生成", record_id)
        record.embedding_status = "skipped"
        await db.flush()
        return False

    try:
        adapter = _get_adapter()
        vector = await adapter.embed_text(embedding_text)

        # 使用原生 SQL 更新 vector 列（pgvector 类型需要特殊处理）
        vector_str = "[" + ",".join(str(v) for v in vector) + "]"
        await db.execute(
            text(
                "UPDATE medical_records SET embedding_vector = :vec, "
                "embedding_status = 'completed' WHERE id = :rid"
            ),
            {"vec": vector_str, "rid": str(record_id)},
        )
        await db.flush()
        logger.info("病历 %s embedding 生成成功", record_id)
        return True
    except Exception as e:
        logger.error("病历 %s embedding 生成失败: %s", record_id, e)
        record.embedding_status = "failed"
        await db.flush()
        return False


async def batch_generate_embeddings(
    db: AsyncSession,
    batch_size: int = 20,
    limit: int = 100,
) -> dict:
    """批量为 pending 状态的病历生成 embedding"""
    result = await db.execute(
        select(MedicalRecord)
        .where(MedicalRecord.embedding_status.in_(["pending", "failed"]))
        .order_by(MedicalRecord.created_at.desc())
        .limit(limit)
    )
    records = list(result.scalars().all())

    if not records:
        return {"processed": 0, "success": 0, "failed": 0}

    adapter = _get_adapter()
    success = 0
    failed = 0

    # 分批处理
    for i in range(0, len(records), batch_size):
        batch = records[i : i + batch_size]
        texts = [build_embedding_text(r) for r in batch]

        # 过滤空文本
        valid_pairs = [(r, t) for r, t in zip(batch, texts) if t.strip()]
        if not valid_pairs:
            continue

        valid_records, valid_texts = zip(*valid_pairs)

        try:
            response = await adapter.embed_texts(list(valid_texts))

            for record, vector in zip(valid_records, response.embeddings):
                vector_str = "[" + ",".join(str(v) for v in vector) + "]"
                await db.execute(
                    text(
                        "UPDATE medical_records SET embedding_vector = :vec, "
                        "embedding_status = 'completed' WHERE id = :rid"
                    ),
                    {"vec": vector_str, "rid": str(record.id)},
                )
                success += 1

        except Exception as e:
            logger.error("批量 embedding 失败: %s", e)
            for r in valid_records:
                await db.execute(
                    update(MedicalRecord)
                    .where(MedicalRecord.id == r.id)
                    .values(embedding_status="failed")
                )
            failed += len(valid_records)

    await db.flush()
    return {"processed": len(records), "success": success, "failed": failed}


async def search_similar_records(
    db: AsyncSession,
    query_text: str,
    user_id: uuid.UUID | None = None,
    is_master: bool = False,
    top_k: int = 5,
    threshold: float = 0.3,
    exclude_record_id: uuid.UUID | None = None,
) -> list[dict]:
    """
    语义搜索：找到与 query_text 最相似的病历记录。
    返回 [{record, similarity}, ...]
    """
    adapter = _get_adapter()
    query_vector = await adapter.embed_text(query_text)
    vector_str = "[" + ",".join(str(v) for v in query_vector) + "]"

    # 构建权限条件
    permission_clause = ""
    params: dict = {
        "vec": vector_str,
        "threshold": threshold,
        "top_k": top_k,
    }

    if not is_master and user_id:
        permission_clause = (
            "AND (mr.owner_id = :user_id OR mr.id IN ("
            "  SELECT record_id FROM record_permissions "
            "  WHERE user_id = :user_id AND revoked = false"
            "))"
        )
        params["user_id"] = str(user_id)

    exclude_clause = ""
    if exclude_record_id:
        exclude_clause = "AND mr.id != :exclude_id"
        params["exclude_id"] = str(exclude_record_id)

    sql = text(f"""
        SELECT mr.id, mr.record_no, mr.poultry_type, mr.breed,
               mr.primary_diagnosis, mr.severity, mr.visit_date,
               mr.record_json,
               1 - (mr.embedding_vector <=> :vec::vector) AS similarity
        FROM medical_records mr
        WHERE mr.embedding_vector IS NOT NULL
          AND mr.status != 'deleted'
          AND 1 - (mr.embedding_vector <=> :vec::vector) > :threshold
          {permission_clause}
          {exclude_clause}
        ORDER BY mr.embedding_vector <=> :vec::vector
        LIMIT :top_k
    """)

    result = await db.execute(sql, params)
    rows = result.fetchall()

    return [
        {
            "id": str(row.id),
            "record_no": row.record_no,
            "poultry_type": row.poultry_type,
            "breed": row.breed,
            "primary_diagnosis": row.primary_diagnosis,
            "severity": row.severity,
            "visit_date": str(row.visit_date) if row.visit_date else None,
            "record_json": row.record_json,
            "similarity": round(float(row.similarity), 4),
        }
        for row in rows
    ]


async def search_similar_by_collected_info(
    db: AsyncSession,
    collected_info: dict,
    user_id: uuid.UUID | None = None,
    is_master: bool = False,
    top_k: int = 3,
    exclude_record_id: uuid.UUID | None = None,
) -> list[dict]:
    """基于对话中收集的信息搜索相似病例"""
    query_text = build_embedding_text_from_info(collected_info)
    if not query_text.strip():
        return []
    return await search_similar_records(
        db, query_text, user_id, is_master, top_k,
        threshold=0.25, exclude_record_id=exclude_record_id,
    )
