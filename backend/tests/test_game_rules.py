import unittest
from app.utils.game_rules import find_winner, is_draw

class GameRulesTests(unittest.TestCase):
    def test_horizontal_winner(self):
        board = [["X", "X", "X"], [None] * 3, [None] * 3]
        winner, line = find_winner(board)
        self.assertEqual(winner, "X")
        self.assertEqual(len(line), 3)

    def test_vertical_winner(self):
        board = [["O", None, None], ["O", "X", None], ["O", None, "X"]]
        self.assertEqual(find_winner(board)[0], "O")

    def test_diagonal_winner(self):
        board = [["X", None, "O"], [None, "X", "O"], ["O", None, "X"]]
        self.assertEqual(find_winner(board)[0], "X")

    def test_no_winner(self):
        self.assertEqual(find_winner([[None] * 3 for _ in range(3)]), (None, None))

    def test_draw(self):
        board = [["X", "O", "X"], ["X", "O", "O"], ["O", "X", "X"]]
        self.assertTrue(is_draw(board))

    def test_full_board_with_winner_is_not_draw(self):
        board = [["X", "X", "X"], ["O", "O", "X"], ["X", "O", "O"]]
        self.assertFalse(is_draw(board))
