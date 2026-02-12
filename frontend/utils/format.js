/**
 * 格式化工具
 */

/**
 * 格式化日期为 YYYY-MM-DD
 */
export function formatDate(dateStr) {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${day}`
}

/**
 * 格式化日期时间为 YYYY-MM-DD HH:mm
 */
export function formatDateTime(dateStr) {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  const h = String(d.getHours()).padStart(2, '0')
  const min = String(d.getMinutes()).padStart(2, '0')
  return `${y}-${m}-${day} ${h}:${min}`
}

/**
 * 相对时间
 */
export function timeAgo(dateStr) {
  if (!dateStr) return ''
  const now = Date.now()
  const diff = now - new Date(dateStr).getTime()
  const minutes = Math.floor(diff / 60000)
  if (minutes < 1) return '刚刚'
  if (minutes < 60) return `${minutes}分钟前`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours}小时前`
  const days = Math.floor(hours / 24)
  if (days < 30) return `${days}天前`
  return formatDate(dateStr)
}

/**
 * 严重度标签
 */
const SEVERITY_MAP = {
  mild: { text: '轻微', color: '#4caf50' },
  moderate: { text: '中度', color: '#ff9800' },
  severe: { text: '严重', color: '#f44336' },
  critical: { text: '危重', color: '#9c27b0' },
}

export function severityLabel(severity) {
  return SEVERITY_MAP[severity]?.text || severity || '未知'
}

export function severityColor(severity) {
  return SEVERITY_MAP[severity]?.color || '#999999'
}

/**
 * 状态标签
 */
const STATUS_MAP = {
  active: '进行中',
  completed: '已完成',
  paused: '已暂停',
  cancelled: '已取消',
  draft: '草稿',
  pending: '待处理',
  confirmed: '已确认',
  dismissed: '已忽略',
}

export function statusLabel(status) {
  return STATUS_MAP[status] || status || ''
}
