import json
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.middleware.cors import CORSMiddleware
from redis.asyncio import Redis
from app.core.config import settings
from app.api.rooms import router as rooms_router
from app.services.room_service import RoomService, RoomError
from app.services.game_service import GameService, GameError
from app.services.websocket_manager import WebSocketManager

@asynccontextmanager
async def lifespan(app: FastAPI):
    redis = Redis.from_url(settings.redis_url, decode_responses=True)
    await redis.ping()
    app.state.redis = redis
    app.state.room_service = RoomService(redis, settings.room_ttl_seconds)
    app.state.ws_manager = WebSocketManager()
    try:
        yield
    finally:
        await redis.aclose()

app = FastAPI(title=settings.app_name, version="1.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=settings.allowed_origins, allow_credentials=True, allow_methods=["GET", "POST"], allow_headers=["*"])
app.include_router(rooms_router)

@app.get("/health")
async def health(request: Request):
    await request.app.state.redis.ping()
    return {"status": "ok", "redis": "connected"}

@app.websocket("/ws/{room_code}/{player_id}")
async def game_socket(websocket: WebSocket, room_code: str, player_id: str):
    manager = websocket.app.state.ws_manager
    service = websocket.app.state.room_service
    code = room_code.upper()
    try:
        game = await service.get(code)
        if player_id not in game.players.values():
            await websocket.close(code=1008, reason="Not a member of this room")
            return
    except RoomError:
        await websocket.close(code=1008, reason="Room not found")
        return

    await manager.connect(code, player_id, websocket)
    await manager.send_player(code, player_id, {"type": "state", "game": game.to_dict()})
    try:
        while True:
            message = await websocket.receive_json()
            event = message.get("type")
            try:
                game = await service.get(code)
                if event == "make_move":
                    game = GameService.make_move(game, player_id, message.get("row"), message.get("col"))
                elif event == "request_rematch":
                    game = GameService.request_rematch(game, player_id)
                elif event == "leave_room":
                    await websocket.close(code=1000)
                    break
                else:
                    raise GameError("Unknown event type.")
                await service.save(game)
                await manager.broadcast(code, {"type": "state", "game": game.to_dict()})
            except (GameError, RoomError, TypeError) as exc:
                await manager.send_player(code, player_id, {"type": "error", "message": str(exc)})
    except WebSocketDisconnect:
        manager.disconnect(code, player_id)
        try:
            game = await service.get(code)
            game.disconnected.add(player_id)
            await service.save(game)
            await manager.broadcast(code, {"type": "player_disconnected", "player_id": player_id, "game": game.to_dict()})
        except RoomError:
            pass
    finally:
        manager.disconnect(code, player_id)
