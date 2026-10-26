# Minimax Tic-Tac-Toe

A Tic-Tac-Toe game where you play against an AI that uses the **Minimax algorithm**.
Made as an AI case study project.

The AI runs on a Python (Flask) backend. Every finished game is saved in a SQLite
database, so scores and history stay after you refresh the page.

## Features

- Play as X or O against the AI
- 3 AI modes:
  - **Optimal (Minimax)**: searches every possible future move, so it never loses
  - **Depth-limited**: only looks 3 moves ahead and guesses after that
  - **Random**: picks any empty cell (baseline to compare against)
- Shows nodes visited, search depth, best score and decision time for each AI move
- Search tree showing the score of every move the AI considered
- Game history and win/draw/loss totals saved in a database
- Unit tests for the algorithm and the API

## Project structure

```
minimax-tictactoe/
├── backend/
│   ├── app.py            Flask server + API routes
│   ├── minimax.py        Minimax algorithm
│   ├── database.py       SQLite helper functions
│   └── requirements.txt
├── frontend/
│   ├── index.html
│   ├── style.css
│   └── script.js         Calls the backend API
├── tests/
│   └── test_backend.py
└── README.md
```

## How to run

You need Python 3.9 or newer.

```bash
cd minimax-tictactoe
pip install -r backend/requirements.txt
python backend/app.py
```

Then open **http://localhost:5000** in your browser.

The database file `backend/games.db` is created automatically the first time.

To use a different port:

```bash
PORT=8000 python backend/app.py
```

## Run the tests

```bash
python -m pytest tests
```

## API

| Method | URL | What it does |
|---|---|---|
| GET | `/api/health` | Check that the server is running |
| POST | `/api/move` | Get the AI's move for a board |
| POST | `/api/games` | Save a finished game |
| GET | `/api/games?limit=10` | Recent games, newest first |
| DELETE | `/api/games` | Clear all saved games |
| GET | `/api/stats` | Win / draw / loss totals (overall and per mode) |

**Example: ask the AI for a move**

```bash
curl -X POST http://localhost:5000/api/move \
  -H "Content-Type: application/json" \
  -d '{"board": ["X","","","","","","","",""], "ai": "O", "mode": "optimal"}'
```

Response:

```json
{
  "move": 4,
  "nodes": 7331,
  "depth": 8,
  "score": 0,
  "ms": 25,
  "branches": [{"i": 1, "score": -7}, {"i": 4, "score": 0}, ...]
}
```

Board cells are numbered 0 to 8:

```
0 | 1 | 2
3 | 4 | 5
6 | 7 | 8
```

## How Minimax works (short version)

- The AI is **MAX** and tries to get the highest score.
- The human is **MIN** and is assumed to pick the lowest score for the AI.
- Finished games are scored: **+10** if the AI wins, **0** for a draw, **-10** if the AI loses.
- The score is adjusted by depth, so the AI prefers a quick win and a slow loss.
- The AI tries every move, follows each one to the end of the game, and picks the move with the best guaranteed score.

Tic-Tac-Toe has fewer than 9! = 362,880 move orders, so the full search is fast.
For bigger games like chess this is far too slow, and you would need depth limits and
alpha-beta pruning.

## Demo steps for class

1. Start in **Optimal** mode and play a few moves. Point out nodes visited and search depth.
2. Show the search tree: the green box is the move the AI picked.
3. Try to beat it. You can't; the best you can get is a draw.
4. Switch to **Random** and win easily. This shows why looking ahead matters.
5. Open the game history to compare results across modes.
