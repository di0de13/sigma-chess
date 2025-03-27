# main.py
"""
Main entry point for the Python Chess application.
Initializes the Tkinter GUI.
"""

import tkinter as tk
from chess_gui import ChessGUI

if __name__ == "__main__":
    root = tk.Tk()
    gui = ChessGUI(root)
    root.mainloop()