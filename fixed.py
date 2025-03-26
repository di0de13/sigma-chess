import chess  
board = chess.Board()  
move = next(iter(board.legal_moves))
board.push(move)  