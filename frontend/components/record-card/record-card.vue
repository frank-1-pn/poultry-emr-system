<template>
  <view class="record-card" @click="$emit('click', record)">
    <view class="card-header">
      <text class="record-no">{{ record.record_no }}</text>
      <view class="severity-badge" :style="{ backgroundColor: severityBg }">
        <text class="severity-text" :style="{ color: severityClr }">{{ severityTxt }}</text>
      </view>
    </view>
    <view class="card-body">
      <view class="info-row">
        <text class="label">禽类:</text>
        <rich-text v-if="highlight" class="value" :nodes="highlightText(record.poultry_type)" />
        <text v-else class="value">{{ record.poultry_type }}</text>
      </view>
      <view class="info-row" v-if="record.primary_diagnosis">
        <text class="label">诊断:</text>
        <rich-text v-if="highlight" class="value" :nodes="highlightText(record.primary_diagnosis)" />
        <text v-else class="value">{{ record.primary_diagnosis }}</text>
      </view>
      <view class="info-row">
        <text class="label">就诊:</text>
        <text class="value">{{ formatDate(record.visit_date) }}</text>
      </view>
    </view>
    <view class="card-footer">
      <text class="status-tag" :class="'status-' + record.status">{{ statusLabel(record.status) }}</text>
      <text class="time-ago">{{ timeAgo(record.created_at) }}</text>
    </view>
  </view>
</template>

<script>
import { formatDate, timeAgo, severityLabel, severityColor, statusLabel } from '../../utils/format'

export default {
  name: 'RecordCard',
  props: {
    record: { type: Object, required: true },
    highlight: { type: String, default: '' },
  },
  emits: ['click'],
  computed: {
    severityTxt() { return severityLabel(this.record.severity) },
    severityClr() { return severityColor(this.record.severity) },
    severityBg() {
      const c = severityColor(this.record.severity)
      return c + '18'
    },
  },
  methods: {
    formatDate,
    timeAgo,
    statusLabel,
    highlightText(text) {
      if (!text || !this.highlight) return text || ''
      const kw = this.highlight.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
      const regex = new RegExp(`(${kw})`, 'gi')
      return text.replace(regex, '<span style="background:#fff9c4;color:#f57f17;font-weight:500;">$1</span>')
    },
  },
}
</script>

<style lang="scss" scoped>
.record-card {
  background: #fff;
  border-radius: 16rpx;
  padding: 24rpx;
  margin-bottom: 20rpx;
  box-shadow: 0 2rpx 12rpx rgba(0, 0, 0, 0.04);
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16rpx;
}
.record-no {
  font-size: 30rpx;
  font-weight: 600;
  color: #333;
}
.severity-badge {
  padding: 4rpx 16rpx;
  border-radius: 20rpx;
}
.severity-text {
  font-size: 22rpx;
  font-weight: 500;
}
.card-body {
  margin-bottom: 16rpx;
}
.info-row {
  display: flex;
  margin-bottom: 8rpx;
}
.label {
  color: #999;
  font-size: 26rpx;
  width: 100rpx;
}
.value {
  color: #333;
  font-size: 26rpx;
  flex: 1;
}
.card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-top: 1rpx solid #f0f0f0;
  padding-top: 12rpx;
}
.status-tag {
  font-size: 22rpx;
  padding: 4rpx 12rpx;
  border-radius: 8rpx;
  background: #e8f5e9;
  color: #2e7d32;
}
.status-completed { background: #e3f2fd; color: #1565c0; }
.status-draft { background: #fff3e0; color: #e65100; }
.time-ago {
  font-size: 22rpx;
  color: #999;
}
</style>
