from app.models.game import Game
from app.utils.game_rules import find_winner, is_draw

class GameError(Exception):
    pass

class GameService:
    @staticmethod
    def make_move(game: Game, player_id: str, row: int, col: int) -> Game:
        if game.status != "PLAYING":
            raise GameError("The game is not currently accepting moves.")
        if not (0 <= row < 3 and 0 <= col < 3):
            raise GameError("Move coordinates must be between 0 and 2.")
        symbol = next((s for s, pid in game.players.items() if pid == player_id), None)
        if symbol is None:
            raise GameError("You are not a player in this room.")
        if symbol != game.current_turn:
            raise GameError("It is not your turn.")
        if game.board[row][col] is not None:
            raise GameError("That cell is already occupied.")
        game.board[row][col] = symbol
        winner, line = find_winner(game.board)
        if winner:
            game.winner, game.winning_line, game.status = winner, line, "FINISHED"
        elif is_draw(game.board):
            game.status = "FINISHED"
        else:
            game.current_turn = "O" if symbol == "X" else "X"
        return game

    @staticmethod
    def request_rematch(game: Game, player_id: str) -> Game:
        if game.status != "FINISHED":
            raise GameError("A rematch can only be requested after the game ends.")
        if player_id not in game.players.values():
            raise GameError("You are not a player in this room.")
        game.rematch_votes.add(player_id)
        if len(game.rematch_votes) == 2:
            game.board = [[None] * 3 for _ in range(3)]
            game.current_turn = "X"
            game.winner = None
            game.winning_line = None
            game.rematch_votes.clear()
            game.disconnected.clear()
            game.status = "PLAYING"
        return game
