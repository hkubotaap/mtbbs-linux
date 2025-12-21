import axios from 'axios'

const apiClient = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
})

export const adminAPI = {
  // Users
  getUsers: () => apiClient.get('/admin/users'),
  getUser: (userId: string) => apiClient.get(`/admin/users/${userId}`),
  createUser: (data: any) => apiClient.post('/admin/users', data),
  deleteUser: (userId: string) => apiClient.delete(`/admin/users/${userId}`),

  // Boards
  getBoards: () => apiClient.get('/admin/boards'),
  getBoard: (boardId: number) => apiClient.get(`/admin/boards/${boardId}`),
  createBoard: (data: any) => apiClient.post('/admin/boards', data),
  deleteBoard: (boardId: number) => apiClient.delete(`/admin/boards/${boardId}`),

  // Stats
  getStats: () => apiClient.get('/admin/stats'),
  getConnections: () => apiClient.get('/admin/connections'),

  // Messages
  getMessages: (category?: string) =>
    apiClient.get(`/admin/messages${category ? `?category=${category}` : ''}`),
  getMessage: (messageKey: string) => apiClient.get(`/admin/messages/${messageKey}`),
  createMessage: (data: any) => apiClient.post('/admin/messages', data),
  updateMessage: (messageKey: string, data: any) =>
    apiClient.put(`/admin/messages/${messageKey}`, data),
  deleteMessage: (messageKey: string) => apiClient.delete(`/admin/messages/${messageKey}`),
  initializeMessages: () => apiClient.post('/admin/messages/initialize'),
}

export const bbsAPI = {
  getBoards: () => apiClient.get('/bbs/boards'),
  getBoardMessages: (boardId: number, skip: number = 0, limit: number = 20) =>
    apiClient.get(`/bbs/boards/${boardId}/messages?skip=${skip}&limit=${limit}`),
  getMessage: (boardId: number, messageNo: number) =>
    apiClient.get(`/bbs/boards/${boardId}/messages/${messageNo}`),
  createMessage: (data: any) => apiClient.post('/bbs/messages', data),
}

export default apiClient
