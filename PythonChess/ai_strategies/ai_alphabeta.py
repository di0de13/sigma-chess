# ai_strategies/ai_alphabeta.py
"""
Implements the Alpha-Beta Pruning algorithm, an optimization of Minimax.
"""

import math
import random
from chess_logic import Board, Move, PIECE_TYPES, PAWN, KNIGHT, BISHOP, ROOK, QUEEN, KING, WHITE, BLACK, CHECKMATE, STALEMATE
from constants import PIECE_NAMES # Optional

# --- Evaluation Constants (same as Minimax) ---
PIECE_VALUES = { PAWN: 100, KNIGHT: 320, BISHOP: 330, ROOK: 500, QUEEN: 900, KING: 20000 }
MATE_SCORE = 100000
DRAW_SCORE = 0

# --- Evaluation Function (can be reused or redefined if needed) ---
# Using the same evaluation function as Minimax for simplicity
def evaluate_board(board: Board) -> int:
    """ Static evaluation of the board state (material count). Positive for White advantage."""
    game_state = board.get_game_state()
    if game_state != 0:
        outcome = board.get_outcome()
        turn = board.turn
        if game_state == CHECKMATE:
            return -MATE_SCORE if turn == WHITE else MATE_SCORE
        elif game_state in [STALEMATE, 3, 4, 5]:
            return DRAW_SCORE

    material_score = 0
    for piece in board.board:
        if piece:
            value = PIECE_VALUES.get(piece.type, 0)
            material_score += value if piece.color == WHITE else -value
    return material_score

# --- Alpha-Beta Algorithm ---
def alphabeta(board: Board, depth: int, alpha: float, beta: float, maximizing_player: bool):
    """
    Recursive Alpha-Beta function.

    Args:
        board: The current board state.
        depth: Current search depth remaining.
        alpha: Best score found so far for the maximizing player (lower bound).
        beta: Best score found so far for the minimizing player (upper bound).
        maximizing_player: True if maximizing (White), False otherwise (Black).

    Returns:
        A tuple: (best_score, best_move_for_this_node)
    """
    if depth == 0 or board.is_game_over():
        return evaluate_board(board), None

    legal_moves = board.get_legal_moves()
    if not legal_moves:
        return evaluate_board(board), None

    best_move_found = None

    # --- Move Ordering (Simple Example: Captures first) ---
    # Good move ordering significantly improves pruning effectiveness.
    # This is a very basic example. More sophisticated ordering would be better.
    ordered_moves = sorted(legal_moves, key=lambda m: m.is_capture(), reverse=True)
    # random.shuffle(legal_moves) # Less effective than ordering

    if maximizing_player:
        max_eval = -math.inf
        for move in ordered_moves: # Iterate through ordered moves
            board.make_move(move)
            eval_score, _ = alphabeta(board, depth - 1, alpha, beta, False)
            board.unmake_move()

            if eval_score > max_eval:
                max_eval = eval_score
                best_move_found = move # Update best move at this node

            alpha = max(alpha, eval_score) # Update alpha (best option for maximizer)
            if beta <= alpha:
                break # Beta cutoff (minimizer has a better option elsewhere)

        return max_eval, best_move_found

    else: # Minimizing player
        min_eval = math.inf
        for move in ordered_moves: # Iterate through ordered moves
            board.make_move(move)
            eval_score, _ = alphabeta(board, depth - 1, alpha, beta, True)
            board.unmake_move()

            if eval_score < min_eval:
                min_eval = eval_score
                best_move_found = move # Update best move at this node

            beta = min(beta, eval_score) # Update beta (best option for minimizer)
            if beta <= alpha:
                break # Alpha cutoff (maximizer has a better option elsewhere)

        return min_eval, best_move_found

# --- AI Interface Function ---
def find_best_move(board: Board) -> Move | None:
    """
    Finds the best move using the Alpha-Beta Pruning algorithm.

    Args:
        board (chess_logic.Board): The current board state.

    Returns:
        chess_logic.Move: The best move found, or None if no legal moves exist.
    """
    search_depth = 3 # Alpha-beta can often search deeper than plain Minimax in the same time. Try 3 or 4.
    print(f"AI (AlphaBeta Depth {search_depth}) thinking...")

    is_maximizing = (board.turn == WHITE)

    # Initial call with alpha = -infinity, beta = +infinity
    score, best_move = alphabeta(board, search_depth, -math.inf, math.inf, is_maximizing)

    if best_move is None:
         print("AlphaBeta returned no move. Falling back to random.")
         legal_moves = board.get_legal_moves()
         return random.choice(legal_moves) if legal_moves else None

    print(f"AlphaBeta suggests move: {best_move} (Eval: {score} from White's perspective)")
    return best_move


# Example usage (optional)
if __name__ == '__main__':
    test_board = Board()
    print("Finding AlphaBeta move for initial board state...")
    move = find_best_move(test_board)
    if move:
        print(f"Chosen AlphaBeta move: {move}")
    else:
        print("No legal moves found.")