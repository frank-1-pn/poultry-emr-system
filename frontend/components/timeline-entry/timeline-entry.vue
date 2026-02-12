<template>
  <view class="timeline-entry">
    <view class="timeline-dot" :class="'dot-' + entry.treatment_type"></view>
    <view class="timeline-line"></view>
    <view class="timeline-content">
      <view class="entry-header">
        <text class="entry-type">{{ entry.treatment_type }}</text>
        <text class="entry-date" v-if="entry.start_date">{{ entry.start_date }}</text>
      </view>
      <view class="entry-body">
        <text class="med-name" v-if="entry.medication_name">{{ entry.medication_name }}</text>
        <view class="detail-row" v-if="entry.dosage">
          <text class="detail-label">剂量:</text>
          <text class="detail-value">{{ entry.dosage }}</text>
        </view>
        <view class="detail-row" v-if="entry.frequency">
          <text class="detail-label">频率:</text>
          <text class="detail-value">{{ entry.frequency }}</text>
        </view>
        <view class="detail-row" v-if="entry.duration_days">
          <text class="detail-label">疗程:</text>
          <text class="detail-value">{{ entry.duration_days }}天</text>
        </view>
        <view class="detail-row" v-if="entry.route">
          <text class="detail-label">途径:</text>
          <text class="detail-value">{{ entry.route }}</text>
        </view>
        <text class="advice" v-if="entry.management_advice">{{ entry.management_advice }}</text>
      </view>
      <!-- 关联媒体文件 -->
      <view class="entry-media" v-if="entry.media_files && entry.media_files.length">
        <view
          class="media-thumb"
          v-for="media in entry.media_files"
          :key="media.id"
          @click="previewMedia(media)"
        >
          <image
            v-if="media.file_type === 'image'"
            :src="media.thumbnail_url || media.url"
            mode="aspectFill"
            class="thumb-img"
          />
          <view v-else class="thumb-video">
            <text class="video-icon">&#9654;</text>
          </view>
        </view>
      </view>
    </view>
  </view>
</template>

<script>
export default {
  name: 'TimelineEntry',
  props: {
    entry: { type: Object, required: true },
  },
  methods: {
    previewMedia(media) {
      if (media.file_type === 'image') {
        uni.previewImage({
          urls: [media.url],
        })
      } else if (media.file_type === 'video') {
        // 可跳转视频预览页
        uni.navigateTo({
          url: `/pages/records/detail?videoUrl=${encodeURIComponent(media.url)}`,
        })
      }
    },
  },
}
</script>

<style lang="scss" scoped>
.timeline-entry {
  display: flex;
  position: relative;
  padding-left: 40rpx;
  margin-bottom: 32rpx;
}
.timeline-dot {
  position: absolute;
  left: 0;
  top: 12rpx;
  width: 20rpx;
  height: 20rpx;
  border-radius: 50%;
  background: #2e7d32;
  z-index: 1;
}
.dot-medication { background: #2196f3; }
.dot-surgery { background: #f44336; }
.dot-management { background: #ff9800; }
.timeline-line {
  position: absolute;
  left: 9rpx;
  top: 32rpx;
  bottom: -32rpx;
  width: 2rpx;
  background: #e0e0e0;
}
.timeline-content {
  flex: 1;
  background: #fff;
  border-radius: 12rpx;
  padding: 20rpx;
  box-shadow: 0 2rpx 8rpx rgba(0, 0, 0, 0.04);
}
.entry-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12rpx;
}
.entry-type {
  font-size: 28rpx;
  font-weight: 600;
  color: #333;
}
.entry-date {
  font-size: 24rpx;
  color: #999;
}
.med-name {
  font-size: 30rpx;
  font-weight: 500;
  color: #2e7d32;
  margin-bottom: 8rpx;
}
.detail-row {
  display: flex;
  margin-bottom: 4rpx;
}
.detail-label {
  font-size: 24rpx;
  color: #999;
  width: 80rpx;
}
.detail-value {
  font-size: 24rpx;
  color: #333;
}
.advice {
  font-size: 24rpx;
  color: #666;
  margin-top: 8rpx;
  padding-top: 8rpx;
  border-top: 1rpx solid #f0f0f0;
}
.entry-media {
  display: flex;
  flex-wrap: wrap;
  margin-top: 12rpx;
  gap: 12rpx;
}
.thumb-img {
  width: 120rpx;
  height: 120rpx;
  border-radius: 8rpx;
}
.thumb-video {
  width: 120rpx;
  height: 120rpx;
  border-radius: 8rpx;
  background: #000;
  display: flex;
  align-items: center;
  justify-content: center;
}
.video-icon {
  color: #fff;
  font-size: 40rpx;
}
</style>
