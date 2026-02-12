<template>
  <view class="login-page">
    <view class="login-header">
      <text class="app-title">禽病诊疗系统</text>
      <text class="app-subtitle">智能禽类电子病历管理</text>
    </view>

    <view class="login-form">
      <view class="form-group">
        <input
          v-model="username"
          class="form-input"
          placeholder="用户名"
          type="text"
        />
      </view>
      <view class="form-group">
        <input
          v-model="password"
          class="form-input"
          placeholder="密码"
          type="password"
        />
      </view>
      <button
        class="login-btn"
        :loading="loading"
        :disabled="loading || !username || !password"
        @click="handleLogin"
      >
        登录
      </button>
    </view>

    <view class="login-footer">
      <text class="footer-text">Poultry EMR v1.0</text>
    </view>
  </view>
</template>

<script>
import { useUserStore } from '../../store/user'

export default {
  data() {
    return {
      username: '',
      password: '',
      loading: false,
    }
  },
  methods: {
    async handleLogin() {
      if (!this.username || !this.password) return
      this.loading = true
      try {
        const userStore = useUserStore()
        await userStore.login(this.username, this.password)
        uni.switchTab({ url: '/pages/home/index' })
      } catch (e) {
        // request.js 已处理 toast
      } finally {
        this.loading = false
      }
    },
  },
}
</script>

<style lang="scss" scoped>
.login-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #1b5e20 0%, #2e7d32 50%, #388e3c 100%);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 48rpx;
}
.login-header {
  text-align: center;
  margin-bottom: 80rpx;
}
.app-title {
  font-size: 56rpx;
  font-weight: 700;
  color: #fff;
  display: block;
  margin-bottom: 16rpx;
}
.app-subtitle {
  font-size: 28rpx;
  color: rgba(255, 255, 255, 0.8);
}
.login-form {
  width: 100%;
  max-width: 600rpx;
}
.form-group {
  margin-bottom: 28rpx;
}
.form-input {
  background: rgba(255, 255, 255, 0.95);
  border-radius: 16rpx;
  padding: 28rpx 32rpx;
  font-size: 30rpx;
  color: #333;
}
.login-btn {
  width: 100%;
  background: #fff;
  color: #2e7d32;
  font-size: 32rpx;
  font-weight: 600;
  border: none;
  border-radius: 16rpx;
  padding: 28rpx 0;
  margin-top: 16rpx;
}
.login-btn:active {
  background: #f0f0f0;
}
.login-btn[disabled] {
  opacity: 0.5;
}
.login-footer {
  position: absolute;
  bottom: 60rpx;
}
.footer-text {
  font-size: 24rpx;
  color: rgba(255, 255, 255, 0.5);
}
</style>
