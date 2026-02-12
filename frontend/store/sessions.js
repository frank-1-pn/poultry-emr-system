import { defineStore } from 'pinia'
import { get, post, patch } from '../utils/request'

export const useSessionsStore = defineStore('sessions', {
  state: () => ({
    list: [],
    total: 0,
    farms: [],
    loading: false,
  }),

  getters: {
    groupedByFarm(state) {
      const groups = {}
      for (const session of state.list) {
        const farmName = session.farm?.name || '未分组'
        if (!groups[farmName]) {
          groups[farmName] = { farm: session.farm, sessions: [] }
        }
        groups[farmName].sessions.push(session)
      }
      return groups
    },
  },

  actions: {
    async fetchSessions(params = {}) {
      this.loading = true
      try {
        const query = new URLSearchParams({
          page: params.page || 1,
          page_size: params.pageSize || 50,
          ...(params.status ? { status: params.status } : {}),
          ...(params.farm_id ? { farm_id: params.farm_id } : {}),
          ...(params.tag ? { tag: params.tag } : {}),
        }).toString()
        const res = await get(`/conversations?${query}`)
        this.list = res.items || []
        this.total = res.total || 0
      } finally {
        this.loading = false
      }
    },

    async fetchFarms(search = '') {
      const query = search ? `?search=${encodeURIComponent(search)}` : ''
      const res = await get(`/farms${query}`)
      this.farms = res.items || []
      return this.farms
    },

    async createSession(data = {}) {
      const res = await post('/conversations', data)
      return res
    },

    async createFarm(data) {
      const res = await post('/farms', data)
      // 刷新列表
      await this.fetchFarms()
      return res
    },

    async updateTags(conversationId, tags) {
      const res = await patch(`/conversations/${conversationId}/tags`, { tags })
      // 更新本地
      const idx = this.list.findIndex(s => s.id === conversationId)
      if (idx >= 0) {
        this.list[idx].tags = tags
      }
      return res
    },
  },
})
