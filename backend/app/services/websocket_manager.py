from collections import defaultdict
from fastapi import WebSocket

class WebSocketManager:
    def __init__(self):
        self.connections: dict[str, dict[str, WebSocket]] = defaultdict(dict)

    async def connect(self, room: str, player_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        self.connections[room][player_id] = websocket

    def disconnect(self, room: str, player_id: str) -> None:
        self.connections.get(room, {}).pop(player_id, None)
        if room in self.connections and not self.connections[room]:
            self.connections.pop(room, None)

    async def send_player(self, room: str, player_id: str, payload: dict) -> None:
        socket = self.connections.get(room, {}).get(player_id)
        if socket:
            await socket.send_json(payload)

    async def broadcast(self, room: str, payload: dict) -> None:
        stale = []
        for player_id, socket in list(self.connections.get(room, {}).items()):
            try:
                await socket.send_json(payload)
            except Exception:
                stale.append(player_id)
        for player_id in stale:
            self.disconnect(room, player_id)
