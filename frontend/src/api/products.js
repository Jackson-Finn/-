import request from './request'

export const productApi = {
  list: (params = {}) => request.get('/products', { params }),
  detail: (id) => request.get(`/products/${id}`),
  create: (payload) => request.post('/products', payload),
  update: (id, payload) => request.put(`/products/${id}`, payload),
  offShelf: (id) => request.post(`/products/${id}/off-shelf`),
  search: (params = {}) => request.get('/search/products', { params }),
  suggest: (params = {}) => request.get('/search/suggest', { params }),
  uploadInit: (payload) => request.post('/media/upload-init', payload),
  uploadComplete: (payload) => request.post('/media/complete', payload),
  aiDraft: (payload) => request.post('/ai/products/draft', payload),
  aiModeration: (payload) => request.post('/ai/moderation/preview', payload),
  chatSummary: (payload) => request.post('/ai/chat/summary', payload)
}
