# AI对话式病历录入系统设计

## 概述
本文档详细描述AI对话式病历录入功能的设计方案，实现兽医通过语音与AI对话来创建和更新病历。

## 核心目标
1. **降低录入门槛**: 兽医无需填写复杂表单，通过自然对话即可完成
2. **提高准确性**: AI主动确认不确定的信息，减少错误
3. **时间序列追踪**: 自动识别病情发展时间线
4. **版本管理**: 每次对话更新都创建新版本，可追溯

## 技术架构

### 语音识别
#### 方案选择
1. **微信同声传译插件** (推荐用于小程序)
   - 优势：集成简单，无需额外配置
   - 限制：需要微信小程序环境
   - 使用：`wx.startRecordPlugin()`

2. **阿里云智能语音服务**
   - 优势：准确率高，支持医疗领域定制
   - 成本：按识别时长计费
   - 支持：实时语音识别、录音文件识别

#### 实现方式
```javascript
// 小程序端 - 微信语音识别
const recorderManager = wx.getRecorderManager()

// 开始录音
recorderManager.start({
  duration: 60000, // 最长60秒
  format: 'mp3',
  sampleRate: 16000
})

// 停止录音
recorderManager.onStop((res) => {
  // 1. 上传语音文件到OSS
  // 2. 调用语音识别API
  // 3. 获取文字结果
  // 4. 发送到AI对话服务
})
```

### AI对话引擎

#### LLM选择
**推荐：OpenAI GPT-4o / Claude 3.5 Sonnet**
- 理解能力强，能准确提取医疗信息
- 支持Function Calling，便于结构化输出
- 中文理解和生成质量高

#### Prompt设计

##### System Prompt
```
你是一个专业的兽医助手，负责帮助兽医创建禽病电子病历。
你的任务是通过对话从兽医那里收集病历信息，并将信息结构化。

核心职责：
1. 引导兽医描述病例情况
2. 从对话中提取关键信息（发病时间、地点、症状、诊断、治疗等）
3. 对不确定的信息（置信度<90%）主动向兽医确认
4. 识别时间序列信息，建立病情发展时间线
5. 确保关键字段不遗漏

必须收集的关键信息：
- 发病日期和就诊日期
- 养殖场信息（名称、地点）
- 禽类类型和品种
- 患病数量和总群体数
- 主要症状
- 初步诊断
- 治疗方案

对话原则：
- 使用专业但友好的语气
- 一次只问一个或相关的几个问题
- 对模糊信息必须确认
- 自动识别日期表达（如"昨天"、"三天前"）
- 当信息完整后，总结给兽医确认

输出格式：
使用JSON格式输出提取的结构化信息，包含每个字段的置信度。
```

##### Function Calling定义
```json
{
  "name": "extract_medical_record_info",
  "description": "从对话中提取病历信息",
  "parameters": {
    "type": "object",
    "properties": {
      "onset_date": {
        "type": "string",
        "description": "发病日期 (YYYY-MM-DD格式)"
      },
      "visit_date": {
        "type": "string",
        "description": "就诊日期 (YYYY-MM-DD格式)"
      },
      "farm_info": {
        "type": "object",
        "properties": {
          "name": {"type": "string"},
          "location": {"type": "string"}
        }
      },
      "poultry_info": {
        "type": "object",
        "properties": {
          "type": {"type": "string"},
          "breed": {"type": "string"},
          "age_days": {"type": "integer"},
          "affected_count": {"type": "integer"},
          "total_flock": {"type": "integer"}
        }
      },
      "symptoms": {
        "type": "array",
        "items": {"type": "string"}
      },
      "diagnosis": {
        "type": "object",
        "properties": {
          "primary": {"type": "string"},
          "differential": {"type": "array", "items": {"type": "string"}}
        }
      },
      "treatment": {
        "type": "object"
      },
      "confidence_scores": {
        "type": "object",
        "description": "每个字段的置信度 0-1"
      },
      "needs_confirmation": {
        "type": "array",
        "items": {"type": "string"},
        "description": "需要确认的字段列表"
      }
    }
  }
}
```

### 对话状态管理

#### 会话状态
```python
class ConversationState(Enum):
    INITIALIZING = "initializing"      # 初始化
    COLLECTING_BASIC = "collecting_basic"  # 收集基本信息
    COLLECTING_SYMPTOMS = "collecting_symptoms"  # 收集症状
    COLLECTING_DIAGNOSIS = "collecting_diagnosis"  # 收集诊断
    COLLECTING_TREATMENT = "collecting_treatment"  # 收集治疗
    CONFIRMING = "confirming"          # 确认信息
    COMPLETED = "completed"            # 完成
    PAUSED = "paused"                  # 暂停
```

#### 对话上下文
```python
class ConversationContext:
    conversation_id: str
    record_id: str
    user_id: str
    state: ConversationState
    collected_info: dict  # 已收集的信息
    confidence_scores: dict  # 置信度
    pending_confirmations: list  # 待确认项
    message_history: list  # 对话历史
    timeline_events: list  # 时间线事件
    created_at: datetime
    updated_at: datetime
```

## 对话流程设计

### 流程图
```
开始对话
  ↓
[AI] "您好，我是AI助手，请描述本次就诊的基本情况"
  ↓
[兽医] 语音描述
  ↓
[系统] 语音识别 → 文字
  ↓
[AI] 分析 → 提取信息 → 计算置信度
  ↓
置信度检查
  ├─ ≥90% → 记录信息
  └─ <90% → 生成确认问题
  ↓
[AI] 回应："我记录了XX信息，[确认问题]，请问YY？"
  ↓
[兽医] 回答
  ↓
检查信息完整度
  ├─ 未完整 → 继续提问
  └─ 已完整 → 进入确认阶段
  ↓
[AI] 总结所有信息："我整理了以下信息：[摘要]，请确认是否正确？"
  ↓
[兽医] 确认或修改
  ↓
保存病历
  ↓
结束对话
```

### 示例对话

#### 场景1：首次创建病历
```
AI: 您好，我是AI助手。请告诉我本次就诊的基本情况，比如什么时候发病的，哪个养殖场。

兽医: [语音] "是这样的，阳光养殖场昨天打电话说鸡不对劲，我今天过去看了，大概有200只鸡在咳嗽，精神也不好"

AI: 好的，我记录了以下信息：
- 养殖场：阳光养殖场 ✓
- 发病时间：1月26日（昨天）
- 就诊时间：1月27日（今天）
- 患病数量：约200只 ✓
- 症状：咳嗽、精神沉郁 ✓

请问是什么品种的鸡？日龄大概多少？群体总共有多少只？

兽医: [语音] "白羽肉鸡，35天左右，一共一万只"

AI: 收到。请问主要症状除了咳嗽和精神沉郁，还有其他表现吗？比如呼吸困难、腹泻、羽毛异常等？

兽医: [语音] "有呼吸困难，张口呼吸，有呼噜声"

AI: 明白了。根据这些症状，您初步诊断是什么？

兽医: [语音] "我怀疑是新城疫，但也可能是禽流感或者传染性支气管炎"

AI: 好的，我已经记录了您的初步诊断。请问采取了什么治疗措施？

兽医: [语音] "先隔离病禽，然后给全群饮水加了抗病毒药，准备明天送检"

AI: 很好。让我总结一下本次病历信息：

**基本信息**
- 养殖场：阳光养殖场
- 发病日期：2026年1月26日
- 就诊日期：2026年1月27日

**病例信息**
- 禽类：白羽肉鸡，35日龄
- 患病数：约200只 / 总群10,000只
- 症状：咳嗽、精神沉郁、呼吸困难、张口呼吸、呼噜音

**诊断**
- 初步诊断：疑似新城疫
- 鉴别诊断：禽流感、传染性支气管炎

**治疗**
- 隔离病禽
- 全群饮水投抗病毒药
- 计划送检

请确认以上信息是否准确？

兽医: [语音] "对的，没问题"

AI: 好的，病历已创建并保存为版本1.0。后续有新的进展可以继续和我对话更新。
```

#### 场景2：更新病历（随访）
```
兽医: [点击病历 → AI更新]

AI: 这是1月27日创建的阳光养殖场新城疫病例，请告诉我最新的进展。

兽医: [语音] "今天1月29号过去看了，用药后情况好多了，咳嗽明显减少，死亡只有3只"

AI: 太好了！我记录一下：
- 随访日期：1月29日
- 病情好转：咳嗽症状明显减轻
- 死亡数：3只

请问现在患病数量还有多少？是否还需要继续用药？

兽医: [语音] "现在大概还有50只左右有轻微症状，准备再用三天药"

AI: 收到。检测结果出来了吗？

兽医: [语音] "出来了，确诊是新城疫"

AI: 好的，我更新了以下信息到病历：

**2026年1月29日 随访记录**
- 病情进展：明显好转
- 症状改善：咳嗽减轻
- 死亡数：3只
- 当前患病数：约50只（症状轻微）
- 实验室检测：确诊新城疫 ✓
- 治疗计划：继续用药3天

诊断已从"疑似新城疫"更新为"新城疫（实验室确诊）"

请确认信息是否正确？

兽医: [语音] "对的"

AI: 病历已更新为版本1.1。
```

## 信息提取算法

### 置信度计算

#### 日期提取
```python
def extract_date_with_confidence(text: str, reference_date: datetime) -> tuple[date, float]:
    """
    从文本中提取日期，返回日期和置信度
    """
    patterns = {
        r'(\d{4})年(\d{1,2})月(\d{1,2})[日号]': 1.0,  # 2026年1月27日
        r'(\d{1,2})月(\d{1,2})[日号]': 0.95,           # 1月27日
        r'昨天': 0.9,
        r'前天': 0.9,
        r'今天': 1.0,
        r'(\d+)天前': 0.85,
    }

    # 匹配并计算置信度
    # 返回 (日期, 置信度)
```

#### 数量提取
```python
def extract_count_with_confidence(text: str) -> tuple[int, float]:
    """
    提取数量，返回数量和置信度
    """
    patterns = {
        r'(\d+)只': 1.0,           # 明确数字
        r'大概(\d+)': 0.8,         # 大概
        r'约(\d+)': 0.8,           # 约
        r'差不多(\d+)': 0.75,      # 差不多
        r'好几百': 0.5,            # 模糊描述 - 需要确认
    }
```

#### 症状提取
```python
def extract_symptoms_with_confidence(text: str, symptom_dict: dict) -> list[tuple[str, float]]:
    """
    提取症状，返回症状列表和置信度
    """
    # 使用症状词典匹配
    # 支持同义词（咳嗽 = 咳 = 咳痰）
    # 支持模糊匹配

    symptoms = []

    # 标准症状名称
    symptom_dict = {
        '呼吸困难': ['呼吸困难', '呼吸急促', '张口呼吸', '喘'],
        '咳嗽': ['咳嗽', '咳', '咳痰'],
        '腹泻': ['拉稀', '腹泻', '稀便'],
        # ...
    }

    # 匹配并标准化
    for standard_name, aliases in symptom_dict.items():
        for alias in aliases:
            if alias in text:
                symptoms.append((standard_name, 0.95))

    return symptoms
```

### 需要确认的阈值
- 置信度 < 0.9: 必须向兽医确认
- 置信度 0.9-0.95: AI复述确认（"您说的是XX，对吗？"）
- 置信度 > 0.95: 直接记录

## 数据库设计

### conversations 表（对话表）
```sql
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    record_id UUID REFERENCES medical_records(id),
    user_id UUID REFERENCES users(id),
    status VARCHAR(20) NOT NULL,  -- active, completed, paused
    state VARCHAR(50) NOT NULL,   -- 对话状态
    context JSONB,                -- 对话上下文
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
);
```

### conversation_messages 表（对话消息表）
```sql
CREATE TABLE conversation_messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id UUID REFERENCES conversations(id),
    role VARCHAR(20) NOT NULL,    -- user, assistant, system
    content TEXT NOT NULL,
    audio_url TEXT,               -- 语音文件URL（如果有）
    extracted_info JSONB,         -- AI提取的信息
    confidence_scores JSONB,      -- 置信度
    timestamp TIMESTAMP NOT NULL
);
```

### record_versions 表（版本表）
```sql
CREATE TABLE record_versions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    record_id UUID REFERENCES medical_records(id),
    version VARCHAR(10) NOT NULL,
    created_at TIMESTAMP NOT NULL,
    created_by UUID REFERENCES users(id),
    source VARCHAR(20),           -- ai_conversation, manual_edit, import
    changes TEXT,                 -- 变更说明
    snapshot JSONB NOT NULL,      -- 完整快照
    diff JSONB                    -- 差异（可选，用于节省空间）
);
```

## API设计

### WebSocket接口
```
ws://api.domain.com/v1/conversation/ws/{conversation_id}
```

#### 消息格式

**客户端 → 服务器**
```json
{
  "type": "user_message",
  "content": "语音识别后的文字",
  "audio_url": "https://oss.../audio.mp3",
  "timestamp": "2026-01-27T10:00:00Z"
}
```

**服务器 → 客户端**
```json
{
  "type": "assistant_message",
  "content": "AI回复内容",
  "extracted_info": {
    "onset_date": "2026-01-26",
    "farm_name": "阳光养殖场"
  },
  "confidence_scores": {
    "onset_date": 0.95,
    "farm_name": 0.98
  },
  "needs_confirmation": [],
  "timestamp": "2026-01-27T10:00:05Z"
}
```

### REST API

#### 创建对话
```
POST /api/v1/conversations
```
**Request**
```json
{
  "record_id": "uuid or null",  // null表示创建新病历
  "user_id": "uuid"
}
```

**Response**
```json
{
  "conversation_id": "uuid",
  "websocket_url": "ws://...",
  "status": "active"
}
```

#### 获取对话历史
```
GET /api/v1/conversations/{conversation_id}/messages
```

#### 完成对话并保存病历
```
POST /api/v1/conversations/{conversation_id}/complete
```

## 前端实现

### 小程序语音录制组件
```vue
<template>
  <view class="voice-recorder">
    <button @touchstart="startRecord" @touchend="stopRecord">
      按住说话
    </button>
    <view v-if="recording" class="recording-indicator">
      录音中...
    </view>
  </view>
</template>

<script>
export default {
  data() {
    return {
      recording: false,
      recorderManager: null
    }
  },
  mounted() {
    this.recorderManager = wx.getRecorderManager()

    this.recorderManager.onStop((res) => {
      // 上传音频
      this.uploadAudio(res.tempFilePath)
    })
  },
  methods: {
    startRecord() {
      this.recording = true
      this.recorderManager.start({
        duration: 60000,
        format: 'mp3'
      })
    },
    stopRecord() {
      this.recording = false
      this.recorderManager.stop()
    },
    async uploadAudio(filePath) {
      // 1. 获取OSS上传凭证
      // 2. 上传到OSS
      // 3. 调用语音识别
      // 4. 发送到WebSocket
    }
  }
}
</script>
```

### 对话界面组件
```vue
<template>
  <view class="conversation-view">
    <scroll-view class="message-list">
      <view v-for="msg in messages" :key="msg.id"
            :class="['message', msg.role]">
        <view class="content">{{ msg.content }}</view>
        <view v-if="msg.extracted_info" class="extracted-info">
          <text>已提取：{{ formatExtractedInfo(msg.extracted_info) }}</text>
        </view>
      </view>
    </scroll-view>

    <VoiceRecorder @send="sendMessage" />
  </view>
</template>
```

## 性能优化

### 语音识别优化
- 使用流式识别，边说边转文字
- 客户端预处理（降噪）
- 音频压缩后上传

### AI响应优化
- 使用流式输出（SSE或WebSocket streaming）
- 关键信息优先提取
- 缓存常见问题的回复模板

### 成本控制
- 语音文件压缩（16kHz, 单声道）
- AI使用合适的模型（GPT-4o-mini在简单场景）
- 缓存已识别的养殖场、症状等常见实体

## 测试方案

### 单元测试
- 日期提取准确性
- 数量提取准确性
- 症状匹配准确性
- 置信度计算正确性

### 集成测试
- WebSocket连接稳定性
- 语音识别准确率
- AI信息提取准确率
- 版本创建正确性

### 用户测试
- 兽医使用体验
- 对话流畅度
- 信息完整性
- 错误纠正能力
