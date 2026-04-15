import request from './request'

export const tradeApi = {
  createOrder: (payload) => request.post('/orders', payload),
  listOrders: () => request.get('/orders'),
  confirmOrder: (id) => request.post(`/orders/${id}/confirm`),
  cancelOrder: (id) => request.post(`/orders/${id}/cancel`),
  createReview: (payload) => request.post('/reviews', payload),
  listReviews: (productId) => request.get(`/reviews/products/${productId}`),
  listSellerReviews: (sellerId) => request.get(`/reviews/sellers/${sellerId}`),
  addFavorite: (productId) => request.post(`/favorites/${productId}`),
  removeFavorite: (productId) => request.delete(`/favorites/${productId}`),
  listFavorites: () => request.get('/favorites'),
  captureHistory: (productId) => request.post(`/history/products/${productId}/view`),
  recentHistory: () => request.get('/history/recent'),
  recommendHome: () => request.get('/recommendations/home'),
  recommendRelated: (productId) => request.get(`/recommendations/products/${productId}/related`)
}
