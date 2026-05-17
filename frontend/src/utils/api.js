import axios from 'axios'

export const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: BASE_URL,
  timeout: 120000
})

export const dealApi = {
  listDeals: () => api.get('/api/deals'),
  getDeal: (id) => api.get(`/api/deals/${id}`),
  deleteDeal: (id) => api.delete(`/api/deals/${id}`)
}

export default api
