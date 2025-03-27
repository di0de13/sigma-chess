# constants.py
"""
Defines constants used throughout the chess application.
"""

# --- Colors ---
WHITE = 0
BLACK = 1
COLORS = [WHITE, BLACK]

# --- Piece Types ---
EMPTY = 0  # Represents an empty square
PAWN = 1
KNIGHT = 2
BISHOP = 3
ROOK = 4
QUEEN = 5
KING = 6
PIECE_TYPES = [PAWN, KNIGHT, BISHOP, ROOK, QUEEN, KING]

# --- Piece Symbols (Unicode) ---
# You might need to ensure your terminal/IDE supports Unicode display
PIECE_SYMBOLS = {
    (WHITE, PAWN): "♙", (BLACK, PAWN): "♟",
    (WHITE, KNIGHT): "♘", (BLACK, KNIGHT): "♞",
    (WHITE, BISHOP): "♗", (BLACK, BISHOP): "♝",
    (WHITE, ROOK): "♖", (BLACK, ROOK): "♜",
    (WHITE, QUEEN): "♕", (BLACK, QUEEN): "♛",
    (WHITE, KING): "♔", (BLACK, KING): "♚",
    (EMPTY, EMPTY): " "  # Represent empty square visually
}

PIECE_NAMES = {
    PAWN: "Pawn", KNIGHT: "Knight", BISHOP: "Bishop",
    ROOK: "Rook", QUEEN: "Queen", KING: "King"
}

# --- Board Representation ---
# Standard algebraic notation to 0-63 index mapping and back
# 0 = a1, 1 = b1, ..., 7 = h1
# 8 = a2, ..., 15 = h2
# ...
# 56 = a8, ..., 63 = h8
FILES = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
RANKS = ['1', '2', '3', '4', '5', '6', '7', '8']

def square_to_index(sq_name):
    """Converts algebraic notation (e.g., 'e4') to 0-63 index."""
    if not isinstance(sq_name, str) or len(sq_name) != 2:
        raise ValueError(f"Invalid square name: {sq_name}")
    file = sq_name[0].lower()
    rank = sq_name[1]
    if file not in FILES or rank not in RANKS:
        raise ValueError(f"Invalid square name: {sq_name}")
    file_idx = FILES.index(file)
    rank_idx = RANKS.index(rank)
    return rank_idx * 8 + file_idx

def index_to_square(index):
    """Converts 0-63 index to algebraic notation (e.g., 'e4')."""
    if not 0 <= index <= 63:
        raise ValueError(f"Invalid square index: {index}")
    rank_idx = index // 8
    file_idx = index % 8
    return FILES[file_idx] + RANKS[rank_idx]

def get_rank(index):
    return index // 8

def get_file(index):
    return index % 8

# --- Castling Rights ---
# Use bit flags for efficient checking and updating
NO_CASTLING = 0
WHITE_KING_SIDE = 1
WHITE_QUEEN_SIDE = 2
BLACK_KING_SIDE = 4
BLACK_QUEEN_SIDE = 8
ALL_CASTLING = WHITE_KING_SIDE | WHITE_QUEEN_SIDE | BLACK_KING_SIDE | BLACK_QUEEN_SIDE

# --- Game States ---
ONGOING = 0
CHECKMATE = 1
STALEMATE = 2
INSUFFICIENT_MATERIAL = 3
FIFTY_MOVE_RULE = 4
THREEFOLD_REPETITION = 5
DRAW_STATES = [STALEMATE, INSUFFICIENT_MATERIAL, FIFTY_MOVE_RULE, THREEFOLD_REPETITION]
WIN_STATES = [CHECKMATE]

# --- Move Flags (for special moves) ---
NORMAL_MOVE = 0
CAPTURE = 1
EN_PASSANT = 2
CASTLING = 3
PROMOTION = 4 # Usually combined with NORMAL_MOVE or CAPTURE

# --- Initial Board Setup (FEN Standard) ---
STARTING_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"

# --- Directions for piece movement generation ---
# (dr, df) - change in rank, change in file
# Rank increases upwards (1 to 8), File increases rightwards (a to h)
DIRECTIONS = {
    'N': (1, 0), 'S': (-1, 0), 'E': (0, 1), 'W': (0, -1),
    'NE': (1, 1), 'NW': (1, -1), 'SE': (-1, 1), 'SW': (-1, -1)
}

# Knight moves (relative dr, df)
KNIGHT_MOVES = [
    (2, 1), (2, -1), (-2, 1), (-2, -1),
    (1, 2), (1, -2), (-1, 2), (-1, -2)
]

# Sliding piece directions
BISHOP_DIRECTIONS = [DIRECTIONS['NE'], DIRECTIONS['NW'], DIRECTIONS['SE'], DIRECTIONS['SW']]
ROOK_DIRECTIONS = [DIRECTIONS['N'], DIRECTIONS['S'], DIRECTIONS['E'], DIRECTIONS['W']]
QUEEN_DIRECTIONS = BISHOP_DIRECTIONS + ROOK_DIRECTIONS

# --- UI ---
BOARD_SIZE = 8
SQUARE_SIZE = 60 # pixels
BOARD_COLOR_LIGHT = "#EADDC5" # Light wood
BOARD_COLOR_DARK = "#BA8C63"  # Dark wood
HIGHLIGHT_COLOR = "#70AFFF" # Light blue highlight
POSSIBLE_MOVE_COLOR = "#A0FFA0" # Light green for possible moves