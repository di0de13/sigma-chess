import random

def get_best_move(board):
    from pieces import create_piece
    possible_moves = []
    for row in range(8):
        for col in range(8):
            piece = board.get_piece_at((row, col))
            if piece and piece[0] == "b":
                piece_obj = create_piece("black", piece[1], (row, col))
                moves = piece_obj.get_valid_moves(board)
                for move in moves:
                    if board.is_valid_move((row, col), move):
                        possible_moves.append(((row, col), move))
    return random.choice(possible_moves) if possible_moves else None