import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field


class RecordCreate(BaseModel):
    farm_id: uuid.UUID | None = None
    visit_date: date
    poultry_type: str = Field(..., max_length=50)
    breed: str | None = None
    age_days: int | None = None
    affected_count: int | None = None
    total_flock: int | None = None
    onset_date: date | None = None
    record_json: dict


class RecordUpdate(BaseModel):
    farm_id: uuid.UUID | None = None
    visit_date: date | None = None
    poultry_type: str | None = None
    breed: str | None = None
    age_days: int | None = None
    affected_count: int | None = None
    total_flock: int | None = None
    onset_date: date | None = None
    record_json: dict | None = None
    primary_diagnosis: str | None = None
    icd_code: str | None = None
    severity: str | None = None
    is_reportable: bool | None = None
    status: str | None = None


class RecordResponse(BaseModel):
    id: uuid.UUID
    record_no: str
    version: str
    veterinarian_id: uuid.UUID | None = None
    farm_id: uuid.UUID | None = None
    visit_date: date
    poultry_type: str
    breed: str | None = None
    age_days: int | None = None
    affected_count: int | None = None
    total_flock: int | None = None
    onset_date: date | None = None
    primary_diagnosis: str | None = None
    icd_code: str | None = None
    confidence: float | None = None
    severity: str | None = None
    is_reportable: bool
    status: str
    owner_id: uuid.UUID
    record_json: dict
    record_markdown: str | None = None
    current_version: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class RecordListItem(BaseModel):
    id: uuid.UUID
    record_no: str
    visit_date: date
    poultry_type: str
    primary_diagnosis: str | None = None
    severity: str | None = None
    status: str
    owner_id: uuid.UUID
    farm_id: uuid.UUID | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class RecordVersionResponse(BaseModel):
    id: uuid.UUID
    record_id: uuid.UUID
    version: str
    created_at: datetime
    created_by: uuid.UUID | None = None
    source: str | None = None
    changes: str | None = None
    snapshot: dict | None = None

    model_config = {"from_attributes": True}


class VersionDetailResponse(BaseModel):
    version: RecordVersionResponse
    record_json: dict


class VersionCompareResponse(BaseModel):
    v1: str
    v2: str
    v1_json: dict
    v2_json: dict
    added: dict
    removed: dict
    modified: dict


class MediaFileResponse(BaseModel):
    id: uuid.UUID
    file_type: str
    media_type: str
    url: str
    thumbnail_url: str | None = None
    description: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class TreatmentTimelineItem(BaseModel):
    id: uuid.UUID
    treatment_type: str
    medication_name: str | None = None
    dosage: str | None = None
    route: str | None = None
    frequency: str | None = None
    duration_days: int | None = None
    management_advice: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    sort_order: int | None = None
    created_at: datetime
    media_files: list[MediaFileResponse] = []

    model_config = {"from_attributes": True}
