<template>
  <view class="empty-state">
    <text class="empty-icon">{{ icon }}</text>
    <text class="empty-text">{{ text }}</text>
    <text class="empty-sub" v-if="subText">{{ subText }}</text>
  </view>
</template>

<script>
export default {
  name: 'EmptyState',
  props: {
    icon: { type: String, default: '📋' },
    text: { type: String, default: '暂无数据' },
    subText: { type: String, default: '' },
  },
}
</script>

<style lang="scss" scoped>
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 120rpx 48rpx;
}
.empty-icon {
  font-size: 80rpx;
  margin-bottom: 24rpx;
}
.empty-text {
  font-size: 30rpx;
  color: #999;
  margin-bottom: 8rpx;
}
.empty-sub {
  font-size: 24rpx;
  color: #bbb;
}
</style>
