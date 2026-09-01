// 后端 API 封装
const BASE = '/api'

async function request(path, params) {
  const url = new URL(BASE + path, window.location.origin)
  if (params) {
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== null && v !== '') url.searchParams.set(k, v)
    })
  }
  const resp = await fetch(url.toString())
  const payload = await resp.json().catch(() => ({ code: -1, message: '响应解析失败', data: null }))
  if (!resp.ok || payload.code !== 0) {
    throw new Error(payload.message || `请求失败 (${resp.status})`)
  }
  return payload.data
}

export const fetchIndices = (market = 'cn') => request('/indices', { market })

export const searchStocks = (keyword, count = 8) => request('/stock/search', { keyword, count })

export const fetchQuote = (code) => request('/stock/quote', { code })

export const fetchWatchList = (params = {}) =>
  request('/watch/list', { sort: params.sort, order: params.order, page: params.page, page_size: params.pageSize })
