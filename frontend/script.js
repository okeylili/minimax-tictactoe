// Minimax Tic-Tac-Toe - frontend
// The AI move is calculated on the server (POST /api/move).
// Finished games are saved to the database (POST /api/games).

const API = '/api';

const boardEl = document.getElementById('board');
const statusText = document.getElementById('statusText');
const turnBadge = document.getElementById('turnBadge');
const difficultyEl = document.getElementById('difficulty');
const treeEl = document.getElementById('tree');
const serverStatus = document.getElementById('serverStatus');
const historyBody = document.getElementById('historyBody');

let human = 'X';
let ai = 'O';
let board = Array(9).fill('');
let moves = [];          // order of cells played this game
let totalNodes = 0;      // nodes the AI searched this game
let gameOver = false;
let thinking = false;
let lastAnalysis = emptyAnalysis();

const wins = [[0,1,2],[3,4,5],[6,7,8],[0,3,6],[1,4,7],[2,5,8],[0,4,8],[2,4,6]];
const modeNames = { optimal: 'Minimax', depth: 'Depth-limited', random: 'Random' };


function emptyAnalysis() {
  return { nodes: 0, depth: 0, score: null, ms: null, move: null, branches: [] };
}

// same check as the server, used for drawing the winning line
function winner(b) {
  for (const [a, c, d] of wins) {
    if (b[a] && b[a] === b[c] && b[a] === b[d]) return { player: b[a], line: [a, c, d] };
  }
  if (b.every(Boolean)) return { player: 'draw', line: [] };
  return null;
}


// ---------- api helpers ----------

async function api(path, options = {}) {
  const res = await fetch(API + path, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Request failed');
  return data;
}

function setServerStatus(online) {
  serverStatus.classList.toggle('offline', !online);
  serverStatus.querySelector('span').textContent = online ? 'Server connected' : 'Server offline';
}

async function checkServer() {
  try {
    await api('/health');
    setServerStatus(true);
    return true;
  } catch {
    setServerStatus(false);
    statusText.textContent = 'Cannot reach the server. Start it with: python backend/app.py';
    return false;
  }
}


// ---------- drawing ----------

function render() {
  boardEl.innerHTML = '';
  board.forEach((v, i) => {
    const cell = document.createElement('button');
    cell.className = 'cell ' + (v ? v.toLowerCase() + ' filled' : '');
    cell.textContent = v;
    cell.onclick = () => humanMove(i);
    boardEl.appendChild(cell);
  });
  const res = winner(board);
  if (res && res.line.length) {
    res.line.forEach(i => boardEl.children[i].classList.add('win'));
  }
}

function updateMetrics() {
  const a = lastAnalysis;
  document.getElementById('nodes').textContent = a.nodes.toLocaleString();
  document.getElementById('depth').textContent = a.depth;
  document.getElementById('bestScore').textContent = a.score === null ? '—' : (a.score > 0 ? '+' : '') + a.score;
  document.getElementById('decisionTime').textContent = a.ms === null ? '—' : a.ms + ' ms';
  document.getElementById('treeCount').textContent = a.branches.length ? a.branches.length + ' CANDIDATE STATES' : '0 STATES';
}

function renderTree() {
  if (!lastAnalysis.branches.length) {
    treeEl.innerHTML = '<div class="tree-empty">Make a move to see the search tree.</div>';
    return;
  }
  const best = Math.max(...lastAnalysis.branches.map(b => b.score));
  const branchesHtml = lastAnalysis.branches.map(b => {
    const cls = b.score > 0 ? 'pos' : b.score < 0 ? 'neg' : 'zero';
    return `
      <div class="branch ${b.score === best ? 'best' : ''}">
        <div class="branch-line"></div>
        <div class="move-node">
          <div class="move">MOVE ${b.i + 1}</div>
          <div class="score ${cls}">${b.score > 0 ? '+' : ''}${b.score}</div>
        </div>
      </div>`;
  }).join('');

  treeEl.innerHTML = `
    <div class="tree-root">
      <div class="root-node">CURRENT STATE • MAX</div>
      <div class="branches">${branchesHtml}</div>
    </div>`;
}

function showScores(stats) {
  document.getElementById('humanScore').textContent = stats.human;
  document.getElementById('drawScore').textContent = stats.draw;
  document.getElementById('aiScore').textContent = stats.ai;
}

async function loadHistory() {
  try {
    const games = await api('/games?limit=10');
    if (!games.length) {
      historyBody.innerHTML = '<tr><td colspan="7" class="empty">No games yet.</td></tr>';
      return;
    }
    const label = { human: 'You won', ai: 'AI won', draw: 'Draw' };
    historyBody.innerHTML = games.map(g => `
      <tr>
        <td>${g.id}</td>
        <td class="result-${g.winner}">${label[g.winner]}</td>
        <td>${modeNames[g.mode] || g.mode}</td>
        <td>${g.human_symbol}</td>
        <td>${g.moves.split(',').map(m => Number(m) + 1).join(' → ')}</td>
        <td>${Number(g.total_nodes).toLocaleString()}</td>
        <td>${g.played_at}</td>
      </tr>`).join('');
  } catch {
    historyBody.innerHTML = '<tr><td colspan="7" class="empty">Could not load history.</td></tr>';
  }
}

async function loadStats() {
  try {
    showScores(await api('/stats'));
  } catch {
    // server offline, scores stay at 0
  }
}


// ---------- game flow ----------

function humanMove(i) {
  if (gameOver || thinking || board[i]) return;
  board[i] = human;
  moves.push(i);
  render();
  if (checkEnd()) return;
  aiTurn();
}

async function aiTurn() {
  thinking = true;
  turnBadge.textContent = 'AI THINKING';
  statusText.textContent = 'The AI is thinking…';
  document.getElementById('analysisState').textContent = 'SEARCHING';

  try {
    const result = await api('/move', {
      method: 'POST',
      body: JSON.stringify({ board, ai, mode: difficultyEl.value }),
    });

    lastAnalysis = result;
    totalNodes += result.nodes;
    if (result.move !== null) {
      board[result.move] = ai;
      moves.push(result.move);
    }

    render();
    updateMetrics();
    renderTree();
    document.getElementById('analysisState').textContent = 'DECISION READY';

    const cell = result.move === null ? 'none' : 'cell ' + (result.move + 1);
    document.getElementById('decisionText').textContent =
      difficultyEl.value === 'optimal'
        ? `Minimax checked ${result.branches.length} possible moves and picked ${cell} (score ${result.score}).`
        : `${modeNames[difficultyEl.value]} mode picked ${cell}.`;

    if (!checkEnd()) {
      turnBadge.textContent = 'YOUR TURN';
      statusText.textContent = 'Your move.';
    }
    setServerStatus(true);
  } catch (err) {
    setServerStatus(false);
    statusText.textContent = 'Server error: ' + err.message;
    turnBadge.textContent = 'ERROR';
  } finally {
    thinking = false;
  }
}

function checkEnd() {
  const r = winner(board);
  if (!r) return false;
  gameOver = true;

  let result;
  if (r.player === 'draw') {
    result = 'draw';
    statusText.textContent = "It's a draw.";
    turnBadge.textContent = 'DRAW';
  } else if (r.player === human) {
    result = 'human';
    statusText.textContent = 'You win!';
    turnBadge.textContent = 'YOU WON';
  } else {
    result = 'ai';
    statusText.textContent = 'The AI wins.';
    turnBadge.textContent = 'AI WON';
  }

  saveGame(result);
  return true;
}

async function saveGame(result) {
  try {
    const data = await api('/games', {
      method: 'POST',
      body: JSON.stringify({
        winner: result,
        mode: difficultyEl.value,
        human_symbol: human,
        moves,
        total_nodes: totalNodes,
      }),
    });
    showScores(data.stats);
    loadHistory();
  } catch (err) {
    console.error('Could not save game:', err);
  }
}

function reset() {
  board = Array(9).fill('');
  moves = [];
  totalNodes = 0;
  gameOver = false;
  thinking = false;
  lastAnalysis = emptyAnalysis();

  statusText.textContent = 'Choose a move.';
  turnBadge.textContent = 'YOUR TURN';
  document.getElementById('analysisState').textContent = 'WAITING';
  document.getElementById('decisionText').textContent = 'Make a move and the AI will respond.';

  render();
  updateMetrics();
  renderTree();

  if (human === 'O') aiTurn();   // X always goes first
}


// ---------- buttons ----------

document.querySelectorAll('.segmented button').forEach(btn => {
  btn.onclick = () => {
    document.querySelectorAll('.segmented button').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    human = btn.dataset.symbol;
    ai = human === 'X' ? 'O' : 'X';
    reset();
  };
});

document.getElementById('newGame').onclick = reset;
difficultyEl.onchange = reset;

document.getElementById('clearHistory').onclick = async () => {
  if (!confirm('Delete all saved games?')) return;
  try {
    const data = await api('/games', { method: 'DELETE' });
    showScores(data.stats);
    loadHistory();
  } catch (err) {
    alert('Could not clear history: ' + err.message);
  }
};


// ---------- start ----------

render();
updateMetrics();
renderTree();

checkServer().then(online => {
  if (online) {
    loadStats();
    loadHistory();
  }
});
