<template>
  <view class="reminder-card" :class="'status-' + reminder.status">
    <view class="reminder-header">
      <text class="reminder-title">{{ reminder.content.title || '治疗提醒' }}</text>
      <text class="reminder-date">{{ reminder.reminder_date }}</text>
    </view>
    <view class="reminder-body">
      <text class="record-no" v-if="reminder.content.record_no">
        病历: {{ reminder.content.record_no }}
      </text>
      <text class="reminder-message">{{ reminder.content.message }}</text>
    </view>
    <view class="reminder-actions" v-if="reminder.status === 'pending'">
      <button class="btn-confirm" @click.stop="$emit('confirm', reminder.id)">已处理</button>
      <button class="btn-dismiss" @click.stop="$emit('dismiss', reminder.id)">忽略</button>
    </view>
    <view class="reminder-done" v-else>
      <text class="done-text">{{ reminder.status === 'confirmed' ? '已确认' : '已忽略' }}</text>
    </view>
  </view>
</template>

<script>
export default {
  name: 'ReminderCard',
  props: {
    reminder: { type: Object, required: true },
  },
  emits: ['confirm', 'dismiss'],
}
</script>

<style lang="scss" scoped>
.reminder-card {
  background: #fff;
  border-radius: 16rpx;
  padding: 24rpx;
  margin-bottom: 16rpx;
  border-left: 6rpx solid #2e7d32;
  box-shadow: 0 2rpx 12rpx rgba(0, 0, 0, 0.04);
}
.status-confirmed {
  border-left-color: #9e9e9e;
  opacity: 0.7;
}
.status-dismissed {
  border-left-color: #bdbdbd;
  opacity: 0.5;
}
.reminder-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 12rpx;
}
.reminder-title {
  font-size: 28rpx;
  font-weight: 600;
  color: #333;
}
.reminder-date {
  font-size: 24rpx;
  color: #999;
}
.record-no {
  font-size: 24rpx;
  color: #2e7d32;
  margin-bottom: 8rpx;
}
.reminder-message {
  font-size: 26rpx;
  color: #666;
  line-height: 1.6;
}
.reminder-actions {
  display: flex;
  gap: 16rpx;
  margin-top: 16rpx;
}
.btn-confirm {
  flex: 1;
  background: #2e7d32;
  color: #fff;
  border: none;
  border-radius: 8rpx;
  font-size: 26rpx;
  padding: 12rpx 0;
}
.btn-dismiss {
  flex: 1;
  background: #f5f5f5;
  color: #666;
  border: none;
  border-radius: 8rpx;
  font-size: 26rpx;
  padding: 12rpx 0;
}
.done-text {
  font-size: 24rpx;
  color: #999;
  margin-top: 8rpx;
}
</style>
