import request from './request'

export const productApi = {
  list: (params = {}) => request.get('/products', { params }),
  mine: () => request.get('/products/mine'),
  detail: (id) => request.get(`/products/${id}`),
  create: (payload) => request.post('/products', payload),
  update: (id, payload) => request.put(`/products/${id}`, payload),
  resubmit: (id) => request.post(`/products/${id}/resubmit`),
  offShelf: (id) => request.post(`/products/${id}/off-shelf`),
  search: (params = {}) => request.get('/search/products', { params }),
  suggest: (params = {}) => request.get('/search/suggest', { params }),
  uploadInit: (payload) => request.post('/media/upload-init', payload),
  uploadFile(assetId, file) {
    const formData = new FormData()
    formData.append('file', file)
    return request.post(`/media/${assetId}/file`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  },
  uploadComplete: (payload) => request.post('/media/complete', payload),
  aiDraft: (payload) => request.post('/ai/products/draft', payload),
  aiListingCopilot: (payload) => request.post('/ai/listings/copilot', payload),
  aiSearchAssist: (payload) => request.post('/ai/search/assist', payload),
  aiPurchaseInsights: (payload) => request.post('/ai/purchase/insights', payload),
  aiModeration: (payload) => request.post('/ai/moderation/preview', payload),
  chatSummary: (payload) => request.post('/ai/chat/summary', payload),
  chatCopilot: (payload) => request.post('/ai/chat/copilot', payload)
}
