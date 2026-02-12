<template>
  <view class="farm-picker">
    <view class="search-row">
      <input
        v-model="searchText"
        class="search-input"
        placeholder="搜索养殖场..."
        @input="onSearch"
      />
      <button class="btn-add" @click="showCreate = true">新增</button>
    </view>

    <scroll-view scroll-y class="farm-list">
      <view
        v-for="farm in farms"
        :key="farm.id"
        class="farm-item"
        :class="{ selected: selectedId === farm.id }"
        @click="selectFarm(farm)"
      >
        <view class="farm-main">
          <text class="farm-name">{{ farm.name }}</text>
          <text class="farm-code">{{ farm.farm_code }}</text>
        </view>
        <text class="farm-owner" v-if="farm.owner_name">{{ farm.owner_name }}</text>
      </view>
      <view class="empty-tip" v-if="!farms.length && !loading">
        <text>暂无养殖场</text>
      </view>
    </scroll-view>

    <!-- 新增弹窗 -->
    <view class="modal-mask" v-if="showCreate" @click="showCreate = false">
      <view class="modal-content" @click.stop>
        <text class="modal-title">新增养殖场</text>
        <input v-model="newFarm.name" class="modal-input" placeholder="养殖场名称" />
        <input v-model="newFarm.owner_name" class="modal-input" placeholder="负责人（选填）" />
        <input v-model="newFarm.contact_phone" class="modal-input" placeholder="联系电话（选填）" />
        <input v-model="newFarm.address" class="modal-input" placeholder="地址（选填）" />
        <view class="modal-actions">
          <button class="btn-cancel" @click="showCreate = false">取消</button>
          <button class="btn-confirm" @click="handleCreate" :disabled="!newFarm.name.trim()">确定</button>
        </view>
      </view>
    </view>
  </view>
</template>

<script>
import { useSessionsStore } from '../../store/sessions'

export default {
  props: {
    selectedId: { type: String, default: null },
  },
  emits: ['select'],
  setup() {
    return { sessionsStore: useSessionsStore() }
  },
  data() {
    return {
      searchText: '',
      loading: false,
      showCreate: false,
      newFarm: { name: '', owner_name: '', contact_phone: '', address: '' },
    }
  },
  computed: {
    farms() {
      return this.sessionsStore.farms
    },
  },
  async mounted() {
    this.loading = true
    await this.sessionsStore.fetchFarms()
    this.loading = false
  },
  methods: {
    async onSearch() {
      this.loading = true
      await this.sessionsStore.fetchFarms(this.searchText)
      this.loading = false
    },
    selectFarm(farm) {
      this.$emit('select', farm)
    },
    async handleCreate() {
      if (!this.newFarm.name.trim()) return
      try {
        const farm = await this.sessionsStore.createFarm(this.newFarm)
        this.showCreate = false
        this.newFarm = { name: '', owner_name: '', contact_phone: '', address: '' }
        this.$emit('select', farm)
      } catch (e) {
        // error handled by request util
      }
    },
  },
}
</script>

<style lang="scss" scoped>
.farm-picker {
  width: 100%;
}
.search-row {
  display: flex;
  gap: 12rpx;
  margin-bottom: 16rpx;
}
.search-input {
  flex: 1;
  background: #f5f5f5;
  border-radius: 16rpx;
  padding: 16rpx 24rpx;
  font-size: 28rpx;
}
.btn-add {
  background: #2e7d32;
  color: #fff;
  border: none;
  border-radius: 16rpx;
  padding: 16rpx 24rpx;
  font-size: 26rpx;
  flex-shrink: 0;
}
.farm-list {
  max-height: 500rpx;
}
.farm-item {
  padding: 20rpx;
  border-radius: 12rpx;
  margin-bottom: 8rpx;
  background: #fafafa;
  border: 2rpx solid transparent;
}
.farm-item.selected {
  background: #e8f5e9;
  border-color: #2e7d32;
}
.farm-main {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.farm-name {
  font-size: 28rpx;
  font-weight: 500;
  color: #333;
}
.farm-code {
  font-size: 22rpx;
  color: #999;
}
.farm-owner {
  font-size: 24rpx;
  color: #666;
  margin-top: 4rpx;
}
.empty-tip {
  text-align: center;
  padding: 40rpx;
  color: #999;
  font-size: 26rpx;
}
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
  width: 600rpx;
  background: #fff;
  border-radius: 20rpx;
  padding: 32rpx;
}
.modal-title {
  font-size: 32rpx;
  font-weight: 600;
  color: #333;
  margin-bottom: 24rpx;
  display: block;
}
.modal-input {
  background: #f5f5f5;
  border-radius: 12rpx;
  padding: 16rpx 20rpx;
  font-size: 28rpx;
  margin-bottom: 16rpx;
}
.modal-actions {
  display: flex;
  gap: 16rpx;
  margin-top: 8rpx;
}
.btn-cancel {
  flex: 1;
  background: #f5f5f5;
  color: #666;
  border: none;
  border-radius: 12rpx;
  padding: 16rpx;
  font-size: 28rpx;
}
.btn-confirm {
  flex: 1;
  background: #2e7d32;
  color: #fff;
  border: none;
  border-radius: 12rpx;
  padding: 16rpx;
  font-size: 28rpx;
}
.btn-confirm[disabled] {
  opacity: 0.5;
}
</style>
