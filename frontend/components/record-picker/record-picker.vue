<template>
  <view class="record-picker">
    <scroll-view scroll-y class="record-list">
      <view
        v-for="r in records"
        :key="r.id"
        class="record-item"
        :class="{ selected: selectedId === r.id }"
        @click="$emit('select', r)"
      >
        <view class="record-header">
          <text class="record-no">{{ r.record_no }}</text>
          <text class="record-status">{{ statusLabel(r.status) }}</text>
        </view>
        <text class="record-info">
          {{ r.poultry_type }}
          <template v-if="r.primary_diagnosis"> - {{ r.primary_diagnosis }}</template>
        </text>
      </view>
      <view class="empty-tip" v-if="!records.length && !loading">
        <text>暂无病历</text>
      </view>
    </scroll-view>
  </view>
</template>

<script>
import { get } from '../../utils/request'
import { statusLabel } from '../../utils/format'

export default {
  props: {
    farmId: { type: String, default: null },
    selectedId: { type: String, default: null },
  },
  emits: ['select'],
  data() {
    return {
      records: [],
      loading: false,
    }
  },
  watch: {
    farmId: {
      handler() { this.fetchRecords() },
      immediate: true,
    },
  },
  methods: {
    statusLabel,
    async fetchRecords() {
      this.loading = true
      try {
        const params = new URLSearchParams({ page_size: '50' })
        if (this.farmId) {
          params.set('farm_id', this.farmId)
        }
        const res = await get(`/records?${params.toString()}`)
        this.records = res.items || []
      } catch (e) {
        this.records = []
      } finally {
        this.loading = false
      }
    },
  },
}
</script>

<style lang="scss" scoped>
.record-picker {
  width: 100%;
}
.record-list {
  max-height: 500rpx;
}
.record-item {
  padding: 20rpx;
  border-radius: 12rpx;
  margin-bottom: 8rpx;
  background: #fafafa;
  border: 2rpx solid transparent;
}
.record-item.selected {
  background: #e8f5e9;
  border-color: #2e7d32;
}
.record-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4rpx;
}
.record-no {
  font-size: 26rpx;
  font-weight: 500;
  color: #2e7d32;
}
.record-status {
  font-size: 22rpx;
  color: #999;
}
.record-info {
  font-size: 24rpx;
  color: #666;
}
.empty-tip {
  text-align: center;
  padding: 40rpx;
  color: #999;
  font-size: 26rpx;
}
</style>
