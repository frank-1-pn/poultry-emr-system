<template>
  <view class="records-page">
    <!-- 搜索栏 -->
    <view class="search-bar">
      <view class="search-row">
        <input
          v-model="keyword"
          class="search-input"
          :placeholder="searchMode === 'semantic' ? '描述症状进行语义搜索...' : '搜索病历号、诊断...'"
          @confirm="handleSearch"
        />
        <view
          class="search-mode-toggle"
          :class="{ active: searchMode === 'semantic' }"
          @click="toggleSearchMode"
        >
          <text class="toggle-text">{{ searchMode === 'semantic' ? '语义' : '关键词' }}</text>
        </view>
      </view>
    </view>

    <!-- 语义搜索结果 -->
    <view v-if="semanticResults.length" class="semantic-results">
      <view class="semantic-header">
        <text class="semantic-title">语义搜索结果</text>
        <text class="semantic-clear" @click="clearSemantic">清除</text>
      </view>
      <view
        v-for="r in semanticResults"
        :key="r.id"
        class="semantic-item"
        @click="goDetail(r)"
      >
        <view class="semantic-item-header">
          <text class="semantic-no">{{ r.record_no }}</text>
          <text class="semantic-score">{{ (r.similarity * 100).toFixed(0) }}% 相似</text>
        </view>
        <text class="semantic-info">
          {{ r.poultry_type }}
          <template v-if="r.primary_diagnosis"> - {{ r.primary_diagnosis }}</template>
        </text>
      </view>
    </view>

    <!-- 筛选 -->
    <scroll-view scroll-x class="filter-row" v-if="searchMode !== 'semantic'">
      <view
        v-for="f in filters"
        :key="f.value"
        class="filter-tag"
        :class="{ active: currentFilter === f.value }"
        @click="setFilter(f.value)"
      >
        <text>{{ f.label }}</text>
      </view>
    </scroll-view>

    <!-- 列表 -->
    <scroll-view
      scroll-y
      class="record-list"
      @scrolltolower="loadMore"
    >
      <template v-if="recordsStore.list.length">
        <record-card
          v-for="r in recordsStore.list"
          :key="r.id"
          :record="r"
          :highlight="searchMode === 'keyword' ? keyword : ''"
          @click="goDetail(r)"
        />
      </template>
      <empty-state v-else-if="!recordsStore.loading" text="暂无病历" />
      <view class="loading-more" v-if="recordsStore.loading">
        <text>加载中...</text>
      </view>
    </scroll-view>

    <!-- 新建按钮 -->
    <view class="fab-group" v-if="showFabMenu">
      <view class="fab-option" @click="goCreate">
        <text class="fab-option-text">手动录入</text>
      </view>
      <view class="fab-option" @click="goChat">
        <text class="fab-option-text">AI 录入</text>
      </view>
    </view>
    <view class="fab" @click="showFabMenu = !showFabMenu">
      <text class="fab-text">{{ showFabMenu ? '×' : '+' }}</text>
    </view>
  </view>
</template>

<script>
import { useRecordsStore } from '../../store/records'
import { get, post } from '../../utils/request'
import RecordCard from '../../components/record-card/record-card.vue'
import EmptyState from '../../components/empty-state/empty-state.vue'

export default {
  components: { RecordCard, EmptyState },
  setup() {
    return { recordsStore: useRecordsStore() }
  },
  data() {
    return {
      keyword: '',
      currentFilter: '',
      searchMode: 'keyword', // keyword | semantic
      semanticResults: [],
      showFabMenu: false,
      filters: [
        { label: '全部', value: '' },
        { label: '进行中', value: 'active' },
        { label: '已完成', value: 'completed' },
        { label: '草稿', value: 'draft' },
      ],
    }
  },
  onShow() {
    this.recordsStore.fetchRecords({ status: this.currentFilter })
  },
  methods: {
    toggleSearchMode() {
      this.searchMode = this.searchMode === 'keyword' ? 'semantic' : 'keyword'
      this.semanticResults = []
    },
    clearSemantic() {
      this.semanticResults = []
    },
    setFilter(val) {
      this.currentFilter = val
      this.recordsStore.fetchRecords({ page: 1, status: val })
    },
    async handleSearch() {
      const kw = this.keyword.trim()
      if (!kw) {
        this.recordsStore.fetchRecords({ page: 1, status: this.currentFilter })
        return
      }

      if (this.searchMode === 'semantic') {
        await this.doSemanticSearch(kw)
      } else {
        await this.doKeywordSearch(kw)
      }
    },
    async doKeywordSearch(keyword) {
      try {
        uni.showLoading({ title: '搜索中...' })
        const params = new URLSearchParams({
          keyword,
          page: '1',
          page_size: '20',
          ...(this.currentFilter ? { status: this.currentFilter } : {}),
        }).toString()
        const res = await get(`/search?${params}`)
        this.recordsStore.list = res.items || []
        this.recordsStore.total = res.total || 0
      } catch (e) {
        uni.showToast({ title: '搜索失败', icon: 'none' })
      } finally {
        uni.hideLoading()
      }
    },
    async doSemanticSearch(query) {
      try {
        uni.showLoading({ title: '语义搜索中...' })
        const res = await post('/search/semantic', { query, top_k: 10 })
        this.semanticResults = res.items || []
      } catch (e) {
        uni.showToast({ title: '搜索失败', icon: 'none' })
      } finally {
        uni.hideLoading()
      }
    },
    loadMore() {
      const store = this.recordsStore
      if (store.list.length < store.total) {
        store.fetchRecords({ page: store.page + 1, status: this.currentFilter })
      }
    },
    goDetail(record) {
      uni.navigateTo({ url: `/pages/records/detail?id=${record.id}` })
    },
    goCreate() {
      this.showFabMenu = false
      uni.navigateTo({ url: '/pages/records/create' })
    },
    goChat() {
      this.showFabMenu = false
      uni.navigateTo({ url: '/pages/sessions/index' })
    },
  },
}
</script>

<style lang="scss" scoped>
.records-page {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: #f5f5f5;
}
.search-bar {
  padding: 16rpx 24rpx;
  background: #fff;
}
.search-row {
  display: flex;
  align-items: center;
  gap: 12rpx;
}
.search-input {
  flex: 1;
  background: #f5f5f5;
  border-radius: 16rpx;
  padding: 16rpx 24rpx;
  font-size: 28rpx;
}
.search-mode-toggle {
  padding: 10rpx 20rpx;
  border-radius: 16rpx;
  background: #f5f5f5;
  flex-shrink: 0;
}
.search-mode-toggle.active {
  background: #e8f5e9;
}
.toggle-text {
  font-size: 24rpx;
  color: #666;
}
.search-mode-toggle.active .toggle-text {
  color: #2e7d32;
  font-weight: 500;
}
.semantic-results {
  background: #fff;
  margin: 16rpx 24rpx;
  border-radius: 16rpx;
  padding: 20rpx;
  box-shadow: 0 2rpx 12rpx rgba(0, 0, 0, 0.04);
}
.semantic-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16rpx;
}
.semantic-title {
  font-size: 28rpx;
  font-weight: 600;
  color: #333;
}
.semantic-clear {
  font-size: 24rpx;
  color: #999;
}
.semantic-item {
  padding: 16rpx 0;
  border-bottom: 1rpx solid #f0f0f0;
}
.semantic-item:last-child {
  border-bottom: none;
}
.semantic-item-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.semantic-no {
  font-size: 26rpx;
  font-weight: 500;
  color: #2e7d32;
}
.semantic-score {
  font-size: 22rpx;
  color: #ff9800;
  font-weight: 500;
}
.semantic-info {
  font-size: 24rpx;
  color: #666;
  margin-top: 4rpx;
}
.filter-row {
  white-space: nowrap;
  padding: 16rpx 24rpx;
  background: #fff;
  border-bottom: 1rpx solid #f0f0f0;
}
.filter-tag {
  display: inline-block;
  padding: 8rpx 28rpx;
  border-radius: 24rpx;
  background: #f5f5f5;
  margin-right: 16rpx;
  font-size: 26rpx;
  color: #666;
}
.filter-tag.active {
  background: #e8f5e9;
  color: #2e7d32;
  font-weight: 500;
}
.record-list {
  flex: 1;
  padding: 24rpx;
  padding-bottom: 120rpx;
}
.loading-more {
  text-align: center;
  padding: 24rpx;
  color: #999;
  font-size: 24rpx;
}
.fab {
  position: fixed;
  right: 32rpx;
  bottom: 200rpx;
  width: 96rpx;
  height: 96rpx;
  border-radius: 50%;
  background: #2e7d32;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 8rpx 24rpx rgba(46, 125, 50, 0.4);
}
.fab-text {
  color: #fff;
  font-size: 48rpx;
  line-height: 1;
}
.fab-group {
  position: fixed;
  right: 32rpx;
  bottom: 310rpx;
  display: flex;
  flex-direction: column;
  gap: 16rpx;
  z-index: 100;
}
.fab-option {
  background: #fff;
  border-radius: 16rpx;
  padding: 16rpx 28rpx;
  box-shadow: 0 4rpx 16rpx rgba(0, 0, 0, 0.12);
}
.fab-option-text {
  font-size: 26rpx;
  color: #333;
  white-space: nowrap;
}
</style>
