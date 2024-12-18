from flask import Flask, request, jsonify, render_template
import chess
import openai
import os

app = Flask(__name__)

openai_api_key = os.getenv("OPENAI_API_KEY")


@app.route('/')
def index():
    return render_template('index.html')

# Convert FEN to a more human-readable format
def fen_to_readable(fen):
    board = chess.Board(fen)
    readable_board = ""
    for row in fen.split()[0].split('/'):
        expanded_row = row.replace('1', ' ').replace('2', '  ').replace('3', '   ').replace('4', '    ').replace('5', '     ').replace('6', '      ').replace('7', '       ').replace('8', '        ')
        readable_board += expanded_row + "\n"
    turn = "White" if board.turn else "Black"
    readable_board += f"Turn: {turn}\n"
    
    return readable_board.strip()

# Define a function to get a move suggestion from ChatGPT
def get_gpt_move(fen, rating, is_retry=False):
    board = chess.Board(fen)
    legal_moves = list(board.legal_moves)
    legal_moves_uci = [move.uci() for move in legal_moves]  # Get the legal moves in UCI format
    
    readable_board = fen_to_readable(fen)
    print(f"Readable Board:\n{readable_board}")  # Print the readable board
    
    retry_message = "The last move did not work. Please try again. " if is_retry else ""
    
    prompt = f"""
    {retry_message}You are playing chess at a skill level of {rating}. The current board position is as follows:
    
    {readable_board}
    
    These are the legal moves you can choose from: {', '.join(legal_moves_uci)}.
    Please provide your next move in UCI format. Make a singular move.
    """

    try:
        print(f"Prompt to GPT: {prompt}")  # Print the prompt sent to GPT
        # response = openai.chat.completions.create(
        #     model="gpt-4-turbo",
        #     messages=[
        #         {"role": "system", "content": "You are a chess engine. Provide moves in UCI format."},
        #         {"role": "user", "content": prompt}
        #     ],
        #     max_tokens=50,
        #     temperature=0.5
        # )
        response = openai.completions.create(
            model="gpt-3.5-turbo-instruct",
            prompt=prompt,
            max_tokens=50,
            temperature=0.5
        )
        # print(f"GPT Response: {response}")  # Print the GPT response
        gpt_move = response.choices[0].text.strip()
        print(f"GPT suggested move: {gpt_move}")  # Print the suggested move
        return gpt_move
    except Exception as e:
        print(f"Error in get_gpt_move: {str(e)}")
        raise


@app.route('/move', methods=['POST'])
def move():
    return process_move(is_retry=False)

@app.route('/retry_move', methods=['POST'])
def retry_move():
    return process_move(is_retry=True)

def process_move(is_retry):
    data = request.json
    fen = data['fen']
    rating = data['rating']
    
    print(f"Received FEN: {fen}")  # Print the received FEN
    print(f"Received rating: {rating}")  # Print the received rating
    
    try:
        gpt_move = get_gpt_move(fen, rating, is_retry)
        board = chess.Board(fen)
        move = chess.Move.from_uci(gpt_move)
        if move in board.legal_moves:
            board.push(move)
            new_fen = board.fen()
            print(f"New FEN after move: {new_fen}")  # Print the new FEN after the move
            return jsonify({"move": gpt_move})
        else:
            print(f"Invalid move generated: {gpt_move}")  # Print invalid move
            return jsonify({"error": "Invalid move generated"}), 400
    except Exception as e:
        print(f"Error in move route: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
