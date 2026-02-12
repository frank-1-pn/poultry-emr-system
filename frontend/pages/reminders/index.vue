<template>
  <view class="reminders-page">
    <!-- 筛选 -->
    <scroll-view scroll-x class="filter-row">
      <view
        v-for="f in filters"
        :key="f.value"
        class="filter-tag"
        :class="{ active: currentFilter === f.value }"
        @click="setFilter(f.value)"
      >
        <text>{{ f.label }}</text>
      </view>
    </scroll-view>

    <!-- 按日期分组 -->
    <scroll-view scroll-y class="reminder-list">
      <template v-if="remindersStore.groupedByDate.length">
        <view v-for="[date, items] in remindersStore.groupedByDate" :key="date" class="date-group">
          <text class="date-label">{{ formatDateLabel(date) }}</text>
          <reminder-card
            v-for="r in items"
            :key="r.id"
            :reminder="r"
            @confirm="handleConfirm"
            @dismiss="handleDismiss"
          />
        </view>
      </template>
      <empty-state v-else-if="!remindersStore.loading" icon="🔔" text="暂无提醒" sub-text="治疗记录确认后会自动生成提醒" />
    </scroll-view>
  </view>
</template>

<script>
import { useRemindersStore } from '../../store/reminders'
import { formatDate } from '../../utils/format'
import ReminderCard from '../../components/reminder-card/reminder-card.vue'
import EmptyState from '../../components/empty-state/empty-state.vue'

export default {
  components: { ReminderCard, EmptyState },
  setup() {
    return { remindersStore: useRemindersStore() }
  },
  data() {
    return {
      currentFilter: '',
      filters: [
        { label: '全部', value: '' },
        { label: '待处理', value: 'pending' },
        { label: '已确认', value: 'confirmed' },
        { label: '已忽略', value: 'dismissed' },
      ],
    }
  },
  onShow() {
    this.remindersStore.fetchReminders({ status: this.currentFilter })
  },
  methods: {
    setFilter(val) {
      this.currentFilter = val
      this.remindersStore.fetchReminders({ status: val })
    },
    formatDateLabel(dateStr) {
      const today = formatDate(new Date().toISOString())
      if (dateStr === today) return '今天'
      const tomorrow = new Date()
      tomorrow.setDate(tomorrow.getDate() + 1)
      if (dateStr === formatDate(tomorrow.toISOString())) return '明天'
      return dateStr
    },
    async handleConfirm(id) {
      await this.remindersStore.confirm(id)
      uni.showToast({ title: '已确认', icon: 'success' })
    },
    async handleDismiss(id) {
      await this.remindersStore.dismiss(id)
      uni.showToast({ title: '已忽略', icon: 'none' })
    },
  },
}
</script>

<style lang="scss" scoped>
.reminders-page {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: #f5f5f5;
}
.filter-row {
  white-space: nowrap;
  padding: 16rpx 24rpx;
  background: #fff;
  border-bottom: 1rpx solid #f0f0f0;
}
.filter-tag {
  display: inline-block;
  padding: 8rpx 28rpx;
  border-radius: 24rpx;
  background: #f5f5f5;
  margin-right: 16rpx;
  font-size: 26rpx;
  color: #666;
}
.filter-tag.active {
  background: #e8f5e9;
  color: #2e7d32;
  font-weight: 500;
}
.reminder-list {
  flex: 1;
  padding: 24rpx;
  padding-bottom: 120rpx;
}
.date-group {
  margin-bottom: 24rpx;
}
.date-label {
  font-size: 28rpx;
  font-weight: 600;
  color: #333;
  margin-bottom: 12rpx;
  display: block;
}
</style>
