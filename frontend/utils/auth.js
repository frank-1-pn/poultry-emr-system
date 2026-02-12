/**
 * Token 存取工具
 */

const TOKEN_KEY = 'emr_access_token'
const REFRESH_TOKEN_KEY = 'emr_refresh_token'
const USER_KEY = 'emr_user_info'

export function getToken() {
  return uni.getStorageSync(TOKEN_KEY)
}

export function setToken(token) {
  uni.setStorageSync(TOKEN_KEY, token)
}

export function getRefreshToken() {
  return uni.getStorageSync(REFRESH_TOKEN_KEY)
}

export function setRefreshToken(token) {
  uni.setStorageSync(REFRESH_TOKEN_KEY, token)
}

export function getUserInfo() {
  const raw = uni.getStorageSync(USER_KEY)
  return raw ? JSON.parse(raw) : null
}

export function setUserInfo(user) {
  uni.setStorageSync(USER_KEY, JSON.stringify(user))
}

export function clearAuth() {
  uni.removeStorageSync(TOKEN_KEY)
  uni.removeStorageSync(REFRESH_TOKEN_KEY)
  uni.removeStorageSync(USER_KEY)
}

export function isLoggedIn() {
  return !!getToken()
}
