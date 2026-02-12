# 开发检查清单

## 前期准备 ☑️

### 云服务配置
- [ ] 注册阿里云账号
- [ ] 开通阿里云OSS服务
  - [ ] 创建Bucket: `poultry-emr`
  - [ ] 设置Bucket权限（私有读写）
  - [ ] 获取AccessKey ID和Secret
  - [ ] 配置CORS规则
- [ ] 开通通义千问DashScope服务
  - [ ] 注册账号: https://dashscope.console.aliyun.com/
  - [ ] 获取API Key
  - [ ] 充值（建议先充100元测试）
- [ ] 可选：注册MiniMax账号
  - [ ] 注册: https://api.minimax.chat/
  - [ ] 获取API Key和Group ID
- [ ] 注册微信小程序
  - [ ] 获取AppID和AppSecret
  - [ ] 配置服务器域名白名单

### 开发环境
- [x] 安装Python 3.10+
- [ ] 安装Node.js 16+
- [ ] 安装PostgreSQL 14+
- [ ] 安装Redis 6+
- [ ] 安装HBuilderX（小程序开发）
- [ ] 安装微信开发者工具
- [x] 安装Git（版本控制）
- [x] 推荐：安装VSCode/PyCharm

## Phase 1: MVP基础功能

### 数据库设置
- [ ] 创建PostgreSQL数据库 `poultry_emr`
- [ ] 安装扩展
  ```sql
  CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
  CREATE EXTENSION IF NOT EXISTS "vector";
  CREATE EXTENSION IF NOT EXISTS "pg_trgm";
  ```
- [ ] 创建数据库表（18张）
  - [x] users
  - [x] farms
  - [x] medical_records
  - [x] clinical_examinations
  - [x] diagnoses
  - [x] treatments
  - [x] media_files
  - [x] lab_tests
  - [x] follow_ups
  - [x] record_tags
  - [x] record_versions 🆕
  - [x] conversations 🆕
  - [x] conversation_messages 🆕
  - [x] record_permissions 🆕
  - [x] ai_models 🆕
  - [x] ai_usage_logs 🆕
  - [x] search_config 🆕
  - [x] audit_logs
- [x] 创建索引
- [x] 插入测试数据（scripts/seed_test_data.py）

### 后端开发
- [x] 项目结构搭建
  ```
  backend/
  ├── app/
  │   ├── api/v1/
  │   │   ├── __init__.py
  │   │   ├── auth.py
  │   │   ├── users.py
  │   │   ├── records.py
  │   │   ├── upload.py
  │   │   └── ...
  │   ├── models/
  │   ├── schemas/
  │   ├── services/
  │   ├── core/
  │   └── utils/
  └── main.py
  ```

- [x] 核心功能
  - [x] 数据库连接配置
  - [x] 环境变量加载
  - [x] JWT认证中间件
  - [x] CORS配置
  - [x] 异常处理

- [x] 用户认证
  - [x] 用户注册API
  - [x] 用户登录API
  - [x] Token刷新API
  - [x] 密码加密
  - [x] 获取当前用户信息

- [x] 权限系统 🆕
  - [x] 角色中间件（Master/兽医）
  - [x] 权限验证装饰器
  - [x] 检查病历访问权限函数
  - [x] Master管理API
    - [x] 获取用户列表
    - [x] 激活/停用用户
    - [x] 授权病历
    - [x] 撤销授权
    - [x] 查看授权记录

- [x] 病历CRUD
  - [x] 创建病历（含权限设置）
  - [x] 查询病历列表（含权限过滤）
  - [x] 查询病历详情（含权限验证）
  - [x] 更新病历（创建新版本）
  - [x] 软删除病历

- [x] OSS集成
  - [x] STS临时凭证生成
  - [x] 文件上传API
  - [x] 签名URL生成
  - [x] 文件删除

- [x] 测试
  - [x] 单元测试
  - [x] 集成测试
  - [x] API文档自动生成

### 前端开发（小程序）
- [x] 项目初始化
  ```bash
  cd frontend
  npm install
  ```

- [x] 基础配置
  - [ ] 配置AppID
  - [x] 配置API地址
  - [x] 配置页面路由

- [x] 公共组件
  - [ ] 导航栏
  - [ ] 底部Tab
  - [ ] Loading组件
  - [x] 空状态组件（empty-state）
  - [ ] 确认弹窗

- [x] 页面开发
  - [x] 登录页
    - [x] 手机号登录
    - [ ] 微信授权登录
    - [x] 记住登录状态

  - [x] 病历列表页
    - [x] 病历卡片展示（record-card组件）
    - [x] 权限标识（我的/只读/可编辑）
    - [x] 下拉刷新
    - [x] 上拉加载更多
    - [x] 搜索功能（含语义搜索）

  - [x] 病历详情页
    - [x] Markdown渲染
    - [x] 多媒体展示
    - [x] 权限提示
    - [x] 编辑按钮（根据权限）
    - [ ] 导出功能

  - [x] 病历录入页（表单）
    - [x] 基本信息表单
    - [x] 症状选择（常见症状标签 + 自由输入）
    - [x] 诊断输入
    - [x] 治疗方案
    - [ ] 照片上传
    - [ ] 视频上传

  - [x] 个人中心
    - [x] 用户信息展示
    - [x] 统计数据
    - [x] 退出登录

### 部署测试
- [ ] 后端部署到测试服务器
- [ ] 配置Nginx反向代理
- [ ] 配置HTTPS证书
- [ ] 小程序真机测试
- [ ] 性能测试

## Phase 2: AI对话录入 🔥

### AI模型配置
- [x] 数据库表
  - [x] ai_models表
  - [x] ai_usage_logs表

- [x] LLM适配器开发
  - [x] 基类 BaseLLMAdapter
  - [x] 通义千问适配器 🆕
  - [x] MiniMax适配器 🆕
  - [x] OpenAI适配器（备用）
  - [x] Claude适配器（备用）
  - [x] 适配器工厂

- [x] AI管理API（仅Master）
  - [x] 配置AI模型
  - [x] 获取模型列表
  - [x] 设置默认模型
  - [x] 测试模型
  - [x] 查看使用统计
  - [x] 设置使用限制

### 语音识别集成
- [ ] 微信同声传译集成
  - [ ] 小程序语音插件配置
  - [ ] 实时识别测试

- [ ] 阿里云语音识别（备选）
  - [ ] SDK集成
  - [ ] 录音文件识别
  - [ ] 实时流式识别

### 对话服务开发
- [x] WebSocket服务
  - [x] 连接管理
  - [x] 消息路由
  - [x] 错误处理
  - [x] 心跳保活

- [x] 对话管理
  - [x] 创建对话会话
  - [x] 发送用户消息
  - [x] AI响应生成
  - [x] 信息提取
  - [x] 置信度计算
  - [x] 确认机制
  - [x] 完成对话并保存病历

- [x] Prompt工程
  - [x] System Prompt设计
  - [x] Few-shot示例
  - [x] Function Calling定义
  - [x] 信息提取规则

### 前端对话界面
- [ ] 语音录制组件
  - [ ] 按住说话
  - [ ] 录音动画
  - [ ] 取消录音

- [x] 对话界面组件
  - [x] 消息气泡（用户/AI）（chat-bubble组件）
  - [ ] 语音播放
  - [x] 提取信息展示
  - [x] 确认按钮
  - [x] 滚动到底部

- [x] AI对话录入页
  - [x] 开始对话
  - [x] 实时对话
  - [x] 暂停/继续
  - [x] 查看病历预览
  - [x] 确认保存

### 测试优化
- [x] 对话流程测试
- [ ] 信息提取准确率测试
- [ ] 语音识别准确率测试
- [ ] 响应速度优化
- [ ] 成本优化

## Phase 3: 版本管理和权限

### 版本管理
- [x] 版本创建API
- [x] 版本列表查询
- [x] 版本详情查询
- [x] 版本对比
- [x] 版本回滚

### 时间轴视图
- [x] 提取时间序列事件
- [x] 时间轴数据结构（API）
- [x] 时间轴渲染组件（前端）（timeline-entry组件）

### Master管理后台
- [ ] Web管理界面（Vue 3 + Element Plus）
  - [ ] 用户管理页面
  - [ ] 病历管理页面
  - [ ] 权限授权页面
  - [ ] AI模型配置页面
  - [ ] 数据统计页面

- [ ] 或使用小程序管理页面
  - [ ] 简化版管理界面

## Phase 4: 完善功能

### 搜索功能
- [x] 全文搜索（PostgreSQL）
- [x] 权限过滤
- [x] 高级筛选
- [x] 搜索结果高亮（record-card highlight prop）

### 导出功能
- [x] PDF导出
- [x] Word导出
- [x] Excel批量导出

### 数据统计
- [x] 疾病统计图表（API）
- [ ] 地图可视化
- [x] 用户活跃度（概览API）
- [x] AI使用统计（概览API）

### 离线功能
- [ ] 离线缓存
- [ ] 离线编辑
- [ ] 网络恢复同步

## Phase 5: AI高级功能

### RAG系统
- [x] ~~Milvus向量数据库~~ pgvector（PostgreSQL扩展）
- [x] 病历向量化（embedding_service + DashScope/OpenAI适配器）
- [x] 相似病例检索（语义搜索API + 对话内检索）
- [x] 检索结果排序（余弦相似度排序）

### AI辅助诊断
- [ ] 症状-疾病知识库
- [ ] 诊断推荐
- [ ] 用药建议
- [ ] 疾病百科

### 图像识别
- [ ] 病变图像识别
- [ ] 症状自动标注
- [ ] 图像质量评估

## 上线准备

### 安全检查
- [ ] SQL注入测试
- [ ] XSS防护测试
- [ ] CSRF防护
- [x] 敏感信息加密
- [x] API限流
- [x] 日志脱敏

### 性能优化
- [ ] 数据库查询优化
- [x] 索引优化
- [x] 缓存策略
- [ ] CDN加速
- [ ] 图片压缩

### 监控告警
- [ ] 服务器监控
- [ ] 数据库监控
- [ ] API监控
- [x] 错误日志收集（结构化日志 + 脱敏）
- [ ] 告警通知

### 文档完善
- [x] API文档
- [ ] 用户手册
- [ ] 运维手册
- [ ] 常见问题FAQ

### 备份恢复
- [ ] 数据库定时备份
- [ ] 备份恢复测试
- [ ] 灾难恢复预案

## 持续迭代

### 用户反馈
- [ ] 用户反馈渠道
- [ ] Bug追踪系统
- [ ] 需求收集

### 功能迭代
- [ ] A/B测试
- [ ] 灰度发布
- [ ] 版本管理

### AI模型优化
- [ ] 收集训练数据
- [ ] 模型微调
- [ ] 准确率提升

---

## 当前进度 📊

✅ **已完成**：
- 项目规划和设计
- 技术选型
- 数据库设计
- 完整文档编写
- 项目目录结构创建
- Phase 1 后端核心（认证、病历CRUD、权限系统、管理API、测试）
- Phase 1 OSS STS 实现 + 签名URL
- Phase 1 病历软删除
- Phase 1 前端页面（登录、首页、病历列表/详情、个人中心）
- Phase 1 前端组件（record-card、empty-state、farm-picker、record-picker）
- Phase 2 AI模型管理（8个LLM适配器 + 工厂 + 管理API）
- Phase 2 对话服务后端（REST API + WebSocket + Prompt工程 + Few-shot + 测试）
- Phase 2 前端对话界面（chat-bubble、会话列表、对话页、暂停/继续/确认保存）
- Phase 2 会话管理前端（session-card、sessions列表、创建会话）
- Phase 3 版本管理完整（创建 + 列表 + 详情 + 对比 + 回滚）
- Phase 3 时间轴（API + 前端 timeline-entry 组件）
- Phase 4 搜索配置管理 API + 全文搜索 + 数据统计
- Phase 4 导出（PDF / Word / Excel）
- Phase 5 RAG系统（pgvector + Embedding适配器 + 语义搜索 + 对话内相似病例检索）
- Phase 5 会话摘要 + 智能续聊
- Phase 5 后台 Embedding 批量生成脚本
- 安全加固：API 限流 + 日志脱敏 + 结构化日志
- 测试数据脚本
- 18/18 张数据库表 ORM 模型 + Alembic 迁移
- 64 个后端测试全部通过

⏳ **待开发**：
- Phase 1: 微信授权登录、导出功能前端、照片/视频上传
- Phase 2: 语音识别集成（微信/阿里云）、语音播放
- Phase 3: Master管理后台（Web 或小程序）
- Phase 4: 地图可视化、离线功能
- Phase 5: AI辅助诊断、图像识别
- 部署上线

---

## 每日开发建议

### 第一天
- [ ] 配置所有云服务账号
- [ ] 安装开发环境
- [ ] 创建数据库和表

### 第一周
- [x] 完成后端基础框架
- [x] 实现用户认证
- [x] 实现基础病历CRUD
- [ ] 测试OSS上传

### 第二周
- [x] 完成权限系统
- [ ] 开发小程序基础页面
- [ ] 联调前后端接口

### 第三-四周
- [ ] 完善病历功能
- [ ] 优化用户体验
- [ ] 测试和bug修复

### 第二个月
- [x] 开始AI对话录入功能
- [x] 集成通义千问/MiniMax
- [ ] 开发对话界面

记得每完成一个任务就打勾 ✅，保持进度可见！
