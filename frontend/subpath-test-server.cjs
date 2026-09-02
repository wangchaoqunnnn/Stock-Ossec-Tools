// 模拟子路径部署：http://127.0.0.1:8899/app/ 托管前端 dist，
// /app/api/* 代理到 Flask 后端 127.0.0.1:5000/api/*
const http = require('http')
const fs = require('fs')
const path = require('path')

const DIST = path.join(__dirname, 'dist')
const BACKEND = { host: '127.0.0.1', port: 5000 }
const PREFIX = '/app'

const MIME = {
  '.html': 'text/html; charset=utf-8',
  '.js': 'application/javascript; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.svg': 'image/svg+xml',
  '.png': 'image/png',
  '.json': 'application/json',
  '.ico': 'image/x-icon',
}

const server = http.createServer((req, res) => {
  const url = new URL(req.url, 'http://x')
  let pathname = decodeURIComponent(url.pathname)

  // API 代理：/app/api/* -> /api/*
  if (pathname.startsWith(PREFIX + '/api/')) {
    const targetPath = pathname.slice(PREFIX.length)
    const proxyReq = http.request(
      { host: BACKEND.host, port: BACKEND.port, path: targetPath + url.search, method: req.method, headers: req.headers },
      (proxyRes) => {
        res.writeHead(proxyRes.statusCode, proxyRes.headers)
        proxyRes.pipe(res)
      }
    )
    proxyReq.on('error', () => {
      res.writeHead(502, { 'Content-Type': 'text/plain; charset=utf-8' })
      res.end('502 Bad Gateway')
    })
    req.pipe(proxyReq)
    return
  }

  // 静态资源：去掉前缀后映射到 dist
  let rel = pathname.startsWith(PREFIX) ? pathname.slice(PREFIX.length) : pathname
  if (rel === '' || rel === '/') rel = '/index.html'
  let file = path.join(DIST, rel)
  if (!file.startsWith(DIST)) {
    res.writeHead(403); res.end('Forbidden'); return
  }
  fs.readFile(file, (err, data) => {
    if (!err) {
      res.writeHead(200, { 'Content-Type': MIME[path.extname(file).toLowerCase()] || 'application/octet-stream' })
      res.end(data)
      return
    }
    // 找不到文件 -> SPA 回退 index.html
    fs.readFile(path.join(DIST, 'index.html'), (err2, html) => {
      if (err2) { res.writeHead(404); res.end('not found'); return }
      res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' })
      res.end(html)
    })
  })
})

server.listen(8899, () => {
  console.log('sub-path test server: http://127.0.0.1:8899/app/')
})
