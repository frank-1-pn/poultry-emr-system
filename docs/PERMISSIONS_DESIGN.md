# 权限管理系统设计

## 概述
本文档描述禽病电子病历系统的权限管理机制，实现Master管理员全局管理和兽医数据隔离。

## 角色定义

### Master管理员
**权限范围**：
- 查看所有病历数据（不受创建者和授权限制）
- 管理所有用户账号（激活、停用、查看）
- 授权任意病历给任意兽医
- 批量授权管理
- 查看全局数据统计
- 系统配置管理

**使用场景**：
- 系统管理员
- 科研人员（需要查看全局数据）
- 数据分析师
- 质量审核人员

### 兽医(Veterinarian)
**权限范围**：
- 创建病历（自动成为owner）
- 查看和编辑自己创建的病历
- 查看被授权的病历（根据授权级别）
- 编辑有写权限的病历
- 使用AI对话录入功能

**使用场景**：
- 一线兽医
- 执业兽医师

## 权限级别

### 病历权限级别
1. **owner（所有者）**: 完全控制权
   - 查看、编辑、删除病历
   - 查看版本历史
   - 导出病历

2. **write（读写）**: 可编辑
   - 查看和编辑病历
   - 添加随访记录
   - 上传多媒体文件
   - 查看版本历史

3. **read（只读）**: 仅查看
   - 查看病历详情
   - 查看多媒体文件
   - 查看版本历史
   - 导出病历（可选）

4. **none（无权限）**: 不可访问

## 数据库设计

### users 表扩展
```sql
CREATE TABLE users (
    -- 原有字段...
    role VARCHAR(20) NOT NULL DEFAULT 'veterinarian',  -- master, veterinarian
    is_active BOOLEAN DEFAULT TRUE,
    last_login_at TIMESTAMP,
    login_count INTEGER DEFAULT 0,
    created_by UUID REFERENCES users(id),  -- 创建人（用于审计）
    -- ...
);

CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_active ON users(is_active);
```

### record_permissions 表（病历授权表）
```sql
CREATE TABLE record_permissions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    record_id UUID NOT NULL REFERENCES medical_records(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    permission_level VARCHAR(20) NOT NULL,  -- read, write
    granted_by UUID NOT NULL REFERENCES users(id),  -- 授权人
    granted_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,  -- 过期时间（可选）
    revoked BOOLEAN DEFAULT FALSE,  -- 是否已撤销
    revoked_at TIMESTAMP,
    revoked_by UUID REFERENCES users(id),
    notes TEXT,  -- 授权备注

    UNIQUE(record_id, user_id),  -- 一个用户对一个病历只有一个权限记录
    CHECK (permission_level IN ('read', 'write'))
);

CREATE INDEX idx_permissions_record ON record_permissions(record_id);
CREATE INDEX idx_permissions_user ON record_permissions(user_id);
CREATE INDEX idx_permissions_granted_by ON record_permissions(granted_by);
CREATE INDEX idx_permissions_active ON record_permissions(record_id, user_id)
    WHERE revoked = FALSE;
```

### medical_records 表扩展
```sql
ALTER TABLE medical_records
ADD COLUMN owner_id UUID NOT NULL REFERENCES users(id);

CREATE INDEX idx_records_owner ON medical_records(owner_id);
```

## 权限验证逻辑

### 检查流程
```python
def check_record_permission(user_id: UUID, record_id: UUID,
                           required_level: str = 'read') -> tuple[bool, str]:
    """
    检查用户对病历的权限

    Returns:
        (has_permission, permission_level)
    """
    user = get_user(user_id)

    # 1. Master拥有所有权限
    if user.role == 'master':
        return True, 'owner'

    # 2. 检查是否是病历创建者
    record = get_record(record_id)
    if record.owner_id == user_id:
        return True, 'owner'

    # 3. 检查授权表
    permission = db.query(RecordPermission).filter(
        RecordPermission.record_id == record_id,
        RecordPermission.user_id == user_id,
        RecordPermission.revoked == False
    ).first()

    if not permission:
        return False, 'none'

    # 4. 检查是否过期
    if permission.expires_at and permission.expires_at < datetime.now():
        return False, 'none'

    # 5. 检查权限级别是否满足要求
    level_hierarchy = {'read': 1, 'write': 2, 'owner': 3}
    if level_hierarchy.get(permission.permission_level, 0) >= level_hierarchy.get(required_level, 0):
        return True, permission.permission_level

    return False, permission.permission_level
```

### FastAPI依赖注入
```python
from fastapi import Depends, HTTPException

async def require_permission(
    record_id: UUID,
    required_level: str = 'read',
    current_user: User = Depends(get_current_user)
) -> RecordPermission:
    """
    权限验证依赖，用于API路由
    """
    has_permission, level = check_record_permission(
        current_user.id,
        record_id,
        required_level
    )

    if not has_permission:
        raise HTTPException(
            status_code=403,
            detail=f"您没有{required_level}该病历的权限"
        )

    return RecordPermission(
        user_id=current_user.id,
        record_id=record_id,
        level=level
    )

# 使用示例
@app.get("/api/v1/records/{record_id}")
async def get_record(
    record_id: UUID,
    permission: RecordPermission = Depends(require_permission)
):
    """获取病历详情"""
    record = get_record_detail(record_id)

    # 根据权限级别决定返回内容
    if permission.level == 'read':
        # 只读用户可能隐藏某些敏感信息
        record.pop('internal_notes', None)

    return record
```

## API设计

### 用户管理API (仅Master)

#### 获取用户列表
```
GET /api/v1/admin/users
Authorization: Bearer {master_token}

Query Parameters:
- role: master|veterinarian
- is_active: true|false
- page: int
- page_size: int
```

**Response**
```json
{
  "total": 50,
  "page": 1,
  "page_size": 20,
  "users": [
    {
      "id": "uuid",
      "username": "zhang_vet",
      "full_name": "张医生",
      "role": "veterinarian",
      "is_active": true,
      "record_count": 123,
      "last_login_at": "2026-01-27T10:00:00Z",
      "created_at": "2025-01-01T00:00:00Z"
    }
  ]
}
```

#### 激活/停用用户
```
PATCH /api/v1/admin/users/{user_id}/status
```

**Request**
```json
{
  "is_active": false,
  "reason": "停用原因"
}
```

### 权限管理API

#### 授权病历（Master操作）
```
POST /api/v1/admin/permissions
Authorization: Bearer {master_token}
```

**Request**
```json
{
  "record_id": "uuid",
  "user_id": "uuid",
  "permission_level": "read",
  "expires_at": "2026-12-31T23:59:59Z",  // 可选
  "notes": "授权用于科研项目"
}
```

**Response**
```json
{
  "permission_id": "uuid",
  "record_id": "uuid",
  "user_id": "uuid",
  "permission_level": "read",
  "granted_by": "master_uuid",
  "granted_at": "2026-01-27T10:00:00Z",
  "expires_at": "2026-12-31T23:59:59Z"
}
```

#### 批量授权
```
POST /api/v1/admin/permissions/batch
```

**Request**
```json
{
  "record_ids": ["uuid1", "uuid2", "uuid3"],
  "user_ids": ["user_uuid1", "user_uuid2"],
  "permission_level": "read",
  "notes": "批量授权给研究团队"
}
```

#### 撤销授权
```
DELETE /api/v1/admin/permissions/{permission_id}
```

**Request**
```json
{
  "reason": "项目结束"
}
```

#### 查看用户的授权列表
```
GET /api/v1/admin/users/{user_id}/permissions
```

**Response**
```json
{
  "user_id": "uuid",
  "permissions": [
    {
      "permission_id": "uuid",
      "record_id": "uuid",
      "record_no": "PR20260127001",
      "farm_name": "阳光养殖场",
      "permission_level": "read",
      "granted_by_name": "系统管理员",
      "granted_at": "2026-01-20T10:00:00Z",
      "expires_at": null
    }
  ]
}
```

#### 查看病历的授权记录
```
GET /api/v1/records/{record_id}/permissions
```

**Response**
```json
{
  "record_id": "uuid",
  "owner": {
    "user_id": "uuid",
    "name": "张医生"
  },
  "shared_with": [
    {
      "permission_id": "uuid",
      "user_id": "uuid",
      "user_name": "李医生",
      "permission_level": "read",
      "granted_by_name": "系统管理员",
      "granted_at": "2026-01-20T10:00:00Z"
    }
  ]
}
```

### 病历查询API（权限过滤）

#### 获取我的病历列表
```
GET /api/v1/records
Authorization: Bearer {token}
```

**逻辑**：
- Master: 返回所有病历
- 兽医: 返回自己创建的 + 被授权的病历

**SQL实现**
```sql
-- 兽医查询
SELECT r.*
FROM medical_records r
WHERE r.owner_id = :user_id  -- 自己的
   OR EXISTS (  -- 或被授权的
       SELECT 1 FROM record_permissions p
       WHERE p.record_id = r.id
         AND p.user_id = :user_id
         AND p.revoked = FALSE
         AND (p.expires_at IS NULL OR p.expires_at > NOW())
   )
ORDER BY r.created_at DESC;

-- Master查询
SELECT r.*
FROM medical_records r
ORDER BY r.created_at DESC;
```

## 前端实现

### 权限标识显示

#### 病历列表
```vue
<template>
  <view class="record-card">
    <view class="header">
      <text class="title">{{ record.record_no }}</text>
      <!-- 权限标识 -->
      <view v-if="record.permission_level === 'read'" class="badge read">
        只读
      </view>
      <view v-else-if="record.permission_level === 'write'" class="badge write">
        可编辑
      </view>
      <view v-else class="badge owner">
        我的
      </view>
    </view>
    <!-- ... -->
  </view>
</template>
```

#### 病历详情
```vue
<template>
  <view class="record-detail">
    <!-- 权限提示 -->
    <view v-if="permissionLevel === 'read'" class="permission-notice">
      <icon type="info" />
      <text>您对此病历仅有查看权限</text>
    </view>

    <!-- 根据权限显示操作按钮 -->
    <view class="actions">
      <button @click="exportPDF">导出</button>
      <button v-if="canEdit" @click="editRecord">编辑</button>
      <button v-if="canEdit" @click="addFollowUp">添加随访</button>
    </view>
  </view>
</template>

<script>
export default {
  computed: {
    canEdit() {
      return ['owner', 'write'].includes(this.permissionLevel)
    }
  }
}
</script>
```

### Master管理后台

#### 用户管理页面
```vue
<template>
  <view class="admin-users">
    <view class="filters">
      <picker @change="filterRole" :range="['全部', 'Master', '兽医']">
        角色筛选
      </picker>
      <picker @change="filterStatus" :range="['全部', '激活', '停用']">
        状态筛选
      </picker>
    </view>

    <view class="user-list">
      <view v-for="user in users" :key="user.id" class="user-item">
        <view class="info">
          <text class="name">{{ user.full_name }}</text>
          <text class="role">{{ user.role }}</text>
          <text class="stats">病历: {{ user.record_count }}</text>
        </view>
        <view class="actions">
          <button @click="viewPermissions(user)">查看权限</button>
          <button @click="toggleActive(user)">
            {{ user.is_active ? '停用' : '激活' }}
          </button>
        </view>
      </view>
    </view>
  </view>
</template>
```

#### 授权管理页面
```vue
<template>
  <view class="admin-permissions">
    <view class="search">
      <input placeholder="搜索病历" @input="searchRecord" />
      <input placeholder="搜索用户" @input="searchUser" />
    </view>

    <view class="grant-form">
      <picker @change="selectRecord" :range="records" range-key="record_no">
        选择病历
      </picker>
      <picker @change="selectUser" :range="users" range-key="full_name">
        选择用户
      </picker>
      <picker @change="selectLevel" :range="['只读', '读写']">
        权限级别
      </picker>
      <button @click="grantPermission">授权</button>
    </view>

    <view class="permission-list">
      <view v-for="perm in permissions" :key="perm.id" class="perm-item">
        <text>{{ perm.record_no }} → {{ perm.user_name }}</text>
        <text class="level">{{ perm.permission_level }}</text>
        <button @click="revoke(perm)">撤销</button>
      </view>
    </view>
  </view>
</template>
```

## 审计日志

### 权限变更记录
所有权限相关操作都记录到 `audit_logs` 表：

```sql
INSERT INTO audit_logs (
    user_id,
    action,
    resource_type,
    resource_id,
    details,
    ip_address
) VALUES (
    :master_user_id,
    'grant_permission',
    'record_permission',
    :permission_id,
    jsonb_build_object(
        'record_id', :record_id,
        'target_user_id', :target_user_id,
        'permission_level', :permission_level
    ),
    :ip_address
);
```

### 查询审计日志
```
GET /api/v1/admin/audit-logs
```

**Query Parameters**:
- action: grant_permission, revoke_permission, activate_user, deactivate_user
- user_id: 操作人ID
- resource_id: 资源ID
- start_date, end_date: 时间范围

## 安全考虑

### 防止权限提升
```python
@app.post("/api/v1/admin/users")
async def create_user(
    user_data: UserCreate,
    current_user: User = Depends(get_current_user)
):
    # 只有Master可以创建用户
    if current_user.role != 'master':
        raise HTTPException(403, "权限不足")

    # 普通Master不能创建新的Master（需要超级管理员）
    if user_data.role == 'master' and not current_user.is_superadmin:
        raise HTTPException(403, "无权创建Master账号")

    # ...
```

### 防止越权访问
```python
@app.get("/api/v1/records/{record_id}")
async def get_record(
    record_id: UUID,
    current_user: User = Depends(get_current_user)
):
    # 检查权限
    has_permission, level = check_record_permission(
        current_user.id,
        record_id,
        'read'
    )

    if not has_permission:
        # 不要泄露病历是否存在
        raise HTTPException(404, "病历不存在")

    # ...
```

### 敏感操作二次验证
```python
@app.delete("/api/v1/records/{record_id}")
async def delete_record(
    record_id: UUID,
    confirmation: str,  # 要求输入病历号确认
    current_user: User = Depends(get_current_user)
):
    record = get_record(record_id)

    # 只有owner可以删除
    if record.owner_id != current_user.id:
        raise HTTPException(403, "只有病历创建者可以删除")

    # 验证确认信息
    if confirmation != record.record_no:
        raise HTTPException(400, "确认信息不匹配")

    # 软删除
    record.is_deleted = True
    record.deleted_at = datetime.now()
    record.deleted_by = current_user.id
    db.commit()
```

## 性能优化

### 缓存用户权限
```python
from functools import lru_cache
import redis

redis_client = redis.Redis()

def get_user_permissions_cached(user_id: UUID) -> set[UUID]:
    """
    获取用户有权限的病历ID列表（缓存5分钟）
    """
    cache_key = f"user_permissions:{user_id}"
    cached = redis_client.get(cache_key)

    if cached:
        return set(json.loads(cached))

    # 查询数据库
    permissions = db.query(RecordPermission).filter(
        RecordPermission.user_id == user_id,
        RecordPermission.revoked == False
    ).all()

    record_ids = {p.record_id for p in permissions}

    # 缓存5分钟
    redis_client.setex(
        cache_key,
        300,
        json.dumps([str(id) for id in record_ids])
    )

    return record_ids
```

### 权限变更时清除缓存
```python
def grant_permission(record_id: UUID, user_id: UUID, level: str):
    # 授权操作
    permission = RecordPermission(...)
    db.add(permission)
    db.commit()

    # 清除缓存
    redis_client.delete(f"user_permissions:{user_id}")
```

## 测试用例

### 单元测试
```python
def test_master_can_access_all_records():
    """Master可以访问所有病历"""
    master = create_user(role='master')
    vet = create_user(role='veterinarian')
    record = create_record(owner_id=vet.id)

    has_permission, level = check_record_permission(master.id, record.id)
    assert has_permission == True
    assert level == 'owner'

def test_vet_can_only_access_own_records():
    """兽医只能访问自己的病历"""
    vet1 = create_user(role='veterinarian')
    vet2 = create_user(role='veterinarian')
    record = create_record(owner_id=vet1.id)

    # vet1可以访问
    has_permission, _ = check_record_permission(vet1.id, record.id)
    assert has_permission == True

    # vet2不能访问
    has_permission, _ = check_record_permission(vet2.id, record.id)
    assert has_permission == False

def test_shared_permission_works():
    """授权后可以访问"""
    master = create_user(role='master')
    vet1 = create_user(role='veterinarian')
    vet2 = create_user(role='veterinarian')
    record = create_record(owner_id=vet1.id)

    # 授权前vet2不能访问
    has_permission, _ = check_record_permission(vet2.id, record.id)
    assert has_permission == False

    # 授权
    grant_permission(record.id, vet2.id, 'read', granted_by=master.id)

    # 授权后可以访问
    has_permission, level = check_record_permission(vet2.id, record.id)
    assert has_permission == True
    assert level == 'read'
```

## 常见问题

### Q: 如果兽医离职，病历怎么办？
A:
1. Master停用该兽医账号（`is_active=False`）
2. 病历所有权不变，仍然归属该账号
3. Master可以查看和管理这些病历
4. 如需转移所有权，Master可以修改`owner_id`

### Q: 授权是否可以级联？
A: 不支持。只有Master可以授权，被授权的兽医不能再授权给其他人。

### Q: 权限过期后会怎样？
A: 系统检查权限时会验证`expires_at`，过期后自动拒绝访问，但权限记录仍保留在数据库中用于审计。

### Q: 是否支持权限组/角色组？
A: MVP阶段不支持，后续可扩展。可以添加`permission_groups`表实现批量授权。
