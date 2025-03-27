# chess_gui.py
"""
Provides a Tkinter-based graphical user interface for the chess game.
Displays material difference and board coordinates. <<< MODIFIED Docstring
"""

import tkinter as tk
from tkinter import messagebox, simpledialog, Menu
import importlib
import threading
import time
import os
import random
import sys

from constants import * # Import constants like FILES, RANKS, SQUARE_SIZE
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

        # Configure grid columns/rows inside board_area_frame if needed for alignment
        # Column 0 for rank labels, Column 1 for board+file labels
        # Row 0 for file labels (top - optional), Row 1 for board+rank labels
        # Let's put files below (row 2), ranks left (col 0)

        # --- Create Rank Labels (8 down to 1) ---
        rank_label_font = ("Arial", 10) # Smaller font for coordinates
        label_width = 2 # Approx width in characters
        for i in range(BOARD_SIZE):
            rank_label_text = RANKS[BOARD_SIZE - 1 - i] # 8, 7, ..., 1
            label = tk.Label(
                self.board_area_frame,
                text=rank_label_text,
                font=rank_label_font,
                width=label_width,
                height=SQUARE_SIZE // 20 # Height approx based on square size
            )
            # Place in row i+1 (leaving row 0 for potential top labels/padding), column 0
            label.grid(row=i + 1, column=0, sticky='ns', padx=(0, 2)) # Stick North-South

        # --- Create File Labels (a to h) ---
        file_label_font = ("Arial", 10)
        label_height = 1 # Approx height
        for i in range(BOARD_SIZE):
            file_label_text = FILES[i] # a, b, ..., h
            label = tk.Label(
                self.board_area_frame,
                text=file_label_text,
                font=file_label_font,
                width=SQUARE_SIZE // 10, # Width approx based on square size
                height=label_height
            )
            # Place in row BOARD_SIZE+1 (below the board), column i+1
            label.grid(row=BOARD_SIZE + 1, column=i + 1, sticky='ew', pady=(2, 0)) # Stick East-West

        # --- Create Board Canvas ---
        self.board_canvas = tk.Canvas(
            self.board_area_frame, # Place canvas inside the frame
            width=BOARD_SIZE * SQUARE_SIZE,
            height=BOARD_SIZE * SQUARE_SIZE
        )
        # Place canvas in row 1->BOARD_SIZE, column 1->BOARD_SIZE
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
        self._game_over_message_shown = False # <<< Added flag initialization


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
            self.ai_strategy_name = available_ais[0]

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
            self.populate_ai_menu()
            return

        if ai_name == self.ai_strategy_name:
            return

        if self.load_ai_strategy(ai_name):
            display_name = ai_name.replace('ai_','').replace('_',' ').title()
            messagebox.showinfo("AI Changed", f"AI strategy set to {display_name}. Changes apply on New Game.")
        else:
            self.populate_ai_menu()


    def load_ai_strategy(self, ai_name):
        """Dynamically imports and loads the AI module. Returns True on success, False on failure."""
        if not ai_name:
             print("Error: Attempted to load an empty AI name.")
             return False

        try:
            if "ai_strategies" in sys.modules:
                 importlib.reload(sys.modules["ai_strategies"])

            module_name = f"ai_strategies.{ai_name}"
            if module_name in sys.modules:
                 self.ai_module = importlib.reload(sys.modules[module_name])
            else:
                 self.ai_module = importlib.import_module(module_name)

            if not hasattr(self.ai_module, "find_best_move"):
                 raise AttributeError(f"AI module {ai_name} does not have 'find_best_move' function.")

            self.ai_strategy_name = ai_name
            print(f"Successfully loaded AI strategy: {ai_name}")
            # Update menu state after successful load might be needed if populate doesn't run again
            # self.populate_ai_menu() # Or just update the variable/check mark if possible
            return True
        except ModuleNotFoundError:
            messagebox.showerror("Error", f"Could not find AI strategy file: {ai_name}.py or its dependencies.")
            self.ai_module = None
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

        self.draw_board()
        self.update_status()
        self.update_material_display()
        print(f"Started new game: {mode}" + (f" (Human plays {'White' if human_color==WHITE else 'Black'})" if mode == MODE_PVC else ""))

        if self.game_mode == MODE_PVC and self.board.turn != self.player_color:
            if not self.ai_module and self.ai_strategy_name: # Check if name exists but module failed
                 print(f"Attempting to reload failed AI '{self.ai_strategy_name}' for new game.")
                 self.load_ai_strategy(self.ai_strategy_name) # Try loading again

            if not self.ai_module:
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
                visual_rank = 7 - rank
                visual_file = file

                x1 = visual_file * SQUARE_SIZE
                y1 = visual_rank * SQUARE_SIZE
                x2 = x1 + SQUARE_SIZE
                y2 = y1 + SQUARE_SIZE

                color = BOARD_COLOR_LIGHT if (rank + file) % 2 != 0 else BOARD_COLOR_DARK
                self.board_canvas.create_rectangle(x1, y1, x2, y2, fill=color, tags="square", outline="gray")

                if index == self.selected_square:
                    self.board_canvas.create_rectangle(x1, y1, x2, y2, outline=HIGHLIGHT_COLOR, width=3)

                piece = self.board.get_piece(index)
                if piece:
                    symbol = piece.symbol()
                    piece_color = "black" if piece.color == BLACK else "white"
                    font_size = int(SQUARE_SIZE * 0.7)
                    self.board_canvas.create_text(
                        x1 + SQUARE_SIZE / 2,
                        y1 + SQUARE_SIZE / 2,
                        text=symbol,
                        font=("Arial", font_size, "bold"),
                        fill=piece_color,
                        tags="piece"
                    )

        if self.selected_square is not None:
             for move in self.possible_moves:
                 dest_index = move.to_sq
                 dest_rank, dest_file = divmod(dest_index, 8)
                 visual_rank = 7 - dest_rank
                 visual_file = dest_file
                 x1 = visual_file * SQUARE_SIZE
                 y1 = visual_rank * SQUARE_SIZE

                 is_capture = self.board.get_piece(dest_index) is not None or move.flags == EN_PASSANT

                 if is_capture:
                     offset = SQUARE_SIZE * 0.15
                     points = [
                         x1, y1, x1 + offset, y1, x1, y1 + offset,
                         x1 + SQUARE_SIZE, y1, x1 + SQUARE_SIZE - offset, y1, x1 + SQUARE_SIZE, y1 + offset,
                         x1, y1 + SQUARE_SIZE, x1 + offset, y1 + SQUARE_SIZE, x1, y1 + SQUARE_SIZE - offset,
                         x1 + SQUARE_SIZE, y1 + SQUARE_SIZE, x1 + SQUARE_SIZE - offset, y1 + SQUARE_SIZE, x1 + SQUARE_SIZE, y1 + SQUARE_SIZE - offset
                     ]
                     self.board_canvas.create_polygon(points, fill=POSSIBLE_MOVE_COLOR, outline="")
                 else:
                     radius = SQUARE_SIZE * 0.15
                     cx = x1 + SQUARE_SIZE / 2
                     cy = y1 + SQUARE_SIZE / 2
                     self.board_canvas.create_oval(
                         cx - radius, cy - radius, cx + radius, cy + radius,
                         fill=POSSIBLE_MOVE_COLOR, outline=""
                     )


    def update_status(self):
        """Updates the status label based on game state."""
        # Avoid status update if game over message sequence has started
        if self._game_over_message_shown: return

        if self.board.is_game_over():
            # Game just ended, status needs final update before message box
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
        else:
            turn_color = "White" if self.board.turn == WHITE else "Black"
            status_text = f"{turn_color}'s Turn"
            if self.board.is_in_check(self.board.turn):
                 status_text += " (Check!)"

            if self.ai_thinking:
                ai_display_name = self.ai_strategy_name.replace('ai_','') if self.ai_strategy_name else "AI"
                status_text = f"Computer ({ai_display_name}) is thinking..."
            elif self.game_mode == MODE_PVC and self.board.turn != self.player_color:
                 status_text = "Waiting for AI..."

            self.status_label.config(text=status_text)


    def add_move_to_history(self, move, piece):
        """Adds the move notation to the move history text widget."""
        move_num_str = ""
        if piece.color == WHITE:
            move_num = self.board.fullmove_number
            move_num_str = f"{move_num}. "

        try:
            notation = self.board.to_san(move, piece) # Use helper if available
        except AttributeError:
            notation = move.uci() # Fallback
        except Exception as e:
            print(f"Error generating SAN for move {move}: {e}")
            notation = move.uci()

        self.move_history_text.config(state=tk.NORMAL)
        if piece.color == WHITE:
            self.move_history_text.insert(tk.END, move_num_str + notation + " ")
        else:
            self.move_history_text.insert(tk.END, notation + "\n")
            self.move_history_text.see(tk.END)
        self.move_history_text.config(state=tk.DISABLED)


    def on_square_click(self, event):
        """Handles clicks on the board canvas."""
        # Get click coordinates relative to the canvas
        canvas_x = event.x
        canvas_y = event.y

        if self.board.is_game_over() or self.ai_thinking:
            return

        if self.game_mode == MODE_PVC and self.board.turn != self.player_color:
            print("Not your turn.")
            return

        # Convert canvas coordinates to board file/rank (0-7)
        file = canvas_x // SQUARE_SIZE
        rank = 7 - (canvas_y // SQUARE_SIZE)

        # Ensure file/rank are within bounds before calculating index
        if not (0 <= file < BOARD_SIZE and 0 <= rank < BOARD_SIZE):
             print(f"Click outside board area ({canvas_x},{canvas_y}) ignored.")
             return

        clicked_index = rank * 8 + file
        clicked_piece = self.board.get_piece(clicked_index)

        if self.selected_square is None:
            # First Click: Selecting a piece
            if clicked_piece and clicked_piece.color == self.board.turn:
                self.selected_square = clicked_index
                all_legal_moves = self.board.get_legal_moves()
                self.possible_moves = [m for m in all_legal_moves if m.from_sq == self.selected_square]
                if not self.possible_moves:
                    self.selected_square = None
                self.draw_board()

        else:
            # Second Click: Moving or deselecting
            is_possible_destination = any(move.to_sq == clicked_index for move in self.possible_moves)

            if clicked_index == self.selected_square:
                self.selected_square = None
                self.possible_moves = []
                self.draw_board()

            elif is_possible_destination:
                potential_moves = [m for m in self.possible_moves if m.to_sq == clicked_index]
                if not potential_moves:
                    print("Error: Move destination mismatch despite check.")
                    self.selected_square = None; self.possible_moves = []; self.draw_board()
                    return

                move_to_make = None
                origin_piece = self.board.get_piece(self.selected_square)
                is_promotion = False
                if origin_piece and origin_piece.type == PAWN:
                    to_rank = get_rank(clicked_index)
                    if (origin_piece.color == WHITE and to_rank == 7) or \
                       (origin_piece.color == BLACK and to_rank == 0):
                        is_promotion = True

                if is_promotion:
                    promotion_moves = [m for m in potential_moves if m.is_promotion()]
                    if not promotion_moves:
                        print("Error: Expected promotion move but none found."); # Cancel
                        self.selected_square = None; self.possible_moves = []; self.draw_board()
                        return
                    else:
                        promo_choice = self.ask_promotion_choice()
                        if promo_choice:
                            move_to_make = next((m for m in promotion_moves if m.promotion == promo_choice), None)
                            if not move_to_make:
                                print(f"Error: Could not find specific promotion move."); # Cancel
                                self.selected_square = None; self.possible_moves = []; self.draw_board()
                                return
                        else: # User cancelled promotion
                            self.selected_square = None; self.possible_moves = []; self.draw_board()
                            return
                else: # Not a promotion
                    if len(potential_moves) == 1: move_to_make = potential_moves[0]
                    else:
                        print(f"Warning: Ambiguous non-promotion move. Selecting first.")
                        move_to_make = potential_moves[0]

                if move_to_make:
                    self.perform_move(move_to_make)
                # State reset happens in perform_move or if move cancelled above

            elif clicked_piece and clicked_piece.color == self.board.turn:
                 # Clicked another of own pieces: Switch selection
                 self.selected_square = clicked_index
                 all_legal_moves = self.board.get_legal_moves()
                 self.possible_moves = [m for m in all_legal_moves if m.from_sq == self.selected_square]
                 if not self.possible_moves: self.selected_square = None
                 self.draw_board()
            else: # Clicked invalid square
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
        choice = tk.IntVar(value=QUEEN)
        tk.Label(dialog, text="Promote pawn to:").pack(pady=10)
        options_frame = tk.Frame(dialog)
        options_frame.pack(pady=5)
        promoter_color = self.board.turn
        promo_pieces = [QUEEN, ROOK, BISHOP, KNIGHT]
        symbols = {pt: PIECE_SYMBOLS.get((promoter_color, pt), '?') for pt in promo_pieces}
        for piece_type in promo_pieces:
            symbol = symbols[piece_type]; name = PIECE_NAMES[piece_type]
            rb = tk.Radiobutton(options_frame, text=f"{name}\n({symbol})", variable=choice, value=piece_type,
                                indicatoron=0, width=8, height=3, font=("Arial", 10))
            rb.pack(side=tk.LEFT, padx=5)
            if piece_type == QUEEN: rb.select()
        dialog.user_choice = None
        def on_ok(): dialog.user_choice = choice.get(); dialog.destroy()
        def on_cancel(): dialog.user_choice = None; dialog.destroy()
        button_frame = tk.Frame(dialog); button_frame.pack(pady=10)
        ok_button = tk.Button(button_frame, text="OK", width=10, command=on_ok); ok_button.pack(side=tk.LEFT, padx=10)
        dialog.protocol("WM_DELETE_WINDOW", on_cancel)
        self.root.update_idletasks()
        root_x, root_y = self.root.winfo_rootx(), self.root.winfo_rooty()
        root_w, root_h = self.root.winfo_width(), self.root.winfo_height()
        dialog.update_idletasks()
        dialog_w, dialog_h = dialog.winfo_width(), dialog.winfo_height()
        x = root_x + (root_w // 2) - (dialog_w // 2); y = root_y + (root_h // 2) - (dialog_h // 2)
        dialog.geometry(f"+{x}+{y}")
        dialog.wait_window()
        return getattr(dialog, 'user_choice', None)


    def perform_move(self, move):
        """Makes the move on the board, updates history, status, material, and triggers AI."""
        piece_moved = self.board.get_piece(move.from_sq)
        if not piece_moved:
             print(f"Error: No piece at {index_to_square(move.from_sq)} for move {move}")
             self.selected_square = None; self.possible_moves = []; self.draw_board()
             return

        self.board.make_move(move)
        self.add_move_to_history(move, piece_moved)
        self.update_material_display() # <<< Ensure this is called

        self.selected_square = None
        self.possible_moves = []

        self.draw_board()
        self.update_status() # Update status *after* drawing

        if self.board.is_game_over():
            if not self._game_over_message_shown: # Check flag before scheduling
                 self.root.after(100, self.show_game_over_message)
            return

        if self.game_mode == MODE_PVC and self.board.turn != self.player_color and not self.ai_thinking:
             self.trigger_ai_move()


    def trigger_ai_move(self):
        """Initiates the AI move calculation in a separate thread."""
        if not self.ai_module or not hasattr(self.ai_module, 'find_best_move'):
             messagebox.showerror("AI Error", "No valid AI strategy loaded or function missing.")
             self.game_mode = MODE_PVP; self.update_status()
             return
        if self.game_mode != MODE_PVC or self.board.turn == self.player_color: return

        self.ai_thinking = True; self.update_status(); self.root.update_idletasks()
        board_copy_for_ai = self.board.copy()
        thread = threading.Thread(target=self._ai_calculation_thread, args=(board_copy_for_ai,), daemon=True); thread.start()


    def _ai_calculation_thread(self, board_instance):
        """Function run in the background thread to calculate the AI move."""
        try:
             start_time = time.time(); ai_move = self.ai_module.find_best_move(board_instance); end_time = time.time()
             print(f"AI ({self.ai_strategy_name}) took {end_time - start_time:.3f} seconds.")
             self.root.after(0, self._process_ai_result, ai_move)
        except Exception as e:
             print(f"Error during AI calculation thread: {e}"); import traceback; traceback.print_exc()
             self.root.after(0, self._handle_ai_error, str(e))


    def _process_ai_result(self, ai_move):
        """Processes the AI's chosen move (executed in the main thread)."""
        self.ai_thinking = False
        if self.board.is_game_over(): print("Game ended while AI was thinking."); self.update_status(); return
        if self.game_mode != MODE_PVC or self.board.turn == self.player_color: print("AI result received, but not AI's turn."); self.update_status(); return

        if ai_move and isinstance(ai_move, Move):
             legal_moves = self.board.get_legal_moves(); actual_move_to_make = None
             for legal_move in legal_moves:
                  if (legal_move.from_sq == ai_move.from_sq and legal_move.to_sq == ai_move.to_sq and legal_move.promotion == ai_move.promotion):
                       actual_move_to_make = legal_move; break
             if actual_move_to_make:
                 try: move_str = self.board.to_san(actual_move_to_make)
                 except: move_str = actual_move_to_make.uci()
                 print(f"AI chooses move: {move_str}"); self.perform_move(actual_move_to_make)
             else:
                 error_msg = f"AI ({self.ai_strategy_name}) returned an illegal move: {ai_move.uci()}."; print(error_msg)
                 fallback_move = self.get_fallback_move()
                 if fallback_move: print(f"AI failed, using fallback."); self.perform_move(fallback_move)
                 else: print("AI failed, no fallback."); self.update_status(); self.show_game_over_message() # Show directly if no moves
        elif ai_move is None:
             print(f"AI ({self.ai_strategy_name}) returned None.")
             legal_moves = self.board.get_legal_moves()
             if not legal_moves: print("Confirmed: No legal moves."); self.update_status(); self.show_game_over_message() # Show directly
             else: print(f"AI returned None, but moves exist!"); fallback_move = self.get_fallback_move(); self.perform_move(fallback_move) if fallback_move else messagebox.showerror("Error", "AI failed, fallback failed.")
        else: print(f"AI returned invalid object: {ai_move}"); messagebox.showerror("AI Error", f"Invalid object from AI: {type(ai_move)}"); self.update_status()


    def _handle_ai_error(self, error_message):
        """Handles exceptions raised within the AI calculation thread."""
        self.ai_thinking = False
        if self.board.is_game_over() or (self.game_mode == MODE_PVC and self.board.turn == self.player_color): print(f"AI error occurred, but state changed."); self.update_status(); return
        messagebox.showerror("AI Calculation Error", f"Error during AI move calculation ({self.ai_strategy_name}):\n{error_message}"); self.update_status()
        print("Attempting fallback move after AI error."); fallback_move = self.get_fallback_move()
        if fallback_move: self.perform_move(fallback_move)
        else: print("No fallback after AI error."); self.show_game_over_message() if self.board.is_game_over() else None


    def get_fallback_move(self):
        """Returns a random legal move as a fallback. Returns None if no moves."""
        try:
            legal_moves = self.board.get_legal_moves()
            if legal_moves: return random.choice(legal_moves)
        except Exception as e: print(f"Error getting fallback moves: {e}")
        return None


    def show_game_over_message(self):
        """Shows a message box indicating the game result."""
        if self._game_over_message_shown: return
        self._game_over_message_shown = True

        state = self.board.get_game_state(); outcome = self.board.get_outcome()
        message = "Game Over!\n"
        if state == CHECKMATE: winner_name = "Black" if outcome == BLACK else "White"; message += f"Checkmate! {winner_name} wins."
        elif state == STALEMATE: message += "Draw by Stalemate."
        elif state == INSUFFICIENT_MATERIAL: message += "Draw by Insufficient Material."
        elif state == FIFTY_MOVE_RULE: message += "Draw by 50-Move Rule."
        elif state == THREEFOLD_REPETITION: message += "Draw by Threefold Repetition."
        else: message += f"Result Unknown (State: {state})."

        self.status_label.config(text=message.replace("\n", " ")) # Update final status
        messagebox.showinfo("Game Over", message)


# Main execution (for testing if run directly)
if __name__ == "__main__":
    print("This is the GUI module. Run main.py to start the application.")
    # root = tk.Tk()
    # gui = ChessGUI(root)
    # root.mainloop()
