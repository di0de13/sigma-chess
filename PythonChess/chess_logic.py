# chess_logic.py
"""
Implements the core chess game logic, including board representation,
move generation, move validation, and game state checking.
Follows standard FIDE rules.
"""

import copy
from constants import *

class Piece:
    """Represents a chess piece."""
    def __init__(self, piece_type, color):
        if piece_type not in PIECE_TYPES:
            raise ValueError(f"Invalid piece type: {piece_type}")
        if color not in COLORS:
            raise ValueError(f"Invalid color: {color}")
        self.type = piece_type
        self.color = color

    def __repr__(self):
        return f"Piece({PIECE_NAMES[self.type]}, {'White' if self.color == WHITE else 'Black'})"

    def symbol(self):
        """Returns the Unicode symbol for the piece."""
        return PIECE_SYMBOLS.get((self.color, self.type), "?")


class Move:
    """Represents a chess move."""
    def __init__(self, from_sq, to_sq, promotion=None, flags=NORMAL_MOVE):
        # from_sq and to_sq are 0-63 indices
        self.from_sq = from_sq
        self.to_sq = to_sq
        self.promotion = promotion # Piece type (QUEEN, ROOK, etc.) if promotion occurs
        self.flags = flags         # Special move flags (CAPTURE, EN_PASSANT, CASTLING)

    def __eq__(self, other):
        if not isinstance(other, Move):
            return NotImplemented
        return (self.from_sq == other.from_sq and
                self.to_sq == other.to_sq and
                self.promotion == other.promotion) # Flags are consequences, not identity

    def __str__(self):
        promo_char = PIECE_NAMES.get(self.promotion, "")[0].lower() if self.promotion else ""
        return index_to_square(self.from_sq) + index_to_square(self.to_sq) + promo_char

    def uci(self):
        """Returns the move in UCI format."""
        return str(self)

    def is_capture(self):
        return self.flags == CAPTURE or self.flags == EN_PASSANT # Check if this logic is sufficient

    def is_promotion(self):
        return self.promotion is not None


class Board:
    """
    Represents the chessboard and manages game state according to FIDE rules.
    Uses a 0x88 representation internally might be better for move gen,
    but a 64-square list is simpler to start with.
    """
    def __init__(self, fen=STARTING_FEN):
        self.board = [None] * 64  # 64 squares, None if empty, Piece object if occupied
        self.turn = WHITE
        self.castling_rights = ALL_CASTLING
        self.en_passant_target = None  # Target square index (0-63) if en passant is possible
        self.halfmove_clock = 0      # Moves since last capture or pawn move (for 50-move rule)
        self.fullmove_number = 1     # Starts at 1, increments after Black's move
        self.history = []            # Stores (move, captured_piece, old_castling, old_ep, old_halfmove)
        self.position_history = {}   # Stores position counts for threefold repetition {position_hash: count}
        self._setup_from_fen(fen)
        self._update_position_history() # Record initial position

    def get_piece(self, index):
        """Returns the Piece at the given index (0-63), or None."""
        if 0 <= index <= 63:
            return self.board[index]
        return None

    def _setup_from_fen(self, fen):
        """Parses a FEN string and sets up the board state."""
        parts = fen.split(' ')
        if len(parts) != 6:
            raise ValueError("Invalid FEN string: must have 6 parts")

        # 1. Piece placement
        fen_board = parts[0]
        rank = 7
        file = 0
        for char in fen_board:
            if char == '/':
                rank -= 1
                file = 0
            elif char.isdigit():
                file += int(char)
            else:
                color = WHITE if char.isupper() else BLACK
                piece_char = char.lower()
                piece_type = None
                if piece_char == 'p': piece_type = PAWN
                elif piece_char == 'n': piece_type = KNIGHT
                elif piece_char == 'b': piece_type = BISHOP
                elif piece_char == 'r': piece_type = ROOK
                elif piece_char == 'q': piece_type = QUEEN
                elif piece_char == 'k': piece_type = KING
                else: raise ValueError(f"Invalid piece character in FEN: {char}")

                index = rank * 8 + file
                self.board[index] = Piece(piece_type, color)
                file += 1

        # 2. Active color
        self.turn = WHITE if parts[1] == 'w' else BLACK

        # 3. Castling availability
        self.castling_rights = NO_CASTLING
        if 'K' in parts[2]: self.castling_rights |= WHITE_KING_SIDE
        if 'Q' in parts[2]: self.castling_rights |= WHITE_QUEEN_SIDE
        if 'k' in parts[3]: self.castling_rights |= BLACK_KING_SIDE # Typo in FEN spec often seen, adjust if needed
        if 'q' in parts[3]: self.castling_rights |= BLACK_QUEEN_SIDE # Typo in FEN spec often seen, adjust if needed
        # Corrected based on standard FEN
        if 'k' in parts[2]: self.castling_rights |= BLACK_KING_SIDE
        if 'q' in parts[2]: self.castling_rights |= BLACK_QUEEN_SIDE


        # 4. En passant target square
        if parts[3] != '-':
            try:
                self.en_passant_target = square_to_index(parts[3])
            except ValueError:
                 raise ValueError(f"Invalid en passant target square in FEN: {parts[3]}")
        else:
            self.en_passant_target = None

        # 5. Halfmove clock
        try:
            self.halfmove_clock = int(parts[4])
        except ValueError:
             raise ValueError(f"Invalid halfmove clock in FEN: {parts[4]}")


        # 6. Fullmove number
        try:
            self.fullmove_number = int(parts[5])
        except ValueError:
             raise ValueError(f"Invalid fullmove number in FEN: {parts[5]}")

    def _generate_fen(self):
        """Generates the FEN string for the current board state."""
        fen = ""
        for r in range(7, -1, -1):
            empty_count = 0
            for f in range(8):
                index = r * 8 + f
                piece = self.board[index]
                if piece:
                    if empty_count > 0:
                        fen += str(empty_count)
                        empty_count = 0
                    symbol = PIECE_SYMBOLS[(piece.color, piece.type)]
                    # Need original case, not just unicode
                    char = ''
                    if piece.type == PAWN: char = 'p'
                    elif piece.type == KNIGHT: char = 'n'
                    elif piece.type == BISHOP: char = 'b'
                    elif piece.type == ROOK: char = 'r'
                    elif piece.type == QUEEN: char = 'q'
                    elif piece.type == KING: char = 'k'
                    fen += char.upper() if piece.color == WHITE else char
                else:
                    empty_count += 1
            if empty_count > 0:
                fen += str(empty_count)
            if r > 0:
                fen += '/'

        fen += f" {'w' if self.turn == WHITE else 'b'}"

        castle_str = ""
        if self.castling_rights & WHITE_KING_SIDE: castle_str += "K"
        if self.castling_rights & WHITE_QUEEN_SIDE: castle_str += "Q"
        if self.castling_rights & BLACK_KING_SIDE: castle_str += "k"
        if self.castling_rights & BLACK_QUEEN_SIDE: castle_str += "q"
        fen += f" {castle_str if castle_str else '-'}"

        fen += f" {index_to_square(self.en_passant_target) if self.en_passant_target is not None else '-'}"
        fen += f" {self.halfmove_clock}"
        fen += f" {self.fullmove_number}"

        return fen

    def _get_position_hash(self):
        """
        Creates a simplified hashable representation of the position
        (pieces, turn, castling, en passant) for threefold repetition checks.
        Excludes move counters.
        """
        board_tuple = tuple(
            (p.type, p.color) if p else None for p in self.board
        )
        return (
            board_tuple,
            self.turn,
            self.castling_rights,
            self.en_passant_target
        )

    def _update_position_history(self):
        """Updates the count for the current position hash."""
        pos_hash = self._get_position_hash()
        self.position_history[pos_hash] = self.position_history.get(pos_hash, 0) + 1

    def _remove_from_position_history(self):
        """Decrements the count for the current position hash (used in unmake_move)."""
        pos_hash = self._get_position_hash()
        if pos_hash in self.position_history:
            self.position_history[pos_hash] -= 1
            if self.position_history[pos_hash] <= 0:
                del self.position_history[pos_hash]

    def make_move(self, move):
        """
        Applies the given Move object to the board state.
        Assumes the move is legal.
        """
        piece = self.board[move.from_sq]
        if not piece:
            raise ValueError(f"No piece at starting square {index_to_square(move.from_sq)}")
        if piece.color != self.turn:
             raise ValueError(f"Cannot move opponent's piece at {index_to_square(move.from_sq)}")


        # --- Store state for undo ---
        captured_piece = self.board[move.to_sq] # Could be None
        old_castling_rights = self.castling_rights
        old_en_passant_target = self.en_passant_target
        old_halfmove_clock = self.halfmove_clock

        # --- Before removing pieces, update position history count ---
        # self._remove_from_position_history() # Do this in unmake_move before restoring state

        # --- Update board ---
        self.board[move.to_sq] = piece
        self.board[move.from_sq] = None
        is_pawn_move = (piece.type == PAWN)
        is_capture = (captured_piece is not None) or (move.flags == EN_PASSANT)

        # --- Handle special moves ---
        new_en_passant_target = None # Reset en passant target unless set below

        # Pawn double step: Set en passant target
        if piece.type == PAWN and abs(move.to_sq - move.from_sq) == 16:
            # Target square is one step behind the moved pawn
            new_en_passant_target = move.from_sq + (8 if piece.color == WHITE else -8)

        # En passant capture: Remove captured pawn
        if move.flags == EN_PASSANT:
            captured_pawn_sq = move.to_sq + (-8 if piece.color == WHITE else 8)
            captured_piece = self.board[captured_pawn_sq] # Store the actual captured piece
            self.board[captured_pawn_sq] = None
            is_capture = True # Ensure flag is set

        # Castling: Move the rook
        if move.flags == CASTLING:
            if move.to_sq == square_to_index('g1'): # White King side
                rook = self.board[square_to_index('h1')]
                self.board[square_to_index('h1')] = None
                self.board[square_to_index('f1')] = rook
            elif move.to_sq == square_to_index('c1'): # White Queen side
                rook = self.board[square_to_index('a1')]
                self.board[square_to_index('a1')] = None
                self.board[square_to_index('d1')] = rook
            elif move.to_sq == square_to_index('g8'): # Black King side
                rook = self.board[square_to_index('h8')]
                self.board[square_to_index('h8')] = None
                self.board[square_to_index('f8')] = rook
            elif move.to_sq == square_to_index('c8'): # Black Queen side
                rook = self.board[square_to_index('a8')]
                self.board[square_to_index('a8')] = None
                self.board[square_to_index('d8')] = rook

        # Promotion: Change piece type
        if move.promotion:
            self.board[move.to_sq] = Piece(move.promotion, piece.color)

        # --- Update Castling Rights ---
        # If King moves
        if piece.type == KING:
            if piece.color == WHITE:
                self.castling_rights &= ~(WHITE_KING_SIDE | WHITE_QUEEN_SIDE)
            else:
                self.castling_rights &= ~(BLACK_KING_SIDE | BLACK_QUEEN_SIDE)
        # If Rook moves or is captured
        if move.from_sq == square_to_index('h1') or move.to_sq == square_to_index('h1'):
             self.castling_rights &= ~WHITE_KING_SIDE
        if move.from_sq == square_to_index('a1') or move.to_sq == square_to_index('a1'):
             self.castling_rights &= ~WHITE_QUEEN_SIDE
        if move.from_sq == square_to_index('h8') or move.to_sq == square_to_index('h8'):
             self.castling_rights &= ~BLACK_KING_SIDE
        if move.from_sq == square_to_index('a8') or move.to_sq == square_to_index('a8'):
             self.castling_rights &= ~BLACK_QUEEN_SIDE
        # If a rook is captured on its starting square
        if captured_piece and captured_piece.type == ROOK:
             if move.to_sq == square_to_index('h1'): self.castling_rights &= ~WHITE_KING_SIDE
             if move.to_sq == square_to_index('a1'): self.castling_rights &= ~WHITE_QUEEN_SIDE
             if move.to_sq == square_to_index('h8'): self.castling_rights &= ~BLACK_KING_SIDE
             if move.to_sq == square_to_index('a8'): self.castling_rights &= ~BLACK_QUEEN_SIDE


        # --- Update Game State Variables ---
        self.en_passant_target = new_en_passant_target

        if is_pawn_move or is_capture:
            self.halfmove_clock = 0
        else:
            self.halfmove_clock += 1

        if self.turn == BLACK:
            self.fullmove_number += 1

        self.turn = BLACK if self.turn == WHITE else WHITE

        # --- Store History ---
        # Need to store the move itself, plus captured piece and state variables *before* the move
        history_entry = (
            move,
            captured_piece, # Piece object or None
            old_castling_rights,
            old_en_passant_target, # Square index or None
            old_halfmove_clock
        )
        self.history.append(history_entry)

        # --- Update position history *after* making the move ---
        self._update_position_history()


    def unmake_move(self):
        """Reverts the last move made."""
        if not self.history:
            return # No moves to undo

        # --- Decrement position count for the *current* state before undoing ---
        self._remove_from_position_history()

        # --- Restore State from History ---
        last_move, captured_piece, old_castling, old_ep, old_halfmove = self.history.pop()

        # --- Switch Turn Back ---
        self.turn = BLACK if self.turn == WHITE else WHITE # Now it's the player who made the move

        # --- Restore Clocks and Counters ---
        self.castling_rights = old_castling
        self.en_passant_target = old_ep
        self.halfmove_clock = old_halfmove
        if self.turn == BLACK: # If Black just moved (meaning it's White's turn now after undo)
             self.fullmove_number -= 1 # Decrement fullmove number

        # --- Undo Piece Movement ---
        moved_piece = self.board[last_move.to_sq] # Piece that arrived at to_sq

        # If promotion occurred, revert piece type
        if last_move.promotion:
             moved_piece = Piece(PAWN, moved_piece.color) # Revert to pawn

        self.board[last_move.from_sq] = moved_piece
        self.board[last_move.to_sq] = captured_piece # Put back captured piece (could be None)

        # --- Undo Special Moves ---
        # En passant: Put captured pawn back
        if last_move.flags == EN_PASSANT:
            captured_pawn_sq = last_move.to_sq + (-8 if moved_piece.color == WHITE else 8)
            # captured_piece should already contain the pawn from history
            self.board[last_move.to_sq] = None # The landing square was empty before EP capture
            self.board[captured_pawn_sq] = captured_piece # Put pawn back

        # Castling: Move rook back
        if last_move.flags == CASTLING:
             if last_move.to_sq == square_to_index('g1'): # White King side
                 rook = self.board[square_to_index('f1')]
                 self.board[square_to_index('f1')] = None
                 self.board[square_to_index('h1')] = rook
             elif last_move.to_sq == square_to_index('c1'): # White Queen side
                 rook = self.board[square_to_index('d1')]
                 self.board[square_to_index('d1')] = None
                 self.board[square_to_index('a1')] = rook
             elif last_move.to_sq == square_to_index('g8'): # Black King side
                 rook = self.board[square_to_index('f8')]
                 self.board[square_to_index('f8')] = None
                 self.board[square_to_index('h8')] = rook
             elif last_move.to_sq == square_to_index('c8'): # Black Queen side
                 rook = self.board[square_to_index('d8')]
                 self.board[square_to_index('d8')] = None
                 self.board[square_to_index('a8')] = rook

        # Note: Position history was already updated at the start of this function


    def is_attacked(self, square_index, attacker_color):
        """Checks if the given square index is attacked by any piece of the attacker_color."""
        target_rank, target_file = get_rank(square_index), get_file(square_index)

        # Check for pawn attacks
        pawn_attack_ranks = [target_rank - 1, target_rank + 1] # Ranks where enemy pawns could be
        pawn_attack_files = [target_file - 1, target_file + 1] # Files where enemy pawns could be
        pawn_direction = -1 if attacker_color == WHITE else 1 # Pawns attack 'forward' relative to opponent

        if get_rank(square_index) + pawn_direction in range(8): # Check if the pawn source rank is on board
             for file_offset in [-1, 1]:
                  check_file = target_file + file_offset
                  if 0 <= check_file < 8:
                       check_index = (target_rank + pawn_direction) * 8 + check_file
                       piece = self.board[check_index]
                       if piece and piece.type == PAWN and piece.color == attacker_color:
                            return True

        # Check for knight attacks
        for dr, df in KNIGHT_MOVES:
            check_rank, check_file = target_rank + dr, target_file + df
            if 0 <= check_rank < 8 and 0 <= check_file < 8:
                check_index = check_rank * 8 + check_file
                piece = self.board[check_index]
                if piece and piece.type == KNIGHT and piece.color == attacker_color:
                    return True

        # Check for sliding attacks (Rook, Bishop, Queen)
        sliding_types = [ROOK, BISHOP, QUEEN]
        for dr, df in QUEEN_DIRECTIONS: # Check all 8 directions
            relevant_piece_types = []
            if dr == 0 or df == 0: relevant_piece_types = [ROOK, QUEEN] # Horizontal/Vertical
            else: relevant_piece_types = [BISHOP, QUEEN] # Diagonal

            for i in range(1, 8): # Max distance on board
                check_rank, check_file = target_rank + i * dr, target_file + i * df
                if not (0 <= check_rank < 8 and 0 <= check_file < 8):
                    break # Off board

                check_index = check_rank * 8 + check_file
                piece = self.board[check_index]
                if piece:
                    if piece.color == attacker_color and piece.type in relevant_piece_types:
                        return True
                    break # Path blocked by a piece (friendly or otherwise)

        # Check for king attacks (adjacent squares)
        for dr in [-1, 0, 1]:
            for df in [-1, 0, 1]:
                if dr == 0 and df == 0: continue
                check_rank, check_file = target_rank + dr, target_file + df
                if 0 <= check_rank < 8 and 0 <= check_file < 8:
                    check_index = check_rank * 8 + check_file
                    piece = self.board[check_index]
                    if piece and piece.type == KING and piece.color == attacker_color:
                        return True

        return False

    def find_king(self, color):
        """Finds the index of the king of the specified color."""
        for i, piece in enumerate(self.board):
            if piece and piece.type == KING and piece.color == color:
                return i
        return None # Should not happen in a legal game

    def is_in_check(self, color):
        """Checks if the king of the specified color is currently in check."""
        king_pos = self.find_king(color)
        if king_pos is None:
             # Consider how to handle this - maybe raise error or return False
             # If king is missing, it can't be in check? Or game state is invalid.
             return False # Let's assume an invalid state isn't 'check' for now
        opponent_color = WHITE if color == BLACK else BLACK
        return self.is_attacked(king_pos, opponent_color)

    def get_pseudo_legal_moves(self):
        """Generates all moves possible for the current player, without checking for checks."""
        moves = []
        current_player = self.turn

        for index, piece in enumerate(self.board):
            if piece and piece.color == current_player:
                from_rank, from_file = get_rank(index), get_file(index)

                # --- Pawn Moves ---
                if piece.type == PAWN:
                    direction = 1 if current_player == WHITE else -1
                    start_rank = 1 if current_player == WHITE else 6

                    # 1. Single step forward
                    to_index = index + 8 * direction
                    if 0 <= to_index <= 63 and self.board[to_index] is None:
                        # Check for promotion
                        to_rank = get_rank(to_index)
                        if to_rank == 7 or to_rank == 0:
                            for promo_piece in [QUEEN, ROOK, BISHOP, KNIGHT]:
                                moves.append(Move(index, to_index, promotion=promo_piece))
                        else:
                            moves.append(Move(index, to_index))

                        # 2. Double step forward (only from start rank)
                        if from_rank == start_rank:
                            to_index_double = index + 16 * direction
                            if self.board[to_index_double] is None:
                                moves.append(Move(index, to_index_double)) # No promotion on double step

                    # 3. Captures (diagonal)
                    for file_offset in [-1, 1]:
                        to_file = from_file + file_offset
                        to_rank = from_rank + direction
                        if 0 <= to_file < 8 and 0 <= to_rank < 8:
                            to_index = to_rank * 8 + to_file
                            target_piece = self.board[to_index]
                            # Normal capture
                            if target_piece and target_piece.color != current_player:
                                if to_rank == 7 or to_rank == 0: # Capture with promotion
                                    for promo_piece in [QUEEN, ROOK, BISHOP, KNIGHT]:
                                        moves.append(Move(index, to_index, promotion=promo_piece, flags=CAPTURE))
                                else:
                                    moves.append(Move(index, to_index, flags=CAPTURE))
                            # En passant capture
                            elif to_index == self.en_passant_target:
                                moves.append(Move(index, to_index, flags=EN_PASSANT))

                # --- Knight Moves ---
                elif piece.type == KNIGHT:
                    for dr, df in KNIGHT_MOVES:
                        to_rank, to_file = from_rank + dr, from_file + df
                        if 0 <= to_rank < 8 and 0 <= to_file < 8:
                            to_index = to_rank * 8 + to_file
                            target_piece = self.board[to_index]
                            if target_piece is None:
                                moves.append(Move(index, to_index))
                            elif target_piece.color != current_player:
                                moves.append(Move(index, to_index, flags=CAPTURE))

                # --- Sliding Moves (Bishop, Rook, Queen) ---
                elif piece.type in [BISHOP, ROOK, QUEEN]:
                    move_directions = []
                    if piece.type == BISHOP: move_directions = BISHOP_DIRECTIONS
                    elif piece.type == ROOK: move_directions = ROOK_DIRECTIONS
                    elif piece.type == QUEEN: move_directions = QUEEN_DIRECTIONS

                    for dr, df in move_directions:
                        for i in range(1, 8):
                            to_rank, to_file = from_rank + i * dr, from_file + i * df
                            if not (0 <= to_rank < 8 and 0 <= to_file < 8):
                                break # Off board

                            to_index = to_rank * 8 + to_file
                            target_piece = self.board[to_index]

                            if target_piece is None:
                                moves.append(Move(index, to_index))
                            elif target_piece.color != current_player:
                                moves.append(Move(index, to_index, flags=CAPTURE))
                                break # Cannot move past a capture
                            else: # Friendly piece
                                break # Blocked

                # --- King Moves ---
                elif piece.type == KING:
                    # Normal 1-step moves
                    for dr in [-1, 0, 1]:
                        for df in [-1, 0, 1]:
                            if dr == 0 and df == 0: continue
                            to_rank, to_file = from_rank + dr, from_file + df
                            if 0 <= to_rank < 8 and 0 <= to_file < 8:
                                to_index = to_rank * 8 + to_file
                                target_piece = self.board[to_index]
                                if target_piece is None:
                                    moves.append(Move(index, to_index))
                                elif target_piece.color != current_player:
                                    moves.append(Move(index, to_index, flags=CAPTURE))

                    # Castling moves (generated here, validated later in get_legal_moves)
                    opponent_color = WHITE if current_player == BLACK else BLACK
                    if not self.is_in_check(current_player): # Cannot castle out of check
                        # King side
                        if current_player == WHITE and (self.castling_rights & WHITE_KING_SIDE):
                             if (self.board[square_to_index('f1')] is None and
                                 self.board[square_to_index('g1')] is None and
                                 not self.is_attacked(square_to_index('e1'), opponent_color) and
                                 not self.is_attacked(square_to_index('f1'), opponent_color) and
                                 not self.is_attacked(square_to_index('g1'), opponent_color)):
                                     moves.append(Move(index, square_to_index('g1'), flags=CASTLING))
                        elif current_player == BLACK and (self.castling_rights & BLACK_KING_SIDE):
                             if (self.board[square_to_index('f8')] is None and
                                 self.board[square_to_index('g8')] is None and
                                 not self.is_attacked(square_to_index('e8'), opponent_color) and
                                 not self.is_attacked(square_to_index('f8'), opponent_color) and
                                 not self.is_attacked(square_to_index('g8'), opponent_color)):
                                     moves.append(Move(index, square_to_index('g8'), flags=CASTLING))
                        # Queen side
                        if current_player == WHITE and (self.castling_rights & WHITE_QUEEN_SIDE):
                             if (self.board[square_to_index('d1')] is None and
                                 self.board[square_to_index('c1')] is None and
                                 self.board[square_to_index('b1')] is None and
                                 not self.is_attacked(square_to_index('e1'), opponent_color) and
                                 not self.is_attacked(square_to_index('d1'), opponent_color) and
                                 not self.is_attacked(square_to_index('c1'), opponent_color)):
                                     moves.append(Move(index, square_to_index('c1'), flags=CASTLING))
                        elif current_player == BLACK and (self.castling_rights & BLACK_QUEEN_SIDE):
                             if (self.board[square_to_index('d8')] is None and
                                 self.board[square_to_index('c8')] is None and
                                 self.board[square_to_index('b8')] is None and
                                 not self.is_attacked(square_to_index('e8'), opponent_color) and
                                 not self.is_attacked(square_to_index('d8'), opponent_color) and
                                 not self.is_attacked(square_to_index('c8'), opponent_color)):
                                     moves.append(Move(index, square_to_index('c8'), flags=CASTLING))

        return moves


    def get_legal_moves(self):
        """Generates all legal moves for the current player (filters pseudo-legal moves)."""
        legal_moves = []
        pseudo_legal_moves = self.get_pseudo_legal_moves()
        current_player = self.turn

        for move in pseudo_legal_moves:
            # Temporarily make the move
            self.make_move(move)

            # Check if the move leaves the king in check
            # Important: Check the king of the player *who just moved*
            if not self.is_in_check(current_player):
                legal_moves.append(move)

            # Undo the move
            self.unmake_move()

        return legal_moves

    def is_checkmate(self):
        """Checks if the current player is checkmated."""
        if not self.is_in_check(self.turn):
            return False # Cannot be checkmate if not in check
        # If in check, check if there are any legal moves
        return len(self.get_legal_moves()) == 0

    def is_stalemate(self):
        """Checks if the current player is stalemated."""
        if self.is_in_check(self.turn):
            return False # Cannot be stalemate if in check
        # If not in check, check if there are any legal moves
        return len(self.get_legal_moves()) == 0

    def is_insufficient_material(self):
        """Checks for draw due to insufficient mating material."""
        # Count pieces (excluding kings)
        piece_counts = {color: {ptype: 0 for ptype in PIECE_TYPES} for color in COLORS}
        has_pawns_or_majors = {color: False for color in COLORS}
        bishops = {color: [] for color in COLORS} # Store square colors of bishops

        for index, piece in enumerate(self.board):
            if piece and piece.type != KING:
                piece_counts[piece.color][piece.type] += 1
                if piece.type in [PAWN, ROOK, QUEEN]:
                    has_pawns_or_majors[piece.color] = True
                if piece.type == BISHOP:
                    rank, file = get_rank(index), get_file(index)
                    square_color = (rank + file) % 2 # 0 for dark, 1 for light (or vice versa)
                    bishops[piece.color].append(square_color)

        w_pieces = sum(piece_counts[WHITE].values())
        b_pieces = sum(piece_counts[BLACK].values())

        # King vs King
        if w_pieces == 0 and b_pieces == 0: return True
        # King vs King + Knight
        if (w_pieces == 0 and b_pieces == 1 and piece_counts[BLACK][KNIGHT] == 1): return True
        if (b_pieces == 0 and w_pieces == 1 and piece_counts[WHITE][KNIGHT] == 1): return True
        # King vs King + Bishop
        if (w_pieces == 0 and b_pieces == 1 and piece_counts[BLACK][BISHOP] == 1): return True
        if (b_pieces == 0 and w_pieces == 1 and piece_counts[WHITE][BISHOP] == 1): return True
        # King + Bishop(s) vs King + Bishop(s) - all bishops on same color squares
        if (not has_pawns_or_majors[WHITE] and not has_pawns_or_majors[BLACK] and
             piece_counts[WHITE][KNIGHT] == 0 and piece_counts[BLACK][KNIGHT] == 0):
             all_bishops = bishops[WHITE] + bishops[BLACK]
             if len(all_bishops) > 0:
                 first_bishop_color = all_bishops[0]
                 if all(bc == first_bishop_color for bc in all_bishops):
                     return True

        return False

    def is_fifty_move_rule(self):
        """Checks for draw due to the 50-move rule."""
        # Rule: 50 moves by each player without a pawn move or capture = 100 halfmoves
        return self.halfmove_clock >= 100

    def is_threefold_repetition(self):
        """Checks for draw due to threefold repetition."""
        current_hash = self._get_position_hash()
        # The same position must have occurred 3 times *with the same player to move*
        # Our hash includes the player to move.
        return self.position_history.get(current_hash, 0) >= 3

    def get_game_state(self):
        """Determines the current state of the game (Ongoing, Checkmate, Draw)."""
        if self.is_checkmate():
            return CHECKMATE
        if self.is_stalemate():
            return STALEMATE
        if self.is_insufficient_material():
            return INSUFFICIENT_MATERIAL
        if self.is_fifty_move_rule():
            return FIFTY_MOVE_RULE
        if self.is_threefold_repetition():
            return THREEFOLD_REPETITION

        return ONGOING

    def is_game_over(self):
        """Checks if the game has ended."""
        return self.get_game_state() != ONGOING

    def get_outcome(self):
        """Returns the winner (WHITE, BLACK) or None for a draw, if game is over."""
        state = self.get_game_state()
        if state == CHECKMATE:
            return BLACK if self.turn == WHITE else WHITE # The player whose turn it IS is checkmated
        elif state in DRAW_STATES:
            return None # Draw
        else:
            return None # Game not over or invalid state

    def copy(self):
         """Creates a deep copy of the board state."""
         # Using copy.deepcopy is simpler but might be slow for frequent use (like MCTS)
         # For performance, a custom copy method is better.
         new_board = Board.__new__(Board) # Create empty object without calling __init__
         new_board.board = [p if p is None else Piece(p.type, p.color) for p in self.board] # Copy pieces
         new_board.turn = self.turn
         new_board.castling_rights = self.castling_rights
         new_board.en_passant_target = self.en_passant_target
         new_board.halfmove_clock = self.halfmove_clock
         new_board.fullmove_number = self.fullmove_number
         # History and position_history: Deep copying these can be complex/slow.
         # For algorithms like MCTS, you often don't need the full history *in the copy*.
         # If needed, implement proper deep copy. Let's start without deep history copy.
         new_board.history = [] # Or maybe copy last few relevant states if needed?
         new_board.position_history = self.position_history.copy() # Shallow copy ok for counts

         # It might be safer/easier for now to just re-parse the FEN
         # return Board(self._generate_fen())
         # Let's stick with the manual copy for now, assuming history isn't needed in copies.
         return new_board

# --- Example Usage ---
if __name__ == "__main__":
    board = Board()
    print("Initial Board:")
    # print(board._generate_fen())
    moves = board.get_legal_moves()
    print(f"Legal moves for White: {len(moves)}")
    # print([str(m) for m in moves])

    # Make a move (e.g., e2e4)
    e2e4_move = None
    for m in moves:
        if str(m) == 'e2e4':
            e2e4_move = m
            break

    if e2e4_move:
        print("\nMaking move: e2e4")
        board.make_move(e2e4_move)
        # print(board._generate_fen())
        print(f"Turn: {'White' if board.turn == WHITE else 'Black'}")
        print(f"EP target: {index_to_square(board.en_passant_target) if board.en_passant_target else '-'}")
        print(f"Castling: {board.castling_rights}")
        print(f"Halfmove clock: {board.halfmove_clock}")
        print(f"Fullmove num: {board.fullmove_number}")

        black_moves = board.get_legal_moves()
        print(f"Legal moves for Black: {len(black_moves)}")

        print("\nUndoing move: e2e4")
        board.unmake_move()
        # print(board._generate_fen())
        print(f"Turn: {'White' if board.turn == WHITE else 'Black'}")
        print(f"EP target: {index_to_square(board.en_passant_target) if board.en_passant_target else '-'}")
        print(f"Castling: {board.castling_rights}")
        print(f"Halfmove clock: {board.halfmove_clock}")
        print(f"Fullmove num: {board.fullmove_number}")

    else:
        print("Could not find move e2e4?")

    # Test checkmate scenario
    # fen = "rnb1kbnr/pppp1ppp/8/4p3/5PPq/8/PPPPP2P/RNBQKBNR w KQkq - 1 3" # Fool's mate
    # board_mate = Board(fen)
    # print(f"\nTesting Fool's Mate (FEN: {fen})")
    # print(f"Is White in check? {board_mate.is_in_check(WHITE)}")
    # print(f"Is game over? {board_mate.is_game_over()}")
    # print(f"Game state: {board_mate.get_game_state()}")
    # print(f"Legal moves for White: {len(board_mate.get_legal_moves())}")
    # print(f"Outcome: {board_mate.get_outcome()}")