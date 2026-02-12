import { defineStore } from 'pinia'
import { post, get } from '../utils/request'
import { setToken, setRefreshToken, setUserInfo, clearAuth, getToken } from '../utils/auth'

export const useUserStore = defineStore('user', {
  state: () => ({
    userInfo: null,
    isLoggedIn: !!getToken(),
  }),

  actions: {
    async login(username, password) {
      const res = await post('/auth/login', { username, password })
      setToken(res.access_token)
      setRefreshToken(res.refresh_token)
      this.isLoggedIn = true
      await this.fetchProfile()
      return res
    },

    async fetchProfile() {
      const user = await get('/auth/me')
      this.userInfo = user
      setUserInfo(user)
      return user
    },

    logout() {
      clearAuth()
      this.userInfo = null
      this.isLoggedIn = false
      uni.reLaunch({ url: '/pages/login/index' })
    },
  },
})
