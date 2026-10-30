import unittest
from app.models.game import Game
from app.services.game_service import GameService, GameError

class GameServiceTests(unittest.TestCase):
    def setUp(self):
        self.game = Game("ABC234")
        self.game.players = {"X": "player-x", "O": "player-o"}
        self.game.status = "PLAYING"

    def test_valid_move_switches_turn(self):
        GameService.make_move(self.game, "player-x", 0, 0)
        self.assertEqual(self.game.board[0][0], "X")
        self.assertEqual(self.game.current_turn, "O")

    def test_rejects_wrong_turn(self):
        with self.assertRaisesRegex(GameError, "not your turn"):
            GameService.make_move(self.game, "player-o", 0, 0)

    def test_rejects_occupied_cell(self):
        self.game.board[0][0] = "X"
        with self.assertRaisesRegex(GameError, "occupied"):
            GameService.make_move(self.game, "player-x", 0, 0)

    def test_rejects_out_of_range(self):
        with self.assertRaises(GameError):
            GameService.make_move(self.game, "player-x", 3, 0)

    def test_rejects_non_player(self):
        with self.assertRaises(GameError):
            GameService.make_move(self.game, "stranger", 0, 0)

    def test_rejects_finished_game(self):
        self.game.status = "FINISHED"
        with self.assertRaises(GameError):
            GameService.make_move(self.game, "player-x", 0, 0)

    def test_winning_move_finishes_game(self):
        self.game.board = [["X", "X", None], ["O", "O", None], [None] * 3]
        self.game.current_turn = "X"
        GameService.make_move(self.game, "player-x", 0, 2)
        self.assertEqual(self.game.winner, "X")
        self.assertEqual(self.game.status, "FINISHED")

    def test_draw_finishes_game(self):
        self.game.board = [["X", "O", "X"], ["X", "O", "O"], ["O", "X", None]]
        self.game.current_turn = "X"
        GameService.make_move(self.game, "player-x", 2, 2)
        self.assertEqual(self.game.status, "FINISHED")
        self.assertIsNone(self.game.winner)

    def test_rematch_requires_finished_game(self):
        with self.assertRaises(GameError):
            GameService.request_rematch(self.game, "player-x")

    def test_rematch_resets_after_both_votes(self):
        self.game.status = "FINISHED"
        self.game.winner = "X"
        GameService.request_rematch(self.game, "player-x")
        self.assertEqual(self.game.status, "FINISHED")
        GameService.request_rematch(self.game, "player-o")
        self.assertEqual(self.game.status, "PLAYING")
        self.assertEqual(self.game.board, [[None] * 3 for _ in range(3)])
        self.assertEqual(self.game.current_turn, "X")

    def test_rematch_rejects_non_player(self):
        self.game.status = "FINISHED"
        with self.assertRaises(GameError):
            GameService.request_rematch(self.game, "stranger")
