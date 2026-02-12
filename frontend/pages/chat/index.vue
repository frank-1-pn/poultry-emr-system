<template>
  <view class="chat-page">
    <!-- 顶部 session 信息 -->
    <view class="session-bar" v-if="chatStore.conversation">
      <text class="session-text">
        Session #{{ chatStore.conversation.session_number || 1 }}
      </text>
      <text class="session-status">{{ statusLabel(chatStore.conversation.status) }}</text>
    </view>

    <!-- 关联病历卡片 -->
    <view
      class="record-card"
      v-if="linkedRecord"
      @click="goRecordDetail(linkedRecord.id)"
    >
      <view class="record-card-header">
        <text class="record-card-no">{{ linkedRecord.record_no }}</text>
        <text class="record-card-type">{{ linkedRecord.poultry_type }}</text>
      </view>
      <text class="record-card-diag" v-if="linkedRecord.primary_diagnosis">
        {{ linkedRecord.primary_diagnosis }}
      </text>
    </view>

    <!-- 相似病例面板 -->
    <view class="similar-panel" v-if="similarCases.length" @click="showSimilar = !showSimilar">
      <view class="similar-header">
        <text class="similar-title">相似病例参考 ({{ similarCases.length }})</text>
        <text class="similar-toggle">{{ showSimilar ? '收起' : '展开' }}</text>
      </view>
      <view v-if="showSimilar" class="similar-list">
        <view
          v-for="c in similarCases"
          :key="c.id"
          class="similar-item"
          @click.stop="goRecordDetail(c.id)"
        >
          <view class="similar-item-row">
            <text class="similar-no">{{ c.record_no }}</text>
            <text class="similar-score">{{ (c.similarity * 100).toFixed(0) }}%</text>
          </view>
          <text class="similar-diag">
            {{ c.poultry_type }}
            <template v-if="c.primary_diagnosis"> - {{ c.primary_diagnosis }}</template>
          </text>
        </view>
      </view>
    </view>

    <!-- 消息列表 -->
    <scroll-view
      scroll-y
      class="message-list"
      :scroll-into-view="scrollTarget"
      scroll-with-animation
    >
      <chat-bubble
        v-for="(msg, i) in chatStore.messages"
        :key="msg.id || i"
        :message="msg"
      />
      <view v-if="chatStore.sending" class="typing-indicator">
        <text class="typing-text">AI 正在思考...</text>
      </view>
      <view :id="'msg-bottom'" style="height: 20rpx;"></view>
    </scroll-view>

    <!-- 完成确认弹窗 -->
    <view class="confirm-bar" v-if="showConfirmBar">
      <text class="confirm-text">病历信息已收集完毕，是否确认保存？</text>
      <view class="confirm-actions">
        <button class="btn-confirm" @click="handleConfirm">确认保存</button>
        <button class="btn-cancel" @click="showConfirmBar = false">继续编辑</button>
      </view>
    </view>

    <!-- 输入区 -->
    <view class="input-bar" v-if="chatStore.conversation?.status === 'active'">
      <input
        v-model="inputText"
        class="msg-input"
        placeholder="描述症状或回答问题..."
        :disabled="chatStore.sending"
        @confirm="sendMessage"
      />
      <button
        class="send-btn"
        :disabled="!inputText.trim() || chatStore.sending"
        @click="sendMessage"
      >
        发送
      </button>
    </view>

    <!-- 完成后信息 -->
    <view class="completed-bar" v-if="chatStore.conversation?.status === 'completed'">
      <text class="completed-text">对话已完成</text>
      <button class="btn-primary-sm" @click="goRecord">查看病历</button>
    </view>
  </view>
</template>

<script>
import { useChatStore } from '../../store/chat'
import { statusLabel } from '../../utils/format'
import ChatBubble from '../../components/chat-bubble/chat-bubble.vue'

export default {
  components: { ChatBubble },
  setup() {
    return { chatStore: useChatStore() }
  },
  data() {
    return {
      inputText: '',
      scrollTarget: '',
      showConfirmBar: false,
      recordId: null,
      similarCases: [],
      showSimilar: false,
    }
  },
  computed: {
    linkedRecord() {
      const conv = this.chatStore.conversation
      if (!conv) return null
      // 优先用 conversation 上的 record 嵌套对象
      if (conv.record) return conv.record
      return null
    },
  },
  async onLoad(query) {
    this.chatStore.clearChat()

    if (query.conversationId) {
      // 恢复已有会话
      await this.chatStore.loadConversation(query.conversationId)
    } else {
      // 兼容旧参数: 从 recordId 创建新会话
      this.recordId = query.recordId || null
      await this.chatStore.createConversation(this.recordId)
    }
    this.scrollToBottom()
  },
  onUnload() {
    // 不清除，允许返回时保持状态
  },
  methods: {
    statusLabel,
    async sendMessage() {
      const text = this.inputText.trim()
      if (!text) return
      this.inputText = ''
      const res = await this.chatStore.sendMessage(text)
      this.scrollToBottom()

      // 更新相似病例
      if (res?.similar_cases) {
        this.similarCases = res.similar_cases
      }

      // 检查是否需要确认
      if (res?.completeness) {
        const required = ['poultry_type', 'visit_date', 'symptoms']
        const allDone = required.every(k => res.completeness[k])
        if (allDone && this.chatStore.conversation.state === 'confirming') {
          this.showConfirmBar = true
        }
      }
    },
    async handleConfirm() {
      this.showConfirmBar = false
      const res = await this.chatStore.confirmRecord(true)
      if (res?.record_id) {
        uni.showToast({ title: '病历已保存', icon: 'success' })
      }
    },
    goRecord() {
      const conv = this.chatStore.conversation
      if (conv?.record_id) {
        uni.redirectTo({ url: `/pages/records/detail?id=${conv.record_id}` })
      }
    },
    goRecordDetail(recordId) {
      uni.navigateTo({ url: `/pages/records/detail?id=${recordId}` })
    },
    scrollToBottom() {
      this.$nextTick(() => {
        this.scrollTarget = 'msg-bottom'
      })
    },
  },
}
</script>

<style lang="scss" scoped>
.chat-page {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: #f5f5f5;
}
.session-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12rpx 24rpx;
  background: #e8f5e9;
  border-bottom: 1rpx solid #c8e6c9;
}
.session-text {
  font-size: 24rpx;
  color: #2e7d32;
  font-weight: 500;
}
.session-status {
  font-size: 22rpx;
  color: #666;
}
.record-card {
  margin: 12rpx 24rpx 0;
  padding: 16rpx 20rpx;
  background: #fff;
  border-radius: 12rpx;
  border-left: 6rpx solid #2e7d32;
  box-shadow: 0 2rpx 8rpx rgba(0, 0, 0, 0.04);
}
.record-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.record-card-no {
  font-size: 26rpx;
  font-weight: 600;
  color: #2e7d32;
}
.record-card-type {
  font-size: 24rpx;
  color: #666;
}
.record-card-diag {
  font-size: 24rpx;
  color: #333;
  margin-top: 4rpx;
}
.similar-panel {
  background: #fff8e1;
  margin: 0 24rpx 8rpx;
  border-radius: 12rpx;
  padding: 16rpx 20rpx;
  border-left: 6rpx solid #ff9800;
}
.similar-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.similar-title {
  font-size: 26rpx;
  font-weight: 600;
  color: #e65100;
}
.similar-toggle {
  font-size: 22rpx;
  color: #999;
}
.similar-list {
  margin-top: 12rpx;
}
.similar-item {
  padding: 12rpx 0;
  border-top: 1rpx solid rgba(255, 152, 0, 0.2);
}
.similar-item-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.similar-no {
  font-size: 24rpx;
  color: #2e7d32;
  font-weight: 500;
}
.similar-score {
  font-size: 22rpx;
  color: #ff9800;
  font-weight: 600;
}
.similar-diag {
  font-size: 22rpx;
  color: #666;
  margin-top: 4rpx;
}
.message-list {
  flex: 1;
  padding: 24rpx 8rpx;
}
.typing-indicator {
  padding: 12rpx 24rpx;
}
.typing-text {
  font-size: 24rpx;
  color: #999;
}
.input-bar {
  display: flex;
  align-items: center;
  padding: 16rpx 20rpx;
  background: #fff;
  border-top: 1rpx solid #f0f0f0;
  padding-bottom: calc(16rpx + env(safe-area-inset-bottom));
  gap: 12rpx;
}
.msg-input {
  flex: 1;
  background: #f5f5f5;
  border-radius: 32rpx;
  padding: 16rpx 24rpx;
  font-size: 28rpx;
}
.send-btn {
  background: #2e7d32;
  color: #fff;
  border: none;
  border-radius: 32rpx;
  padding: 16rpx 32rpx;
  font-size: 28rpx;
  flex-shrink: 0;
}
.send-btn[disabled] {
  opacity: 0.5;
}
.confirm-bar {
  background: #fff;
  padding: 24rpx;
  border-top: 1rpx solid #f0f0f0;
}
.confirm-text {
  font-size: 28rpx;
  color: #333;
  margin-bottom: 16rpx;
  display: block;
}
.confirm-actions {
  display: flex;
  gap: 16rpx;
}
.btn-confirm {
  flex: 1;
  background: #2e7d32;
  color: #fff;
  border: none;
  border-radius: 12rpx;
  padding: 16rpx;
  font-size: 28rpx;
}
.btn-cancel {
  flex: 1;
  background: #f5f5f5;
  color: #666;
  border: none;
  border-radius: 12rpx;
  padding: 16rpx;
  font-size: 28rpx;
}
.completed-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20rpx 24rpx;
  background: #fff;
  border-top: 1rpx solid #f0f0f0;
  padding-bottom: calc(20rpx + env(safe-area-inset-bottom));
}
.completed-text {
  font-size: 28rpx;
  color: #999;
}
.btn-primary-sm {
  background: #2e7d32;
  color: #fff;
  border: none;
  border-radius: 12rpx;
  padding: 12rpx 28rpx;
  font-size: 26rpx;
}
</style>
