# chess_gui.py
"""
Provides a Tkinter-based graphical user interface for the chess game.
Displays material difference and board coordinates.
"""

import tkinter as tk
from tkinter import messagebox, simpledialog, Menu
import importlib
import threading
import time
import os
import random
import sys

# Import constants including the new CAPTURE_MOVE_COLOR
from constants import *
from chess_logic import Board, Move, Piece

# --- Game Modes ---
MODE_PVP = "Player vs Player"
MODE_PVC = "Player vs Computer"

class ChessGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Python Chess")
        self.root.resizable(False, False)

        self.board = Board()

        self.board_area_frame = tk.Frame(root)
        self.board_area_frame.pack(side=tk.LEFT, padx=(10, 0), pady=10)

        # --- Create Rank Labels (8 down to 1) ---
        rank_label_font = ("Arial", 10)
        label_width = 2
        for i in range(BOARD_SIZE):
            rank_label_text = RANKS[BOARD_SIZE - 1 - i]
            label = tk.Label(
                self.board_area_frame,
                text=rank_label_text,
                font=rank_label_font,
                width=label_width,
                height=SQUARE_SIZE // 20
            )
            label.grid(row=i + 1, column=0, sticky='ns', padx=(0, 2))

        # --- Create File Labels (a to h) ---
        file_label_font = ("Arial", 10)
        label_height = 1
        for i in range(BOARD_SIZE):
            file_label_text = FILES[i]
            label = tk.Label(
                self.board_area_frame,
                text=file_label_text,
                font=file_label_font,
                width=SQUARE_SIZE // 10,
                height=label_height
            )
            label.grid(row=BOARD_SIZE + 1, column=i + 1, sticky='ew', pady=(2, 0))

        # --- Create Board Canvas ---
        self.board_canvas = tk.Canvas(
            self.board_area_frame,
            width=BOARD_SIZE * SQUARE_SIZE,
            height=BOARD_SIZE * SQUARE_SIZE
        )
        self.board_canvas.grid(row=1, column=1, rowspan=BOARD_SIZE, columnspan=BOARD_SIZE, sticky='nsew')
        self.board_canvas.bind("<Button-1>", self.on_square_click)


        # --- UI Elements (Control Panel on the Right) ---
        self.control_frame = tk.Frame(root)
        self.control_frame.pack(side=tk.RIGHT, padx=10, pady=10, fill=tk.Y, expand=False)

        self.status_label = tk.Label(self.control_frame, text="White's Turn", font=("Arial", 14))
        self.status_label.pack(pady=5)

        self.material_label = tk.Label(self.control_frame, text="Material: Even", font=("Arial", 11))
        self.material_label.pack(pady=5)

        # Move History
        self.move_history_frame = tk.Frame(self.control_frame)
        self.move_history_frame.pack(pady=10, expand=True, fill=tk.BOTH)

        self.move_history_text = tk.Text(self.move_history_frame, height=15, width=20, state=tk.DISABLED, font=("Courier", 10))
        self.move_history_scroll = tk.Scrollbar(self.move_history_frame, command=self.move_history_text.yview)
        self.move_history_text.config(yscrollcommand=self.move_history_scroll.set)

        self.move_history_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.move_history_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)


        # --- Game State Variables ---
        self.selected_square = None
        self.possible_moves = []
        self.player_color = WHITE
        self.game_mode = MODE_PVP
        self.ai_module = None
        self.ai_thinking = False
        self.ai_strategy_name = "ai_random"
        self._game_over_message_shown = False


        # --- Menu ---
        self.menu_bar = Menu(root)
        self.root.config(menu=self.menu_bar)

        self.game_menu = Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Game", menu=self.game_menu)
        self.game_menu.add_command(label="New Game (PvP)", command=lambda: self.start_new_game(MODE_PVP))
        self.game_menu.add_command(label="New Game (PvC - Play White)", command=lambda: self.start_new_game(MODE_PVC, human_color=WHITE))
        self.game_menu.add_command(label="New Game (PvC - Play Black)", command=lambda: self.start_new_game(MODE_PVC, human_color=BLACK))
        self.game_menu.add_separator()
        self.game_menu.add_command(label="Exit", command=root.quit)

        self.ai_menu = Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="AI Strategy", menu=self.ai_menu)
        self.populate_ai_menu()


        # --- Initial Setup ---
        self.load_ai_strategy(self.ai_strategy_name)
        self.draw_board()
        self.update_status()
        self.update_material_display()


    def update_material_display(self):
        """Calculates material scores based on pieces on board and updates the label."""
        white_score = 0
        black_score = 0
        for piece in self.board.board:
            if piece:
                value = PIECE_VALUES.get(piece.type, 0)
                if piece.color == WHITE:
                    white_score += value
                else:
                    black_score += value

        material_diff = white_score - black_score
        display_text = "Material: "
        if material_diff > 0:
            display_text += f"White +{material_diff}"
        elif material_diff < 0:
            display_text += f"Black +{-material_diff}"
        else:
            display_text += "Even"

        self.material_label.config(text=display_text)


    def populate_ai_menu(self):
        """Finds available AI strategies in the ai_strategies folder and adds them to the menu."""
        self.ai_menu.delete(0, tk.END)
        try:
            script_dir = os.path.dirname(__file__)
            ai_dir = os.path.join(script_dir, "ai_strategies")
        except NameError:
            ai_dir = "ai_strategies"

        try:
            available_ais = [
                f.replace(".py", "")
                for f in os.listdir(ai_dir)
                if f.startswith("ai_") and f.endswith(".py") and f != "__init__.py" and f != "ai_interface.py"
            ]
            available_ais.sort()
        except FileNotFoundError:
            available_ais = []
            print(f"Warning: AI strategies directory '{ai_dir}' not found.")

        if not available_ais:
             self.ai_menu.add_command(label="No AI found", state=tk.DISABLED)
             self.ai_strategy_name = None
             return

        if self.ai_strategy_name not in available_ais:
            self.ai_strategy_name = available_ais[0] if available_ais else None # Handle empty list case

        current_ai_var = tk.StringVar(value=self.ai_strategy_name)

        for ai_name in available_ais:
            display_name = ai_name.replace("ai_", "").replace("_", " ").title()
            self.ai_menu.add_radiobutton(
                label=display_name,
                variable=current_ai_var,
                value=ai_name,
                command=lambda name=ai_name: self.select_ai_strategy(name)
            )


    def select_ai_strategy(self, ai_name):
        """Loads the selected AI strategy."""
        if self.ai_thinking:
            messagebox.showwarning("AI Busy", "Cannot change AI while it's thinking.")
            # Need to reset the radio button state if change failed
            self.populate_ai_menu() # Repopulating will reset the variable binding
            return

        if ai_name == self.ai_strategy_name:
            return

        if self.load_ai_strategy(ai_name):
            display_name = ai_name.replace('ai_','').replace('_',' ').title()
            messagebox.showinfo("AI Changed", f"AI strategy set to {display_name}. Changes apply on New Game.")
        else:
            # Reloading failed, revert selection in menu
            self.populate_ai_menu()


    def load_ai_strategy(self, ai_name):
        """Dynamically imports and loads the AI module. Returns True on success, False on failure."""
        if not ai_name:
             print("Error: Attempted to load an empty AI name.")
             # Ensure ai_strategy_name is cleared if loading fails here
             old_name = self.ai_strategy_name
             self.ai_strategy_name = None
             self.ai_module = None
             return False

        try:
            # Ensure the parent directory is in path if running as script/module issue
            script_dir = os.path.dirname(os.path.abspath(__file__))
            parent_dir = os.path.dirname(script_dir)
            if script_dir not in sys.path:
                sys.path.insert(0, script_dir)
            if parent_dir not in sys.path:
                 sys.path.insert(0, parent_dir) # Needed if ai_strategies is sibling

            # Reload parent package first if necessary
            if "ai_strategies" in sys.modules:
                 importlib.reload(sys.modules["ai_strategies"]) # Maybe not needed, check behavior

            module_name = f"ai_strategies.{ai_name}"
            if module_name in sys.modules:
                 self.ai_module = importlib.reload(sys.modules[module_name])
            else:
                 self.ai_module = importlib.import_module(module_name)

            if not hasattr(self.ai_module, "find_best_move"):
                 raise AttributeError(f"AI module {ai_name} does not have 'find_best_move' function.")

            self.ai_strategy_name = ai_name
            print(f"Successfully loaded AI strategy: {ai_name}")
            return True
        except ModuleNotFoundError:
            messagebox.showerror("Error", f"Could not find AI strategy file: {ai_name}.py or its dependencies.")
            self.ai_module = None
            # Keep old strategy name if load fails? Or clear? Let's clear.
            self.ai_strategy_name = None
            return False
        except AttributeError as e:
             messagebox.showerror("Error", f"Error loading AI {ai_name}: {e}")
             self.ai_module = None
             self.ai_strategy_name = None
             return False
        except Exception as e:
             messagebox.showerror("Error", f"An unexpected error occurred loading AI {ai_name}: {e}")
             import traceback
             traceback.print_exc()
             self.ai_module = None
             self.ai_strategy_name = None
             return False


    def start_new_game(self, mode, human_color=WHITE):
        """Resets the board and game state for a new game."""
        if self.ai_thinking:
            messagebox.showwarning("AI Busy", "Cannot start a new game while AI is thinking.")
            return

        self.board = Board()
        self.selected_square = None
        self.possible_moves = []
        self.game_mode = mode
        self.player_color = human_color if mode == MODE_PVC else WHITE
        self.ai_thinking = False
        self._game_over_message_shown = False # Reset flag

        self.move_history_text.config(state=tk.NORMAL)
        self.move_history_text.delete('1.0', tk.END)
        self.move_history_text.config(state=tk.DISABLED)

        # Ensure the AI strategy selected in the menu is actually loaded
        if self.game_mode == MODE_PVC and not self.ai_module:
            if self.ai_strategy_name: # If a name is selected but module isn't loaded
                print(f"Attempting to load selected AI '{self.ai_strategy_name}' for new game.")
                if not self.load_ai_strategy(self.ai_strategy_name):
                     messagebox.showerror("AI Error", f"Failed to load AI '{self.ai_strategy_name}'. Switching to PvP.")
                     self.game_mode = MODE_PVP
                     self.player_color = WHITE # Reset player color concept
            else: # No AI strategy selected/available
                 messagebox.showerror("AI Error", "No AI strategy selected or available. Switching to PvP.")
                 self.game_mode = MODE_PVP
                 self.player_color = WHITE

        self.draw_board()
        self.update_status()
        self.update_material_display()
        print(f"Started new game: {mode}" + (f" (Human plays {'White' if human_color==WHITE else 'Black'})" if mode == MODE_PVC else ""))

        # Trigger AI move if it's AI's turn at start
        if self.game_mode == MODE_PVC and self.board.turn != self.player_color:
            if not self.ai_module: # Double check after potential load attempt above
                 messagebox.showerror("AI Error", "Cannot start PvC game: No AI strategy loaded.")
                 self.game_mode = MODE_PVP
                 self.update_status()
            else:
                 self.trigger_ai_move()


    def draw_board(self):
        """Draws the chessboard squares and pieces."""
        self.board_canvas.delete("all")
        for rank in range(BOARD_SIZE):
            for file in range(BOARD_SIZE):
                index = rank * 8 + file
                # Visual coordinates (y=0 at top)
                visual_rank = 7 - rank
                visual_file = file

                x1 = visual_file * SQUARE_SIZE
                y1 = visual_rank * SQUARE_SIZE
                x2 = x1 + SQUARE_SIZE
                y2 = y1 + SQUARE_SIZE

                # Draw square background
                color = BOARD_COLOR_LIGHT if (rank + file) % 2 != 0 else BOARD_COLOR_DARK
                self.board_canvas.create_rectangle(x1, y1, x2, y2, fill=color, tags="square", outline="gray")

                # Highlight selected square
                if index == self.selected_square:
                    self.board_canvas.create_rectangle(x1, y1, x2, y2, outline=HIGHLIGHT_COLOR, width=3)

                # Draw piece
                piece = self.board.get_piece(index)
                if piece:
                    symbol = piece.symbol()
                    # Piece color differs from text color usually
                    piece_draw_color = "black" # Default for black pieces
                    # Simple text color adjustment based on symbol maybe? Better: Define colors.
                    # Let's use simple black/white text for pieces for now.
                    if symbol in ["♙", "♘", "♗", "♖", "♕", "♔"]:
                        piece_draw_color = "white"

                    font_size = int(SQUARE_SIZE * 0.7)
                    # Use outline for better visibility on same-colored squares (optional but good)
                    outline_color = "black" if piece_draw_color == "white" else "white"
                    self.board_canvas.create_text(
                        x1 + SQUARE_SIZE / 2,
                        y1 + SQUARE_SIZE / 2,
                        text=symbol,
                        font=("Arial", font_size), # Removed 'bold' for wider font support
                        fill=piece_draw_color,
                        # outline=outline_color, # Consider adding this
                        tags="piece"
                    )

        # Draw possible move indicators if a piece is selected
        if self.selected_square is not None:
             for move in self.possible_moves:
                 dest_index = move.to_sq
                 dest_rank, dest_file = divmod(dest_index, 8)
                 # Visual coordinates for destination
                 visual_rank = 7 - dest_rank
                 visual_file = dest_file
                 x1 = visual_file * SQUARE_SIZE
                 y1 = visual_rank * SQUARE_SIZE

                 # Determine if it's a capture (for coloring)
                 # En passant flag or destination square occupied by opponent
                 is_capture = (move.flags == EN_PASSANT or
                               (self.board.get_piece(dest_index) is not None and
                                self.board.get_piece(dest_index).color != self.board.turn))

                 # --- MODIFICATION START ---
                 indicator_color = CAPTURE_MOVE_COLOR if is_capture else POSSIBLE_MOVE_COLOR
                 # --- MODIFICATION END ---

                 if is_capture:
                     # Draw capture indicator (polygon around edges)
                     offset = SQUARE_SIZE * 0.05 # Smaller offset looks cleaner
                     width = 4 # Thickness of the border
                     self.board_canvas.create_rectangle(
                         x1 + offset, y1 + offset,
                         x1 + SQUARE_SIZE - offset, y1 + SQUARE_SIZE - offset,
                         outline=indicator_color, # Use outline for captures
                         width=width,
                         tags="move_indicator"
                     )

                 else:
                     # Draw normal move indicator (circle in center)
                     radius = SQUARE_SIZE * 0.15
                     cx = x1 + SQUARE_SIZE / 2
                     cy = y1 + SQUARE_SIZE / 2
                     self.board_canvas.create_oval(
                         cx - radius, cy - radius, cx + radius, cy + radius,
                         fill=indicator_color, # Use fill for non-captures
                         outline="", # No border for the circle
                         tags="move_indicator"
                     )


    def update_status(self):
        """Updates the status label based on game state."""
        if self._game_over_message_shown: return

        if self.board.is_game_over():
            state = self.board.get_game_state()
            outcome = self.board.get_outcome()
            message = "Game Over: "
            if state == CHECKMATE:
                winner_name = "Black" if outcome == BLACK else "White"
                message += f"Checkmate! {winner_name} wins."
            elif state == STALEMATE: message = "Draw by Stalemate."
            elif state == INSUFFICIENT_MATERIAL: message = "Draw by Insufficient Material."
            elif state == FIFTY_MOVE_RULE: message = "Draw by 50-Move Rule."
            elif state == THREEFOLD_REPETITION: message = "Draw by Threefold Repetition."
            else: message = "Game Over - Unknown State"

            self.status_label.config(text=message)
            self.ai_thinking = False
            # Schedule the popup after status is updated
            if not self._game_over_message_shown:
                 self.root.after(100, self.show_game_over_message)
        else:
            turn_color = "White" if self.board.turn == WHITE else "Black"
            status_text = f"{turn_color}'s Turn"
            if self.board.is_in_check(self.board.turn):
                 status_text += " (Check!)"

            if self.ai_thinking:
                ai_display_name = self.ai_strategy_name.replace('ai_','').replace('_',' ').title() if self.ai_strategy_name else "AI"
                status_text = f"Computer ({ai_display_name}) is thinking..."
            elif self.game_mode == MODE_PVC and self.board.turn != self.player_color:
                 status_text = "Waiting for AI..." # Keep it simple

            self.status_label.config(text=status_text)


    # Helper method (Optional but recommended for SAN)
    def get_san(self, move):
        """Tries to generate Standard Algebraic Notation for a move."""
        # Basic SAN generation (can be improved significantly)
        piece = self.board.get_piece(move.from_sq)
        if not piece: return move.uci() # Fallback

        piece_char = ""
        if piece.type != PAWN:
            piece_char = PIECE_SYMBOLS.get((WHITE, piece.type), '?') # Use white symbol base
            # Need uppercase letter, not symbol for SAN usually
            name = PIECE_NAMES.get(piece.type, '')
            if name: piece_char = name[0].upper()
            if piece_char == 'P': piece_char = '' # Pawn uses no letter unless capturing

        dest_sq = index_to_square(move.to_sq)
        is_capture = (self.board.get_piece(move.to_sq) is not None) or move.flags == EN_PASSANT

        # Basic format: Pxd4, Nf3, O-O, e8=Q
        san = piece_char
        if piece.type == PAWN and is_capture:
            san += FILES[get_file(move.from_sq)] # Add origin file for pawn captures

        if is_capture:
            san += 'x'

        san += dest_sq

        if move.promotion:
            promo_name = PIECE_NAMES.get(move.promotion, '')
            if promo_name: san += "=" + promo_name[0].upper()

        # Check/Checkmate suffix - Requires looking ahead slightly or checking state *after* move
        # For history, we might omit this or add it later if needed. Let's omit for simplicity now.

        # Castling notation
        if move.flags == CASTLING:
            if dest_sq == 'g1' or dest_sq == 'g8': san = "O-O"
            elif dest_sq == 'c1' or dest_sq == 'c8': san = "O-O-O"

        # Disambiguation (e.g., Nbd2 vs Nfd2) - Complex, requires checking other legal moves
        # Omitting full disambiguation for simplicity.

        return san


    def add_move_to_history(self, move, piece):
        """Adds the move notation to the move history text widget."""
        move_num_str = ""
        if piece.color == WHITE:
            # Use the fullmove number *before* it increments (if it increments after black moves)
            # The board state reflects *after* the move, so use current fullmove number.
            move_num = self.board.fullmove_number
            move_num_str = f"{move_num}. "

        try:
            # Use basic SAN helper or fallback to UCI
            notation = self.get_san(move)
        except Exception as e:
            print(f"Error generating SAN for move {move}: {e}")
            notation = move.uci() # Fallback

        self.move_history_text.config(state=tk.NORMAL)
        if piece.color == WHITE:
            # Add number and first half of move pair
            self.move_history_text.insert(tk.END, move_num_str + notation + " ")
        else:
            # Add second half and newline
            self.move_history_text.insert(tk.END, notation + "\n")
            # Scroll to end only after Black's move (end of line)
            self.move_history_text.see(tk.END)
        self.move_history_text.config(state=tk.DISABLED)


    def on_square_click(self, event):
        """Handles clicks on the board canvas."""
        if self.board.is_game_over() or self.ai_thinking:
            return

        if self.game_mode == MODE_PVC and self.board.turn != self.player_color:
            print("Not your turn.")
            return

        canvas_x = event.x
        canvas_y = event.y
        file = canvas_x // SQUARE_SIZE
        rank = 7 - (canvas_y // SQUARE_SIZE)

        if not (0 <= file < BOARD_SIZE and 0 <= rank < BOARD_SIZE):
             print(f"Click outside board area ({canvas_x},{canvas_y}) ignored.")
             return

        clicked_index = rank * 8 + file
        clicked_piece = self.board.get_piece(clicked_index)

        if self.selected_square is None:
            # First Click: Select piece
            if clicked_piece and clicked_piece.color == self.board.turn:
                self.selected_square = clicked_index
                # Get all legal moves for the current player
                all_legal_moves = self.board.get_legal_moves()
                # Filter for moves starting from the selected square
                self.possible_moves = [m for m in all_legal_moves if m.from_sq == self.selected_square]
                if not self.possible_moves:
                    self.selected_square = None # No legal moves from here
                self.draw_board() # Redraw to show selection and possible moves

        else:
            # Second Click: Try to move or deselect
            is_possible_destination = any(move.to_sq == clicked_index for move in self.possible_moves)

            if clicked_index == self.selected_square:
                # Clicked same square again: Deselect
                self.selected_square = None
                self.possible_moves = []
                self.draw_board()

            elif is_possible_destination:
                # Clicked a valid destination square
                # Find the specific move object(s) matching this destination
                potential_moves = [m for m in self.possible_moves if m.to_sq == clicked_index]

                move_to_make = None
                origin_piece = self.board.get_piece(self.selected_square)

                # Handle promotion ambiguity
                is_promotion_landing = False
                if origin_piece and origin_piece.type == PAWN:
                    to_rank = get_rank(clicked_index)
                    if (origin_piece.color == WHITE and to_rank == 7) or \
                       (origin_piece.color == BLACK and to_rank == 0):
                        is_promotion_landing = True

                if is_promotion_landing:
                    # Check if the potential moves actually include promotion flags
                    promotion_moves = [m for m in potential_moves if m.promotion is not None]
                    if promotion_moves:
                        promo_choice = self.ask_promotion_choice()
                        if promo_choice:
                            # Find the specific promotion move
                            move_to_make = next((m for m in promotion_moves if m.promotion == promo_choice), None)
                            if not move_to_make: print("Error: Could not find chosen promotion move.")
                        else:
                            # User cancelled promotion dialog
                            self.selected_square = None; self.possible_moves = []; self.draw_board()
                            return # Cancel the move attempt
                    else:
                         # This case shouldn't happen if get_legal_moves is correct, but handle defensively
                         print("Error: Landed on promotion rank, but no promotion moves found.")
                         # Fallback to non-promotion move if one exists? Risky. Let's just select the first match.
                         if potential_moves: move_to_make = potential_moves[0]

                else: # Not a promotion
                    # Should normally only be one move, but handle defensively
                    if potential_moves:
                        move_to_make = potential_moves[0]
                        if len(potential_moves) > 1:
                             print(f"Warning: Ambiguous non-promotion move to {index_to_square(clicked_index)}. Choosing first.")
                    else:
                         print(f"Error: Clicked possible destination {index_to_square(clicked_index)}, but no matching move found.")


                if move_to_make:
                    self.perform_move(move_to_make)
                else:
                     # If no move was selected (e.g., cancelled promotion, error)
                     print("Move cancelled or error occurred.")
                     self.selected_square = None; self.possible_moves = []; self.draw_board()


            elif clicked_piece and clicked_piece.color == self.board.turn:
                 # Clicked another of own pieces: Switch selection
                 self.selected_square = clicked_index
                 all_legal_moves = self.board.get_legal_moves()
                 self.possible_moves = [m for m in all_legal_moves if m.from_sq == self.selected_square]
                 if not self.possible_moves: self.selected_square = None # No legal moves
                 self.draw_board()

            else:
                 # Clicked an empty square (not a valid destination) or opponent's piece
                 self.selected_square = None
                 self.possible_moves = []
                 self.draw_board()


    def ask_promotion_choice(self):
        """Asks the user which piece to promote a pawn to."""
        dialog = tk.Toplevel(self.root)
        dialog.title("Pawn Promotion")
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.resizable(False, False)

        # Use a variable that belongs to the dialog instance
        dialog.choice_var = tk.IntVar(value=QUEEN)

        tk.Label(dialog, text="Promote pawn to:").pack(pady=10)
        options_frame = tk.Frame(dialog)
        options_frame.pack(pady=5)

        promoter_color = self.board.turn # Color of the player whose turn it is
        promo_pieces = [QUEEN, ROOK, BISHOP, KNIGHT]

        # Get symbols based on the actual player color
        symbols = {pt: PIECE_SYMBOLS.get((promoter_color, pt), '?') for pt in promo_pieces}

        for piece_type in promo_pieces:
            symbol = symbols[piece_type]
            name = PIECE_NAMES[piece_type]
            rb = tk.Radiobutton(options_frame, text=f"{name}\n({symbol})",
                                variable=dialog.choice_var, # Use the dialog's variable
                                value=piece_type,
                                indicatoron=0, width=8, height=3, font=("Arial", 10))
            rb.pack(side=tk.LEFT, padx=5)
            if piece_type == QUEEN: rb.select() # Pre-select Queen

        dialog.user_choice = None # Store result on the dialog instance

        def on_ok():
            dialog.user_choice = dialog.choice_var.get() # Get value from dialog's variable
            dialog.destroy()

        def on_cancel():
            dialog.user_choice = None # Indicate cancellation
            dialog.destroy()

        button_frame = tk.Frame(dialog)
        button_frame.pack(pady=10)
        ok_button = tk.Button(button_frame, text="OK", width=10, command=on_ok)
        ok_button.pack(side=tk.LEFT, padx=10)
        # Add a Cancel button maybe? For now, closing window cancels.
        dialog.protocol("WM_DELETE_WINDOW", on_cancel) # Handle window close

        # Center dialog relative to root window
        self.root.update_idletasks()
        root_x, root_y = self.root.winfo_rootx(), self.root.winfo_rooty()
        root_w, root_h = self.root.winfo_width(), self.root.winfo_height()
        dialog.update_idletasks()
        dialog_w, dialog_h = dialog.winfo_width(), dialog.winfo_height()
        x = root_x + (root_w // 2) - (dialog_w // 2)
        y = root_y + (root_h // 2) - (dialog_h // 2)
        dialog.geometry(f"+{x}+{y}")

        dialog.wait_window() # Wait for the dialog to close

        # Return the choice stored on the dialog instance
        return getattr(dialog, 'user_choice', None)


    def perform_move(self, move):
        """Makes the move on the board, updates history, status, material, and triggers AI."""
        piece_moved = self.board.get_piece(move.from_sq)
        if not piece_moved:
             print(f"Error: No piece at {index_to_square(move.from_sq)} for move {move}")
             self.selected_square = None; self.possible_moves = []; self.draw_board()
             return

        # Make move BEFORE adding to history, so history shows the correct move number/state
        self.board.make_move(move)

        # Add to history AFTER making move, using the piece that *was* moved
        self.add_move_to_history(move, piece_moved)

        # Update UI elements AFTER move
        self.update_material_display()
        self.selected_square = None
        self.possible_moves = []
        self.draw_board() # Redraw board reflecting the move
        self.update_status() # Update status label (whose turn, check)

        # Check for game over AFTER updating status/board
        if self.board.is_game_over():
            # Status update already handled game over text, just need popup logic
            if not self._game_over_message_shown:
                 # Use `after` to allow UI to update before blocking with messagebox
                 self.root.after(100, self.show_game_over_message)
            return # Don't trigger AI if game is over

        # Trigger AI if applicable
        if self.game_mode == MODE_PVC and self.board.turn != self.player_color and not self.ai_thinking:
             self.trigger_ai_move()


    def trigger_ai_move(self):
        """Initiates the AI move calculation in a separate thread."""
        if not self.ai_module or not hasattr(self.ai_module, 'find_best_move'):
             messagebox.showerror("AI Error", "No valid AI strategy loaded or function missing.")
             # Revert to PvP?
             self.game_mode = MODE_PVP; self.update_status()
             return
        # Double check it's actually AI's turn
        if self.game_mode != MODE_PVC or self.board.turn == self.player_color:
             print("Trigger AI called, but not AI's turn or mode.")
             return

        self.ai_thinking = True
        self.update_status() # Show "AI is thinking..."
        self.root.update_idletasks() # Ensure status label updates

        # Create a copy for the AI to work on, preserving the main board state
        board_copy_for_ai = self.board.copy()

        # Run AI calculation in a separate thread
        thread = threading.Thread(target=self._ai_calculation_thread, args=(board_copy_for_ai,), daemon=True)
        thread.start()


    def _ai_calculation_thread(self, board_instance):
        """Function run in the background thread to calculate the AI move."""
        ai_move = None
        try:
             start_time = time.time()
             ai_move = self.ai_module.find_best_move(board_instance)
             end_time = time.time()
             print(f"AI ({self.ai_strategy_name}) took {end_time - start_time:.3f} seconds.")
             # Schedule the result processing back on the main thread
             self.root.after(0, self._process_ai_result, ai_move)
        except Exception as e:
             print(f"Error during AI calculation thread: {e}")
             import traceback; traceback.print_exc()
             # Schedule error handling back on the main thread
             self.root.after(0, self._handle_ai_error, str(e))


    def _process_ai_result(self, ai_move):
        """Processes the AI's chosen move (executed in the main Tkinter thread)."""
        self.ai_thinking = False # AI finished thinking

        # Check if game ended or mode changed while AI was thinking
        if self.board.is_game_over():
             print("Game ended while AI was thinking.")
             self.update_status() # Ensure final status shown
             return
        if self.game_mode != MODE_PVC or self.board.turn == self.player_color:
             print("AI result received, but not AI's turn or mode changed.")
             self.update_status()
             return

        if ai_move and isinstance(ai_move, Move):
             # Validate the AI move against current legal moves (important!)
             # The AI worked on a copy, the state might have changed (very unlikely in strict turns, but good practice)
             legal_moves = self.board.get_legal_moves()
             actual_move_to_make = None
             for legal_move in legal_moves:
                  # Compare essential move components
                  if (legal_move.from_sq == ai_move.from_sq and
                      legal_move.to_sq == ai_move.to_sq and
                      legal_move.promotion == ai_move.promotion): # Promotion type must match
                       actual_move_to_make = legal_move # Use the validated legal move object
                       break

             if actual_move_to_make:
                 try: move_str = self.get_san(actual_move_to_make)
                 except: move_str = actual_move_to_make.uci()
                 print(f"AI chooses move: {move_str}")
                 self.perform_move(actual_move_to_make)
             else:
                 # AI returned a move that is NOT currently legal
                 error_msg = f"AI ({self.ai_strategy_name}) returned an illegal move: {ai_move.uci()} in current position."
                 print(error_msg)
                 messagebox.showerror("AI Error", error_msg + "\nAttempting fallback.")
                 fallback_move = self.get_fallback_move()
                 if fallback_move:
                      print(f"AI failed, using fallback: {self.get_san(fallback_move)}")
                      self.perform_move(fallback_move)
                 else:
                      print("AI failed, no legal fallback moves available.")
                      self.update_status() # Update status to show potential stalemate/checkmate
                      self.show_game_over_message() # Game ends if no moves
        elif ai_move is None:
             # AI explicitly returned None, likely meaning it thinks there are no moves
             print(f"AI ({self.ai_strategy_name}) returned None (suggesting no moves).")
             legal_moves = self.board.get_legal_moves()
             if not legal_moves:
                 print("Confirmed: No legal moves for AI.")
                 # Board state is already game over (checkmate/stalemate), update status and show message
                 self.update_status()
                 self.show_game_over_message()
             else:
                 # AI failed to find a move, but legal moves exist!
                 print(f"AI ERROR: Returned None, but legal moves exist! Using fallback.")
                 messagebox.showerror("AI Error", "AI failed to find a move. Attempting fallback.")
                 fallback_move = self.get_fallback_move()
                 if fallback_move:
                     self.perform_move(fallback_move)
                 else: # Should not happen if legal_moves existed, but defensive check
                     print("Fallback failed after AI returned None.")
                     self.update_status(); self.show_game_over_message()
        else:
             # AI returned something other than a Move object or None
             print(f"AI returned invalid object type: {type(ai_move)}")
             messagebox.showerror("AI Error", f"AI ({self.ai_strategy_name}) returned invalid data type: {type(ai_move)}. Using fallback.")
             fallback_move = self.get_fallback_move()
             if fallback_move: self.perform_move(fallback_move)
             else: print("Fallback failed after AI returned invalid data."); self.update_status(); self.show_game_over_message()


    def _handle_ai_error(self, error_message):
        """Handles exceptions raised within the AI calculation thread."""
        self.ai_thinking = False
        # Check if state changed while AI was erroring out
        if self.board.is_game_over() or (self.game_mode == MODE_PVC and self.board.turn == self.player_color):
             print(f"AI error occurred, but game state changed. Ignoring error.")
             self.update_status()
             return

        messagebox.showerror("AI Calculation Error", f"Error during AI move calculation ({self.ai_strategy_name}):\n{error_message}")
        print("Attempting fallback move after AI error.")
        self.update_status() # Update status from "thinking"

        fallback_move = self.get_fallback_move()
        if fallback_move:
             print(f"Using fallback after AI error: {self.get_san(fallback_move)}")
             self.perform_move(fallback_move)
        else:
             print("No legal fallback moves available after AI error.")
             # Game must be over if no moves available
             self.show_game_over_message()


    def get_fallback_move(self):
        """Returns a random legal move as a fallback. Returns None if no moves."""
        try:
            legal_moves = self.board.get_legal_moves()
            if legal_moves:
                return random.choice(legal_moves)
        except Exception as e:
            print(f"Error getting fallback moves: {e}")
        return None


    def show_game_over_message(self):
        """Shows a message box indicating the game result. Prevents multiple popups."""
        # Check flag *before* showing message
        if self._game_over_message_shown:
            return
        self._game_over_message_shown = True # Set flag immediately

        state = self.board.get_game_state()
        outcome = self.board.get_outcome()
        message = "Game Over!\n\n" # Add newline for better spacing

        if state == CHECKMATE:
            winner_name = "Black" if outcome == BLACK else "White"
            message += f"Checkmate!\n{winner_name} wins."
        elif state == STALEMATE:
            message += "Draw by Stalemate."
        elif state == INSUFFICIENT_MATERIAL:
            message += "Draw by Insufficient Material."
        elif state == FIFTY_MOVE_RULE:
            message += "Draw by 50-Move Rule."
        elif state == THREEFOLD_REPETITION:
            message += "Draw by Threefold Repetition."
        else:
            # Should not happen if logic is correct
            message += f"Result Unknown (State: {state})."

        # Ensure final status label reflects the outcome correctly
        self.status_label.config(text=message.replace("\n\n", "\n").replace("\n", " ")) # Single line status
        messagebox.showinfo("Game Over", message)


# Main execution
if __name__ == "__main__":
    # Ensure ai_strategies directory is discoverable if running main.py directly
    script_dir = os.path.dirname(os.path.abspath(__file__))
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)
    # Add parent dir if ai_strategies is a sibling (common structure)
    parent_dir = os.path.dirname(script_dir)
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)

    root = tk.Tk()
    gui = ChessGUI(root)
    root.mainloop()
