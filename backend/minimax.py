"""
Minimax logic for Tic-Tac-Toe.

Board is a list of 9 strings: "X", "O" or "" (empty).
Index layout:
    0 | 1 | 2
    3 | 4 | 5
    6 | 7 | 8
"""

import random
import time

WIN_LINES = [
    (0, 1, 2), (3, 4, 5), (6, 7, 8),  # rows
    (0, 3, 6), (1, 4, 7), (2, 5, 8),  # columns
    (0, 4, 8), (2, 4, 6),             # diagonals
]


def check_winner(board):
    """Returns {"player": "X"/"O"/"draw", "line": [...]} or None if game is still going."""
    for a, b, c in WIN_LINES:
        if board[a] and board[a] == board[b] == board[c]:
            return {"player": board[a], "line": [a, b, c]}
    if all(board):
        return {"player": "draw", "line": []}
    return None


def empty_cells(board):
    return [i for i, v in enumerate(board) if v == ""]


def terminal_score(board, depth, ai, human):
    """+10 for AI win, -10 for AI loss, 0 for draw. Depth makes faster wins score higher."""
    result = check_winner(board)
    if result is None:
        return None
    if result["player"] == ai:
        return 10 - depth
    if result["player"] == human:
        return depth - 10
    return 0


def heuristic(board, ai, human):
    """Rough guess used when depth-limited search stops early: centre and corners are worth more."""
    value = 0
    if board[4] == ai:
        value += 2
    elif board[4] == human:
        value -= 2
    for i in (0, 2, 6, 8):
        if board[i] == ai:
            value += 1
        elif board[i] == human:
            value -= 1
    return value


class Search:
    def __init__(self, ai, human, depth_limit=None):
        self.ai = ai
        self.human = human
        self.depth_limit = depth_limit
        self.nodes = 0
        self.max_depth = 0

    def minimax(self, board, maximizing, depth):
        self.nodes += 1
        self.max_depth = max(self.max_depth, depth)

        score = terminal_score(board, depth, self.ai, self.human)
        if score is not None:
            return score

        if self.depth_limit is not None and depth >= self.depth_limit:
            return heuristic(board, self.ai, self.human)

        if maximizing:
            best = float("-inf")
            for i in empty_cells(board):
                board[i] = self.ai
                best = max(best, self.minimax(board, False, depth + 1))
                board[i] = ""
            return best
        else:
            best = float("inf")
            for i in empty_cells(board):
                board[i] = self.human
                best = min(best, self.minimax(board, True, depth + 1))
                board[i] = ""
            return best


def choose_move(board, ai, human, mode="optimal"):
    """
    Picks the AI move and returns the analysis shown on the dashboard.
    mode: "optimal" | "depth" | "random"
    """
    board = list(board)  # don't change the caller's board
    start = time.perf_counter()
    moves = empty_cells(board)

    if not moves or check_winner(board):
        return {"move": None, "nodes": 0, "depth": 0, "score": None, "ms": 0, "branches": []}

    if mode == "random":
        move = random.choice(moves)
        return {
            "move": move,
            "nodes": 1,
            "depth": 1,
            "score": 0,
            "ms": 1,
            "branches": [{"i": m, "score": 0} for m in moves],
        }

    search = Search(ai, human, depth_limit=3 if mode == "depth" else None)
    best_score = float("-inf")
    best_move = None
    branches = []

    for i in moves:
        board[i] = ai
        score = search.minimax(board, False, 1)
        board[i] = ""
        branches.append({"i": i, "score": score})
        if score > best_score:
            best_score = score
            best_move = i

    ms = max(1, round((time.perf_counter() - start) * 1000))

    return {
        "move": best_move,
        "nodes": search.nodes,
        "depth": search.max_depth,
        "score": best_score,
        "ms": ms,
        "branches": branches,
    }
