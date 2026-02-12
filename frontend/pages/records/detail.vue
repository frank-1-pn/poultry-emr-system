<template>
  <view class="detail-page" v-if="record">
    <!-- 基本信息 -->
    <view class="card">
      <view class="card-title-row">
        <text class="card-title">{{ record.record_no }}</text>
        <view class="severity-badge" :style="{ backgroundColor: severityBg }">
          <text :style="{ color: severityClr, fontSize: '24rpx' }">{{ severityTxt }}</text>
        </view>
      </view>
      <view class="info-grid">
        <editable-field
          label="禽类"
          :value="record.poultry_type"
          field="poultry_type"
          @save="saveField"
        />
        <editable-field
          label="品种"
          :value="record.breed"
          field="breed"
          @save="saveField"
        />
        <editable-field
          label="日龄"
          :value="record.age_days != null ? record.age_days + '' : ''"
          field="age_days"
          inputType="number"
          @save="saveField"
        />
        <editable-field
          label="就诊日期"
          :value="record.visit_date"
          field="visit_date"
          @save="saveField"
        />
        <editable-field
          label="发病数"
          :value="record.affected_count != null ? record.affected_count + '' : ''"
          field="affected_count"
          inputType="number"
          @save="saveField"
        />
        <editable-field
          label="总数"
          :value="record.total_flock != null ? record.total_flock + '' : ''"
          field="total_flock"
          inputType="number"
          @save="saveField"
        />
      </view>
    </view>

    <!-- 诊断（可编辑） -->
    <view class="card">
      <text class="section-label">诊断</text>
      <editable-field
        label=""
        :value="record.primary_diagnosis || ''"
        field="primary_diagnosis"
        :inline="false"
        @save="saveField"
      />
      <view class="severity-edit-row">
        <text class="info-label">严重度</text>
        <view class="severity-options">
          <view
            v-for="s in severityOptions"
            :key="s.value"
            class="severity-opt"
            :class="{ active: record.severity === s.value }"
            @click="saveField('severity', s.value)"
          >
            <text :style="{ color: s.color, fontSize: '24rpx' }">{{ s.label }}</text>
          </view>
        </view>
      </view>
    </view>

    <!-- 症状 (from record_json) -->
    <view class="card" v-if="symptoms.length || editingSymptoms">
      <view class="section-header">
        <text class="section-label">症状</text>
        <text class="edit-icon" @click="editingSymptoms = !editingSymptoms">
          {{ editingSymptoms ? '完成' : '编辑' }}
        </text>
      </view>
      <view class="symptom-tags">
        <text class="symptom-tag" v-for="(s, i) in symptoms" :key="i">
          {{ s }}
          <text v-if="editingSymptoms" class="symptom-remove" @click="removeSymptom(i)">x</text>
        </text>
      </view>
      <view class="add-symptom-row" v-if="editingSymptoms">
        <input
          v-model="newSymptom"
          class="symptom-input"
          placeholder="添加症状..."
          @confirm="addSymptom"
        />
        <button class="btn-add-symptom" @click="addSymptom" :disabled="!newSymptom.trim()">添加</button>
      </view>
    </view>

    <!-- 治疗时间线 -->
    <view class="card" v-if="timeline.length">
      <text class="section-label">治疗时间线</text>
      <timeline-entry
        v-for="t in timeline"
        :key="t.id"
        :entry="t"
      />
    </view>

    <!-- 操作按钮 -->
    <view class="action-bar">
      <button class="btn-outline" @click="goChat">AI 继续问诊</button>
    </view>
  </view>
</template>

<script>
import { useRecordsStore } from '../../store/records'
import { put } from '../../utils/request'
import { severityLabel, severityColor } from '../../utils/format'
import TimelineEntry from '../../components/timeline-entry/timeline-entry.vue'

const EditableField = {
  props: {
    label: { type: String, default: '' },
    value: { type: String, default: '' },
    field: { type: String, required: true },
    inputType: { type: String, default: 'text' },
    inline: { type: Boolean, default: true },
  },
  emits: ['save'],
  data() {
    return { editing: false, editValue: '' }
  },
  template: `
    <view :class="inline ? 'info-item' : 'edit-block'">
      <text class="info-label" v-if="label">{{ label }}</text>
      <view class="value-row" v-if="!editing" @click="startEdit">
        <text class="info-value">{{ value || '-' }}</text>
        <text class="edit-icon-inline">E</text>
      </view>
      <view class="edit-row" v-else>
        <input
          v-model="editValue"
          :type="inputType"
          class="edit-input"
          @confirm="confirmEdit"
        />
        <text class="edit-ok" @click="confirmEdit">OK</text>
        <text class="edit-cancel" @click="editing = false">X</text>
      </view>
    </view>
  `,
  methods: {
    startEdit() {
      this.editValue = this.value || ''
      this.editing = true
    },
    confirmEdit() {
      this.editing = false
      if (this.editValue !== this.value) {
        this.$emit('save', this.field, this.editValue)
      }
    },
  },
}

export default {
  components: { TimelineEntry, EditableField },
  setup() {
    return { recordsStore: useRecordsStore() }
  },
  data() {
    return {
      timeline: [],
      editingSymptoms: false,
      newSymptom: '',
      severityOptions: [
        { value: 'mild', label: '轻微', color: '#4caf50' },
        { value: 'moderate', label: '中度', color: '#ff9800' },
        { value: 'severe', label: '严重', color: '#f44336' },
        { value: 'critical', label: '危重', color: '#9c27b0' },
      ],
    }
  },
  computed: {
    record() {
      return this.recordsStore.currentRecord
    },
    severityTxt() { return severityLabel(this.record?.severity) },
    severityClr() { return severityColor(this.record?.severity) },
    severityBg() { return severityColor(this.record?.severity) + '18' },
    symptoms() {
      const json = this.record?.record_json
      if (!json) return []
      const s = json.symptoms
      if (Array.isArray(s)) return s
      if (typeof s === 'string') return [s]
      return []
    },
  },
  async onLoad(query) {
    if (query.id) {
      await this.recordsStore.fetchRecord(query.id)
      this.timeline = await this.recordsStore.fetchTimeline(query.id)
    }
  },
  methods: {
    goChat() {
      if (this.record) {
        uni.navigateTo({ url: `/pages/chat/index?recordId=${this.record.id}` })
      }
    },
    async saveField(field, value) {
      if (!this.record) return
      const data = {}
      // 数值字段转换
      if (['age_days', 'affected_count', 'total_flock'].includes(field)) {
        data[field] = value ? parseInt(value, 10) : null
      } else {
        data[field] = value || null
      }
      try {
        const updated = await put(`/records/${this.record.id}`, data)
        this.recordsStore.currentRecord = updated
        uni.showToast({ title: '已保存', icon: 'success', duration: 1000 })
      } catch (e) {
        // error handled by request util
      }
    },
    async removeSymptom(index) {
      const list = [...this.symptoms]
      list.splice(index, 1)
      await this.saveSymptoms(list)
    },
    async addSymptom() {
      const s = this.newSymptom.trim()
      if (!s) return
      const list = [...this.symptoms, s]
      this.newSymptom = ''
      await this.saveSymptoms(list)
    },
    async saveSymptoms(list) {
      if (!this.record) return
      const json = { ...(this.record.record_json || {}), symptoms: list }
      try {
        const updated = await put(`/records/${this.record.id}`, { record_json: json })
        this.recordsStore.currentRecord = updated
      } catch (e) {
        // error handled by request util
      }
    },
  },
}
</script>

<style lang="scss" scoped>
.detail-page {
  padding: 24rpx;
  padding-bottom: 160rpx;
}
.card {
  background: #fff;
  border-radius: 16rpx;
  padding: 24rpx;
  margin-bottom: 20rpx;
  box-shadow: 0 2rpx 12rpx rgba(0, 0, 0, 0.04);
}
.card-title-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20rpx;
}
.card-title {
  font-size: 34rpx;
  font-weight: 700;
  color: #333;
}
.severity-badge {
  padding: 4rpx 16rpx;
  border-radius: 20rpx;
}
.info-grid {
  display: flex;
  flex-wrap: wrap;
}
.info-item {
  width: 50%;
  margin-bottom: 16rpx;
}
.info-label {
  font-size: 24rpx;
  color: #999;
  display: block;
}
.info-value {
  font-size: 28rpx;
  color: #333;
  font-weight: 500;
}
.value-row {
  display: flex;
  align-items: center;
  gap: 8rpx;
}
.edit-icon-inline {
  font-size: 20rpx;
  color: #2e7d32;
  background: #e8f5e9;
  padding: 2rpx 8rpx;
  border-radius: 6rpx;
}
.edit-row {
  display: flex;
  align-items: center;
  gap: 8rpx;
}
.edit-input {
  flex: 1;
  background: #f5f5f5;
  border-radius: 8rpx;
  padding: 8rpx 12rpx;
  font-size: 26rpx;
}
.edit-ok {
  color: #2e7d32;
  font-size: 24rpx;
  font-weight: 600;
}
.edit-cancel {
  color: #999;
  font-size: 24rpx;
}
.edit-block {
  margin-bottom: 12rpx;
}
.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.section-label {
  font-size: 30rpx;
  font-weight: 600;
  color: #333;
  margin-bottom: 16rpx;
  display: block;
}
.edit-icon {
  font-size: 24rpx;
  color: #2e7d32;
  font-weight: 500;
}
.diagnosis-text {
  font-size: 28rpx;
  color: #2e7d32;
  font-weight: 500;
}
.severity-edit-row {
  margin-top: 16rpx;
}
.severity-options {
  display: flex;
  gap: 12rpx;
  margin-top: 8rpx;
}
.severity-opt {
  padding: 8rpx 20rpx;
  border-radius: 20rpx;
  background: #f5f5f5;
  border: 2rpx solid transparent;
}
.severity-opt.active {
  border-color: currentColor;
  background: #fff;
}
.symptom-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 12rpx;
}
.symptom-tag {
  background: #fff3e0;
  color: #e65100;
  padding: 8rpx 20rpx;
  border-radius: 20rpx;
  font-size: 24rpx;
  display: flex;
  align-items: center;
  gap: 8rpx;
}
.symptom-remove {
  color: #999;
  font-size: 22rpx;
}
.add-symptom-row {
  display: flex;
  gap: 12rpx;
  margin-top: 16rpx;
}
.symptom-input {
  flex: 1;
  background: #f5f5f5;
  border-radius: 12rpx;
  padding: 12rpx 16rpx;
  font-size: 26rpx;
}
.btn-add-symptom {
  background: #e65100;
  color: #fff;
  border: none;
  border-radius: 12rpx;
  padding: 12rpx 24rpx;
  font-size: 26rpx;
  flex-shrink: 0;
}
.btn-add-symptom[disabled] { opacity: 0.5; }
.action-bar {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  background: #fff;
  padding: 20rpx 32rpx;
  border-top: 1rpx solid #f0f0f0;
  padding-bottom: calc(20rpx + env(safe-area-inset-bottom));
}
.btn-outline {
  background: #fff;
  color: #2e7d32;
  border: 2rpx solid #2e7d32;
  border-radius: 12rpx;
  padding: 20rpx;
  font-size: 30rpx;
  text-align: center;
}
</style>
