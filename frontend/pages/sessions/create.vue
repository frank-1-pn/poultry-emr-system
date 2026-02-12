<template>
  <view class="create-page">
    <!-- Step 1: 选择养殖场 -->
    <view class="step-card" v-if="step === 1">
      <text class="step-title">Step 1: 选择养殖场（可跳过）</text>
      <farm-picker :selected-id="selectedFarm?.id" @select="onFarmSelect" />
      <view class="step-actions">
        <button class="btn-skip" @click="step = 2">跳过</button>
        <button class="btn-next" :disabled="!selectedFarm" @click="step = 2">下一步</button>
      </view>
    </view>

    <!-- Step 2: 选择模式 -->
    <view class="step-card" v-if="step === 2">
      <text class="step-title">Step 2: 选择模式</text>
      <view class="mode-options">
        <view
          class="mode-option"
          :class="{ active: mode === 'new' }"
          @click="mode = 'new'"
        >
          <text class="mode-label">新建病历</text>
          <text class="mode-desc">开始全新的诊疗对话</text>
        </view>
        <view
          class="mode-option"
          :class="{ active: mode === 'existing' }"
          @click="mode = 'existing'"
        >
          <text class="mode-label">继续已有病历</text>
          <text class="mode-desc">关联到已有的病历记录</text>
        </view>
      </view>

      <view v-if="mode === 'existing'" class="record-picker-area">
        <record-picker
          :farm-id="selectedFarm?.id"
          :selected-id="selectedRecord?.id"
          @select="onRecordSelect"
        />
      </view>

      <view class="step-actions">
        <button class="btn-back" @click="step = 1">上一步</button>
        <button
          class="btn-next"
          :disabled="mode === 'existing' && !selectedRecord"
          @click="step = 3"
        >下一步</button>
      </view>
    </view>

    <!-- Step 3: 标签 -->
    <view class="step-card" v-if="step === 3">
      <text class="step-title">Step 3: 添加标签（可选）</text>
      <view class="preset-tags">
        <view
          v-for="t in presetTags"
          :key="t"
          class="preset-tag"
          :class="{ active: selectedTags.includes(t) }"
          @click="toggleTag(t)"
        >
          <text>{{ t }}</text>
        </view>
      </view>
      <view class="custom-tag-row">
        <input
          v-model="customTag"
          class="custom-tag-input"
          placeholder="自定义标签..."
          @confirm="addCustomTag"
        />
        <button class="btn-add-tag" @click="addCustomTag" :disabled="!customTag.trim()">添加</button>
      </view>
      <view class="selected-tags" v-if="selectedTags.length">
        <text class="tags-label">已选标签：</text>
        <view class="tag-list">
          <view class="tag-item" v-for="(t, i) in selectedTags" :key="i">
            <text>{{ t }}</text>
            <text class="tag-remove" @click="removeTag(i)">x</text>
          </view>
        </view>
      </view>

      <view class="step-actions">
        <button class="btn-back" @click="step = 2">上一步</button>
        <button class="btn-submit" @click="handleSubmit" :disabled="submitting">
          {{ submitting ? '创建中...' : '创建会话' }}
        </button>
      </view>
    </view>
  </view>
</template>

<script>
import { useSessionsStore } from '../../store/sessions'
import FarmPicker from '../../components/farm-picker/farm-picker.vue'
import RecordPicker from '../../components/record-picker/record-picker.vue'

export default {
  components: { FarmPicker, RecordPicker },
  setup() {
    return { sessionsStore: useSessionsStore() }
  },
  data() {
    return {
      step: 1,
      selectedFarm: null,
      mode: 'new',
      selectedRecord: null,
      selectedTags: [],
      customTag: '',
      submitting: false,
      presetTags: ['复查', '紧急', '常规', '疫苗', '用药指导'],
    }
  },
  methods: {
    onFarmSelect(farm) {
      this.selectedFarm = this.selectedFarm?.id === farm.id ? null : farm
    },
    onRecordSelect(record) {
      this.selectedRecord = this.selectedRecord?.id === record.id ? null : record
    },
    toggleTag(tag) {
      const idx = this.selectedTags.indexOf(tag)
      if (idx >= 0) {
        this.selectedTags.splice(idx, 1)
      } else {
        this.selectedTags.push(tag)
      }
    },
    addCustomTag() {
      const tag = this.customTag.trim()
      if (tag && !this.selectedTags.includes(tag)) {
        this.selectedTags.push(tag)
      }
      this.customTag = ''
    },
    removeTag(index) {
      this.selectedTags.splice(index, 1)
    },
    async handleSubmit() {
      this.submitting = true
      try {
        const data = {
          tags: this.selectedTags,
        }
        if (this.selectedFarm) data.farm_id = this.selectedFarm.id
        if (this.mode === 'existing' && this.selectedRecord) {
          data.record_id = this.selectedRecord.id
        }

        const conv = await this.sessionsStore.createSession(data)
        uni.redirectTo({
          url: `/pages/chat/index?conversationId=${conv.id}`,
        })
      } catch (e) {
        // error handled by request util
      } finally {
        this.submitting = false
      }
    },
  },
}
</script>

<style lang="scss" scoped>
.create-page {
  padding: 24rpx;
  min-height: 100vh;
  background: #f5f5f5;
}
.step-card {
  background: #fff;
  border-radius: 16rpx;
  padding: 28rpx;
  box-shadow: 0 2rpx 12rpx rgba(0, 0, 0, 0.04);
}
.step-title {
  font-size: 32rpx;
  font-weight: 600;
  color: #333;
  margin-bottom: 24rpx;
  display: block;
}
.step-actions {
  display: flex;
  gap: 16rpx;
  margin-top: 24rpx;
}
.btn-skip, .btn-back {
  flex: 1;
  background: #f5f5f5;
  color: #666;
  border: none;
  border-radius: 12rpx;
  padding: 16rpx;
  font-size: 28rpx;
}
.btn-next, .btn-submit {
  flex: 1;
  background: #2e7d32;
  color: #fff;
  border: none;
  border-radius: 12rpx;
  padding: 16rpx;
  font-size: 28rpx;
}
.btn-next[disabled], .btn-submit[disabled] {
  opacity: 0.5;
}
.mode-options {
  display: flex;
  gap: 16rpx;
  margin-bottom: 20rpx;
}
.mode-option {
  flex: 1;
  padding: 24rpx;
  border-radius: 12rpx;
  background: #fafafa;
  border: 2rpx solid transparent;
  text-align: center;
}
.mode-option.active {
  background: #e8f5e9;
  border-color: #2e7d32;
}
.mode-label {
  font-size: 28rpx;
  font-weight: 600;
  color: #333;
  display: block;
  margin-bottom: 4rpx;
}
.mode-desc {
  font-size: 22rpx;
  color: #999;
}
.record-picker-area {
  margin-top: 16rpx;
}
.preset-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 12rpx;
  margin-bottom: 16rpx;
}
.preset-tag {
  padding: 10rpx 24rpx;
  border-radius: 24rpx;
  background: #f5f5f5;
  font-size: 26rpx;
  color: #666;
  border: 2rpx solid transparent;
}
.preset-tag.active {
  background: #f3e5f5;
  color: #7b1fa2;
  border-color: #ce93d8;
}
.custom-tag-row {
  display: flex;
  gap: 12rpx;
  margin-bottom: 16rpx;
}
.custom-tag-input {
  flex: 1;
  background: #f5f5f5;
  border-radius: 12rpx;
  padding: 12rpx 20rpx;
  font-size: 26rpx;
}
.btn-add-tag {
  background: #7b1fa2;
  color: #fff;
  border: none;
  border-radius: 12rpx;
  padding: 12rpx 24rpx;
  font-size: 26rpx;
  flex-shrink: 0;
}
.btn-add-tag[disabled] { opacity: 0.5; }
.selected-tags {
  margin-bottom: 8rpx;
}
.tags-label {
  font-size: 24rpx;
  color: #999;
  margin-bottom: 8rpx;
  display: block;
}
.tag-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8rpx;
}
.tag-item {
  display: flex;
  align-items: center;
  gap: 4rpx;
  background: #f3e5f5;
  color: #7b1fa2;
  padding: 6rpx 16rpx;
  border-radius: 16rpx;
  font-size: 24rpx;
}
.tag-remove {
  color: #999;
  margin-left: 4rpx;
  font-size: 22rpx;
}
</style>
