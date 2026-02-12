/**
 * uni.request 封装，Token 自动注入，401 拦截
 */

import { getToken, getRefreshToken, setToken, clearAuth } from './auth'

const BASE_URL = '/api/v1'

let isRefreshing = false
let pendingRequests = []

function request(options) {
  return new Promise((resolve, reject) => {
    const token = getToken()
    const header = {
      'Content-Type': 'application/json',
      ...(options.header || {}),
    }
    if (token) {
      header['Authorization'] = `Bearer ${token}`
    }

    uni.request({
      url: BASE_URL + options.url,
      method: options.method || 'GET',
      data: options.data,
      header,
      success: async (res) => {
        if (res.statusCode === 401) {
          // 尝试刷新 token
          if (!isRefreshing) {
            isRefreshing = true
            try {
              await refreshToken()
              isRefreshing = false
              // 重放等待中的请求
              pendingRequests.forEach(cb => cb())
              pendingRequests = []
              // 重试当前请求
              const result = await request(options)
              resolve(result)
            } catch (e) {
              isRefreshing = false
              pendingRequests = []
              clearAuth()
              uni.reLaunch({ url: '/pages/login/index' })
              reject(new Error('登录已过期'))
            }
          } else {
            // 等待刷新完成后重试
            return new Promise((r) => {
              pendingRequests.push(async () => {
                const result = await request(options)
                r(result)
              })
            }).then(resolve).catch(reject)
          }
          return
        }
        if (res.statusCode >= 400) {
          const msg = res.data?.detail || '请求失败'
          uni.showToast({ title: msg, icon: 'none' })
          reject(new Error(msg))
          return
        }
        resolve(res.data)
      },
      fail: (err) => {
        uni.showToast({ title: '网络异常', icon: 'none' })
        reject(err)
      },
    })
  })
}

async function refreshToken() {
  const refreshTokenVal = getRefreshToken()
  if (!refreshTokenVal) throw new Error('No refresh token')

  return new Promise((resolve, reject) => {
    uni.request({
      url: BASE_URL + '/auth/refresh',
      method: 'POST',
      header: { 'Content-Type': 'application/json' },
      data: { refresh_token: refreshTokenVal },
      success: (res) => {
        if (res.statusCode === 200 && res.data.access_token) {
          setToken(res.data.access_token)
          resolve()
        } else {
          reject(new Error('刷新失败'))
        }
      },
      fail: reject,
    })
  })
}

export const get = (url, data) => request({ url, method: 'GET', data })
export const post = (url, data) => request({ url, method: 'POST', data })
export const put = (url, data) => request({ url, method: 'PUT', data })
export const patch = (url, data) => request({ url, method: 'PATCH', data })
export const del = (url, data) => request({ url, method: 'DELETE', data })

export default request
