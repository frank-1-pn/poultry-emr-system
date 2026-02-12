<template>
  <view class="sessions-page">
    <!-- 顶部操作栏 -->
    <view class="top-bar">
      <button class="btn-create" @click="goCreate">新建会话</button>
    </view>

    <!-- 状态筛选 -->
    <scroll-view scroll-x class="filter-row">
      <view
        v-for="f in statusFilters"
        :key="f.value"
        class="filter-tag"
        :class="{ active: currentStatus === f.value }"
        @click="setStatus(f.value)"
      >
        <text>{{ f.label }}</text>
      </view>
    </scroll-view>

    <!-- 标签筛选 -->
    <scroll-view scroll-x class="filter-row tag-filter" v-if="allTags.length">
      <view
        v-for="t in allTags"
        :key="t"
        class="filter-tag tag-chip"
        :class="{ active: currentTag === t }"
        @click="setTag(t)"
      >
        <text>{{ t }}</text>
      </view>
    </scroll-view>

    <!-- 按养殖场分组 -->
    <scroll-view scroll-y class="session-list">
      <template v-if="Object.keys(grouped).length">
        <view v-for="(group, farmName) in grouped" :key="farmName" class="farm-group">
          <view class="group-header" @click="toggleGroup(farmName)">
            <text class="group-name">{{ farmName }}</text>
            <text class="group-count">{{ group.sessions.length }} 个会话</text>
            <text class="group-arrow">{{ collapsed[farmName] ? '>' : 'v' }}</text>
          </view>
          <template v-if="!collapsed[farmName]">
            <session-card
              v-for="s in group.sessions"
              :key="s.id"
              :session="s"
              @click="goChat(s)"
            />
          </template>
        </view>
      </template>
      <view class="empty-state" v-else-if="!sessionsStore.loading">
        <text class="empty-text">暂无会话</text>
        <text class="empty-sub">点击上方按钮新建会话</text>
      </view>
      <view class="loading-tip" v-if="sessionsStore.loading">
        <text>加载中...</text>
      </view>
    </scroll-view>
  </view>
</template>

<script>
import { useSessionsStore } from '../../store/sessions'
import SessionCard from '../../components/session-card/session-card.vue'

export default {
  components: { SessionCard },
  setup() {
    return { sessionsStore: useSessionsStore() }
  },
  data() {
    return {
      currentStatus: '',
      currentTag: '',
      collapsed: {},
      statusFilters: [
        { label: '全部', value: '' },
        { label: '进行中', value: 'active' },
        { label: '已完成', value: 'completed' },
        { label: '已暂停', value: 'paused' },
      ],
    }
  },
  computed: {
    grouped() {
      return this.sessionsStore.groupedByFarm
    },
    allTags() {
      const tags = new Set()
      for (const s of this.sessionsStore.list) {
        if (s.tags) s.tags.forEach(t => tags.add(t))
      }
      return Array.from(tags)
    },
  },
  onShow() {
    this.loadData()
  },
  methods: {
    loadData() {
      this.sessionsStore.fetchSessions({
        status: this.currentStatus || undefined,
        tag: this.currentTag || undefined,
      })
    },
    setStatus(val) {
      this.currentStatus = val
      this.loadData()
    },
    setTag(val) {
      this.currentTag = this.currentTag === val ? '' : val
      this.loadData()
    },
    toggleGroup(name) {
      this.collapsed[name] = !this.collapsed[name]
    },
    goCreate() {
      uni.navigateTo({ url: '/pages/sessions/create' })
    },
    goChat(session) {
      uni.navigateTo({ url: `/pages/chat/index?conversationId=${session.id}` })
    },
  },
}
</script>

<style lang="scss" scoped>
.sessions-page {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: #f5f5f5;
}
.top-bar {
  padding: 16rpx 24rpx;
  background: #fff;
}
.btn-create {
  background: #2e7d32;
  color: #fff;
  border: none;
  border-radius: 12rpx;
  padding: 16rpx;
  font-size: 30rpx;
  width: 100%;
}
.filter-row {
  white-space: nowrap;
  padding: 12rpx 24rpx;
  background: #fff;
  border-bottom: 1rpx solid #f0f0f0;
}
.tag-filter {
  border-bottom: none;
  padding-bottom: 8rpx;
}
.filter-tag {
  display: inline-block;
  padding: 8rpx 28rpx;
  border-radius: 24rpx;
  background: #f5f5f5;
  margin-right: 12rpx;
  font-size: 26rpx;
  color: #666;
}
.filter-tag.active {
  background: #e8f5e9;
  color: #2e7d32;
  font-weight: 500;
}
.tag-chip {
  background: #f3e5f5;
  color: #7b1fa2;
}
.tag-chip.active {
  background: #ce93d8;
  color: #fff;
}
.session-list {
  flex: 1;
  padding: 16rpx 24rpx;
  padding-bottom: 120rpx;
}
.farm-group {
  margin-bottom: 16rpx;
}
.group-header {
  display: flex;
  align-items: center;
  padding: 12rpx 16rpx;
  background: #e3f2fd;
  border-radius: 12rpx;
  margin-bottom: 8rpx;
}
.group-name {
  font-size: 28rpx;
  font-weight: 600;
  color: #1565c0;
  flex: 1;
}
.group-count {
  font-size: 22rpx;
  color: #666;
  margin-right: 12rpx;
}
.group-arrow {
  font-size: 24rpx;
  color: #999;
}
.empty-state {
  text-align: center;
  padding: 120rpx 0;
}
.empty-text {
  font-size: 32rpx;
  color: #999;
  display: block;
  margin-bottom: 12rpx;
}
.empty-sub {
  font-size: 26rpx;
  color: #ccc;
}
.loading-tip {
  text-align: center;
  padding: 24rpx;
  color: #999;
  font-size: 24rpx;
}
</style>
