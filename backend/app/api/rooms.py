import secrets
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from app.services.room_service import RoomService, RoomError

router = APIRouter(prefix="/api/rooms", tags=["rooms"])

class CreateRoomResponse(BaseModel):
    room_code: str
    player_id: str
    symbol: str
    game: dict

class JoinRoomRequest(BaseModel):
    player_id: str = Field(min_length=20, max_length=100)

def get_service(request: Request) -> RoomService:
    return request.app.state.room_service

@router.post("", response_model=CreateRoomResponse)
async def create_room(service: RoomService = Depends(get_service)):
    player_id = secrets.token_urlsafe(32)
    try:
        game, symbol = await service.create(player_id)
    except RoomError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return CreateRoomResponse(room_code=game.room_code, player_id=player_id, symbol=symbol, game=game.to_dict())

@router.post("/{room_code}/join", response_model=CreateRoomResponse)
async def join_room(room_code: str, body: JoinRoomRequest, service: RoomService = Depends(get_service)):
    try:
        game, symbol = await service.join(room_code, body.player_id)
    except RoomError as exc:
        raise HTTPException(status_code=404 if "not found" in str(exc).lower() else 409, detail=str(exc)) from exc
    return CreateRoomResponse(room_code=game.room_code, player_id=body.player_id, symbol=symbol, game=game.to_dict())
