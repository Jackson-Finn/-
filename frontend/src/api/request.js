import axios from 'axios'

const request = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 10000
})

request.interceptors.request.use((config) => {
  const token = localStorage.getItem('advanced-marketplace-token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

request.interceptors.response.use(
  (response) => response.data.data,
  (error) => {
    const responseMessage = error.response?.data?.message
    const detailMessage = Array.isArray(error.response?.data?.detail)
      ? error.response.data.detail.map((item) => item?.msg).filter(Boolean).join('；')
      : error.response?.data?.detail
    const message = responseMessage || detailMessage || error.message || 'Request failed'
    return Promise.reject(new Error(message))
  }
)

export default request
