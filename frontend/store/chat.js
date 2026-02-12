import { defineStore } from 'pinia'
import { post, get } from '../utils/request'

export const useChatStore = defineStore('chat', {
  state: () => ({
    conversation: null,
    messages: [],
    loading: false,
    sending: false,
    similarCases: [],
  }),

  actions: {
    async createConversation(recordId = null) {
      this.loading = true
      try {
        const data = recordId ? { record_id: recordId } : {}
        const res = await post('/conversations', data)
        this.conversation = res.conversation || res
        // 加载初始消息
        await this.fetchMessages(this.conversation.id)
        return this.conversation
      } finally {
        this.loading = false
      }
    },

    async loadConversation(conversationId) {
      this.loading = true
      try {
        const conv = await get(`/conversations/${conversationId}`)
        this.conversation = conv
        // 如果是暂停状态，自动恢复
        if (conv.status === 'paused') {
          const resumed = await post(`/conversations/${conversationId}/resume`)
          this.conversation = resumed
        }
        // 加载历史消息
        await this.fetchMessages(conversationId)
        return this.conversation
      } finally {
        this.loading = false
      }
    },

    async fetchMessages(conversationId) {
      const res = await get(`/conversations/${conversationId}/messages`)
      this.messages = res.items || res
      return this.messages
    },

    async sendMessage(content) {
      if (!this.conversation) return
      this.sending = true
      try {
        // 乐观添加用户消息
        this.messages.push({
          id: 'temp-' + Date.now(),
          role: 'user',
          content,
          created_at: new Date().toISOString(),
        })

        const res = await post(`/conversations/${this.conversation.id}/messages`, {
          content,
        })

        // 替换临时消息并添加 AI 回复
        if (res.message) {
          this.messages.push({
            id: res.message.id,
            role: 'assistant',
            content: res.message.content,
            created_at: res.message.created_at,
          })
        }

        // 更新对话状态
        if (res.collected_info) {
          this.conversation.collected_info = res.collected_info
        }
        if (res.confidence_scores) {
          this.conversation.confidence_scores = res.confidence_scores
        }
        if (res.similar_cases) {
          this.similarCases = res.similar_cases
        }

        return res
      } finally {
        this.sending = false
      }
    },

    async confirmRecord(confirmed = true, corrections = null) {
      if (!this.conversation) return
      const res = await post(`/conversations/${this.conversation.id}/confirm`, {
        confirmed,
        corrections,
      })
      this.conversation = res.conversation
      return res
    },

    clearChat() {
      this.conversation = null
      this.messages = []
      this.similarCases = []
    },
  },
})
