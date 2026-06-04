import asyncio
import logging
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
        if not self.connections.get(user_id):
            self.connections.pop(user_id, None)

    def is_connected(self, user_id: int) -> bool:
        return bool(self.connections.get(user_id))

    async def _broadcast(self, event: str, payload: dict) -> None:
        for user_id, connections in list(self.connections.items()):
            for connection in list(connections):
                try:
                    await connection.send_json({"event": event, "payload": payload})
                except Exception:
                    pass

    def broadcast(self, event: str, payload: dict) -> None:
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self._broadcast(event, payload))
        except RuntimeError:
            asyncio.run(self._broadcast(event, payload))

    async def push(self, user_id: int, event: str, payload: dict) -> None:
        for connection in list(self.connections.get(user_id, [])):
            await connection.send_json({"event": event, "payload": payload})


manager = ConnectionManager()
