import request from './request'

export const interactionApi = {
  listSessions: () => request.get('/chat/sessions'),
  createSession: (payload) => request.post('/chat/sessions', payload),
  listMessages: (sessionId) => request.get(`/chat/sessions/${sessionId}/messages`),
  sendMessage: (sessionId, payload) => request.post(`/chat/sessions/${sessionId}/messages`, payload),
  updatePresence: (payload) => request.put('/chat/presence', payload),
  chatCopilot: (payload) => request.post('/ai/chat/copilot', payload),
  listNotifications: () => request.get('/notifications'),
  markNotificationRead: (id) => request.post(`/notifications/${id}/read`)
}

export function createWs(userId, onMessage, onStatusChange) {
  const baseUrl =
    import.meta.env.VITE_WS_BASE_URL ||
    `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/api/ws`
  const socket = new WebSocket(`${baseUrl}?user_id=${userId}`)

  socket.addEventListener('open', () => onStatusChange?.('OPEN'))
  socket.addEventListener('close', () => onStatusChange?.('CLOSED'))
  socket.addEventListener('error', () => onStatusChange?.('ERROR'))
  socket.addEventListener('message', (event) => {
    const payload = JSON.parse(event.data)
    onMessage?.(payload)
  })

  return socket
}
