import request from './request'

export const userApi = {
  detail: (id) => request.get(`/users/${id}`),
  products: (id) => request.get(`/users/${id}/products`)
}
