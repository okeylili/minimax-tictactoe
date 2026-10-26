"""
Flask server for the Minimax Tic-Tac-Toe project.

- Serves the frontend (../frontend)
- POST /api/move     -> AI picks a move using minimax
- POST /api/games    -> save a finished game
- GET  /api/games    -> recent games
- GET  /api/stats    -> win / draw / loss totals
- DELETE /api/games  -> clear history

Run:  python app.py   then open http://localhost:5000
"""

import os

from flask import Flask, jsonify, request, send_from_directory

import database
from minimax import check_winner, choose_move

FRONTEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "frontend")
VALID_MODES = ("optimal", "depth", "random")

app = Flask(__name__, static_folder=None)
database.init_db()


def bad_request(message):
    return jsonify({"error": message}), 400


def validate_board(board):
    if not isinstance(board, list) or len(board) != 9:
        return "board must be a list of 9 cells"
    if any(cell not in ("X", "O", "") for cell in board):
        return "cells can only be 'X', 'O' or ''"
    x, o = board.count("X"), board.count("O")
    if not (x == o or x == o + 1):
        return "board has an impossible number of X and O"
    return None


# ---------- frontend ----------

@app.route("/")
def index():
    return send_from_directory(FRONTEND_DIR, "index.html")


@app.route("/<path:filename>")
def static_files(filename):
    return send_from_directory(FRONTEND_DIR, filename)


# ---------- api ----------

@app.route("/api/health")
def health():
    return jsonify({"status": "ok"})


@app.route("/api/move", methods=["POST"])
def ai_move():
    data = request.get_json(silent=True) or {}
    board = data.get("board")
    ai = data.get("ai", "O")
    mode = data.get("mode", "optimal")

    error = validate_board(board)
    if error:
        return bad_request(error)
    if ai not in ("X", "O"):
        return bad_request("ai must be 'X' or 'O'")
    if mode not in VALID_MODES:
        return bad_request(f"mode must be one of {VALID_MODES}")
    if check_winner(board):
        return bad_request("game is already over")

    human = "O" if ai == "X" else "X"
    result = choose_move(board, ai, human, mode)
    return jsonify(result)


@app.route("/api/games", methods=["POST"])
def save_game():
    data = request.get_json(silent=True) or {}
    winner = data.get("winner")
    mode = data.get("mode")
    human_symbol = data.get("human_symbol")
    moves = data.get("moves", [])
    total_nodes = data.get("total_nodes", 0)

    if winner not in ("human", "ai", "draw"):
        return bad_request("winner must be 'human', 'ai' or 'draw'")
    if mode not in VALID_MODES:
        return bad_request("invalid mode")
    if human_symbol not in ("X", "O"):
        return bad_request("human_symbol must be 'X' or 'O'")
    if not isinstance(moves, list) or not all(isinstance(m, int) and 0 <= m <= 8 for m in moves):
        return bad_request("moves must be a list of cell numbers 0-8")

    game_id = database.save_game(winner, mode, human_symbol, moves, int(total_nodes or 0))
    return jsonify({"id": game_id, "stats": database.get_stats()}), 201


@app.route("/api/games", methods=["GET"])
def list_games():
    limit = min(request.args.get("limit", 10, type=int), 50)
    return jsonify(database.recent_games(limit))


@app.route("/api/games", methods=["DELETE"])
def delete_games():
    database.clear_games()
    return jsonify({"cleared": True, "stats": database.get_stats()})


@app.route("/api/stats")
def stats():
    return jsonify(database.get_stats())


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
