# chess_gui.py
"""
Provides a Tkinter-based graphical user interface for the chess game.
"""

import tkinter as tk
from tkinter import messagebox, simpledialog, Menu
import importlib # To dynamically load AI modules
import threading # To run AI calculation without freezing GUI
import time
import os

from constants import *
from chess_logic import Board, Move, Piece

# --- Game Modes ---
MODE_PVP = "Player vs Player"
MODE_PVC = "Player vs Computer"

class ChessGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Python Chess")
        self.root.resizable(False, False) # Prevent resizing

        self.board = Board()
        self.board_canvas = tk.Canvas(root, width=BOARD_SIZE * SQUARE_SIZE, height=BOARD_SIZE * SQUARE_SIZE)
        self.board_canvas.pack(side=tk.LEFT, padx=10, pady=10)
        self.board_canvas.bind("<Button-1>", self.on_square_click)

        # --- UI Elements ---
        self.control_frame = tk.Frame(root)
        self.control_frame.pack(side=tk.RIGHT, padx=10, pady=10, fill=tk.Y)

        self.status_label = tk.Label(self.control_frame, text="White's Turn", font=("Arial", 14))
        self.status_label.pack(pady=10)

        self.move_history_text = tk.Text(self.control_frame, height=20, width=20, state=tk.DISABLED, font=("Courier", 10))
        self.move_history_scroll = tk.Scrollbar(self.control_frame, command=self.move_history_text.yview)
        self.move_history_text.config(yscrollcommand=self.move_history_scroll.set)
        self.move_history_text.pack(side=tk.LEFT, fill=tk.Y)
        self.move_history_scroll.pack(side=tk.RIGHT, fill=tk.Y)


        # --- Game State Variables ---
        self.selected_square = None # Store the index (0-63) of the first click
        self.possible_moves = []   # Store legal moves (Move objects) from the selected square
        self.player_color = WHITE  # In PvC, the human player's color
        self.game_mode = MODE_PVP
        self.ai_module = None
        self.ai_thinking = False # Flag to prevent clicks while AI calculates
        self.ai_strategy_name = "ai_random" # Default AI

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
        self.populate_ai_menu() # Add available AI strategies


        # --- Initial Setup ---
        self.load_ai_strategy(self.ai_strategy_name) # Load default AI
        self.draw_board()
        self.update_status()

    def populate_ai_menu(self):
        """Finds available AI strategies in the ai_strategies folder and adds them to the menu."""
        self.ai_menu.delete(0, tk.END) # Clear existing entries
        ai_dir = "ai_strategies"
        try:
            available_ais = [
                f.replace(".py", "")
                for f in os.listdir(ai_dir)
                if f.startswith("ai_") and f.endswith(".py") and f != "ai_interface.py"
            ]
        except FileNotFoundError:
            available_ais = []
            print(f"Warning: AI strategies directory '{ai_dir}' not found.")

        if not available_ais:
             self.ai_menu.add_command(label="No AI found", state=tk.DISABLED)
             return

        current_ai_var = tk.StringVar(value=self.ai_strategy_name)

        for ai_name in available_ais:
            self.ai_menu.add_radiobutton(
                label=ai_name.replace("ai_", "").replace("_", " ").title(),
                variable=current_ai_var,
                value=ai_name,
                command=lambda name=ai_name: self.select_ai_strategy(name)
            )
        self.ai_strategy_name = current_ai_var.get() # Ensure consistency if default changed


    def select_ai_strategy(self, ai_name):
        """Loads the selected AI strategy."""
        if self.ai_thinking:
            messagebox.showwarning("AI Busy", "Cannot change AI while it's thinking.")
            # Need to reset the radio button visually if change failed - tricky with lambda
            self.populate_ai_menu() # Repopulate to reset selection state
            return
        self.load_ai_strategy(ai_name)
        messagebox.showinfo("AI Changed", f"AI strategy set to {ai_name}. Changes apply on New Game.")


    def load_ai_strategy(self, ai_name):
        """Dynamically imports and loads the AI module."""
        try:
            module_name = f"ai_strategies.{ai_name}"
            self.ai_module = importlib.import_module(module_name)
            # Check if the required function exists
            if not hasattr(self.ai_module, "find_best_move"):
                 raise AttributeError(f"AI module {ai_name} does not have 'find_best_move' function.")
            self.ai_strategy_name = ai_name
            print(f"Successfully loaded AI strategy: {ai_name}")
            # Update menu checkmark (easier via repopulation)
            self.populate_ai_menu()
        except ModuleNotFoundError:
            messagebox.showerror("Error", f"Could not find AI strategy file: {ai_name}.py")
            self.ai_module = None
            self.ai_strategy_name = None
        except AttributeError as e:
             messagebox.showerror("Error", f"Error loading AI {ai_name}: {e}")
             self.ai_module = None
             self.ai_strategy_name = None
        except Exception as e:
             messagebox.showerror("Error", f"An unexpected error occurred loading AI {ai_name}: {e}")
             self.ai_module = None
             self.ai_strategy_name = None


    def start_new_game(self, mode, human_color=WHITE):
        """Resets the board and game state for a new game."""
        if self.ai_thinking:
            messagebox.showwarning("AI Busy", "Cannot start a new game while AI is thinking.")
            return

        self.board = Board() # Reset logic
        self.selected_square = None
        self.possible_moves = []
        self.game_mode = mode
        self.player_color = human_color if mode == MODE_PVC else WHITE # Default human to white in PvP
        self.ai_thinking = False

        # Clear move history text
        self.move_history_text.config(state=tk.NORMAL)
        self.move_history_text.delete('1.0', tk.END)
        self.move_history_text.config(state=tk.DISABLED)

        self.draw_board()
        self.update_status()
        print(f"Started new game: {mode}" + (f" (Human plays {'White' if human_color==WHITE else 'Black'})" if mode == MODE_PVC else ""))

        # If PvC and AI plays White, trigger AI's first move
        if self.game_mode == MODE_PVC and self.board.turn != self.player_color:
            self.trigger_ai_move()


    def draw_board(self):
        """Draws the chessboard squares and pieces."""
        self.board_canvas.delete("all") # Clear previous drawings
        for rank in range(BOARD_SIZE):
            for file in range(BOARD_SIZE):
                index = (7 - rank) * 8 + file # Map 0-63 to visual grid (a8=top-left)
                x1 = file * SQUARE_SIZE
                y1 = rank * SQUARE_SIZE
                x2 = x1 + SQUARE_SIZE
                y2 = y1 + SQUARE_SIZE

                # Draw square
                color = BOARD_COLOR_LIGHT if (rank + file) % 2 == 0 else BOARD_COLOR_DARK
                self.board_canvas.create_rectangle(x1, y1, x2, y2, fill=color, tags="square")

                # Highlight selected square
                if index == self.selected_square:
                    self.board_canvas.create_rectangle(x1, y1, x2, y2, outline=HIGHLIGHT_COLOR, width=3)

                # Draw piece (using Unicode characters)
                piece = self.board.get_piece(index)
                if piece:
                    symbol = piece.symbol()
                    piece_color = "black" if piece.color == BLACK else "white" # Text color for symbol
                    # Adjust font size based on square size for better fit
                    font_size = int(SQUARE_SIZE * 0.6)
                    self.board_canvas.create_text(
                        x1 + SQUARE_SIZE / 2,
                        y1 + SQUARE_SIZE / 2,
                        text=symbol,
                        font=("Arial", font_size, "bold"),
                        fill=piece_color, # Use piece_color for symbol fill
                        tags="piece"
                    )

        # Highlight possible move destinations
        if self.selected_square is not None:
             for move in self.possible_moves:
                 rank, file = divmod(move.to_sq, 8)
                 visual_rank = 7 - rank
                 visual_file = file
                 x1 = visual_file * SQUARE_SIZE
                 y1 = visual_rank * SQUARE_SIZE
                 # Draw a small circle or different highlight
                 radius = SQUARE_SIZE * 0.15
                 cx = x1 + SQUARE_SIZE / 2
                 cy = y1 + SQUARE_SIZE / 2
                 self.board_canvas.create_oval(
                     cx - radius, cy - radius, cx + radius, cy + radius,
                     fill=POSSIBLE_MOVE_COLOR, outline=""
                 )


    def update_status(self):
        """Updates the status label based on game state."""
        if self.board.is_game_over():
            state = self.board.get_game_state()
            winner = self.board.get_outcome()
            if state == CHECKMATE:
                winner_name = "Black" if winner == BLACK else "White"
                message = f"Checkmate! {winner_name} wins."
            elif state == STALEMATE:
                message = "Draw by Stalemate."
            elif state == INSUFFICIENT_MATERIAL:
                message = "Draw by Insufficient Material."
            elif state == FIFTY_MOVE_RULE:
                message = "Draw by 50-Move Rule."
            elif state == THREEFOLD_REPETITION:
                message = "Draw by Threefold Repetition."
            else:
                message = "Game Over - Unknown State" # Should not happen
            self.status_label.config(text=message)
        else:
            turn_color = "White" if self.board.turn == WHITE else "Black"
            status_text = f"{turn_color}'s Turn"
            if self.board.is_in_check(self.board.turn):
                 status_text += " (Check!)"
            if self.ai_thinking:
                status_text = "Computer is thinking..."

            self.status_label.config(text=status_text)

    def add_move_to_history(self, move, piece):
        """Adds the move notation to the move history text widget."""
        move_num_str = ""
        if piece.color == WHITE:
            move_num_str = f"{self.board.fullmove_number}. "

        # Basic algebraic notation (needs improvement for checks, captures, disambiguation)
        piece_char = PIECE_NAMES[piece.type][0] if piece.type != PAWN else ""
        # Improve notation slightly
        capture_char = 'x' if move.is_capture() else ''
        from_sq_str = index_to_square(move.from_sq)
        to_sq_str = index_to_square(move.to_sq)
        promo_char = f"={PIECE_NAMES[move.promotion][0]}" if move.promotion else ""

        # Simplistic notation for now
        move_str = f"{piece_char}{from_sq_str}{capture_char}{to_sq_str}{promo_char}"

        # Add check/checkmate symbols (approximate)
        # This check needs to happen *after* the move is made, so we pass the board *after* the move
        # temp_board = self.board.copy() # Use the actual board state after the move
        # if temp_board.is_checkmate():
        #      move_str += "#"
        # elif temp_board.is_in_check(temp_board.turn): # Check if the *next* player is in check
        #      move_str += "+"
        # (This logic is complex to get exactly right with history/state)

        # Simplified: just record basic move string
        notation = f"{move_num_str}{move_str}"

        self.move_history_text.config(state=tk.NORMAL)
        if piece.color == WHITE:
            self.move_history_text.insert(tk.END, notation + " ")
        else:
            self.move_history_text.insert(tk.END, notation + "\n")
            self.move_history_text.see(tk.END) # Scroll to bottom
        self.move_history_text.config(state=tk.DISABLED)


    def on_square_click(self, event):
        """Handles clicks on the board canvas."""
        if self.board.is_game_over() or self.ai_thinking:
            return # Do nothing if game is over or AI is busy

        # Check if it's the human's turn in PvC mode
        if self.game_mode == MODE_PVC and self.board.turn != self.player_color:
            return # Not human's turn

        file = event.x // SQUARE_SIZE
        rank = event.y // SQUARE_SIZE
        clicked_index = (7 - rank) * 8 + file

        clicked_piece = self.board.get_piece(clicked_index)

        if self.selected_square is None:
            # --- First Click: Selecting a piece ---
            if clicked_piece and clicked_piece.color == self.board.turn:
                self.selected_square = clicked_index
                # Get legal moves for the selected piece
                all_legal_moves = self.board.get_legal_moves()
                self.possible_moves = [m for m in all_legal_moves if m.from_sq == self.selected_square]
                if not self.possible_moves: # Clicked own piece with no moves
                    self.selected_square = None
                self.draw_board() # Redraw to show selection and possible moves
            else:
                 # Clicked empty square or opponent's piece on first click
                 self.selected_square = None
                 self.possible_moves = []
                 # self.draw_board() # Optional: redraw to clear any previous highlight

        else:
            # --- Second Click: Moving or deselecting ---
            is_possible_destination = any(move.to_sq == clicked_index for move in self.possible_moves)

            if clicked_index == self.selected_square:
                # Clicked the same square again: Deselect
                self.selected_square = None
                self.possible_moves = []
                self.draw_board()

            elif is_possible_destination:
                # Find the specific move object
                move_to_make = None
                potential_moves = [m for m in self.possible_moves if m.to_sq == clicked_index]

                if not potential_moves: # Should not happen if is_possible_destination is true
                    print("Error: Move destination mismatch.")
                    return

                # Handle pawn promotion choice
                piece = self.board.get_piece(self.selected_square)
                if piece.type == PAWN and (get_rank(clicked_index) == 7 or get_rank(clicked_index) == 0):
                     promo_choice = self.ask_promotion_choice()
                     if promo_choice:
                         # Find the promotion move matching the choice
                         move_to_make = next((m for m in potential_moves if m.promotion == promo_choice), None)
                     else:
                          # User cancelled promotion selection
                          self.selected_square = None
                          self.possible_moves = []
                          self.draw_board()
                          return
                else:
                     # Not a promotion, should be only one move possible
                     if len(potential_moves) == 1:
                         move_to_make = potential_moves[0]
                     else:
                          # Ambiguity? Should not happen with current logic unless castling/other flags differ
                          print(f"Warning: Ambiguous move selection. Potential moves: {potential_moves}")
                          # Fallback: just take the first one? Or require more specific selection?
                          move_to_make = potential_moves[0]


                if move_to_make:
                    self.perform_move(move_to_make)

                # Reset selection after move attempt
                self.selected_square = None
                self.possible_moves = []
                # self.draw_board() # perform_move calls draw_board and update_status
                # self.update_status()

            elif clicked_piece and clicked_piece.color == self.board.turn:
                 # Clicked another of own pieces: Switch selection
                 self.selected_square = clicked_index
                 all_legal_moves = self.board.get_legal_moves()
                 self.possible_moves = [m for m in all_legal_moves if m.from_sq == self.selected_square]
                 self.draw_board() # Redraw for new selection
            else:
                 # Clicked an invalid square (empty or opponent's piece as destination)
                 # Keep selection for now, or deselect? Let's deselect.
                 self.selected_square = None
                 self.possible_moves = []
                 self.draw_board() # Redraw to clear selection

    def ask_promotion_choice(self):
        """Asks the user which piece to promote a pawn to."""
        dialog = tk.Toplevel(self.root)
        dialog.title("Pawn Promotion")
        dialog.transient(self.root) # Keep dialog on top
        dialog.grab_set() # Modal dialog
        dialog.resizable(False, False)

        choice = tk.IntVar(value=QUEEN) # Default to Queen

        tk.Label(dialog, text="Promote pawn to:").pack(pady=10)

        options_frame = tk.Frame(dialog)
        options_frame.pack(pady=5)

        color = self.board.turn # The color of the pawn being promoted
        promo_pieces = [QUEEN, ROOK, BISHOP, KNIGHT]
        symbols = {pt: PIECE_SYMBOLS[(color, pt)] for pt in promo_pieces}

        for piece_type in promo_pieces:
            symbol = symbols[piece_type]
            name = PIECE_NAMES[piece_type]
            rb = tk.Radiobutton(options_frame, text=f"{name} ({symbol})", variable=choice, value=piece_type, indicatoron=0, width=10, height=2)
            rb.pack(side=tk.LEFT, padx=5)

        def on_ok():
            dialog.user_choice = choice.get()
            dialog.destroy()

        def on_cancel():
            dialog.user_choice = None
            dialog.destroy()

        button_frame = tk.Frame(dialog)
        button_frame.pack(pady=10)
        ok_button = tk.Button(button_frame, text="OK", width=10, command=on_ok)
        ok_button.pack(side=tk.LEFT, padx=10)
        cancel_button = tk.Button(button_frame, text="Cancel", width=10, command=on_cancel)
        cancel_button.pack(side=tk.RIGHT, padx=10)
        dialog.protocol("WM_DELETE_WINDOW", on_cancel) # Handle closing window

        # Center the dialog
        self.root.update_idletasks()
        dialog.geometry(f"+{self.root.winfo_rootx()+50}+{self.root.winfo_rooty()+50}")

        dialog.wait_window() # Wait until dialog is closed

        return getattr(dialog, 'user_choice', None) # Return the choice or None if cancelled


    def perform_move(self, move):
        """Makes the move on the board, updates history, status, and triggers AI if needed."""
        piece_moved = self.board.get_piece(move.from_sq) # Get piece info before it moves
        if not piece_moved: return # Should not happen if move is valid

        self.board.make_move(move)
        self.add_move_to_history(move, piece_moved) # Add based on the piece that *was* moved

        # Reset selection state after any move
        self.selected_square = None
        self.possible_moves = []

        self.draw_board()
        self.update_status() # Update status after move

        # Check for game over immediately after move
        if self.board.is_game_over():
            self.show_game_over_message()
            return # Don't trigger AI if game ended

        # --- Trigger AI if applicable ---
        if self.game_mode == MODE_PVC and self.board.turn != self.player_color:
             # If it's now the AI's turn
             self.trigger_ai_move()


    def trigger_ai_move(self):
        """Initiates the AI move calculation in a separate thread."""
        if not self.ai_module or not hasattr(self.ai_module, 'find_best_move'):
             messagebox.showerror("AI Error", "No valid AI strategy loaded or function missing.")
             self.update_status() # Reset status from "thinking"
             return

        self.ai_thinking = True
        self.update_status() # Show "Computer is thinking..."
        self.root.update_idletasks() # Ensure GUI updates before blocking call

        # Run AI calculation in a background thread
        thread = threading.Thread(target=self._ai_calculation_thread, daemon=True)
        thread.start()


    def _ai_calculation_thread(self):
        """Function run in the background thread to calculate the AI move."""
        try:
             start_time = time.time()
             # Create a copy of the board for the AI to work on,
             # especially important for AIs that modify the board state internally (like MCTS simulators)
             board_copy = self.board.copy()

             # Call the loaded AI's function
             ai_move = self.ai_module.find_best_move(board_copy) # Pass the copy
             end_time = time.time()
             print(f"AI ({self.ai_strategy_name}) took {end_time - start_time:.3f} seconds.")

             # Schedule the result processing back on the main Tkinter thread
             self.root.after(0, self._process_ai_result, ai_move)

        except Exception as e:
             print(f"Error during AI calculation: {e}")
             import traceback
             traceback.print_exc()
             # Schedule error handling back on the main thread
             self.root.after(0, self._handle_ai_error, str(e))


    def _process_ai_result(self, ai_move):
        """Processes the AI's chosen move (executed in the main thread)."""
        self.ai_thinking = False

        if self.board.is_game_over(): # Check again in case game ended while AI was thinking
             self.update_status()
             return

        if ai_move and isinstance(ai_move, Move):
             # Validate the move again on the *actual* board, just in case
             # (This requires comparing Move objects, ensure __eq__ is robust)
             legal_moves = self.board.get_legal_moves()
             is_legal_on_current_board = False
             actual_move_obj = None
             for legal_move in legal_moves:
                  # Simple comparison based on squares and promotion
                  if (legal_move.from_sq == ai_move.from_sq and
                      legal_move.to_sq == ai_move.to_sq and
                      legal_move.promotion == ai_move.promotion):
                       is_legal_on_current_board = True
                       actual_move_obj = legal_move # Use the move object from get_legal_moves
                       break

             if is_legal_on_current_board and actual_move_obj:
                 print(f"AI chooses move: {actual_move_obj}")
                 self.perform_move(actual_move_obj) # Use the validated move object
             else:
                 print(f"AI returned an illegal move: {ai_move}. Attempting random move instead.")
                 # Fallback: AI failed, maybe pick a random move?
                 random_fallback_move = self.get_fallback_move()
                 if random_fallback_move:
                      self.perform_move(random_fallback_move)
                 else: # No moves left? Should be game over state.
                      self.update_status() # Update status (might show checkmate/stalemate)
                      self.show_game_over_message()
        else:
             print("AI failed to return a valid move. Checking game state.")
             # AI returned None or invalid object. Assume no moves possible?
             self.update_status() # Update status (might show checkmate/stalemate)
             if not self.board.is_game_over():
                 # If game isn't over but AI returned nothing, maybe AI error?
                 messagebox.showerror("AI Error", "AI failed to find a move, but game is not over.")
                 # Could try fallback move here too
                 fallback = self.get_fallback_move()
                 if fallback: self.perform_move(fallback)

             elif self.board.is_game_over():
                 self.show_game_over_message()


    def _handle_ai_error(self, error_message):
        """Handles errors from the AI calculation thread."""
        self.ai_thinking = False
        messagebox.showerror("AI Calculation Error", f"An error occurred during AI move calculation:\n{error_message}")
        self.update_status() # Reset status from "thinking"
        # Consider trying a fallback move if appropriate

    def get_fallback_move(self):
        """Returns a random legal move as a fallback."""
        legal_moves = self.board.get_legal_moves()
        if legal_moves:
             return random.choice(legal_moves)
        return None

    def show_game_over_message(self):
        """Shows a message box indicating the game result."""
        state = self.board.get_game_state()
        winner = self.board.get_outcome()
        message = "Game Over!\n"
        if state == CHECKMATE:
            winner_name = "Black" if winner == BLACK else "White"
            message += f"Checkmate! {winner_name} wins."
        elif state == STALEMATE:
            message += "Draw by Stalemate."
        elif state == INSUFFICIENT_MATERIAL:
            message += "Draw by Insufficient Material."
        elif state == FIFTY_MOVE_RULE:
            message += "Draw by 50-Move Rule."
        elif state == THREEFOLD_REPETITION:
            message += "Draw by Threefold Repetition."
        else:
             message += "Result Unknown." # Should not happen

        messagebox.showinfo("Game Over", message)