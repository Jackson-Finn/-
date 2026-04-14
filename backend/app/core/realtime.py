from collections import defaultdict

from fastapi import WebSocket


class ConnectionManager:
    def __init__(self) -> None:
        self.connections: dict[int, list[WebSocket]] = defaultdict(list)

    async def connect(self, user_id: int, websocket: WebSocket) -> None:
        await websocket.accept()
        self.connections[user_id].append(websocket)

    def disconnect(self, user_id: int, websocket: WebSocket) -> None:
        if websocket in self.connections.get(user_id, []):
            self.connections[user_id].remove(websocket)

    async def push(self, user_id: int, event: str, payload: dict) -> None:
        for connection in list(self.connections.get(user_id, [])):
            await connection.send_json({"event": event, "payload": payload})


manager = ConnectionManager()

