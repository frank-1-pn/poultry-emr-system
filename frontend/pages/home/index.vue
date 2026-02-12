<template>
  <view class="home-page">
    <!-- 顶部欢迎区 -->
    <view class="welcome-section">
      <view class="welcome-left">
        <text class="welcome-text">你好，{{ userStore.userInfo?.full_name || '兽医' }}</text>
        <text class="welcome-date">{{ todayStr }}</text>
      </view>
      <view class="welcome-right" @click="goChat">
        <text class="quick-btn-text">AI 问诊</text>
      </view>
    </view>

    <!-- 统计卡片 -->
    <view class="stats-row">
      <view class="stat-card">
        <text class="stat-num">{{ recordsStore.total }}</text>
        <text class="stat-label">病历总数</text>
      </view>
      <view class="stat-card stat-blue">
        <text class="stat-num">{{ sessionsStore.total }}</text>
        <text class="stat-label">会话数</text>
      </view>
      <view class="stat-card stat-orange">
        <text class="stat-num">{{ remindersStore.pendingCount }}</text>
        <text class="stat-label">待处理</text>
      </view>
    </view>

    <!-- 今日提醒 -->
    <view class="section" v-if="todayReminders.length">
      <view class="section-header">
        <text class="section-title">今日提醒</text>
        <text class="section-more" @click="goReminders">查看全部</text>
      </view>
      <reminder-card
        v-for="r in todayReminders"
        :key="r.id"
        :reminder="r"
        @confirm="handleConfirm"
        @dismiss="handleDismiss"
      />
    </view>

    <!-- 最近会话 -->
    <view class="section" v-if="sessionsStore.list.length">
      <view class="section-header">
        <text class="section-title">最近会话</text>
        <text class="section-more" @click="goSessions">查看全部</text>
      </view>
      <session-card
        v-for="s in sessionsStore.list.slice(0, 3)"
        :key="s.id"
        :session="s"
        @click="resumeSession(s)"
      />
    </view>

    <!-- 最近病历 -->
    <view class="section">
      <view class="section-header">
        <text class="section-title">最近病历</text>
        <text class="section-more" @click="goRecords">查看全部</text>
      </view>
      <template v-if="recordsStore.list.length">
        <record-card
          v-for="r in recordsStore.list.slice(0, 5)"
          :key="r.id"
          :record="r"
          @click="goDetail(r)"
        />
      </template>
      <empty-state v-else text="暂无病历" sub-text="点击右上角开始 AI 问诊" />
    </view>
  </view>
</template>

<script>
import { useUserStore } from '../../store/user'
import { useRecordsStore } from '../../store/records'
import { useRemindersStore } from '../../store/reminders'
import { useSessionsStore } from '../../store/sessions'
import { formatDate } from '../../utils/format'
import { isLoggedIn } from '../../utils/auth'
import RecordCard from '../../components/record-card/record-card.vue'
import ReminderCard from '../../components/reminder-card/reminder-card.vue'
import SessionCard from '../../components/session-card/session-card.vue'
import EmptyState from '../../components/empty-state/empty-state.vue'

export default {
  components: { RecordCard, ReminderCard, SessionCard, EmptyState },
  setup() {
    return {
      userStore: useUserStore(),
      recordsStore: useRecordsStore(),
      remindersStore: useRemindersStore(),
      sessionsStore: useSessionsStore(),
    }
  },
  computed: {
    todayStr() {
      return formatDate(new Date().toISOString())
    },
    todayReminders() {
      const today = this.todayStr
      return this.remindersStore.list.filter(
        r => r.reminder_date === today && r.status === 'pending'
      ).slice(0, 3)
    },
  },
  onShow() {
    if (!isLoggedIn()) {
      uni.reLaunch({ url: '/pages/login/index' })
      return
    }
    this.loadData()
  },
  methods: {
    async loadData() {
      try {
        await Promise.all([
          this.userStore.fetchProfile(),
          this.recordsStore.fetchRecords({ page: 1, pageSize: 5 }),
          this.remindersStore.fetchReminders(),
          this.sessionsStore.fetchSessions(),
        ])
      } catch (e) {
        // 401 处理在 request.js 中
      }
    },
    goChat() {
      uni.navigateTo({ url: '/pages/chat/index' })
    },
    goRecords() {
      uni.switchTab({ url: '/pages/records/index' })
    },
    goReminders() {
      uni.switchTab({ url: '/pages/reminders/index' })
    },
    goSessions() {
      uni.navigateTo({ url: '/pages/sessions/index' })
    },
    resumeSession(session) {
      uni.navigateTo({ url: `/pages/chat/index?session_id=${session.id}` })
    },
    goDetail(record) {
      uni.navigateTo({ url: `/pages/records/detail?id=${record.id}` })
    },
    async handleConfirm(id) {
      await this.remindersStore.confirm(id)
    },
    async handleDismiss(id) {
      await this.remindersStore.dismiss(id)
    },
  },
}
</script>

<style lang="scss" scoped>
.home-page {
  padding: 24rpx;
  padding-bottom: 120rpx;
}
.welcome-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: linear-gradient(135deg, #2e7d32, #43a047);
  border-radius: 20rpx;
  padding: 32rpx;
  margin-bottom: 24rpx;
  color: #fff;
}
.welcome-text {
  font-size: 34rpx;
  font-weight: 600;
}
.welcome-date {
  font-size: 24rpx;
  opacity: 0.8;
  margin-top: 8rpx;
}
.welcome-right {
  background: rgba(255, 255, 255, 0.2);
  border-radius: 12rpx;
  padding: 16rpx 28rpx;
}
.quick-btn-text {
  color: #fff;
  font-size: 28rpx;
  font-weight: 500;
}
.stats-row {
  display: flex;
  gap: 20rpx;
  margin-bottom: 32rpx;
}
.stat-card {
  flex: 1;
  background: #fff;
  border-radius: 16rpx;
  padding: 28rpx;
  text-align: center;
  box-shadow: 0 2rpx 12rpx rgba(0, 0, 0, 0.04);
}
.stat-num {
  font-size: 48rpx;
  font-weight: 700;
  color: #2e7d32;
  display: block;
}
.stat-blue .stat-num {
  color: #1976d2;
}
.stat-orange .stat-num {
  color: #ff9800;
}
.stat-label {
  font-size: 24rpx;
  color: #999;
  margin-top: 4rpx;
}
.section {
  margin-bottom: 32rpx;
}
.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16rpx;
}
.section-title {
  font-size: 32rpx;
  font-weight: 600;
  color: #333;
}
.section-more {
  font-size: 26rpx;
  color: #2e7d32;
}
</style>
