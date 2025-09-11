import axios from 'axios'

const API = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  timeout: 20000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 요청 인터셉터
API.interceptors.request.use(
  (config) => {
    console.log('API 요청:', config.method?.toUpperCase(), config.url)
    return config
  },
  (error) => {
    console.error('API 요청 오류:', error)
    return Promise.reject(error)
  }
)

// 응답 인터셉터 (에러처리)
API.interceptors.response.use(
  (response) => {
    console.log('API 응답:', response.status, response.data)
    return response
  },
  (error) => {
    console.error('API 응답 오류:', error.response?.data || error.message)
    return Promise.reject(error)
  }
)

export const chatAPI = {
  sendMessage: (message) => API.post('/api/chat', { message }),
  getDrugs: () => API.get('/api/drugs'),
  getDrugInfo: (drugName) => API.get(`/api/drugs/${drugName}`),

  // RAG 성능 테스트용 (개발 중에만!! 나중에 삭제)
  testEmbedding: (query) => API.get(`/api/embedding-test/${encodeURIComponent(query)}`)
}

export default API