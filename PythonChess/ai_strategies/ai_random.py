# ai_strategies/ai_random.py
"""
A simple AI strategy that chooses a random legal move.
"""

import random
from chess_logic import Move, Board # Assuming chess_logic is accessible

def find_best_move(board: Board) -> Move | None:
    """
    Analyzes the board state and returns a random legal move.

    Args:
        board (chess_logic.Board): The current board state.

    Returns:
        chess_logic.Move: A randomly chosen legal move, or None if no legal moves exist.
    """
    legal_moves = board.get_legal_moves()
    if not legal_moves:
        return None
    return random.choice(legal_moves)

# Example usage (optional)
if __name__ == '__main__':
    from chess_logic import Board
    test_board = Board()
    print("Finding random move for initial board state...")
    move = find_best_move(test_board)
    if move:
        print(f"Chosen random move: {move}")
    else:
        print("No legal moves found.")
