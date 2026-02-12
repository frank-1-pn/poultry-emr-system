<template>
  <view class="session-card" @click="$emit('click')">
    <view class="card-header">
      <text class="session-no">Session #{{ session.session_number || 1 }}</text>
      <view class="status-badge" :class="'status-' + session.status">
        <text class="status-text">{{ statusLabel(session.status) }}</text>
      </view>
    </view>

    <!-- 关联病历摘要 -->
    <view class="record-summary" v-if="session.record">
      <text class="record-no">{{ session.record.record_no }}</text>
      <text class="record-info">
        {{ session.record.poultry_type }}
        <template v-if="session.record.primary_diagnosis">
          - {{ session.record.primary_diagnosis }}
        </template>
      </text>
    </view>

    <!-- 养殖场 -->
    <view class="farm-row" v-if="session.farm">
      <text class="farm-name">{{ session.farm.name }}</text>
    </view>

    <!-- 摘要 -->
    <view class="summary-row" v-if="session.summary">
      <text class="summary-text">{{ session.summary }}</text>
    </view>

    <!-- 标签 -->
    <view class="tag-row" v-if="session.tags && session.tags.length">
      <text class="tag" v-for="(t, i) in session.tags" :key="i">{{ t }}</text>
    </view>

    <view class="card-footer">
      <text class="time-text">{{ timeAgo(session.created_at) }}</text>
    </view>
  </view>
</template>

<script>
import { statusLabel, timeAgo } from '../../utils/format'

export default {
  props: {
    session: { type: Object, required: true },
  },
  emits: ['click'],
  methods: { statusLabel, timeAgo },
}
</script>

<style lang="scss" scoped>
.session-card {
  background: #fff;
  border-radius: 16rpx;
  padding: 24rpx;
  margin-bottom: 16rpx;
  box-shadow: 0 2rpx 12rpx rgba(0, 0, 0, 0.04);
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12rpx;
}
.session-no {
  font-size: 30rpx;
  font-weight: 600;
  color: #333;
}
.status-badge {
  padding: 4rpx 16rpx;
  border-radius: 20rpx;
}
.status-active { background: #e8f5e9; }
.status-active .status-text { color: #2e7d32; }
.status-completed { background: #e3f2fd; }
.status-completed .status-text { color: #1565c0; }
.status-paused { background: #fff3e0; }
.status-paused .status-text { color: #e65100; }
.status-cancelled { background: #fce4ec; }
.status-cancelled .status-text { color: #c62828; }
.status-text { font-size: 22rpx; }
.record-summary {
  margin-bottom: 8rpx;
}
.record-no {
  font-size: 24rpx;
  color: #2e7d32;
  font-weight: 500;
  margin-right: 12rpx;
}
.record-info {
  font-size: 24rpx;
  color: #666;
}
.farm-row {
  margin-bottom: 8rpx;
}
.farm-name {
  font-size: 24rpx;
  color: #1565c0;
}
.summary-row {
  margin-bottom: 8rpx;
  padding: 8rpx 12rpx;
  background: #f5f5f5;
  border-radius: 8rpx;
}
.summary-text {
  font-size: 24rpx;
  color: #555;
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.tag-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8rpx;
  margin-bottom: 8rpx;
}
.tag {
  background: #f3e5f5;
  color: #7b1fa2;
  padding: 4rpx 16rpx;
  border-radius: 16rpx;
  font-size: 22rpx;
}
.card-footer {
  display: flex;
  justify-content: flex-end;
}
.time-text {
  font-size: 22rpx;
  color: #999;
}
</style>
