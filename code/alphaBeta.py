import chess

def evaluate(board):
    """
    Evaluate the board state based on piece values and board control.
    
    Args:
        board (chess.Board): Current chess board state
    
    Returns:
        float: Evaluation score (positive favors white, negative favors black)
    """
    # 基本子力价值评估
    piece_values = {
        chess.PAWN: 100,   # 增加精度
        chess.KNIGHT: 320,  # 调整子力价值
        chess.BISHOP: 330,
        chess.ROOK: 500,
        chess.QUEEN: 900,
        chess.KING: 20000   # 王的价值设置很高
    }
    
    # 额外的位置奖励表（示例）
    pawn_table = [
        0,  0,  0,  0,  0,  0,  0,  0,
        50, 50, 50, 50, 50, 50, 50, 50,
        10, 10, 20, 30, 30, 20, 10, 10,
        5,  5, 10, 25, 25, 10,  5,  5,
        0,  0,  0, 20, 20,  0,  0,  0,
        5, -5,-10,  0,  0,-10, -5,  5,
        5, 10, 10,-20,-20, 10, 10,  5,
        0,  0,  0,  0,  0,  0,  0,  0
    ]
    
    # 评估函数计算
    white_eval = 0
    black_eval = 0
    
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece is not None:
            # 子力价值
            value = piece_values[piece.piece_type]
            
            # 位置价值（以白方视角）
            if piece.color == chess.WHITE:
                # 使用位置表提升棋子位置价值
                if piece.piece_type == chess.PAWN:
                    value += pawn_table[square]
                white_eval += value
            else:
                # 黑方，反转位置表
                if piece.piece_type == chess.PAWN:
                    value += pawn_table[chess.square_mirror(square)]
                black_eval += value
    
    # 根据当前轮到谁走给予额外调整
    multiplier = 1 if board.turn == chess.WHITE else -1
    
    return (white_eval - black_eval) * multiplier

def minimax(board, depth, alpha, beta, maximizing_player):
    """
    Alpha-Beta剪枝的Minimax算法
    
    Args:
        board (chess.Board): 当前棋盘状态
        depth (int): 搜索深度
        alpha (float): Alpha值
        beta (float): Beta值
        maximizing_player (bool): 是否为最大化玩家（白方）
    
    Returns:
        float: 当前局面评估值
    """
    # 到达搜索深度或游戏结束
    if depth == 0 or board.is_game_over():
        return evaluate(board)
    
    if maximizing_player:
        max_eval = float('-inf')
        for move in board.legal_moves:
            board.push(move)
            eval = minimax(board, depth - 1, alpha, beta, False)
            board.pop()
            
            max_eval = max(max_eval, eval)
            alpha = max(alpha, eval)
            
            # Alpha-Beta剪枝
            if beta <= alpha:
                break  # Beta剪枝
        return max_eval
    else:
        min_eval = float('inf')
        for move in board.legal_moves:
            board.push(move)
            eval = minimax(board, depth - 1, alpha, beta, True)
            board.pop()
            
            min_eval = min(min_eval, eval)
            beta = min(beta, eval)
            
            # Alpha-Beta剪枝
            if beta <= alpha:
                break  # Alpha剪枝
        return min_eval

def find_best_move(board, depth):
    """
    使用Alpha-Beta剪枝找到最佳走法
    
    Args:
        board (chess.Board): 当前棋盘状态
        depth (int): 搜索深度
    
    Returns:
        chess.Move: 最佳走法
    """
    best_move = None
    best_value = float('-inf')
    alpha = float('-inf')
    beta = float('inf')
    
    # 对所有合法走法进行评估
    for move in board.legal_moves:
        board.push(move)
        move_value = minimax(board, depth - 1, alpha, beta, False)
        board.pop()
        
        # 更新最佳走法
        if move_value > best_value:
            best_value = move_value
            best_move = move
        
        # 更新alpha值
        alpha = max(alpha, move_value)
    
    return best_move

def play_game():
    """
    模拟一场国际象棋对局
    """
    board = chess.Board()
    print("初始棋盘：")
    print(board)
    
    move_count = 0
    max_moves = 100  # 防止无限循环
    
    while not board.is_game_over() and move_count < max_moves:
        # 白方走棋
        if board.turn == chess.WHITE:
            print("\n白方走棋：")
            white_move = find_best_move(board, depth=3)
            board.push(white_move)
            print(f"白方选择走法：{white_move}")
        
        # 黑方走棋
        else:
            print("\n黑方走棋：")
            black_move = find_best_move(board, depth=3)
            board.push(black_move)
            print(f"黑方选择走法：{black_move}")
        
        print(board)
        move_count += 1
    
    # 输出游戏结果
    print("\n游戏结果：")
    print(board.result())

if __name__ == "__main__":
    play_game()