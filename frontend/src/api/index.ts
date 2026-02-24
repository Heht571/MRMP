import axios from 'axios'
import { ElMessage } from 'element-plus'

const api = axios.create({
  baseURL: '/api', // Use relative path to leverage Vite proxy
  timeout: 30000,
  // Let axios set Content-Type automatically based on data type
  // headers: {
  //   'Content-Type': 'application/json'
  // }
})

api.interceptors.request.use(
  config => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`
    }
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

api.interceptors.response.use(
  response => response,
  error => {
    console.error('API Interceptor caught error:', error)
    let message = '请求失败'
    if (error.response?.data?.detail) {
      const detail = error.response.data.detail
      message = typeof detail === 'string' 
        ? detail 
        : JSON.stringify(detail)
    } else if (error.message) {
      message = error.message
    }
    
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      window.location.href = '/login'
      return Promise.reject(error)
    }

    // Prevent showing duplicate messages for 404s if handled locally
    if (error.response?.status !== 404) {
      // Use string message to avoid Element Plus crash
      ElMessage.error(String(message))
    }
    return Promise.reject(error)
  }
)

export default api
