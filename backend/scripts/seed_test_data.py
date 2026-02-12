"""插入测试数据脚本

用法：
  cd backend
  python -m scripts.seed_test_data
"""

import asyncio
import uuid
from datetime import date, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal, engine, Base
from app.core.security import hash_password
from app.models.user import User
from app.models.farm import Farm
from app.models.medical_record import MedicalRecord
from app.models.record_version import RecordVersion
from app.services.search_config_service import init_defaults as init_search_defaults


SAMPLE_RECORDS = [
    {
        "poultry_type": "鸡",
        "breed": "蛋鸡",
        "age_days": 120,
        "affected_count": 30,
        "total_flock": 500,
        "primary_diagnosis": "新城疫",
        "severity": "severe",
        "record_json": {
            "basic_info": {"species": "蛋鸡", "age_days": 120},
            "symptoms": ["精神萎靡", "采食下降", "绿色稀便", "产蛋率下降"],
            "primary_diagnosis": "新城疫",
            "severity": "severe",
            "treatment": {"drug": "新城疫IV系疫苗", "method": "饮水免疫", "duration": "紧急免疫"},
            "notes": "建议隔离发病鸡群，加强消毒",
        },
    },
    {
        "poultry_type": "鸡",
        "breed": "肉鸡",
        "age_days": 28,
        "affected_count": 15,
        "total_flock": 1000,
        "primary_diagnosis": "慢性呼吸道病(CRD)",
        "severity": "moderate",
        "record_json": {
            "basic_info": {"species": "肉鸡", "age_days": 28},
            "symptoms": ["打喷嚏", "流鼻涕", "甩头", "呼吸啰音"],
            "primary_diagnosis": "慢性呼吸道病(CRD)",
            "severity": "moderate",
            "treatment": {"drug": "恩诺沙星", "method": "饮水", "concentration": "0.1%", "duration": "5天"},
        },
    },
    {
        "poultry_type": "鸭",
        "breed": "樱桃谷鸭",
        "age_days": 45,
        "affected_count": 8,
        "total_flock": 200,
        "primary_diagnosis": "鸭瘟",
        "severity": "severe",
        "record_json": {
            "basic_info": {"species": "樱桃谷鸭", "age_days": 45},
            "symptoms": ["流泪", "眼周水肿", "腹泻", "头颈肿大"],
            "primary_diagnosis": "鸭瘟",
            "severity": "severe",
            "treatment": {"drug": "鸭瘟弱毒疫苗", "method": "注射", "dosage": "1头份/只"},
        },
    },
    {
        "poultry_type": "鹅",
        "breed": "狮头鹅",
        "age_days": 60,
        "affected_count": 5,
        "total_flock": 100,
        "primary_diagnosis": "小鹅瘟",
        "severity": "moderate",
        "record_json": {
            "basic_info": {"species": "狮头鹅", "age_days": 60},
            "symptoms": ["腹泻", "食欲减退", "精神不振"],
            "primary_diagnosis": "小鹅瘟",
            "severity": "moderate",
            "treatment": {"drug": "小鹅瘟高免血清", "method": "皮下注射", "dosage": "0.5ml/只"},
        },
    },
    {
        "poultry_type": "鸡",
        "breed": "三黄鸡",
        "age_days": 90,
        "affected_count": 20,
        "total_flock": 800,
        "primary_diagnosis": "球虫病",
        "severity": "mild",
        "record_json": {
            "basic_info": {"species": "三黄鸡", "age_days": 90},
            "symptoms": ["血便", "贫血", "消瘦"],
            "primary_diagnosis": "球虫病",
            "severity": "mild",
            "treatment": {"drug": "地克珠利", "method": "饮水", "duration": "3天"},
        },
    },
    {
        "poultry_type": "鸡",
        "breed": "蛋鸡",
        "age_days": 200,
        "affected_count": 50,
        "total_flock": 2000,
        "primary_diagnosis": "禽流感(H9N2)",
        "severity": "critical",
        "is_reportable": True,
        "record_json": {
            "basic_info": {"species": "蛋鸡", "age_days": 200},
            "symptoms": ["产蛋率骤降", "鸡冠发紫", "呼吸困难", "大量死亡"],
            "primary_diagnosis": "禽流感(H9N2)",
            "severity": "critical",
            "is_reportable": True,
            "notes": "已上报当地畜牧局",
        },
    },
    {
        "poultry_type": "鸽",
        "breed": "信鸽",
        "age_days": 365,
        "affected_count": 3,
        "total_flock": 50,
        "primary_diagnosis": "毛滴虫病",
        "severity": "mild",
        "record_json": {
            "basic_info": {"species": "信鸽", "age_days": 365},
            "symptoms": ["口腔黄色伪膜", "吞咽困难", "消瘦"],
            "primary_diagnosis": "毛滴虫病",
            "severity": "mild",
            "treatment": {"drug": "甲硝唑", "method": "口服", "duration": "7天"},
        },
    },
    {
        "poultry_type": "鹌鹑",
        "breed": "日本鹌鹑",
        "age_days": 40,
        "affected_count": 10,
        "total_flock": 300,
        "primary_diagnosis": "溃疡性肠炎",
        "severity": "moderate",
        "record_json": {
            "basic_info": {"species": "日本鹌鹑", "age_days": 40},
            "symptoms": ["腹泻", "血便", "脱水"],
            "primary_diagnosis": "溃疡性肠炎",
            "severity": "moderate",
            "treatment": {"drug": "林可霉素", "method": "饮水", "duration": "5天"},
        },
    },
]


async def seed():
    async with AsyncSessionLocal() as db:
        # 创建用户
        master = User(
            username="admin",
            phone="13800000000",
            password_hash=hash_password("admin123456"),
            full_name="系统管理员",
            role="master",
            is_active=True,
        )
        vet1 = User(
            username="zhangvet",
            phone="13900000001",
            password_hash=hash_password("vet123456"),
            full_name="张兽医",
            role="veterinarian",
            is_active=True,
        )
        vet2 = User(
            username="livet",
            phone="13900000002",
            password_hash=hash_password("vet123456"),
            full_name="李兽医",
            role="veterinarian",
            is_active=True,
        )
        db.add_all([master, vet1, vet2])
        await db.flush()

        # 创建养殖场
        farm1 = Farm(
            farm_code="FARM-SD-001",
            name="阳光养鸡场",
            owner_name="张兽医",
            address="山东省潍坊市",
            province="山东省",
            city="潍坊市",
            contact_phone="13900000001",
            scale="large",
        )
        farm2 = Farm(
            farm_code="FARM-JS-001",
            name="绿源鸭业",
            owner_name="李兽医",
            address="江苏省南京市",
            province="江苏省",
            city="南京市",
            contact_phone="13900000002",
            scale="medium",
        )
        db.add_all([farm1, farm2])
        await db.flush()

        # 创建病历
        for i, data in enumerate(SAMPLE_RECORDS):
            owner = vet1 if i % 2 == 0 else vet2
            farm = farm1 if i % 2 == 0 else farm2
            visit = date.today() - timedelta(days=len(SAMPLE_RECORDS) - i)

            now_str = visit.strftime("%Y%m%d")
            unique = uuid.uuid4().hex[:6].upper()

            record = MedicalRecord(
                record_no=f"EMR-{now_str}-{unique}",
                owner_id=owner.id,
                veterinarian_id=owner.id,
                farm_id=farm.id,
                visit_date=visit,
                poultry_type=data["poultry_type"],
                breed=data.get("breed"),
                age_days=data.get("age_days"),
                affected_count=data.get("affected_count"),
                total_flock=data.get("total_flock"),
                primary_diagnosis=data.get("primary_diagnosis"),
                severity=data.get("severity"),
                is_reportable=data.get("is_reportable", False),
                record_json=data["record_json"],
                record_markdown=f"# {data['primary_diagnosis']}\n\n禽类: {data['poultry_type']}",
            )
            db.add(record)
            await db.flush()

            version = RecordVersion(
                record_id=record.id,
                version="1.0",
                created_by=owner.id,
                source="manual_edit",
                changes="初始创建",
                snapshot=data["record_json"],
            )
            db.add(version)

        # 初始化搜索配置
        await init_search_defaults(db)

        await db.commit()
        print(f"测试数据插入成功！")
        print(f"  管理员: admin / admin123456")
        print(f"  兽医1:  zhangvet / vet123456")
        print(f"  兽医2:  livet / vet123456")
        print(f"  病历数: {len(SAMPLE_RECORDS)}")
        print(f"  养殖场: 2")


if __name__ == "__main__":
    asyncio.run(seed())
