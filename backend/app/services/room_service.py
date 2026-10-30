import secrets
import string
from redis.asyncio import Redis
from app.models.game import Game

ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"

class RoomError(Exception):
    pass

class RoomService:
    def __init__(self, redis: Redis, ttl_seconds: int = 86400):
        self.redis = redis
        self.ttl_seconds = ttl_seconds

    def _key(self, code: str) -> str:
        return f"ttt:room:{code}"

    async def _save(self, game: Game) -> None:
        import json
        await self.redis.set(self._key(game.room_code), json.dumps(game.to_dict()), ex=self.ttl_seconds)

    async def get(self, code: str) -> Game:
        import json
        raw = await self.redis.get(self._key(code.upper()))
        if not raw:
            raise RoomError("Room not found or expired.")
        data = json.loads(raw)
        game = Game(room_code=data["room_code"])
        game.board = data["board"]
        game.players = data["players"]
        game.current_turn = data["current_turn"]
        game.status = data["status"]
        game.winner = data.get("winner")
        game.winning_line = data.get("winning_line")
        game.rematch_votes = set(data.get("rematch_votes", []))
        game.disconnected = set(data.get("disconnected", []))
        return game

    async def create(self, player_id: str) -> tuple[Game, str]:
        for _ in range(10):
            code = "".join(secrets.choice(ALPHABET) for _ in range(6))
            if not await self.redis.exists(self._key(code)):
                game = Game(room_code=code)
                game.players["X"] = player_id
                await self._save(game)
                return game, "X"
        raise RoomError("Could not allocate a room. Please try again.")

    async def join(self, code: str, player_id: str) -> tuple[Game, str]:
        game = await self.get(code)
        if player_id in game.players.values():
            symbol = next(s for s, pid in game.players.items() if pid == player_id)
            return game, symbol
        if game.status != "WAITING" or game.players["O"] is not None:
            raise RoomError("This room is already full or in progress.")
        game.players["O"] = player_id
        game.status = "PLAYING"
        await self._save(game)
        return game, "O"

    async def save(self, game: Game) -> None:
        await self._save(game)
