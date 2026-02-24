import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/api'

export const useAuthStore = defineStore('auth', () => {
  const router = useRouter()
  
  const token = ref(localStorage.getItem('token') || '')
  const user = ref<any>(null)
  
  const isAuthenticated = computed(() => !!token.value)
  
  const login = async (form: any) => {
    try {
      // Use URLSearchParams for OAuth2 standard compatibility
      const params = new URLSearchParams()
      params.append('username', form.username)
      params.append('password', form.password)
      
      console.log('Sending login request...')
      const res = await api.post('/v1/login/access-token', params)
      console.log('Login response:', res)
      
      token.value = res.data.access_token
      localStorage.setItem('token', token.value)
      
      await fetchUser()
      return true
    } catch (error) {
      console.error('Login failed in store:', error)
      return false
    }
  }
  
  const fetchUser = async () => {
    if (!token.value) return
    try {
      const res = await api.get('/v1/users/me')
      user.value = res.data
    } catch (error) {
      logout()
    }
  }
  
  const logout = () => {
    token.value = ''
    user.value = null
    localStorage.removeItem('token')
    // router.push('/login')
    window.location.href = '/login'
  }
  
  return {
    token,
    user,
    isAuthenticated,
    login,
    logout,
    fetchUser
  }
})
