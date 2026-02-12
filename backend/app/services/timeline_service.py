"""时间轴服务 — 提取病历生命周期事件"""

import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.medical_record import MedicalRecord
from app.models.record_version import RecordVersion
from app.models.clinical import ClinicalExamination, Diagnosis, Treatment
from app.models.lab_test import LabTest
from app.models.follow_up import FollowUp
from app.models.media import MediaFile


async def get_record_timeline(
    db: AsyncSession, record_id: uuid.UUID
) -> list[dict]:
    """
    提取病历的完整时间线事件，按时间排序。
    事件类型包括：创建、更新、版本、检查、诊断、治疗、检验、随访、上传。
    """
    events: list[dict] = []

    # 1. 版本历史事件
    versions_result = await db.execute(
        select(RecordVersion)
        .where(RecordVersion.record_id == record_id)
        .order_by(RecordVersion.created_at.asc())
    )
    for v in versions_result.scalars().all():
        event_type = "create" if v.version == "1.0" else "update"
        if v.source == "rollback":
            event_type = "rollback"
        events.append({
            "type": event_type,
            "time": _to_iso(v.created_at),
            "title": f"版本 {v.version}" if event_type != "create" else "创建病历",
            "description": v.changes or "",
            "source": v.source,
            "version": v.version,
        })

    # 2. 临床检查
    exams_result = await db.execute(
        select(ClinicalExamination)
        .where(ClinicalExamination.record_id == record_id)
        .order_by(ClinicalExamination.created_at.asc())
    )
    for exam in exams_result.scalars().all():
        events.append({
            "type": "examination",
            "time": _to_iso(exam.created_at),
            "title": f"临床检查: {exam.exam_type}" if hasattr(exam, 'exam_type') else "临床检查",
            "description": exam.findings if hasattr(exam, 'findings') else "",
        })

    # 3. 诊断
    diag_result = await db.execute(
        select(Diagnosis)
        .where(Diagnosis.record_id == record_id)
        .order_by(Diagnosis.created_at.asc())
    )
    for d in diag_result.scalars().all():
        events.append({
            "type": "diagnosis",
            "time": _to_iso(d.created_at),
            "title": f"诊断: {d.diagnosis_name}" if hasattr(d, 'diagnosis_name') else "诊断",
            "description": d.notes if hasattr(d, 'notes') else "",
        })

    # 4. 治疗
    treat_result = await db.execute(
        select(Treatment)
        .where(Treatment.record_id == record_id)
        .order_by(Treatment.created_at.asc())
    )
    for t in treat_result.scalars().all():
        events.append({
            "type": "treatment",
            "time": _to_iso(t.created_at),
            "title": f"治疗: {t.treatment_type}" if hasattr(t, 'treatment_type') else "治疗",
            "description": t.description if hasattr(t, 'description') else "",
        })

    # 5. 实验室检查
    lab_result = await db.execute(
        select(LabTest)
        .where(LabTest.record_id == record_id)
        .order_by(LabTest.created_at.asc())
    )
    for lt in lab_result.scalars().all():
        events.append({
            "type": "lab_test",
            "time": _to_iso(lt.created_at),
            "title": f"检验: {lt.test_name}" if hasattr(lt, 'test_name') else "实验室检查",
            "description": lt.result if hasattr(lt, 'result') else "",
        })

    # 6. 随访
    follow_result = await db.execute(
        select(FollowUp)
        .where(FollowUp.record_id == record_id)
        .order_by(FollowUp.created_at.asc())
    )
    for f in follow_result.scalars().all():
        events.append({
            "type": "follow_up",
            "time": _to_iso(f.created_at),
            "title": "随访记录",
            "description": f.notes if hasattr(f, 'notes') else "",
        })

    # 7. 媒体文件上传
    media_result = await db.execute(
        select(MediaFile)
        .where(MediaFile.record_id == record_id)
        .order_by(MediaFile.created_at.asc())
    )
    for m in media_result.scalars().all():
        events.append({
            "type": "media_upload",
            "time": _to_iso(m.created_at),
            "title": f"上传{m.file_type}文件",
            "description": m.description or "",
            "media_type": m.media_type,
        })

    # 按时间排序
    events.sort(key=lambda e: e["time"])
    return events


async def get_treatment_timeline(
    db: AsyncSession, record_id: uuid.UUID
) -> list[Treatment]:
    """获取治疗时间线，按 start_date 排序，包含关联 media_files（通过 selectin 加载）"""
    from sqlalchemy.orm import selectinload

    result = await db.execute(
        select(Treatment)
        .where(Treatment.record_id == record_id)
        .options(selectinload(Treatment.media_files))
        .order_by(
            Treatment.start_date.asc().nullslast(),
            Treatment.sort_order.asc().nullslast(),
            Treatment.created_at.asc(),
        )
    )
    return list(result.scalars().all())


def _to_iso(dt: datetime | None) -> str:
    if dt is None:
        return ""
    return dt.isoformat()
