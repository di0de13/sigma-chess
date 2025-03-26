class Piece:
    def __init__(self, color, piece_type, position):
        self.color = color
        self.piece_type = piece_type
        self.position = position

    def get_valid_moves(self, board):
        return []

class Pawn(Piece):
    def get_valid_moves(self, board):
        moves = []
        row, col = self.position
        direction = 1 if self.color == "black" else -1
        # 前进
        if not board.get_piece_at((row + direction, col)):
            moves.append((row + direction, col))
            if ((self.color == "white" and row == 6) or (self.color == "black" and row == 1)) and \
               not board.get_piece_at((row + 2 * direction, col)):
                moves.append((row + 2 * direction, col))
        # 吃子
        for dc in [-1, 1]:
            new_row, new_col = row + direction, col + dc
            target = board.get_piece_at((new_row, new_col))
            if 0 <= new_row < 8 and 0 <= new_col < 8 and target and target[0] != self.color[0]:
                moves.append((new_row, new_col))
            # 吃过路兵
            if (new_row, new_col) == board.en_passant_target:
                moves.append((new_row, new_col))
        return moves

class Rook(Piece):
    def get_valid_moves(self, board):
        moves = []
        row, col = self.position
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        for dr, dc in directions:
            for step in range(1, 8):
                new_row, new_col = row + dr * step, col + dc * step
                if not (0 <= new_row < 8 and 0 <= new_col < 8):
                    break
                target = board.get_piece_at((new_row, new_col))
                if not target:
                    moves.append((new_row, new_col))
                elif target[0] != self.color[0]:
                    moves.append((new_row, new_col))
                    break
                else:
                    break
        return moves

class Knight(Piece):
    def get_valid_moves(self, board):
        moves = []
        row, col = self.position
        knight_moves = [(-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1)]
        for dr, dc in knight_moves:
            new_row, new_col = row + dr, col + dc
            if 0 <= new_row < 8 and 0 <= new_col < 8:
                target = board.get_piece_at((new_row, new_col))
                if not target or target[0] != self.color[0]:
                    moves.append((new_row, new_col))
        return moves

class Bishop(Piece):
    def get_valid_moves(self, board):
        moves = []
        row, col = self.position
        directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
        for dr, dc in directions:
            for step in range(1, 8):
                new_row, new_col = row + dr * step, col + dc * step
                if not (0 <= new_row < 8 and 0 <= new_col < 8):
                    break
                target = board.get_piece_at((new_row, new_col))
                if not target:
                    moves.append((new_row, new_col))
                elif target[0] != self.color[0]:
                    moves.append((new_row, new_col))
                    break
                else:
                    break
        return moves

class Queen(Piece):
    def get_valid_moves(self, board):
        moves = Rook(self.color, "R", self.position).get_valid_moves(board)
        moves.extend(Bishop(self.color, "B", self.position).get_valid_moves(board))
        return moves

class King(Piece):
    def get_valid_moves(self, board):
        moves = []
        row, col = self.position
        directions = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
        for dr, dc in directions:
            new_row, new_col = row + dr, col + dc
            if 0 <= new_row < 8 and 0 <= new_col < 8:
                target = board.get_piece_at((new_row, new_col))
                if not target or target[0] != self.color[0]:
                    moves.append((new_row, new_col))

        # 王车易位
        if not board.castling_rights[self.color]["king_moved"]:
            # 短易位（王侧）
            if not board.castling_rights[self.color]["right_rook_moved"]:
                if all(not board.get_piece_at((row, c)) for c in [5, 6]):
                    moves.append((row, 6))
            # 长易位（后侧）
            if not board.castling_rights[self.color]["left_rook_moved"]:
                if all(not board.get_piece_at((row, c)) for c in [1, 2, 3]):
                    moves.append((row, 2))
        return moves

def create_piece(color, piece_type, position):
    if piece_type == "P":
        return Pawn(color, piece_type, position)
    elif piece_type == "R":
        return Rook(color, piece_type, position)
    elif piece_type == "N":
        return Knight(color, piece_type, position)
    elif piece_type == "B":
        return Bishop(color, piece_type, position)
    elif piece_type == "Q":
        return Queen(color, piece_type, position)
    elif piece_type == "K":
        return King(color, piece_type, position)
    return None