import request from './request'

export const authApi = {
  register: (payload) => request.post('/auth/register', payload),
  login: (payload) => request.post('/auth/login', payload),
  me: () => request.get('/auth/me'),
  workspace: () => request.get('/me/workspace')
}
