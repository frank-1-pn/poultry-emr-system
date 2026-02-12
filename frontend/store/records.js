import { defineStore } from 'pinia'
import { get } from '../utils/request'

export const useRecordsStore = defineStore('records', {
  state: () => ({
    list: [],
    total: 0,
    page: 1,
    pageSize: 20,
    currentRecord: null,
    treatmentTimeline: [],
    loading: false,
  }),

  actions: {
    async fetchRecords(params = {}) {
      this.loading = true
      try {
        const query = new URLSearchParams({
          page: params.page || this.page,
          page_size: params.pageSize || this.pageSize,
          ...(params.status ? { status: params.status } : {}),
          ...(params.poultry_type ? { poultry_type: params.poultry_type } : {}),
        }).toString()
        const res = await get(`/records?${query}`)
        this.list = res.items
        this.total = res.total
        this.page = res.page
      } finally {
        this.loading = false
      }
    },

    async fetchRecord(id) {
      this.loading = true
      try {
        this.currentRecord = await get(`/records/${id}`)
        return this.currentRecord
      } finally {
        this.loading = false
      }
    },

    async fetchTimeline(recordId) {
      this.treatmentTimeline = await get(`/records/${recordId}/treatment-timeline`)
      return this.treatmentTimeline
    },
  },
})
