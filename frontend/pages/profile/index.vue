<template>
  <view class="profile-page">
    <!-- 头像区 -->
    <view class="profile-header">
      <view class="avatar-circle">
        <text class="avatar-letter">{{ avatarLetter }}</text>
      </view>
      <text class="user-name">{{ userStore.userInfo?.full_name || '用户' }}</text>
      <text class="user-role">{{ roleLabel }}</text>
    </view>

    <!-- 菜单 -->
    <view class="menu-section">
      <view class="menu-item" @click="goMemory">
        <text class="menu-icon">🧠</text>
        <text class="menu-text">AI 记忆管理</text>
        <text class="menu-arrow">›</text>
      </view>
      <view class="menu-item" @click="goReminders">
        <text class="menu-icon">🔔</text>
        <text class="menu-text">提醒设置</text>
        <text class="menu-arrow">›</text>
      </view>
      <view class="menu-item">
        <text class="menu-icon">📊</text>
        <text class="menu-text">使用统计</text>
        <text class="menu-arrow">›</text>
      </view>
      <view class="menu-item">
        <text class="menu-icon">⚙️</text>
        <text class="menu-text">系统设置</text>
        <text class="menu-arrow">›</text>
      </view>
    </view>

    <!-- AI 记忆信息 -->
    <view class="card" v-if="memory">
      <text class="section-label">AI 记忆摘要</text>
      <view v-if="memory.content.farm_context && Object.keys(memory.content.farm_context).length">
        <text class="memory-label">养殖场信息</text>
        <view v-for="(v, k) in memory.content.farm_context" :key="k" class="memory-item">
          <text class="memory-key">{{ k }}:</text>
          <text class="memory-value">{{ v }}</text>
        </view>
      </view>
      <view v-if="memory.content.preferences && Object.keys(memory.content.preferences).length">
        <text class="memory-label">偏好设置</text>
        <view v-for="(v, k) in memory.content.preferences" :key="k" class="memory-item">
          <text class="memory-key">{{ k }}:</text>
          <text class="memory-value">{{ v }}</text>
        </view>
      </view>
      <text class="memory-update" v-if="memory.updated_at">
        更新于: {{ formatDateTime(memory.updated_at) }}
      </text>
    </view>

    <!-- 退出登录 -->
    <button class="logout-btn" @click="handleLogout">退出登录</button>
  </view>
</template>

<script>
import { useUserStore } from '../../store/user'
import { get } from '../../utils/request'
import { formatDateTime } from '../../utils/format'

export default {
  setup() {
    return { userStore: useUserStore() }
  },
  data() {
    return {
      memory: null,
    }
  },
  computed: {
    avatarLetter() {
      const name = this.userStore.userInfo?.full_name || 'U'
      return name.charAt(0)
    },
    roleLabel() {
      const role = this.userStore.userInfo?.role
      return role === 'master' ? '管理员' : '兽医'
    },
  },
  async onShow() {
    try {
      this.memory = await get('/memory')
    } catch (e) {
      // 可能是新用户
    }
  },
  methods: {
    formatDateTime,
    handleLogout() {
      uni.showModal({
        title: '确认退出',
        content: '确定要退出登录吗？',
        success: (res) => {
          if (res.confirm) {
            this.userStore.logout()
          }
        },
      })
    },
    goMemory() {
      // 可以跳转到独立记忆管理页面
      uni.showToast({ title: '记忆管理', icon: 'none' })
    },
    goReminders() {
      uni.switchTab({ url: '/pages/reminders/index' })
    },
  },
}
</script>

<style lang="scss" scoped>
.profile-page {
  padding-bottom: 120rpx;
}
.profile-header {
  background: linear-gradient(135deg, #2e7d32, #43a047);
  padding: 60rpx 32rpx 48rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
}
.avatar-circle {
  width: 120rpx;
  height: 120rpx;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.3);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 16rpx;
}
.avatar-letter {
  color: #fff;
  font-size: 48rpx;
  font-weight: 700;
}
.user-name {
  color: #fff;
  font-size: 36rpx;
  font-weight: 600;
  margin-bottom: 4rpx;
}
.user-role {
  color: rgba(255, 255, 255, 0.8);
  font-size: 26rpx;
}
.menu-section {
  background: #fff;
  margin: 24rpx;
  border-radius: 16rpx;
  overflow: hidden;
}
.menu-item {
  display: flex;
  align-items: center;
  padding: 28rpx 24rpx;
  border-bottom: 1rpx solid #f5f5f5;
}
.menu-item:last-child {
  border-bottom: none;
}
.menu-icon {
  font-size: 36rpx;
  margin-right: 20rpx;
}
.menu-text {
  flex: 1;
  font-size: 30rpx;
  color: #333;
}
.menu-arrow {
  color: #ccc;
  font-size: 36rpx;
}
.card {
  background: #fff;
  border-radius: 16rpx;
  padding: 24rpx;
  margin: 0 24rpx 20rpx;
}
.section-label {
  font-size: 30rpx;
  font-weight: 600;
  color: #333;
  margin-bottom: 16rpx;
  display: block;
}
.memory-label {
  font-size: 26rpx;
  color: #2e7d32;
  font-weight: 500;
  margin: 12rpx 0 8rpx;
}
.memory-item {
  display: flex;
  margin-bottom: 4rpx;
}
.memory-key {
  font-size: 24rpx;
  color: #999;
  margin-right: 8rpx;
}
.memory-value {
  font-size: 24rpx;
  color: #333;
  flex: 1;
}
.memory-update {
  font-size: 22rpx;
  color: #bbb;
  margin-top: 12rpx;
}
.logout-btn {
  margin: 24rpx;
  background: #fff;
  color: #f44336;
  border: 2rpx solid #f44336;
  border-radius: 12rpx;
  font-size: 30rpx;
  padding: 20rpx;
}
</style>
