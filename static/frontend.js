let board = null;
let game = new Chess();
let lastFen = null;
let lastRating = null;

function onDragStart(source, piece, position, orientation) {
    if (game.game_over() || piece.search(/^b/) !== -1) {
        return false;
    }
}

function onDrop(source, target) {
    let move = game.move({
        from: source,
        to: target,
        promotion: 'q'
    });

    if (move === null) return 'snapback';

    updateStatus();
    if (!game.game_over()) {
        getAIMove();
    }
}

function getAIMove(isRetry = false) {
    let rating = document.getElementById('rating').value || '1200';
    lastFen = game.fen();
    lastRating = rating;

    document.getElementById('retryMove').style.display = 'none';

    let endpoint = isRetry ? '/retry_move' : '/move';

    fetch(endpoint, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ fen: lastFen, rating: lastRating })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        if (data.error) {
            throw new Error(data.error);
        }
        // Make AI's move using the UCI format
        let aiMove = game.move(data.move, {sloppy: true});
        if (aiMove === null) {
            throw new Error('Invalid move received from AI');
        }
        board.position(game.fen());
        updateStatus();
    })
    .catch(error => {
        console.error('Error:', error);
        document.getElementById('status').innerText = `Error: ${error.message || 'Unknown error occurred'}`;
        document.getElementById('retryMove').style.display = 'inline-block';
    });
}

function updateStatus() {
    let status = '';
    let statusEl = document.getElementById('status');

    if (game.in_checkmate()) {
        let winner = game.turn() === 'w' ? 'Black' : 'White';
        status = `Checkmate! ${winner} wins!`;
        statusEl.style.color = 'red';
        statusEl.style.fontWeight = 'bold';
        statusEl.style.fontSize = '24px';
    } else if (game.in_draw()) {
        status = 'Game over, drawn position';
        statusEl.style.color = 'blue';
        statusEl.style.fontWeight = 'bold';
    } else {
        status = (game.turn() === 'w' ? 'White' : 'Black') + ' to move';
        if (game.in_check()) {
            status += ', ' + (game.turn() === 'w' ? 'White' : 'Black') + ' is in check';
        }
        statusEl.style.color = 'black';
        statusEl.style.fontWeight = 'normal';
        statusEl.style.fontSize = '18px';
    }

    statusEl.innerText = status;
}

const config = {
    draggable: true,
    position: 'start',
    onDragStart: onDragStart,
    onDrop: onDrop,
    pieceTheme: (piece) => {
        const pieceMap = {
            'wP': 'wP.png', 'wN': 'wN.png', 'wB': 'wB.png',
            'wR': 'wR.png', 'wQ': 'wQ.png', 'wK': 'wK.png',
            'bP': 'bP.png', 'bN': 'bN.png', 'bB': 'bB.png',
            'bR': 'bR.png', 'bQ': 'bQ.png', 'bK': 'bK.png'
        };
        return `/static/wikipedia/${pieceMap[piece]}`;
    }
};

board = Chessboard('board', config);

document.getElementById('reset').addEventListener('click', function() {
    game.reset();
    board.start();
    updateStatus();
    document.getElementById('retryMove').style.display = 'none';
});

document.getElementById('retryMove').addEventListener('click', function() {
    getAIMove(true);
});

updateStatus();