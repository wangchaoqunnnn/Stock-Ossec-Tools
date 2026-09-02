// 后端 API 封装
//
// 使用相对路径（如 fetch('api/indices')）：请求会跟随当前页面所在目录解析，
// 与页面同源同前缀，兼容部署在任意子路径的场景：
//   - 页面在 https://host/        -> 请求 https://host/api/...
//   - 页面在 https://host/tools/  -> 请求 https://host/tools/api/...
// 前端代码中不使用任何绝对路径（/api、/assets），由部署环境（Nginx/Flask 等）统一路由。

async function request(path, params) {
  let url = path
  if (params) {
    const qs = new URLSearchParams()
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== null && v !== '') qs.set(k, v)
    })
    const query = qs.toString()
    if (query) url += (url.includes('?') ? '&' : '?') + query
  }

  const resp = await fetch(url)

  // 先取文本再解析：若服务端返回的不是 JSON（如 404 静态页、网关错误页），
  // 给出可诊断的报错而不是笼统的"响应解析失败"
  const text = await resp.text().catch(() => '')
  let payload = null
  try {
    payload = JSON.parse(text)
  } catch (e) {
    payload = null
  }
  if (payload === null) {
    const ct = (resp.headers.get('content-type') || '').toLowerCase()
    throw new Error(
      ct.includes('json')
        ? '服务返回空响应'
        : '服务响应异常（非 JSON，疑似返回了 HTML），请检查后端服务是否启动、反向代理与部署路径（前缀）配置是否正确'
    )
  }
  if (!resp.ok || payload.code !== 0) {
    throw new Error(payload.message || `请求失败 (${resp.status})`)
  }
  return payload.data
}

export const fetchIndices = (market = 'cn') => request('api/indices', { market })

export const searchStocks = (keyword, count = 8) => request('api/stock/search', { keyword, count })

export const fetchQuote = (code) => request('api/stock/quote', { code })

export const fetchBatchQuotes = (codes) => request('api/stock/batch', { codes: codes.join(',') })

export const fetchMarketBreadth = () => request('api/rankings/market-breadth')

export const fetchIndustryFlow = (limit = 20) => request('api/rankings/industry-flow', { limit })

export const fetchStockRank = (type = 'gainers', limit = 20) => request('api/rankings/top', { type, limit })
