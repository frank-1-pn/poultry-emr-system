# 数据库设计文档

## 概述
本系统采用PostgreSQL作为主数据库，存储结构化数据。病历内容采用JSON+Markdown混合格式存储。

本系统共设计 **18张数据表**。

## 表结构设计

### 1. users (用户表)
存储兽医用户信息

| 字段名 | 类型 | 说明 | 约束 |
|--------|------|------|------|
| id | UUID | 用户ID | PK |
| username | VARCHAR(50) | 用户名 | UNIQUE, NOT NULL |
| email | VARCHAR(100) | 邮箱 | UNIQUE |
| phone | VARCHAR(20) | 手机号 | UNIQUE, NOT NULL |
| password_hash | VARCHAR(255) | 密码哈希 | NOT NULL |
| full_name | VARCHAR(100) | 姓名 | NOT NULL |
| license_number | VARCHAR(50) | 兽医执照号 | UNIQUE |
| avatar_url | TEXT | 头像URL | |
| role | VARCHAR(20) | 角色 | NOT NULL, DEFAULT 'veterinarian' |
| is_active | BOOLEAN | 是否激活 | DEFAULT TRUE |
| last_login_at | TIMESTAMP | 最后登录时间 | |
| login_count | INTEGER | 登录次数 | DEFAULT 0 |
| created_by | UUID | 创建人 | FK -> users.id |
| created_at | TIMESTAMP | 创建时间 | NOT NULL |
| updated_at | TIMESTAMP | 更新时间 | NOT NULL |

### 2. farms (养殖场表)
存储养殖场基本信息

| 字段名 | 类型 | 说明 | 约束 |
|--------|------|------|------|
| id | UUID | 养殖场ID | PK |
| farm_code | VARCHAR(50) | 养殖场编号 | UNIQUE, NOT NULL |
| name | VARCHAR(200) | 养殖场名称 | NOT NULL |
| owner_name | VARCHAR(100) | 场主姓名 | |
| contact_phone | VARCHAR(20) | 联系电话 | |
| province | VARCHAR(50) | 省份 | |
| city | VARCHAR(50) | 城市 | |
| district | VARCHAR(50) | 区县 | |
| address | TEXT | 详细地址 | |
| location_lat | DECIMAL(10,6) | 纬度 | |
| location_lng | DECIMAL(10,6) | 经度 | |
| scale | VARCHAR(20) | 养殖规模 | |
| poultry_types | JSONB | 养殖禽类类型 | |
| created_at | TIMESTAMP | 创建时间 | NOT NULL |
| updated_at | TIMESTAMP | 更新时间 | NOT NULL |

### 3. medical_records (病历主表)
存储病历核心信息

**数据冗余策略说明**：本表采用"独立字段 + JSONB全量"双存储模式：
- **独立字段**（如 `primary_diagnosis`, `poultry_type` 等）：用于数据库索引、查询过滤、排序，是查询的主要依据
- **record_json**（JSONB）：存储完整的结构化病历数据，作为**数据源（Source of Truth）**
- **record_markdown**：由 `record_json` 生成的可读文本，用于前端展示和全文搜索
- **同步机制**：每次更新病历时，先更新 `record_json`，然后从中提取关键字段更新独立列，最后重新生成 `record_markdown`。此逻辑封装在 `record_service` 中统一处理

| 字段名 | 类型 | 说明 | 约束 |
|--------|------|------|------|
| id | UUID | 病历ID | PK |
| record_no | VARCHAR(50) | 病历号 | UNIQUE, NOT NULL |
| version | VARCHAR(10) | 版本号 | DEFAULT '1.0' |
| veterinarian_id | UUID | 兽医ID | FK -> users.id |
| farm_id | UUID | 养殖场ID | FK -> farms.id |
| visit_date | DATE | 就诊日期 | NOT NULL |
| poultry_type | VARCHAR(50) | 禽类类型 | NOT NULL |
| breed | VARCHAR(50) | 品种 | |
| age_days | INTEGER | 日龄 | |
| affected_count | INTEGER | 患病数量 | |
| total_flock | INTEGER | 群体总数 | |
| onset_date | DATE | 发病日期 | |
| primary_diagnosis | VARCHAR(200) | 主要诊断 | |
| icd_code | VARCHAR(20) | 疾病编码 | |
| confidence | DECIMAL(3,2) | 诊断置信度 | |
| severity | VARCHAR(20) | 严重程度 | |
| is_reportable | BOOLEAN | 是否应报告疫病 | DEFAULT FALSE |
| status | VARCHAR(20) | 病历状态 | NOT NULL, DEFAULT 'active' |
| owner_id | UUID | 病历创建者 | FK -> users.id, NOT NULL |
| record_json | JSONB | 完整JSON数据 | NOT NULL |
| record_markdown | TEXT | Markdown文本 | |
| embedding_status | VARCHAR(20) | 向量化状态 | DEFAULT 'pending' |
| embedding_vector | VECTOR(1536) | 向量表示 (pgvector扩展) | |
| data_quality_score | DECIMAL(3,2) | 数据质量评分 | |
| current_version | VARCHAR(10) | 当前版本号 | DEFAULT '1.0' |
| created_at | TIMESTAMP | 创建时间 | NOT NULL |
| updated_at | TIMESTAMP | 更新时间 | NOT NULL |

### 4. clinical_examinations (临床检查表)
详细的临床检查数据

| 字段名 | 类型 | 说明 | 约束 |
|--------|------|------|------|
| id | UUID | 检查ID | PK |
| record_id | UUID | 病历ID | FK -> medical_records.id |
| body_temperature | DECIMAL(4,2) | 体温(°C) | |
| respiratory_rate | INTEGER | 呼吸频率 | |
| heart_rate | INTEGER | 心率 | |
| body_condition_score | INTEGER | 体况评分 | |
| mental_status | VARCHAR(50) | 精神状态 | |
| symptoms | JSONB | 症状列表 | |
| physical_findings | TEXT | 体格检查发现 | |
| created_at | TIMESTAMP | 创建时间 | NOT NULL |

### 5. diagnoses (诊断表)
诊断信息

| 字段名 | 类型 | 说明 | 约束 |
|--------|------|------|------|
| id | UUID | 诊断ID | PK |
| record_id | UUID | 病历ID | FK -> medical_records.id |
| diagnosis_type | VARCHAR(20) | 诊断类型 | NOT NULL |
| disease_name | VARCHAR(200) | 疾病名称 | NOT NULL |
| icd_code | VARCHAR(20) | ICD编码 | |
| confidence | DECIMAL(3,2) | 置信度 | |
| basis | TEXT | 诊断依据 | |
| created_at | TIMESTAMP | 创建时间 | NOT NULL |

### 6. treatments (治疗方案表)
治疗方案

| 字段名 | 类型 | 说明 | 约束 |
|--------|------|------|------|
| id | UUID | 治疗ID | PK |
| record_id | UUID | 病历ID | FK -> medical_records.id |
| treatment_type | VARCHAR(20) | 治疗类型 | NOT NULL |
| medication_name | VARCHAR(200) | 药物名称 | |
| dosage | VARCHAR(100) | 剂量 | |
| route | VARCHAR(50) | 给药途径 | |
| frequency | VARCHAR(100) | 用药频率 | |
| duration_days | INTEGER | 疗程天数 | |
| management_advice | TEXT | 管理建议 | |
| created_at | TIMESTAMP | 创建时间 | NOT NULL |

### 7. media_files (多媒体文件表)
图片、视频等文件信息

| 字段名 | 类型 | 说明 | 约束 |
|--------|------|------|------|
| id | UUID | 文件ID | PK |
| record_id | UUID | 病历ID | FK -> medical_records.id |
| file_type | VARCHAR(20) | 文件类型 | NOT NULL |
| media_type | VARCHAR(50) | 媒体类型 | NOT NULL |
| oss_key | VARCHAR(500) | OSS存储键 | NOT NULL |
| url | TEXT | 访问URL | NOT NULL |
| thumbnail_url | TEXT | 缩略图URL | |
| file_size | BIGINT | 文件大小(字节) | |
| width | INTEGER | 宽度(像素) | |
| height | INTEGER | 高度(像素) | |
| duration | INTEGER | 时长(秒,视频) | |
| description | TEXT | 文件描述 | |
| captured_at | TIMESTAMP | 拍摄时间 | |
| created_at | TIMESTAMP | 创建时间 | NOT NULL |

### 8. lab_tests (实验室检测表)
实验室检测结果

| 字段名 | 类型 | 说明 | 约束 |
|--------|------|------|------|
| id | UUID | 检测ID | PK |
| record_id | UUID | 病历ID | FK -> medical_records.id |
| test_name | VARCHAR(200) | 检测名称 | NOT NULL |
| test_result | VARCHAR(100) | 检测结果 | |
| result_value | DECIMAL(10,2) | 结果数值 | |
| unit | VARCHAR(50) | 单位 | |
| reference_range | VARCHAR(100) | 参考范围 | |
| test_date | DATE | 检测日期 | |
| lab_name | VARCHAR(200) | 检测机构 | |
| report_url | TEXT | 报告文件URL | |
| created_at | TIMESTAMP | 创建时间 | NOT NULL |

### 9. follow_ups (随访表)
随访记录

| 字段名 | 类型 | 说明 | 约束 |
|--------|------|------|------|
| id | UUID | 随访ID | PK |
| record_id | UUID | 病历ID | FK -> medical_records.id |
| follow_up_date | DATE | 随访日期 | NOT NULL |
| status | VARCHAR(50) | 随访状态 | |
| outcome | VARCHAR(100) | 随访结果 | |
| notes | TEXT | 随访备注 | |
| next_visit_date | DATE | 下次随访日期 | |
| created_by | UUID | 创建人 | FK -> users.id |
| created_at | TIMESTAMP | 创建时间 | NOT NULL |

### 10. record_tags (病历标签表)
病历标签（多对多关系）

| 字段名 | 类型 | 说明 | 约束 |
|--------|------|------|------|
| id | UUID | 标签ID | PK |
| record_id | UUID | 病历ID | FK -> medical_records.id |
| tag | VARCHAR(50) | 标签名称 | NOT NULL |
| created_at | TIMESTAMP | 创建时间 | NOT NULL |

### 11. record_versions (病历版本表) 🆕
病历版本快照

**存储策略**：为避免大量完整快照导致存储膨胀：
- 每10个版本保留一个完整快照（`snapshot` 字段非空）
- 中间版本只存储差异（`diff` 字段），`snapshot` 置空
- 版本1.0始终保留完整快照
- 回溯旧版本时，从最近的完整快照 + 后续 diff 重建

| 字段名 | 类型 | 说明 | 约束 |
|--------|------|------|------|
| id | UUID | 版本ID | PK |
| record_id | UUID | 病历ID | FK -> medical_records.id |
| version | VARCHAR(10) | 版本号 | NOT NULL |
| created_at | TIMESTAMP | 创建时间 | NOT NULL |
| created_by | UUID | 创建人 | FK -> users.id |
| source | VARCHAR(20) | 来源 | ai_conversation/manual_edit/import |
| changes | TEXT | 变更说明 | |
| snapshot | JSONB | 完整数据快照 | NOT NULL |
| diff | JSONB | 与上版本差异 | |

### 12. conversations (AI对话表) 🆕
AI对话会话

| 字段名 | 类型 | 说明 | 约束 |
|--------|------|------|------|
| id | UUID | 对话ID | PK |
| record_id | UUID | 病历ID | FK -> medical_records.id |
| user_id | UUID | 用户ID | FK -> users.id |
| status | VARCHAR(20) | 状态 | active/completed/paused |
| state | VARCHAR(50) | 对话状态 | initializing/collecting_basic/... |
| context | JSONB | 对话上下文 | |
| created_at | TIMESTAMP | 创建时间 | NOT NULL |
| updated_at | TIMESTAMP | 更新时间 | NOT NULL |
| completed_at | TIMESTAMP | 完成时间 | |

### 13. conversation_messages (对话消息表) 🆕
AI对话消息记录

| 字段名 | 类型 | 说明 | 约束 |
|--------|------|------|------|
| id | UUID | 消息ID | PK |
| conversation_id | UUID | 对话ID | FK -> conversations.id |
| role | VARCHAR(20) | 角色 | user/assistant/system |
| content | TEXT | 消息内容 | NOT NULL |
| audio_url | TEXT | 语音文件URL | |
| model_used | VARCHAR(100) | 使用的AI模型 | 如 qwen/qwen-plus |
| extracted_info | JSONB | AI提取的信息 | |
| confidence_scores | JSONB | 置信度评分 | |
| timestamp | TIMESTAMP | 时间戳 | NOT NULL |

注：`model_used` 字段记录每条AI回复使用的模型，便于追溯和分析

### 14. record_permissions (病历授权表) 🆕
病历访问权限控制

| 字段名 | 类型 | 说明 | 约束 |
|--------|------|------|------|
| id | UUID | 授权ID | PK |
| record_id | UUID | 病历ID | FK -> medical_records.id |
| user_id | UUID | 被授权用户ID | FK -> users.id |
| permission_level | VARCHAR(20) | 权限级别 | read/write |
| granted_by | UUID | 授权人 | FK -> users.id |
| granted_at | TIMESTAMP | 授权时间 | NOT NULL |
| expires_at | TIMESTAMP | 过期时间 | |
| revoked | BOOLEAN | 是否撤销 | DEFAULT FALSE |
| revoked_at | TIMESTAMP | 撤销时间 | |
| revoked_by | UUID | 撤销人 | FK -> users.id |
| notes | TEXT | 授权备注 | |

约束: UNIQUE(record_id, user_id)

### 15. search_config (搜索配置表) 🆕
混合检索配置

| 字段名 | 类型 | 说明 | 约束 |
|--------|------|------|------|
| id | UUID | 配置ID | PK |
| config_key | VARCHAR(50) | 配置键 | UNIQUE, NOT NULL |
| config_value | JSONB | 配置值 | NOT NULL |
| description | TEXT | 配置说明 | |
| updated_at | TIMESTAMP | 更新时间 | NOT NULL |
| updated_by | UUID | 更新人 | FK -> users.id |

默认配置：
```json
{
  "rag_weight": 0.7,
  "keyword_weight": 0.3,
  "top_k": 10,
  "min_score": 0.5,
  "enable_synonym": true
}
```

### 16. ai_models (AI模型配置表) 🆕
AI模型配置信息

| 字段名 | 类型 | 说明 | 约束 |
|--------|------|------|------|
| id | UUID | 模型ID | PK |
| provider | VARCHAR(50) | 提供商 | NOT NULL |
| model_name | VARCHAR(100) | 模型名称 | NOT NULL |
| display_name | VARCHAR(100) | 显示名称 | NOT NULL |
| api_endpoint | TEXT | API地址 | NOT NULL |
| api_key_encrypted | TEXT | 加密API密钥 | NOT NULL |
| is_active | BOOLEAN | 是否启用 | DEFAULT TRUE |
| is_default | BOOLEAN | 是否默认模型 | DEFAULT FALSE |
| config | JSONB | 模型配置参数 | |
| usage_limit | JSONB | 使用限制 | |
| created_at | TIMESTAMP | 创建时间 | NOT NULL |
| updated_at | TIMESTAMP | 更新时间 | NOT NULL |
| created_by | UUID | 创建人 | FK -> users.id |

### 17. ai_usage_logs (AI使用日志表) 🆕
AI模型调用日志

| 字段名 | 类型 | 说明 | 约束 |
|--------|------|------|------|
| id | UUID | 日志ID | PK |
| model_id | UUID | 模型ID | FK -> ai_models.id |
| user_id | UUID | 用户ID | FK -> users.id |
| conversation_id | UUID | 对话ID | FK -> conversations.id |
| request_tokens | INTEGER | 请求token数 | |
| response_tokens | INTEGER | 响应token数 | |
| total_tokens | INTEGER | 总token数 | |
| cost | DECIMAL(10,4) | 成本（元） | |
| latency_ms | INTEGER | 响应延迟（毫秒） | |
| status | VARCHAR(20) | 状态 | success/error/timeout |
| error_message | TEXT | 错误信息 | |
| created_at | TIMESTAMP | 创建时间 | NOT NULL |

### 18. audit_logs (审计日志表)
操作审计日志

| 字段名 | 类型 | 说明 | 约束 |
|--------|------|------|------|
| id | UUID | 日志ID | PK |
| user_id | UUID | 操作用户ID | FK -> users.id |
| action | VARCHAR(50) | 操作类型 | NOT NULL |
| resource_type | VARCHAR(50) | 资源类型 | NOT NULL |
| resource_id | UUID | 资源ID | |
| details | JSONB | 操作详情 | |
| ip_address | VARCHAR(45) | IP地址 | |
| user_agent | TEXT | 用户代理 | |
| created_at | TIMESTAMP | 创建时间 | NOT NULL |

## 索引设计

### 主要索引
```sql
-- users表
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_active ON users(is_active);

-- medical_records表
CREATE INDEX idx_records_owner ON medical_records(owner_id);
CREATE INDEX idx_records_vet ON medical_records(veterinarian_id);
CREATE INDEX idx_records_farm ON medical_records(farm_id);
CREATE INDEX idx_records_visit_date ON medical_records(visit_date);
CREATE INDEX idx_records_diagnosis ON medical_records(primary_diagnosis);
CREATE INDEX idx_records_status ON medical_records(status);
CREATE INDEX idx_records_created ON medical_records(created_at DESC);
CREATE INDEX idx_records_json ON medical_records USING GIN(record_json);

-- record_permissions表 🆕
CREATE INDEX idx_permissions_record ON record_permissions(record_id);
CREATE INDEX idx_permissions_user ON record_permissions(user_id);
CREATE INDEX idx_permissions_granted_by ON record_permissions(granted_by);
CREATE INDEX idx_permissions_active ON record_permissions(record_id, user_id)
  WHERE revoked = FALSE;

-- record_versions表 🆕
CREATE INDEX idx_versions_record ON record_versions(record_id);
CREATE INDEX idx_versions_created ON record_versions(created_at DESC);

-- conversations表 🆕
CREATE INDEX idx_conversations_record ON conversations(record_id);
CREATE INDEX idx_conversations_user ON conversations(user_id);
CREATE INDEX idx_conversations_status ON conversations(status);

-- conversation_messages表 🆕
CREATE INDEX idx_messages_conversation ON conversation_messages(conversation_id);
CREATE INDEX idx_messages_timestamp ON conversation_messages(timestamp);

-- media_files表
CREATE INDEX idx_media_record ON media_files(record_id);
CREATE INDEX idx_media_type ON media_files(file_type);

-- ai_models表 🆕
CREATE INDEX idx_models_provider ON ai_models(provider);
CREATE INDEX idx_models_active ON ai_models(is_active);
CREATE INDEX idx_models_default ON ai_models(is_default) WHERE is_default = TRUE;

-- ai_usage_logs表 🆕
CREATE INDEX idx_usage_model ON ai_usage_logs(model_id);
CREATE INDEX idx_usage_user ON ai_usage_logs(user_id);
CREATE INDEX idx_usage_date ON ai_usage_logs(created_at);

-- 全文搜索索引
CREATE INDEX idx_records_fulltext ON medical_records USING GIN(
  to_tsvector('simple', coalesce(record_markdown, ''))
);

-- 向量搜索索引 (需要pgvector扩展)
CREATE INDEX idx_records_embedding ON medical_records
USING ivfflat (embedding_vector vector_cosine_ops);
```

## 数据关系图

```
users (用户: Master/兽医)
  ├─ 1:N -> medical_records (创建的病历, owner_id)
  ├─ 1:N -> conversations (发起的对话)
  ├─ 1:N -> record_permissions (被授权记录, user_id)
  ├─ 1:N -> record_permissions (授权操作, granted_by)
  ├─ 1:N -> ai_usage_logs (AI使用日志)
  └─ 1:N -> audit_logs (审计日志)

farms (养殖场)
  └─ 1:N -> medical_records (病历)

medical_records (病历)
  ├─ 1:N -> clinical_examinations (临床检查)
  ├─ 1:N -> diagnoses (诊断)
  ├─ 1:N -> treatments (治疗)
  ├─ 1:N -> media_files (多媒体)
  ├─ 1:N -> lab_tests (实验室检测)
  ├─ 1:N -> follow_ups (随访)
  ├─ 1:N -> record_tags (标签)
  ├─ 1:N -> record_versions (版本历史) 🆕
  ├─ 1:N -> record_permissions (授权记录) 🆕
  └─ 1:N -> conversations (关联对话) 🆕

conversations (AI对话) 🆕
  └─ 1:N -> conversation_messages (对话消息)

ai_models (AI模型配置) 🆕
  └─ 1:N -> ai_usage_logs (使用日志)
```

## 扩展要求

### PostgreSQL扩展
- `uuid-ossp`: UUID生成
- `pgvector`: 向量存储和搜索
- `pg_trgm`: 模糊搜索
- `zhparser` 或 `pg_jieba` (推荐): 中文分词支持

### 安装扩展
```sql
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- 中文分词（二选一）
-- 方案1: zhparser（推荐，需预先编译安装）
CREATE EXTENSION IF NOT EXISTS "zhparser";
CREATE TEXT SEARCH CONFIGURATION chinese (PARSER = zhparser);
ALTER TEXT SEARCH CONFIGURATION chinese ADD MAPPING FOR n,v,a,i,e,l WITH simple;

-- 方案2: 使用 'simple' 配置 + jieba 在应用层分词后存入
-- 适合无法安装 zhparser 扩展的环境
```

### 中文全文搜索说明
默认的 `'simple'` tsvector 配置只按空格分词，对中文支持不佳。建议：
1. **优先方案**：安装 `zhparser` 扩展，将全文搜索索引改为 `to_tsvector('chinese', ...)`
2. **备选方案**：在应用层使用 jieba 分词后，将分词结果（空格分隔）存入专用字段，再用 `'simple'` 配置索引
3. **终极方案**：对搜索质量要求高时，引入 Elasticsearch + IK 分词器作为专用搜索引擎

## 数据迁移
使用Alembic进行数据库版本管理和迁移。

## 性能优化建议
1. 对高频查询字段建立索引
2. 使用JSONB的GIN索引加速JSON查询
3. 定期VACUUM和ANALYZE
4. 考虑分区表（按年/月分区病历表）
5. 使用连接池管理数据库连接
