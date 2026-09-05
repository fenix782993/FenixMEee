from collections import defaultdict
from fastapi import WebSocket
class ConnectionManager:
    def __init__(self): self.rooms = defaultdict(set)
    async def connect(self, chat_id: int, ws: WebSocket):
        await ws.accept(); self.rooms[chat_id].add(ws)
    def disconnect(self, chat_id: int, ws: WebSocket): self.rooms[chat_id].discard(ws)
    async def broadcast(self, chat_id: int, payload: dict):
        dead=[]
        for ws in list(self.rooms[chat_id]):
            try: await ws.send_json(payload)
            except Exception: dead.append(ws)
        for ws in dead: self.disconnect(chat_id, ws)
manager=ConnectionManager()
