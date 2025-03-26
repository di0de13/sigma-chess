class ChessBoard:
    def __init__(self):
        self.board = [
            ["bR", "bN", "bB", "bQ", "bK", "bB", "bN", "bR"],
            ["bP", "bP", "bP", "bP", "bP", "bP", "bP", "bP"],
            [None] * 8,
            [None] * 8,
            [None] * 8,
            [None] * 8,
            ["wP"] * 8,
            ["wR", "wN", "wB", "wQ", "wK", "wB", "wN", "wR"]
        ]
        self.current_turn = "white"
        self.move_log = []
        self.white_king_pos = (7, 4)
        self.black_king_pos = (0, 4)
        self.castling_rights = {
            "white": {"king_moved": False, "left_rook_moved": False, "right_rook_moved": False},
            "black": {"king_moved": False, "left_rook_moved": False, "right_rook_moved": False}
        }
        self.en_passant_target = None  # 吃过路兵的目标位置

    def move_piece(self, start_pos, end_pos):
        start_row, start_col = start_pos
        end_row, end_col = end_pos
        piece = self.board[start_row][start_col]

        # 处理王车易位
        if piece == "wK" or piece == "bK":
            if abs(end_col - start_col) == 2:  # 王移动两格，说明是易位
                if end_col == 6:  # 短易位
                    self.board[start_row][5] = self.board[start_row][7]
                    self.board[start_row][7] = None
                elif end_col == 2:  # 长易位
                    self.board[start_row][3] = self.board[start_row][0]
                    self.board[start_row][0] = None

        # 处理吃过路兵
        if piece[1] == "P" and end_pos == self.en_passant_target:
            captured_row = start_row
            self.board[captured_row][end_col] = None

        # 更新吃过路兵目标
        self.en_passant_target = None
        if piece[1] == "P" and abs(start_row - end_row) == 2:
            self.en_passant_target = (start_row + (end_row - start_row) // 2, start_col)

        # 执行移动
        self.board[end_row][end_col] = piece
        self.board[start_row][start_col] = None

        # 更新王位置
        if piece == "wK":
            self.white_king_pos = end_pos
            self.castling_rights["white"]["king_moved"] = True
        elif piece == "bK":
            self.black_king_pos = end_pos
            self.castling_rights["black"]["king_moved"] = True

        # 更新车移动状态
        if piece == "wR":
            if start_pos == (7, 0):
                self.castling_rights["white"]["left_rook_moved"] = True
            elif start_pos == (7, 7):
                self.castling_rights["white"]["right_rook_moved"] = True
        elif piece == "bR":
            if start_pos == (0, 0):
                self.castling_rights["black"]["left_rook_moved"] = True
            elif start_pos == (0, 7):
                self.castling_rights["black"]["right_rook_moved"] = True

        # 兵升变（简单实现：升变为后）
        if piece[1] == "P" and (end_row == 0 or end_row == 7):
            self.board[end_row][end_col] = piece[0] + "Q"

        self.move_log.append((start_pos, end_pos))
        self.current_turn = "black" if self.current_turn == "white" else "white"

    def is_valid_move(self, start_pos, end_pos):
        start_row, start_col = start_pos
        end_row, end_col = end_pos
        piece = self.board[start_row][start_col]
        if not piece or (self.current_turn == "white" and piece[0] != "w") or \
           (self.current_turn == "black" and piece[0] != "b"):
            return False
        if not (0 <= end_row < 8 and 0 <= end_col < 8):
            return False
        target = self.board[end_row][end_col]
        if target and target[0] == piece[0]:
            return False

        # 模拟移动并检查是否导致己方王被将军
        original_piece = self.board[end_row][end_col]
        self.board[end_row][end_col] = piece
        self.board[start_row][start_col] = None
        if piece[1] == "K":
            king_pos = end_pos
        else:
            king_pos = self.white_king_pos if self.current_turn == "white" else self.black_king_pos
        in_check = self.is_in_check(self.current_turn)
        self.board[start_row][start_col] = piece
        self.board[end_row][end_col] = original_piece
        return not in_check

    def get_piece_at(self, position):
        row, col = position
        return self.board[row][col] if 0 <= row < 8 and 0 <= col < 8 else None

    def is_in_check(self, color):
        king_pos = self.white_king_pos if color == "white" else self.black_king_pos
        opponent = "black" if color == "white" else "white"
        for row in range(8):
            for col in range(8):
                piece = self.get_piece_at((row, col))
                if piece and piece[0] == opponent[0]:
                    from pieces import create_piece
                    piece_obj = create_piece(opponent, piece[1], (row, col))
                    if king_pos in piece_obj.get_valid_moves(self):
                        return True
        return False

    def is_checkmate(self):
        if not self.is_in_check(self.current_turn):
            return False
        from pieces import create_piece
        for row in range(8):
            for col in range(8):
                piece = self.get_piece_at((row, col))
                if piece and piece[0] == self.current_turn[0]:
                    piece_obj = create_piece(self.current_turn, piece[1], (row, col))
                    for move in piece_obj.get_valid_moves(self):
                        if self.is_valid_move((row, col), move):
                            return False
        return True

    def is_stalemate(self):
        if self.is_in_check(self.current_turn):
            return False
        from pieces import create_piece
        for row in range(8):
            for col in range(8):
                piece = self.get_piece_at((row, col))
                if piece and piece[0] == self.current_turn[0]:
                    piece_obj = create_piece(self.current_turn, piece[1], (row, col))
                    if piece_obj.get_valid_moves(self):
                        return False
        return True

    def is_square_under_attack(self, pos, color):
        opponent = "black" if color == "white" else "white"
        from pieces import create_piece
        for row in range(8):
            for col in range(8):
                piece = self.get_piece_at((row, col))
                if piece and piece[0] == opponent[0]:
                    piece_obj = create_piece(opponent, piece[1], (row, col))
                    if pos in piece_obj.get_valid_moves(self):
                        return True
        return False

    def will_be_in_check_after_move(self, start_pos, end_pos):
        # 模拟移动并检查是否会导致己方被将军
        start_row, start_col = start_pos
        end_row, end_col = end_pos
        piece = self.board[start_row][start_col]
        original_piece = self.board[end_row][end_col]
        
        # 临时移动棋子
        self.board[end_row][end_col] = piece
        self.board[start_row][start_col] = None
        
        # 如果移动的是王，需要更新王的位置
        original_white_king_pos = self.white_king_pos
        original_black_king_pos = self.black_king_pos
        if piece == "wK":
            self.white_king_pos = end_pos
        elif piece == "bK":
            self.black_king_pos = end_pos
        
        # 检查是否处于将军状态
        in_check = self.is_in_check("white" if piece[0] == "w" else "black")
        
        # 恢复棋盘状态
        self.board[start_row][start_col] = piece
        self.board[end_row][end_col] = original_piece
        self.white_king_pos = original_white_king_pos
        self.black_king_pos = original_black_king_pos
        
        return in_check