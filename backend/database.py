"""
Small SQLite layer for saving finished games.
The database file is created automatically on first run.
"""

import os
import sqlite3

DB_PATH = os.environ.get(
    "DB_PATH",
    os.path.join(os.path.dirname(__file__), "games.db"),
)


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS games (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                winner       TEXT NOT NULL,      -- 'human', 'ai' or 'draw'
                mode         TEXT NOT NULL,      -- 'optimal', 'depth', 'random'
                human_symbol TEXT NOT NULL,      -- 'X' or 'O'
                moves        TEXT NOT NULL,      -- cell order, e.g. '4,0,8,2'
                total_nodes  INTEGER DEFAULT 0,  -- nodes the AI searched in this game
                played_at    TEXT DEFAULT (datetime('now', 'localtime'))
            )
            """
        )


def save_game(winner, mode, human_symbol, moves, total_nodes):
    with get_connection() as conn:
        cur = conn.execute(
            "INSERT INTO games (winner, mode, human_symbol, moves, total_nodes) VALUES (?, ?, ?, ?, ?)",
            (winner, mode, human_symbol, ",".join(str(m) for m in moves), total_nodes),
        )
        return cur.lastrowid


def recent_games(limit=10):
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM games ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
    return [dict(r) for r in rows]


def get_stats():
    with get_connection() as conn:
        totals = conn.execute(
            "SELECT winner, COUNT(*) AS n FROM games GROUP BY winner"
        ).fetchall()
        per_mode = conn.execute(
            "SELECT mode, winner, COUNT(*) AS n FROM games GROUP BY mode, winner"
        ).fetchall()

    stats = {"human": 0, "ai": 0, "draw": 0, "by_mode": {}}
    for row in totals:
        stats[row["winner"]] = row["n"]
    for row in per_mode:
        mode = stats["by_mode"].setdefault(row["mode"], {"human": 0, "ai": 0, "draw": 0})
        mode[row["winner"]] = row["n"]
    stats["total"] = stats["human"] + stats["ai"] + stats["draw"]
    return stats


def clear_games():
    with get_connection() as conn:
        conn.execute("DELETE FROM games")
