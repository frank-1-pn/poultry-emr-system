# 禽病电子病历系统 - 快速开始指南

## 项目概览

这是一个面向兽医的智能禽病电子病历管理系统，核心特性包括：

✅ **AI对话式录入** - 通过语音与AI对话，自动创建病历
✅ **多模型支持** - 支持通义千问、MiniMax等多种AI模型
✅ **权限管理** - Master管理员 + 兽医数据隔离
✅ **版本追踪** - 完整的病历版本历史和时间轴
✅ **多媒体支持** - 图片、视频直传阿里云OSS
✅ **混合数据格式** - JSON结构化 + Markdown可读性

## 技术栈

- **前端**: uni-app (Vue 3) + 微信小程序
- **后端**: Python FastAPI + PostgreSQL + Redis
- **AI**: 通义千问 / MiniMax (可配置)
- **存储**: 阿里云OSS
- **向量搜索**: pgvector (PostgreSQL扩展，用于RAG语义搜索)

## 环境准备

### 必需软件

1. **Python 3.10+**
   ```bash
   python --version
   ```

2. **Node.js 16+**
   ```bash
   node --version
   npm --version
   ```

3. **PostgreSQL 14+**
   ```bash
   psql --version
   ```

4. **Redis 6+**
   ```bash
   redis-server --version
   ```

5. **HBuilderX** (用于uni-app开发)
   - 下载地址: https://www.dcloud.io/hbuilderx.html

### 云服务账号

1. **阿里云**
   - 开通OSS服务
   - 开通通义千问DashScope服务
   - 可选：开通语音识别服务

2. **MiniMax** (可选)
   - 注册账号: https://api.minimax.chat/
   - 获取API Key和Group ID

3. **微信小程序**
   - 注册小程序账号
   - 获取AppID和AppSecret

## 快速开始

### 1. 克隆项目（或使用现有目录）

```bash
cd C:\Users\ke\poultry-emr-system
```

### 2. 后端设置

#### 2.1 安装Python依赖

```bash
cd backend

# 创建虚拟环境（推荐）
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# Linux/Mac:
# source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

#### 2.2 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑.env文件，填入配置
notepad .env  # Windows
# nano .env   # Linux/Mac
```

**必填配置项**：
```bash
# 数据库
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/poultry_emr

# Redis
REDIS_URL=redis://localhost:6379/0

# 阿里云OSS
ALIYUN_OSS_ACCESS_KEY_ID=your-access-key-id
ALIYUN_OSS_ACCESS_KEY_SECRET=your-access-key-secret
ALIYUN_OSS_ENDPOINT=oss-cn-hangzhou.aliyuncs.com
ALIYUN_OSS_BUCKET=poultry-emr

# 通义千问（推荐）
QWEN_API_KEY=sk-xxxxxxxxxx
QWEN_MODEL=qwen-plus

# MiniMax（可选）
MINIMAX_API_KEY=xxxxx
MINIMAX_GROUP_ID=xxxxx

# Embedding（语义搜索）
EMBEDDING_PROVIDER=dashscope
EMBEDDING_MODEL=text-embedding-v1
EMBEDDING_API_KEY=  # 留空则自动使用QWEN_API_KEY
EMBEDDING_DIMENSIONS=1536

# 微信小程序
WECHAT_APPID=your-wechat-appid
WECHAT_SECRET=your-wechat-secret

# JWT密钥
JWT_SECRET_KEY=your-secret-key-change-in-production
```

#### 2.3 初始化数据库

```bash
# 创建数据库
createdb poultry_emr

# 或使用psql
psql -U postgres
CREATE DATABASE poultry_emr;
\q

# 运行数据库迁移（后续开发）
# alembic upgrade head

# 初始化数据（创建Master账号和默认AI模型）
# python scripts/init_db.py
```

#### 2.4 启动后端服务

```bash
# 开发模式（热重载）
uvicorn main:app --reload --port 8000

# 访问API文档
# http://localhost:8000/docs
```

### 3. 前端设置

#### 3.1 安装Node.js依赖

```bash
cd ../frontend

# 安装依赖
npm install
```

#### 3.2 配置小程序

编辑 `frontend/manifest.json`，填入微信小程序AppID：

```json
{
  "mp-weixin": {
    "appid": "your-wechat-appid"
  }
}
```

#### 3.3 启动开发服务器

**方式1：使用HBuilderX**
1. 打开HBuilderX
2. 文件 → 打开目录 → 选择 `frontend` 文件夹
3. 运行 → 运行到小程序模拟器 → 微信开发者工具

**方式2：使用命令行**
```bash
# 开发模式
npm run dev:mp-weixin

# 构建生产版本
npm run build:mp-weixin
```

#### 3.4 微信开发者工具

1. 打开微信开发者工具
2. 导入项目 → 选择 `frontend/dist/dev/mp-weixin`
3. 填入AppID
4. 开始开发

## 项目结构

```
poultry-emr-system/
├── backend/                 # FastAPI后端
│   ├── app/
│   │   ├── api/v1/         # API路由 (auth, records, upload, admin, conversations, search)
│   │   ├── adapters/       # LLM/Embedding适配器 (8个LLM + 2个Embedding)
│   │   ├── models/         # ORM模型 (18张表)
│   │   ├── schemas/        # Pydantic验证
│   │   ├── services/       # 业务逻辑 (auth, record, conversation, embedding, summary...)
│   │   ├── core/           # 核心配置 (config, database, redis, security)
│   │   └── utils/          # 工具函数
│   ├── alembic/            # 数据库迁移
│   ├── scripts/            # 脚本 (generate_embeddings, seed_test_data)
│   ├── tests/              # 测试
│   ├── requirements.txt    # Python依赖
│   ├── .env               # 环境变量（需创建）
│   └── main.py            # 入口文件
│
├── frontend/               # uni-app前端
│   ├── pages/             # 页面 (login, home, records, chat, sessions, reminders, profile)
│   ├── components/        # 组件 (chat-bubble, session-card, record-card, empty-state...)
│   ├── store/             # 状态管理 (user, records, sessions, chat, reminders)
│   ├── utils/             # 工具 (request, auth, format)
│   └── manifest.json      # 小程序配置
│
├── docs/                   # 文档
│   ├── PROJECT_PLAN.md
│   ├── AI_CONVERSATION_DESIGN.md
│   ├── PERMISSIONS_DESIGN.md
│   ├── AI_MODEL_CONFIGURATION.md
│   └── database/
│       └── schema.md
│
├── README.md              # 项目说明
└── GETTING_STARTED.md     # 本文件
```

## 开发流程

### Phase 1: MVP基础功能 ✅ 已完成

1. **后端基础框架**
   - [x] FastAPI项目结构搭建
   - [x] 数据库连接配置
   - [x] JWT认证实现
   - [x] 用户注册/登录API

2. **数据库设计**
   - [x] 创建所有表（18张，含Alembic迁移）
   - [x] 添加索引
   - [x] 安装PostgreSQL扩展（uuid-ossp, pgvector, pg_trgm）

3. **权限系统**
   - [x] 角色中间件（Master/兽医）
   - [x] 权限验证装饰器
   - [x] 病历访问控制

4. **基础病历API**
   - [x] 创建病历
   - [x] 查询病历列表（含权限过滤）
   - [x] 查询病历详情
   - [x] 更新病历（含版本管理）

5. **OSS集成**
   - [x] STS临时凭证生成
   - [x] 文件上传API
   - [x] 签名URL生成

6. **前端小程序**
   - [x] 登录页面
   - [x] 病历列表页（含搜索、语义搜索）
   - [x] 病历详情页
   - [ ] 表单录入页（基础版）

### Phase 2: AI对话录入 ✅ 大部分完成

1. **AI模型配置**
   - [x] 通义千问SDK集成
   - [x] MiniMax SDK集成
   - [x] LLM适配器开发（8个适配器 + 工厂模式）
   - [x] Master管理后台（AI模型配置API）

2. **语音识别**
   - [ ] 微信语音插件集成
   - [ ] 阿里云语音识别集成
   - [ ] 语音文件上传OSS

3. **对话管理**
   - [x] WebSocket服务
   - [x] 对话状态管理
   - [x] 信息提取逻辑
   - [x] 置信度计算

4. **前端对话界面**
   - [ ] 语音录制组件
   - [x] 对话气泡展示（chat-bubble组件）
   - [x] 实时信息确认
   - [x] 病历预览

### Phase 3-5: 高级功能 ✅ 大部分完成

- [x] 版本管理（创建/列表/详情/对比/回滚）
- [x] 时间轴视图（API + 前端组件）
- [x] 全文搜索 + 高级筛选
- [x] 导出（PDF / Word / Excel）
- [x] RAG语义搜索（pgvector + Embedding适配器）
- [x] 对话内相似病例检索
- [x] 会话摘要 + 智能续聊
- [ ] AI辅助诊断
- [ ] 图像识别
- [ ] Master管理后台（Web界面）

### 下一步建议

**待开发项目**：

1. **病历录入页（表单版）**
   - 手动填写病历的表单界面
   - 基本信息、症状、诊断、治疗方案

2. **语音识别集成**
   - 微信同声传译插件
   - 阿里云语音识别（备选）

3. **Master管理后台**
   - Web管理界面（Vue 3 + Element Plus）
   - 用户管理、病历管理、AI模型配置

4. **部署上线**
   - 服务器部署 + Nginx + HTTPS
   - 小程序真机测试和发布

## 常用命令

### 后端开发

```bash
# 启动服务
uvicorn main:app --reload

# 数据库迁移
alembic revision --autogenerate -m "描述"
alembic upgrade head

# 运行测试
pytest

# 代码格式化
black .
```

### 前端开发

```bash
# 开发模式
npm run dev:mp-weixin

# 构建
npm run build:mp-weixin

# 代码检查
npm run lint
npm run lint:fix
```

## 调试技巧

### 后端调试

1. **查看日志**
   ```python
   from loguru import logger
   logger.info("调试信息")
   ```

2. **API文档**
   访问 http://localhost:8000/docs 查看所有API

3. **数据库查询**
   ```bash
   psql -U postgres poultry_emr
   SELECT * FROM users;
   ```

### 前端调试

1. **微信开发者工具**
   - 控制台查看日志
   - Network面板查看请求
   - Storage查看本地存储

2. **uni-app调试**
   ```javascript
   console.log('调试信息')
   uni.showToast({ title: '提示信息' })
   ```

## 常见问题

### Q: 数据库连接失败？
A: 检查PostgreSQL是否启动，密码是否正确，DATABASE_URL配置是否正确

### Q: OSS上传失败？
A: 检查Bucket权限设置，AccessKey是否有效，网络是否可达

### Q: AI模型调用失败？
A: 检查API Key是否正确，余额是否充足，网络是否可达

### Q: 小程序无法登录？
A: 检查AppID配置，后端API地址是否正确，服务器域名是否在白名单

## 获取帮助

- **项目文档**: 查看 `docs/` 目录下的详细文档
- **API文档**: http://localhost:8000/docs
- **问题反馈**: 创建GitHub Issue

## 下一步学习

1. 阅读 [PROJECT_PLAN.md](PROJECT_PLAN.md) 了解完整规划
2. 阅读 [AI_CONVERSATION_DESIGN.md](docs/AI_CONVERSATION_DESIGN.md) 了解AI对话设计
3. 阅读 [PERMISSIONS_DESIGN.md](docs/PERMISSIONS_DESIGN.md) 了解权限管理
4. 阅读 [数据库设计](docs/database/schema.md) 了解数据结构

## 开发团队协作

如果多人开发，建议：

1. **分支管理**
   - main: 稳定版本
   - develop: 开发版本
   - feature/xxx: 功能分支

2. **代码审查**
   - 所有代码通过PR合并
   - 至少一人审查

3. **环境隔离**
   - 开发环境: dev
   - 测试环境: test
   - 生产环境: prod

---

🎉 **祝开发顺利！**
