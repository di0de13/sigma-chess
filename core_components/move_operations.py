import chess

def generate_legal_moves(board):
    """生成当前局面的所有合法走法"""
    return list(board.legal_moves)

def move_to_string(move):
    """将走法对象转换为字符串"""
    return move.uci()

def string_to_move(board, move_str):
    """将字符串转换为走法对象"""
    try:
        return chess.Move.from_uci(move_str)
    except ValueError:
        return None