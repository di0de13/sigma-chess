# ai_strategies/ai_minimax.py
"""
Implements a basic Minimax AI strategy with a simple evaluation function.
"""

import math
import random
from chess_logic import Board, Move, PIECE_TYPES, PAWN, KNIGHT, BISHOP, ROOK, QUEEN, KING, WHITE, BLACK, CHECKMATE, STALEMATE
from constants import PIECE_NAMES # Optional: for printing piece names if needed

# --- Evaluation Constants ---
# Simple material values
PIECE_VALUES = {
    PAWN: 100,
    KNIGHT: 320,
    BISHOP: 330,
    ROOK: 500,
    QUEEN: 900,
    KING: 20000 # High value, but typically not counted in material evaluation directly
}
# Add bonuses for piece positions later (piece-square tables)

# Define values for checkmate and stalemate
MATE_SCORE = 100000 # A large number indicating checkmate
DRAW_SCORE = 0      # Score for stalemate or other draws

# --- Evaluation Function ---
def evaluate_board(board: Board) -> int:
    """
    Evaluates the board state from the perspective of the current player.
    Positive score means advantage for White, negative for Black.
    Basic implementation: Material count.
    """
    # Check for terminal states first
    game_state = board.get_game_state()
    if game_state != 0: # Using 0 for ONGOING from constants might be better
         outcome = board.get_outcome() # Winner (WHITE/BLACK) or None for draw
         turn = board.turn # Whose turn it IS

         if game_state == CHECKMATE:
             # The player whose turn it IS has been checkmated.
             # So the *other* player delivered the mate.
             # Return a high score favoring the winner.
             return -MATE_SCORE if turn == WHITE else MATE_SCORE # If white's turn -> black won -> negative score
         elif game_state in [STALEMATE, 3, 4, 5]: # Draw states
             return DRAW_SCORE

    # If not terminal, calculate material score
    material_score = 0
    for piece in board.board:
        if piece:
            value = PIECE_VALUES.get(piece.type, 0)
            if piece.color == WHITE:
                material_score += value
            else:
                material_score -= value

    # Return score relative to whose turn it *currently* is in the evaluation call.
    # Minimax expects score from the perspective of the *maximizing* player (usually White).
    # This function directly returns White's advantage (positive) or Black's (negative).
    return material_score

# --- Minimax Algorithm ---
def minimax(board: Board, depth: int, maximizing_player: bool):
    """
    Recursive Minimax function.

    Args:
        board: The current board state (chess_logic.Board).
        depth: Current search depth remaining.
        maximizing_player: True if the current player is maximizing (White), False otherwise (Black).

    Returns:
        A tuple: (best_score, best_move_for_this_node)
        'best_move_for_this_node' is None at leaf nodes or when no moves are possible.
    """
    if depth == 0 or board.is_game_over():
        # Return static evaluation when depth limit reached or game over
        # Evaluation should be from White's perspective always for consistency here
        return evaluate_board(board), None

    legal_moves = board.get_legal_moves()
    if not legal_moves: # Should be caught by is_game_over, but safety check
        return evaluate_board(board), None


    best_move_found = None # Keep track of the best move at this level

    if maximizing_player:
        max_eval = -math.inf
        # Optional: Shuffle moves for variety if scores are equal
        # random.shuffle(legal_moves)
        for move in legal_moves:
            board.make_move(move)
            eval_score, _ = minimax(board, depth - 1, False) # Recursive call for minimizing player
            board.unmake_move()

            if eval_score > max_eval:
                max_eval = eval_score
                best_move_found = move
            # Simple tie-breaking (optional): could prefer shorter paths to mate, etc.
            # Or just keep the first best move found.

        return max_eval, best_move_found

    else: # Minimizing player (Black)
        min_eval = math.inf
        # Optional: Shuffle moves
        # random.shuffle(legal_moves)
        for move in legal_moves:
            board.make_move(move)
            eval_score, _ = minimax(board, depth - 1, True) # Recursive call for maximizing player
            board.unmake_move()

            if eval_score < min_eval:
                min_eval = eval_score
                best_move_found = move

        return min_eval, best_move_found

# --- AI Interface Function ---
def find_best_move(board: Board) -> Move | None:
    """
    Finds the best move using the Minimax algorithm.

    Args:
        board (chess_logic.Board): The current board state.

    Returns:
        chess_logic.Move: The best move found, or None if no legal moves exist.
    """
    search_depth = 2 # Adjust depth: Higher = Stronger but Slower. Start with 2 or 3.
    print(f"AI (Minimax Depth {search_depth}) thinking...")

    # Determine if the current player to move is the maximizing player (White)
    is_maximizing = (board.turn == WHITE)

    # Call the minimax function
    # The score returned is from White's perspective. The move returned is the best for the current player.
    score, best_move = minimax(board, search_depth, is_maximizing)

    if best_move is None:
         print("Minimax returned no move. Falling back to random.")
         legal_moves = board.get_legal_moves()
         return random.choice(legal_moves) if legal_moves else None

    # The score is relative to White. We don't necessarily need it here, just the move.
    print(f"Minimax suggests move: {best_move} (Eval: {score} from White's perspective)")
    return best_move


# Example usage (optional)
if __name__ == '__main__':
    test_board = Board()
    print("Finding Minimax move for initial board state...")
    move = find_best_move(test_board)
    if move:
        print(f"Chosen Minimax move: {move}")
    else:
        print("No legal moves found.")

    # Example Evaluation
    # test_board.make_move(Move(square_to_index('e2'), square_to_index('e4')))
    # print(f"Evaluation after e4: {evaluate_board(test_board)}")