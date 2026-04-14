import request from './request'

export const adminApi = {
  pendingProducts: () => request.get('/admin/products/pending'),
  auditProduct: (id, payload) => request.post(`/admin/products/${id}/audit`, payload),
  reports: () => request.get('/admin/reports'),
  reportContext: (id) => request.get(`/admin/reports/${id}/context`),
  processReport: (id, payload) => request.post(`/admin/reports/${id}/process`, payload),
  appeals: () => request.get('/admin/appeals'),
  appealContext: (id) => request.get(`/admin/appeals/${id}/context`),
  reviewAppeal: (id, payload) => request.post(`/admin/appeals/${id}/review`, payload),
  roles: () => request.get('/admin/roles'),
  permissions: () => request.get('/admin/permissions'),
  users: () => request.get('/admin/users'),
  assignRoles: (userId, payload) => request.post(`/admin/users/${userId}/roles`, payload),
  overview: () => request.get('/admin/statistics/overview'),
  charts: () => request.get('/admin/statistics/charts'),
  rebuildRecommendations: () => request.post('/admin/recommendations/rebuild'),
  reindexSearch: () => request.post('/admin/search/reindex'),
  auditTasks: () => request.get('/admin/audit/tasks'),
  operations: () => request.get('/admin/operations')
}
