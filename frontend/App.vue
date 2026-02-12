<script>
export default {
  onLaunch() {
    console.log('App Launch')
  },
  onShow() {
    console.log('App Show')
  },
  onHide() {
    console.log('App Hide')
  },
}
</script>

<style lang="scss">
@import './uni.scss';

page {
  background-color: $bg-color;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  font-size: 28rpx;
  color: $text-color;
  line-height: 1.5;
}

/* 全局工具类 */
.container {
  padding: 24rpx;
}

.card {
  background: #fff;
  border-radius: 16rpx;
  padding: 24rpx;
  margin-bottom: 20rpx;
  box-shadow: 0 2rpx 12rpx rgba(0, 0, 0, 0.04);
}

.text-muted {
  color: $text-muted;
}

.text-primary {
  color: $primary-color;
}

.text-danger {
  color: $danger-color;
}

.text-warning {
  color: $warning-color;
}

.flex-row {
  display: flex;
  align-items: center;
}

.flex-between {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.flex-1 {
  flex: 1;
}

.mt-20 {
  margin-top: 20rpx;
}

.mb-20 {
  margin-bottom: 20rpx;
}

.btn-primary {
  background: $primary-color;
  color: #fff;
  border: none;
  border-radius: 12rpx;
  padding: 20rpx 40rpx;
  font-size: 28rpx;
  text-align: center;
}

.btn-primary:active {
  background: $primary-dark;
}

.btn-outline {
  background: #fff;
  color: $primary-color;
  border: 2rpx solid $primary-color;
  border-radius: 12rpx;
  padding: 20rpx 40rpx;
  font-size: 28rpx;
  text-align: center;
}
</style>
