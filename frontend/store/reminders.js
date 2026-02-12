import { defineStore } from 'pinia'
import { get, post } from '../utils/request'

export const useRemindersStore = defineStore('reminders', {
  state: () => ({
    list: [],
    total: 0,
    page: 1,
    loading: false,
  }),

  getters: {
    pendingCount: (state) => state.list.filter(r => r.status === 'pending').length,

    groupedByDate: (state) => {
      const groups = {}
      state.list.forEach(r => {
        const date = r.reminder_date
        if (!groups[date]) groups[date] = []
        groups[date].push(r)
      })
      return Object.entries(groups).sort(([a], [b]) => a.localeCompare(b))
    },
  },

  actions: {
    async fetchReminders(params = {}) {
      this.loading = true
      try {
        const query = new URLSearchParams({
          page: params.page || this.page,
          page_size: '50',
          ...(params.date ? { reminder_date: params.date } : {}),
          ...(params.status ? { status: params.status } : {}),
        }).toString()
        const res = await get(`/reminders?${query}`)
        this.list = res.items
        this.total = res.total
        this.page = res.page
      } finally {
        this.loading = false
      }
    },

    async confirm(reminderId) {
      const res = await post(`/reminders/${reminderId}/confirm`)
      const idx = this.list.findIndex(r => r.id === reminderId)
      if (idx >= 0) this.list[idx] = res
      return res
    },

    async dismiss(reminderId) {
      const res = await post(`/reminders/${reminderId}/dismiss`)
      const idx = this.list.findIndex(r => r.id === reminderId)
      if (idx >= 0) this.list[idx] = res
      return res
    },
  },
})
