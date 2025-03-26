import chess
import random
board = chess.Board()while not board.is_game_over():
    move = random.choice(list(board.legal_moves))
    board.push(move)