# 禽病电子病历系统 (Poultry EMR System)

## 项目简介
面向兽医的智能禽病电子病历管理系统，提供高可读性病历记录、多媒体数据管理和AI辅助诊断功能。

## 核心特性
- ✅ **高可读性**: 混合JSON+Markdown格式，既适合人类阅读又便于机器处理
- ✅ **多媒体支持**: 图片、视频等多媒体文件直传阿里云OSS
- ✅ **智能辅助**: 基于RAG的相似病例检索和AI辅助诊断
- ✅ **微信小程序**: uni-app开发，跨平台支持
- ✅ **数据训练友好**: 结构化数据便于后续AI模型训练

## 技术栈
- **前端**: uni-app (Vue 3) + 微信小程序
- **后端**: Python FastAPI + PostgreSQL + Redis
- **存储**: 阿里云OSS
- **AI/RAG**: LangChain + Milvus + PyTorch

## 快速开始

### 环境要求
- Python 3.10+
- Node.js 16+
- PostgreSQL 14+
- Redis 6+
- 阿里云OSS账号

### 安装依赖

#### 后端
```bash
cd backend
pip install -r requirements.txt
```

#### 前端
```bash
cd frontend
npm install
```

### 配置

1. 复制配置文件模板
```bash
cp backend/.env.example backend/.env
```

2. 编辑 `.env` 文件，填入必要的配置信息：
   - 数据库连接
   - 阿里云OSS配置
   - 微信小程序配置

### 运行

#### 后端服务
```bash
cd backend
uvicorn main:app --reload --port 8000
```

#### 前端（HBuilderX或命令行）
```bash
cd frontend
npm run dev:mp-weixin
```

## 项目文档
详细文档请查看 [PROJECT_PLAN.md](./PROJECT_PLAN.md)

## 目录结构
```
poultry-emr-system/
├── backend/          # FastAPI后端服务
├── frontend/         # uni-app小程序前端
├── ai-training/      # AI模型训练脚本
├── docs/             # 项目文档
└── scripts/          # 工具脚本
```

## 开发进度
- [ ] Phase 1: MVP基础功能
- [ ] Phase 2: 完善功能
- [ ] Phase 3: AI集成
- [ ] Phase 4: 优化迭代

## 贡献指南
欢迎提交Issue和Pull Request

## 许可证
MIT License
