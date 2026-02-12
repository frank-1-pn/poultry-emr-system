import json
import logging
import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import and_, or_, select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.medical_record import MedicalRecord
from app.models.record_permission import RecordPermission
from app.models.record_version import RecordVersion
from app.models.user import User
from app.schemas.record import RecordCreate, RecordUpdate
from app.services.audit_service import log_action

logger = logging.getLogger(__name__)


def _generate_record_no() -> str:
    now = datetime.now(timezone.utc)
    unique = uuid.uuid4().hex[:6].upper()
    return f"EMR-{now.strftime('%Y%m%d')}-{unique}"


def _sync_indexed_fields(record: MedicalRecord, record_json: dict) -> None:
    """Extract key fields from JSONB to indexed columns."""
    if "primary_diagnosis" in record_json:
        record.primary_diagnosis = record_json["primary_diagnosis"]
    if "icd_code" in record_json:
        record.icd_code = record_json["icd_code"]
    if "confidence" in record_json:
        record.confidence = record_json["confidence"]
    if "severity" in record_json:
        record.severity = record_json["severity"]
    if "is_reportable" in record_json:
        record.is_reportable = record_json["is_reportable"]
    if "poultry_type" in record_json:
        record.poultry_type = record_json["poultry_type"]
    if "breed" in record_json:
        record.breed = record_json["breed"]
    if "age_days" in record_json:
        record.age_days = record_json["age_days"]
    if "affected_count" in record_json:
        record.affected_count = record_json["affected_count"]
    if "total_flock" in record_json:
        record.total_flock = record_json["total_flock"]


def _generate_markdown(record_json: dict) -> str:
    """Convert JSONB to readable markdown."""
    lines = ["# 病历记录\n"]

    if "basic_info" in record_json:
        info = record_json["basic_info"]
        lines.append("## 基本信息")
        for k, v in info.items():
            lines.append(f"- **{k}**: {v}")
        lines.append("")

    if "primary_diagnosis" in record_json:
        lines.append(f"## 诊断\n- **主要诊断**: {record_json['primary_diagnosis']}")
        if "severity" in record_json:
            lines.append(f"- **严重程度**: {record_json['severity']}")
        lines.append("")

    if "symptoms" in record_json:
        lines.append("## 症状")
        symptoms = record_json["symptoms"]
        if isinstance(symptoms, list):
            for s in symptoms:
                lines.append(f"- {s}")
        elif isinstance(symptoms, dict):
            for k, v in symptoms.items():
                lines.append(f"- **{k}**: {v}")
        lines.append("")

    if "treatment" in record_json:
        lines.append("## 治疗方案")
        treatment = record_json["treatment"]
        if isinstance(treatment, dict):
            for k, v in treatment.items():
                lines.append(f"- **{k}**: {v}")
        elif isinstance(treatment, list):
            for t in treatment:
                lines.append(f"- {t}")
        lines.append("")

    if "notes" in record_json:
        lines.append(f"## 备注\n{record_json['notes']}\n")

    return "\n".join(lines)


async def create_record(
    db: AsyncSession, user: User, data: RecordCreate
) -> MedicalRecord:
    record = MedicalRecord(
        record_no=_generate_record_no(),
        owner_id=user.id,
        veterinarian_id=user.id,
        farm_id=data.farm_id,
        visit_date=data.visit_date,
        poultry_type=data.poultry_type,
        breed=data.breed,
        age_days=data.age_days,
        affected_count=data.affected_count,
        total_flock=data.total_flock,
        onset_date=data.onset_date,
        record_json=data.record_json,
    )

    _sync_indexed_fields(record, data.record_json)
    record.record_markdown = _generate_markdown(data.record_json)

    db.add(record)
    await db.flush()

    # Create version 1.0
    version = RecordVersion(
        record_id=record.id,
        version="1.0",
        created_by=user.id,
        source="manual_edit",
        changes="初始创建",
        snapshot=data.record_json,
    )
    db.add(version)
    await db.flush()

    # 异步触发 embedding 生成（失败不阻塞）
    try:
        from app.services.embedding_service import generate_record_embedding
        await generate_record_embedding(db, record.id)
    except Exception as e:
        logger.warning("自动 embedding 生成失败 (record=%s): %s", record.id, e)

    return record


async def update_record(
    db: AsyncSession,
    record_id: uuid.UUID,
    data: RecordUpdate,
    user: User,
) -> MedicalRecord:
    result = await db.execute(
        select(MedicalRecord).where(MedicalRecord.id == record_id)
    )
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="病历不存在")

    update_data = data.model_dump(exclude_unset=True)

    # Update record_json and sync fields
    new_record_json = None
    if "record_json" in update_data and update_data["record_json"]:
        new_record_json = update_data.pop("record_json")
        record.record_json = new_record_json
        _sync_indexed_fields(record, record.record_json)
        record.record_markdown = _generate_markdown(record.record_json)

    # Update remaining explicit fields
    for field, value in update_data.items():
        if hasattr(record, field):
            setattr(record, field, value)

    # Bump version
    current = record.current_version or "1.0"
    major, minor = current.split(".")
    new_version = f"{major}.{int(minor) + 1}"
    record.current_version = new_version
    record.version = new_version

    # Create version record
    version_num = int(minor) + 1
    snapshot = record.record_json if (version_num % 10 == 0) else None
    # 构建 diff：包含 record_json 变更和其他字段变更
    diff_data = dict(update_data)
    if new_record_json and not snapshot:
        diff_data["record_json"] = new_record_json
    version = RecordVersion(
        record_id=record.id,
        version=new_version,
        created_by=user.id,
        source="manual_edit",
        changes=f"更新病历 v{new_version}",
        snapshot=snapshot,
        diff=diff_data if not snapshot else None,
    )
    db.add(version)
    await db.flush()
    await db.refresh(record)

    # 重新生成 embedding（内容变更后需要刷新）
    try:
        record.embedding_status = "pending"
        await db.flush()
        from app.services.embedding_service import generate_record_embedding
        await generate_record_embedding(db, record.id)
    except Exception as e:
        logger.warning("更新后 embedding 重新生成失败 (record=%s): %s", record.id, e)

    return record


async def get_record(db: AsyncSession, record_id: uuid.UUID) -> MedicalRecord:
    result = await db.execute(
        select(MedicalRecord)
        .where(MedicalRecord.id == record_id)
        .options(
            selectinload(MedicalRecord.examinations),
            selectinload(MedicalRecord.diagnoses),
            selectinload(MedicalRecord.treatments),
            selectinload(MedicalRecord.media_files),
            selectinload(MedicalRecord.lab_tests),
            selectinload(MedicalRecord.follow_ups),
            selectinload(MedicalRecord.tags),
        )
    )
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="病历不存在")
    return record


async def list_records(
    db: AsyncSession,
    user: User,
    page: int = 1,
    page_size: int = 20,
    status_filter: str | None = None,
    poultry_type: str | None = None,
    farm_id: uuid.UUID | None = None,
) -> tuple[list[MedicalRecord], int]:
    query = select(MedicalRecord)

    # Permission filtering
    if user.role != "master":
        # User can see own records + authorized records
        authorized_subq = (
            select(RecordPermission.record_id)
            .where(
                and_(
                    RecordPermission.user_id == user.id,
                    RecordPermission.revoked == False,
                )
            )
            .scalar_subquery()
        )
        query = query.where(
            or_(
                MedicalRecord.owner_id == user.id,
                MedicalRecord.id.in_(authorized_subq),
            )
        )

    # 默认排除已删除的病历
    if status_filter:
        query = query.where(MedicalRecord.status == status_filter)
    else:
        query = query.where(MedicalRecord.status != "deleted")
    if poultry_type:
        query = query.where(MedicalRecord.poultry_type == poultry_type)
    if farm_id:
        query = query.where(MedicalRecord.farm_id == farm_id)

    # Count total
    count_result = await db.execute(
        select(func.count()).select_from(query.subquery())
    )
    total = count_result.scalar() or 0

    # Paginate
    query = query.order_by(MedicalRecord.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    records = list(result.scalars().all())

    return records, total


async def get_record_versions(
    db: AsyncSession, record_id: uuid.UUID
) -> list[RecordVersion]:
    result = await db.execute(
        select(RecordVersion)
        .where(RecordVersion.record_id == record_id)
        .order_by(RecordVersion.created_at.desc())
    )
    return list(result.scalars().all())


async def delete_record(
    db: AsyncSession, record_id: uuid.UUID, user: User
) -> MedicalRecord:
    """软删除病历：将 status 设为 deleted 并记录版本"""
    result = await db.execute(
        select(MedicalRecord).where(MedicalRecord.id == record_id)
    )
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="病历不存在")

    if record.status == "deleted":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="病历已删除")

    record.status = "deleted"

    # Bump version
    current = record.current_version or "1.0"
    major, minor = current.split(".")
    new_version = f"{major}.{int(minor) + 1}"
    record.current_version = new_version
    record.version = new_version

    version = RecordVersion(
        record_id=record.id,
        version=new_version,
        created_by=user.id,
        source="manual_edit",
        changes="软删除病历",
        snapshot=record.record_json,
    )
    db.add(version)

    await log_action(
        db, user_id=user.id, action="delete_record",
        resource_type="medical_record", resource_id=record.id,
    )
    await db.flush()
    await db.refresh(record)
    return record


async def get_version_detail(
    db: AsyncSession, record_id: uuid.UUID, version: str
) -> dict:
    """获取单个版本详情，通过快照重建 record_json"""
    # 获取目标版本
    result = await db.execute(
        select(RecordVersion).where(
            and_(
                RecordVersion.record_id == record_id,
                RecordVersion.version == version,
            )
        )
    )
    target = result.scalar_one_or_none()
    if not target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="版本不存在")

    # 如果目标版本有快照，直接返回
    if target.snapshot:
        return {
            "version": target,
            "record_json": target.snapshot,
        }

    # 否则往前找最近的快照版本，然后按序应用 diff
    all_versions_result = await db.execute(
        select(RecordVersion)
        .where(RecordVersion.record_id == record_id)
        .order_by(RecordVersion.created_at.asc())
    )
    all_versions = list(all_versions_result.scalars().all())

    # 找到最近的快照版本（在目标版本之前或等于目标版本）
    snapshot_json = {}
    apply_from_idx = 0

    for i, v in enumerate(all_versions):
        if v.snapshot:
            snapshot_json = dict(v.snapshot)
            apply_from_idx = i + 1
        if v.version == version:
            break

    # 从快照之后按序应用 diff 直到目标版本
    for v in all_versions[apply_from_idx:]:
        if v.diff:
            # 如果 diff 中包含 record_json，说明是完整替换
            if "record_json" in v.diff and isinstance(v.diff["record_json"], dict):
                snapshot_json = dict(v.diff["record_json"])
            else:
                snapshot_json.update(v.diff)
        if v.version == version:
            break

    return {
        "version": target,
        "record_json": snapshot_json,
    }


async def compare_versions(
    db: AsyncSession, record_id: uuid.UUID, v1: str, v2: str
) -> dict:
    """对比两个版本的 record_json 差异"""
    detail1 = await get_version_detail(db, record_id, v1)
    detail2 = await get_version_detail(db, record_id, v2)

    json1 = detail1["record_json"]
    json2 = detail2["record_json"]

    # 逐字段对比
    all_keys = set(list(json1.keys()) + list(json2.keys()))
    added = {}
    removed = {}
    modified = {}

    for key in all_keys:
        if key not in json1:
            added[key] = json2[key]
        elif key not in json2:
            removed[key] = json1[key]
        elif json1[key] != json2[key]:
            modified[key] = {"old": json1[key], "new": json2[key]}

    return {
        "v1": v1,
        "v2": v2,
        "v1_json": json1,
        "v2_json": json2,
        "added": added,
        "removed": removed,
        "modified": modified,
    }


async def rollback_to_version(
    db: AsyncSession, record_id: uuid.UUID, version: str, user: User
) -> MedicalRecord:
    """回滚到指定版本：恢复 record_json 并创建新版本"""
    detail = await get_version_detail(db, record_id, version)
    restored_json = detail["record_json"]

    result = await db.execute(
        select(MedicalRecord).where(MedicalRecord.id == record_id)
    )
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="病历不存在")

    # 更新 record_json 及索引字段
    record.record_json = restored_json
    _sync_indexed_fields(record, restored_json)
    record.record_markdown = _generate_markdown(restored_json)

    # Bump version
    current = record.current_version or "1.0"
    major, minor = current.split(".")
    new_version = f"{major}.{int(minor) + 1}"
    record.current_version = new_version
    record.version = new_version

    # 创建回滚版本记录（带完整快照）
    rollback_version = RecordVersion(
        record_id=record.id,
        version=new_version,
        created_by=user.id,
        source="rollback",
        changes=f"回滚到版本 {version}",
        snapshot=restored_json,
    )
    db.add(rollback_version)

    await log_action(
        db, user_id=user.id, action="rollback_record",
        resource_type="medical_record", resource_id=record.id,
        details={"target_version": version, "new_version": new_version},
    )
    await db.flush()
    await db.refresh(record)
    return record
