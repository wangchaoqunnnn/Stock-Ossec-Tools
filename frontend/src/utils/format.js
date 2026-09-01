// 数值格式化工具

// 涨跌颜色 class
export function trendClass(v) {
  if (v === null || v === undefined || Number.isNaN(v)) return 'flat'
  if (v > 0) return 'up'
  if (v < 0) return 'down'
  return 'flat'
}

// 带正负号
export function signed(v, digits = 2) {
  if (v === null || v === undefined || Number.isNaN(v)) return '--'
  const s = Number(v).toFixed(digits)
  return Number(v) > 0 ? `+${s}` : s
}

// 涨跌幅字符串
export function pct(v, digits = 2) {
  if (v === null || v === undefined || Number.isNaN(v)) return '--'
  return `${signed(v, digits)}%`
}

// 普通数字
export function num(v, digits = 2) {
  if (v === null || v === undefined || Number.isNaN(v)) return '--'
  return Number(v).toFixed(digits)
}

// 大额：万 / 亿
export function mv(v) {
  if (v === null || v === undefined || Number.isNaN(v)) return '--'
  const n = Number(v)
  if (Math.abs(n) >= 1e8) return `${(n / 1e8).toFixed(2)}亿`
  if (Math.abs(n) >= 1e4) return `${(n / 1e4).toFixed(2)}万`
  return n.toFixed(0)
}

// 成交量（手 -> 万手/亿手）
export function volume(v) {
  if (v === null || v === undefined || Number.isNaN(v)) return '--'
  const n = Number(v)
  if (n >= 1e8) return `${(n / 1e8).toFixed(2)}亿手`
  if (n >= 1e4) return `${(n / 1e4).toFixed(2)}万手`
  return `${n.toFixed(0)}手`
}
