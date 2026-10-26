import os
import sys
import tempfile

# use a throwaway database for tests
os.environ["DB_PATH"] = os.path.join(tempfile.mkdtemp(), "test.db")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

import pytest

from app import app
from minimax import check_winner, choose_move


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as c:
        c.delete("/api/games")
        yield c


# ---------- minimax ----------

def test_winner_detection():
    assert check_winner(["X", "X", "X", "", "", "", "", "", ""])["player"] == "X"
    assert check_winner(["X", "O", "X", "X", "O", "O", "O", "X", "X"])["player"] == "draw"
    assert check_winner([""] * 9) is None


def test_ai_takes_winning_move():
    # O can win at cell 2
    board = ["O", "O", "", "X", "X", "", "X", "", ""]
    assert choose_move(board, "O", "X")["move"] == 2


def test_ai_blocks_human():
    # X threatens 0-1-2, O must block at 2
    board = ["X", "X", "", "", "O", "", "", "", ""]
    assert choose_move(board, "O", "X")["move"] == 2


def test_perfect_play_is_a_draw():
    board = [""] * 9
    turn = "X"
    while not check_winner(board):
        other = "O" if turn == "X" else "X"
        board[choose_move(board, turn, other)["move"]] = turn
        turn = other
    assert check_winner(board)["player"] == "draw"


def test_random_mode_returns_empty_cell():
    board = ["X", "", "", "", "", "", "", "", ""]
    move = choose_move(board, "O", "X", "random")["move"]
    assert board[move] == ""


# ---------- api ----------

def test_move_endpoint(client):
    res = client.post("/api/move", json={"board": ["X"] + [""] * 8, "ai": "O", "mode": "optimal"})
    data = res.get_json()
    assert res.status_code == 200
    assert data["move"] == 4          # best reply to a corner is the centre
    assert data["nodes"] > 0


def test_move_rejects_bad_board(client):
    assert client.post("/api/move", json={"board": ["X"] * 3}).status_code == 400
    assert client.post("/api/move", json={"board": ["X", "X"] + [""] * 7}).status_code == 400


def test_save_and_stats(client):
    client.post("/api/games", json={"winner": "ai", "mode": "optimal", "human_symbol": "X", "moves": [0, 4]})
    client.post("/api/games", json={"winner": "draw", "mode": "depth", "human_symbol": "O", "moves": [4, 0]})

    stats = client.get("/api/stats").get_json()
    assert stats["ai"] == 1 and stats["draw"] == 1 and stats["total"] == 2

    games = client.get("/api/games").get_json()
    assert len(games) == 2
    assert games[0]["mode"] == "depth"   # newest first


def test_save_rejects_bad_data(client):
    res = client.post("/api/games", json={"winner": "nobody", "mode": "optimal", "human_symbol": "X"})
    assert res.status_code == 400
