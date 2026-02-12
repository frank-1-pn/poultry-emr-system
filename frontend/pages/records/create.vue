<template>
  <view class="create-page">
    <scroll-view scroll-y class="form-scroll">
      <!-- 基本信息 -->
      <view class="section">
        <text class="section-title">基本信息</text>

        <view class="form-group">
          <text class="label required">就诊日期</text>
          <picker mode="date" :value="form.visit_date" @change="form.visit_date = $event.detail.value">
            <view class="picker-value">
              <text :class="{ placeholder: !form.visit_date }">
                {{ form.visit_date || '请选择日期' }}
              </text>
            </view>
          </picker>
        </view>

        <view class="form-group">
          <text class="label required">禽类类型</text>
          <picker :range="poultryTypes" @change="form.poultry_type = poultryTypes[$event.detail.value]">
            <view class="picker-value">
              <text :class="{ placeholder: !form.poultry_type }">
                {{ form.poultry_type || '请选择' }}
              </text>
            </view>
          </picker>
        </view>

        <view class="form-group">
          <text class="label">品种</text>
          <input v-model="form.breed" class="form-input" placeholder="如：海兰褐、白羽肉鸡" />
        </view>

        <view class="form-group">
          <text class="label">日龄（天）</text>
          <input v-model.number="form.age_days" class="form-input" type="number" placeholder="请输入日龄" />
        </view>

        <view class="form-group">
          <text class="label">养殖场</text>
          <view class="farm-select" @click="showFarmPicker = true">
            <text :class="{ placeholder: !selectedFarm }">
              {{ selectedFarm ? selectedFarm.name : '选择养殖场（可选）' }}
            </text>
          </view>
        </view>
      </view>

      <!-- 群体信息 -->
      <view class="section">
        <text class="section-title">群体信息</text>

        <view class="form-row">
          <view class="form-group half">
            <text class="label">发病数量</text>
            <input v-model.number="form.affected_count" class="form-input" type="number" placeholder="发病数" />
          </view>
          <view class="form-group half">
            <text class="label">存栏总数</text>
            <input v-model.number="form.total_flock" class="form-input" type="number" placeholder="总数" />
          </view>
        </view>

        <view class="form-group">
          <text class="label">发病日期</text>
          <picker mode="date" :value="form.onset_date" @change="form.onset_date = $event.detail.value">
            <view class="picker-value">
              <text :class="{ placeholder: !form.onset_date }">
                {{ form.onset_date || '请选择（可选）' }}
              </text>
            </view>
          </picker>
        </view>
      </view>

      <!-- 症状 -->
      <view class="section">
        <text class="section-title">临床症状</text>

        <view class="symptoms-grid">
          <view
            v-for="s in commonSymptoms"
            :key="s"
            class="symptom-tag"
            :class="{ active: selectedSymptoms.includes(s) }"
            @click="toggleSymptom(s)"
          >
            <text>{{ s }}</text>
          </view>
        </view>

        <view class="form-group">
          <text class="label">其他症状</text>
          <textarea
            v-model="otherSymptoms"
            class="form-textarea"
            placeholder="描述其他症状..."
            :maxlength="500"
          />
        </view>
      </view>

      <!-- 诊断 -->
      <view class="section">
        <text class="section-title">诊断信息</text>

        <view class="form-group">
          <text class="label">初步诊断</text>
          <input v-model="form.primary_diagnosis" class="form-input" placeholder="如：新城疫、禽流感..." />
        </view>

        <view class="form-group">
          <text class="label">严重程度</text>
          <view class="severity-row">
            <view
              v-for="s in severityLevels"
              :key="s.value"
              class="severity-tag"
              :class="[s.value, { active: form.severity === s.value }]"
              @click="form.severity = s.value"
            >
              <text>{{ s.label }}</text>
            </view>
          </view>
        </view>
      </view>

      <!-- 治疗方案 -->
      <view class="section">
        <text class="section-title">治疗方案</text>

        <view class="form-group">
          <text class="label">用药</text>
          <input v-model="treatment.drug" class="form-input" placeholder="药物名称" />
        </view>

        <view class="form-group">
          <text class="label">用法</text>
          <input v-model="treatment.method" class="form-input" placeholder="如：饮水、拌料、注射" />
        </view>

        <view class="form-group">
          <text class="label">剂量</text>
          <input v-model="treatment.dosage" class="form-input" placeholder="如：0.1ml/只" />
        </view>

        <view class="form-group">
          <text class="label">疗程（天）</text>
          <input v-model.number="treatment.duration_days" class="form-input" type="number" placeholder="天数" />
        </view>
      </view>

      <!-- 备注 -->
      <view class="section">
        <text class="section-title">补充信息</text>

        <view class="form-group">
          <text class="label">环境情况</text>
          <textarea
            v-model="environment"
            class="form-textarea"
            placeholder="通风、温度、密度等..."
            :maxlength="500"
          />
        </view>

        <view class="form-group">
          <text class="label">备注</text>
          <textarea
            v-model="notes"
            class="form-textarea"
            placeholder="其他补充信息..."
            :maxlength="1000"
          />
        </view>
      </view>

      <!-- 提交按钮 -->
      <view class="submit-area">
        <button class="btn-draft" @click="handleSubmit('draft')">保存为草稿</button>
        <button class="btn-submit" @click="handleSubmit('active')" :disabled="!canSubmit">提交病历</button>
      </view>
    </scroll-view>

    <!-- 养殖场选择弹窗 -->
    <view class="modal-mask" v-if="showFarmPicker" @click="showFarmPicker = false">
      <view class="modal-content" @click.stop>
        <text class="modal-title">选择养殖场</text>
        <farm-picker :selected-id="form.farm_id" @select="onFarmSelect" />
        <button class="btn-close" @click="showFarmPicker = false">关闭</button>
      </view>
    </view>
  </view>
</template>

<script>
import { post, put } from '../../utils/request'
import FarmPicker from '../../components/farm-picker/farm-picker.vue'

export default {
  components: { FarmPicker },
  data() {
    const today = new Date()
    const todayStr = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`
    return {
      form: {
        visit_date: todayStr,
        poultry_type: '',
        breed: '',
        age_days: null,
        farm_id: null,
        affected_count: null,
        total_flock: null,
        onset_date: '',
        primary_diagnosis: '',
        severity: '',
      },
      selectedFarm: null,
      showFarmPicker: false,
      selectedSymptoms: [],
      otherSymptoms: '',
      treatment: {
        drug: '',
        method: '',
        dosage: '',
        duration_days: null,
      },
      environment: '',
      notes: '',
      submitting: false,
      poultryTypes: ['鸡', '鸭', '鹅', '火鸡', '鸽', '鹌鹑', '其他'],
      commonSymptoms: [
        '精神萎靡', '食欲下降', '饮水增多', '呼吸困难',
        '咳嗽', '打喷嚏', '流鼻涕', '眼肿',
        '腹泻', '绿色粪便', '白色粪便', '血便',
        '产蛋下降', '软壳蛋', '畸形蛋',
        '羽毛蓬松', '瘫痪', '扭颈', '关节肿胀',
        '皮肤出血', '冠髯发紫', '突然死亡',
      ],
      severityLevels: [
        { value: 'mild', label: '轻度' },
        { value: 'moderate', label: '中度' },
        { value: 'severe', label: '重度' },
        { value: 'critical', label: '危重' },
      ],
    }
  },
  computed: {
    canSubmit() {
      return this.form.visit_date && this.form.poultry_type
    },
  },
  methods: {
    toggleSymptom(s) {
      const idx = this.selectedSymptoms.indexOf(s)
      if (idx >= 0) {
        this.selectedSymptoms.splice(idx, 1)
      } else {
        this.selectedSymptoms.push(s)
      }
    },
    onFarmSelect(farm) {
      this.selectedFarm = farm
      this.form.farm_id = farm.id
      this.showFarmPicker = false
    },
    buildRecordJson() {
      const json = {}

      // 症状
      const allSymptoms = [...this.selectedSymptoms]
      if (this.otherSymptoms.trim()) {
        allSymptoms.push(this.otherSymptoms.trim())
      }
      if (allSymptoms.length) {
        json.symptoms = allSymptoms
      }

      // 治疗
      const t = this.treatment
      if (t.drug || t.method || t.dosage) {
        json.treatment = {}
        if (t.drug) json.treatment.drug = t.drug
        if (t.method) json.treatment.method = t.method
        if (t.dosage) json.treatment.dosage = t.dosage
        if (t.duration_days) json.treatment.duration_days = t.duration_days
      }

      if (this.environment.trim()) {
        json.environment = this.environment.trim()
      }
      if (this.notes.trim()) {
        json.notes = this.notes.trim()
      }

      return json
    },
    async handleSubmit(status) {
      if (this.submitting) return
      if (!this.form.visit_date || !this.form.poultry_type) {
        uni.showToast({ title: '请填写就诊日期和禽类类型', icon: 'none' })
        return
      }

      this.submitting = true
      try {
        const payload = {
          visit_date: this.form.visit_date,
          poultry_type: this.form.poultry_type,
          record_json: this.buildRecordJson(),
        }

        // 可选字段
        if (this.form.breed) payload.breed = this.form.breed
        if (this.form.age_days) payload.age_days = this.form.age_days
        if (this.form.farm_id) payload.farm_id = this.form.farm_id
        if (this.form.affected_count) payload.affected_count = this.form.affected_count
        if (this.form.total_flock) payload.total_flock = this.form.total_flock
        if (this.form.onset_date) payload.onset_date = this.form.onset_date

        const res = await post('/records', payload)

        // 如果有诊断信息，更新病历
        if (this.form.primary_diagnosis || this.form.severity || status === 'draft') {
          const updatePayload = {}
          if (this.form.primary_diagnosis) updatePayload.primary_diagnosis = this.form.primary_diagnosis
          if (this.form.severity) updatePayload.severity = this.form.severity
          if (status === 'draft') updatePayload.status = 'draft'
          await put(`/records/${res.id}`, updatePayload)
        }

        uni.showToast({ title: status === 'draft' ? '已保存草稿' : '病历已创建', icon: 'success' })
        setTimeout(() => {
          uni.navigateBack()
        }, 1500)
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
  height: 100vh;
  background: #f5f5f5;
}
.form-scroll {
  height: 100%;
  padding-bottom: 40rpx;
}
.section {
  background: #fff;
  margin: 16rpx 0;
  padding: 24rpx;
}
.section-title {
  font-size: 30rpx;
  font-weight: 600;
  color: #333;
  margin-bottom: 20rpx;
  display: block;
  padding-left: 12rpx;
  border-left: 6rpx solid #2e7d32;
}
.form-group {
  margin-bottom: 20rpx;
}
.form-row {
  display: flex;
  gap: 16rpx;
}
.form-group.half {
  flex: 1;
}
.label {
  font-size: 26rpx;
  color: #666;
  margin-bottom: 8rpx;
  display: block;
}
.label.required::after {
  content: ' *';
  color: #e53935;
}
.form-input {
  background: #f5f5f5;
  border-radius: 12rpx;
  padding: 16rpx 20rpx;
  font-size: 28rpx;
  width: 100%;
  box-sizing: border-box;
}
.form-textarea {
  background: #f5f5f5;
  border-radius: 12rpx;
  padding: 16rpx 20rpx;
  font-size: 28rpx;
  width: 100%;
  min-height: 120rpx;
  box-sizing: border-box;
}
.picker-value {
  background: #f5f5f5;
  border-radius: 12rpx;
  padding: 16rpx 20rpx;
  font-size: 28rpx;
}
.placeholder {
  color: #bbb;
}
.farm-select {
  background: #f5f5f5;
  border-radius: 12rpx;
  padding: 16rpx 20rpx;
  font-size: 28rpx;
}

/* 症状标签网格 */
.symptoms-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 12rpx;
  margin-bottom: 16rpx;
}
.symptom-tag {
  padding: 10rpx 20rpx;
  border-radius: 20rpx;
  background: #f5f5f5;
  font-size: 24rpx;
  color: #666;
  border: 2rpx solid transparent;
}
.symptom-tag.active {
  background: #e8f5e9;
  color: #2e7d32;
  border-color: #2e7d32;
  font-weight: 500;
}

/* 严重程度 */
.severity-row {
  display: flex;
  gap: 12rpx;
}
.severity-tag {
  flex: 1;
  text-align: center;
  padding: 14rpx 0;
  border-radius: 12rpx;
  font-size: 26rpx;
  background: #f5f5f5;
  color: #666;
  border: 2rpx solid transparent;
}
.severity-tag.active.mild {
  background: #e8f5e9;
  color: #2e7d32;
  border-color: #2e7d32;
}
.severity-tag.active.moderate {
  background: #fff3e0;
  color: #ef6c00;
  border-color: #ef6c00;
}
.severity-tag.active.severe {
  background: #fce4ec;
  color: #c62828;
  border-color: #c62828;
}
.severity-tag.active.critical {
  background: #f3e5f5;
  color: #6a1b9a;
  border-color: #6a1b9a;
}

/* 提交区域 */
.submit-area {
  display: flex;
  gap: 16rpx;
  padding: 24rpx;
  background: #fff;
  margin-top: 16rpx;
  margin-bottom: 40rpx;
}
.btn-draft {
  flex: 1;
  background: #f5f5f5;
  color: #666;
  border: none;
  border-radius: 12rpx;
  padding: 20rpx;
  font-size: 28rpx;
}
.btn-submit {
  flex: 2;
  background: #2e7d32;
  color: #fff;
  border: none;
  border-radius: 12rpx;
  padding: 20rpx;
  font-size: 28rpx;
  font-weight: 500;
}
.btn-submit[disabled] {
  opacity: 0.5;
}

/* 弹窗 */
.modal-mask {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0,0,0,0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 999;
}
.modal-content {
  width: 650rpx;
  max-height: 80vh;
  background: #fff;
  border-radius: 20rpx;
  padding: 32rpx;
  overflow-y: auto;
}
.modal-title {
  font-size: 32rpx;
  font-weight: 600;
  color: #333;
  margin-bottom: 20rpx;
  display: block;
}
.btn-close {
  margin-top: 16rpx;
  background: #f5f5f5;
  color: #666;
  border: none;
  border-radius: 12rpx;
  padding: 16rpx;
  font-size: 28rpx;
}
</style>
