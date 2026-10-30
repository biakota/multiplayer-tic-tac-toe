from typing import Optional

LINES = [
    [[0, 0], [0, 1], [0, 2]], [[1, 0], [1, 1], [1, 2]], [[2, 0], [2, 1], [2, 2]],
    [[0, 0], [1, 0], [2, 0]], [[0, 1], [1, 1], [2, 1]], [[0, 2], [1, 2], [2, 2]],
    [[0, 0], [1, 1], [2, 2]], [[0, 2], [1, 1], [2, 0]],
]

def find_winner(board: list[list[Optional[str]]]) -> tuple[Optional[str], Optional[list[list[int]]]]:
    for line in LINES:
        values = [board[row][col] for row, col in line]
        if values[0] is not None and values.count(values[0]) == 3:
            return values[0], line
    return None, None

def is_draw(board: list[list[Optional[str]]]) -> bool:
    return all(cell is not None for row in board for cell in row) and find_winner(board)[0] is None
