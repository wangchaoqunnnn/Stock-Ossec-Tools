// 自动刷新组合式函数：组件挂载后按固定间隔执行 fn，卸载时自动清理。
//
// 用法：
//   useAutoRefresh(loadData, 15000)
//
// 行为：
//   - 挂载时立即执行一次 fn（immediate: false 可关闭）；
//   - 每 interval 毫秒执行一次；
//   - 页面从后台切回（visibilitychange -> visible）时立即执行一次，
//     保证切回页面看到最新数据（refreshOnVisible: false 可关闭）。
import { onMounted, onUnmounted } from 'vue'

export function useAutoRefresh(fn, interval = 15000, { immediate = true, refreshOnVisible = true } = {}) {
  let timer = null

  const stop = () => {
    if (timer) {
      clearInterval(timer)
      timer = null
    }
  }

  const start = () => {
    stop()
    timer = setInterval(fn, interval)
  }

  const onVisible = () => {
    if (document.visibilityState === 'visible') fn()
  }

  if (immediate) fn()

  onMounted(() => {
    start()
    if (refreshOnVisible) document.addEventListener('visibilitychange', onVisible)
  })

  onUnmounted(() => {
    stop()
    if (refreshOnVisible) document.removeEventListener('visibilitychange', onVisible)
  })

  return { start, stop }
}
