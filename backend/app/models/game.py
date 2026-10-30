from dataclasses import dataclass, field
from typing import Optional

@dataclass
class Game:
    room_code: str
    board: list[list[Optional[str]]] = field(default_factory=lambda: [[None] * 3 for _ in range(3)])
    players: dict[str, Optional[str]] = field(default_factory=lambda: {"X": None, "O": None})
    current_turn: str = "X"
    status: str = "WAITING"
    winner: Optional[str] = None
    winning_line: Optional[list[list[int]]] = None
    rematch_votes: set[str] = field(default_factory=set)
    disconnected: set[str] = field(default_factory=set)
    def to_dict(self) -> dict:
        return {
            "room_code": self.room_code, "board": self.board,
            "players": self.players, "current_turn": self.current_turn,
            "status": self.status, "winner": self.winner,
            "winning_line": self.winning_line,
            "rematch_votes": sorted(self.rematch_votes),
            "disconnected": sorted(self.disconnected),
        }
