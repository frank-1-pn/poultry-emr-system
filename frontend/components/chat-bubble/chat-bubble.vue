<template>
  <view class="bubble-wrapper" :class="isUser ? 'bubble-right' : 'bubble-left'">
    <view class="avatar" v-if="!isUser">
      <text class="avatar-text">AI</text>
    </view>
    <view class="bubble" :class="isUser ? 'user-bubble' : 'ai-bubble'">
      <text class="bubble-content">{{ message.content }}</text>
      <text class="bubble-time">{{ formatTime(message.created_at) }}</text>
    </view>
    <view class="avatar" v-if="isUser">
      <text class="avatar-text">我</text>
    </view>
  </view>
</template>

<script>
export default {
  name: 'ChatBubble',
  props: {
    message: { type: Object, required: true },
  },
  computed: {
    isUser() {
      return this.message.role === 'user'
    },
  },
  methods: {
    formatTime(dateStr) {
      if (!dateStr) return ''
      const d = new Date(dateStr)
      const h = String(d.getHours()).padStart(2, '0')
      const m = String(d.getMinutes()).padStart(2, '0')
      return `${h}:${m}`
    },
  },
}
</script>

<style lang="scss" scoped>
.bubble-wrapper {
  display: flex;
  align-items: flex-start;
  margin-bottom: 24rpx;
  padding: 0 16rpx;
}
.bubble-right {
  justify-content: flex-end;
}
.bubble-left {
  justify-content: flex-start;
}
.avatar {
  width: 64rpx;
  height: 64rpx;
  border-radius: 50%;
  background: #2e7d32;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.bubble-right .avatar {
  background: #1565c0;
  margin-left: 12rpx;
}
.bubble-left .avatar {
  margin-right: 12rpx;
}
.avatar-text {
  color: #fff;
  font-size: 24rpx;
  font-weight: 600;
}
.bubble {
  max-width: 70%;
  padding: 20rpx 24rpx;
  border-radius: 16rpx;
  position: relative;
}
.user-bubble {
  background: #e3f2fd;
  border-top-right-radius: 4rpx;
}
.ai-bubble {
  background: #fff;
  border-top-left-radius: 4rpx;
  box-shadow: 0 2rpx 8rpx rgba(0, 0, 0, 0.06);
}
.bubble-content {
  font-size: 28rpx;
  color: #333;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-all;
}
.bubble-time {
  display: block;
  font-size: 20rpx;
  color: #999;
  margin-top: 8rpx;
  text-align: right;
}
</style>
