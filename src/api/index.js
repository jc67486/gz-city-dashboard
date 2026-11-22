import axios from 'axios'

/**
 * 两种数据模式：
 *  - 默认（dev / 有后端）：走 /api，Vite proxy 转发到 Flask :5001
 *  - 静态（.env.production，Vercel 部署）：读 /mock/*.json，纯静态可跑
 */
const STATIC = import.meta.env.VITE_DATA_MODE === 'static'

const service = axios.create({
  baseURL: import.meta.env.VITE_API_BASE || '/api',
  timeout: 10000
})

const ERR_MAP = {
  400: '请求参数有误',
  404: '接口不存在',
  500: '服务端开小差了',
  ECONNABORTED: '请求超时，请稍后重试'
}

service.interceptors.response.use(
  (res) => {
    const body = res.data
    if (body && body.code === 0) return body.data
    return Promise.reject(new Error(body?.msg || '业务异常'))
  },
  (error) => {
    const key = error.response?.status || error.code
    const msg = ERR_MAP[key] || error.message || '网络异常'
    return Promise.reject(new Error(msg))
  }
)

/** 读静态 JSON，保持与接口相同的 { code, data, msg } 结构 */
const fromStatic = (name) =>
  axios.get(`${import.meta.env.BASE_URL}mock/${name}.json`, { timeout: 8000 })
    .then((res) => {
      const body = res.data
      if (body && body.code === 0) return body.data
      return Promise.reject(new Error(body?.msg || '静态数据异常'))
    })

export const getOverview = () =>
  STATIC ? fromStatic('overview') : service.get('/overview')

export const getTrend = (range = 6) =>
  STATIC
    ? fromStatic('trend').then((d) => ({ list: d.list.slice(-range) }))
    : service.get('/trend', { params: { range } })

export const getRegionShare = () =>
  STATIC ? fromStatic('region-share') : service.get('/region-share')

export const getCityRank = (top = 10) =>
  STATIC
    ? fromStatic('city-rank').then((d) => ({ list: d.list.slice(0, top) }))
    : service.get('/city-rank', { params: { top } })

export const getCityMap = () =>
  STATIC ? fromStatic('city-map') : service.get('/city-map')

export const getIndustry = () =>
  STATIC ? fromStatic('industry') : service.get('/industry')

export default service
