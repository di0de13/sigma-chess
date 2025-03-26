import pygame
from board import ChessBoard
from pieces import create_piece
from ai import get_best_move

pygame.init()

from config import WIDTH, SQUARE_SIZE, COLORS, BOARD_LIGHT, BOARD_DARK, HIGHLIGHT, MENU_BG, MENU_OPTIONS

screen = pygame.display.set_mode((WIDTH, WIDTH))
pygame.display.set_caption("Chess Game")

def draw_board(screen, board, selected_piece, valid_moves):
    for row in range(8):
        for col in range(8):
            color = BOARD_LIGHT if (row + col) % 2 == 0 else BOARD_DARK
            pygame.draw.rect(screen, color, (col * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))
            if (row, col) in valid_moves:
                pygame.draw.rect(screen, HIGHLIGHT, (col * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE), 4)
            piece = board.get_piece_at((row, col))
            if piece:
                pygame.draw.circle(screen, COLORS[piece[0]], 
                                  (col * SQUARE_SIZE + SQUARE_SIZE // 2, row * SQUARE_SIZE + SQUARE_SIZE // 2), 
                                  SQUARE_SIZE // 3)
                font = pygame.font.SysFont(None, 36)
                text = font.render(piece[1], True, (255, 0, 0))
                screen.blit(text, (col * SQUARE_SIZE + SQUARE_SIZE // 2 - 10, row * SQUARE_SIZE + SQUARE_SIZE // 2 - 10))
    if selected_piece:
        row, col = selected_piece
        pygame.draw.rect(screen, (255, 0, 0), (col * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE), 4)

def draw_menu(screen, selected_option, hover_option=None, result=None):
    screen.fill(MENU_BG)
    font = pygame.font.SysFont(None, 48)
    if result:
        text = font.render(result, True, (255, 0, 0))
        screen.blit(text, (WIDTH // 2 - 100, 100))
    for i, option in enumerate(MENU_OPTIONS):
        # 计算菜单项的矩形区域
        text = font.render(option, True, (0, 0, 0))
        text_rect = text.get_rect()
        text_rect.topleft = (WIDTH // 2 - 100, 200 + i * 60)
        text_rect.width += 40  # 增加一些边距
        text_rect.height += 10
        text_rect.x -= 20

        # 绘制选中或悬停效果
        if i == selected_option or i == hover_option:
            pygame.draw.rect(screen, (255, 0, 0), text_rect, 2)
            color = (255, 0, 0)
        else:
            color = (0, 0, 0)

        text = font.render(option, True, color)
        screen.blit(text, (WIDTH // 2 - 100, 200 + i * 60))

def main():
    board = ChessBoard()
    selected_piece = None
    valid_moves = []
    game_state = "menu"
    selected_menu_option = 0
    hover_menu_option = None
    result = None
    player_color = "white"

    clock = pygame.time.Clock()

    while True:
        clock.tick(60)

        if game_state == "menu":
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    return
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_UP:
                        selected_menu_option = (selected_menu_option - 1) % len(MENU_OPTIONS)
                    elif event.key == pygame.K_DOWN:
                        selected_menu_option = (selected_menu_option + 1) % len(MENU_OPTIONS)
                    elif event.key == pygame.K_RETURN:
                        if selected_menu_option == 0:  # New Game (White)
                            board = ChessBoard()
                            selected_piece = None
                            valid_moves = []
                            game_state = "playing"
                            result = None
                            player_color = "white"
                        elif selected_menu_option == 1:  # New Game (Black)
                            board = ChessBoard()
                            selected_piece = None
                            valid_moves = []
                            game_state = "playing"
                            result = None
                            player_color = "black"
                            # 当玩家选择黑方时，让AI先走一步
                            move = get_best_move(board)
                            if move:
                                board.move_piece(move[0], move[1])
                        elif selected_menu_option == 2:  # Restart
                            board = ChessBoard()
                            selected_piece = None
                            valid_moves = []
                            game_state = "playing"
                            result = None
                        elif selected_menu_option == 3:  # Quit
                            pygame.quit()
                            return
                elif event.type == pygame.MOUSEMOTION:
                    x, y = pygame.mouse.get_pos()
                    if 200 <= y <= 200 + len(MENU_OPTIONS) * 60 and WIDTH // 2 - 120 <= x <= WIDTH // 2 + 100:
                        hover_menu_option = (y - 200) // 60
                    else:
                        hover_menu_option = None
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if hover_menu_option is not None:
                        selected_menu_option = hover_menu_option
                        if selected_menu_option == 0:  # New Game (White)
                            board = ChessBoard()
                            selected_piece = None
                            valid_moves = []
                            game_state = "playing"
                            result = None
                            player_color = "white"
                        elif selected_menu_option == 1:  # New Game (Black)
                            board = ChessBoard()
                            selected_piece = None
                            valid_moves = []
                            game_state = "playing"
                            result = None
                            player_color = "black"
                        elif selected_menu_option == 2:  # Restart
                            board = ChessBoard()
                            selected_piece = None
                            valid_moves = []
                            game_state = "playing"
                            result = None
                        elif selected_menu_option == 3:  # Quit
                            pygame.quit()
                            return
            draw_menu(screen, selected_menu_option, hover_menu_option, result)
            pygame.display.flip()

        elif game_state == "playing":
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    return
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if board.current_turn == player_color:
                        x, y = pygame.mouse.get_pos()
                        col, row = x // SQUARE_SIZE, y // SQUARE_SIZE
                        if selected_piece is None:
                            piece = board.get_piece_at((row, col))
                            if piece and piece[0] == ("w" if player_color == "white" else "b"):
                                selected_piece = (row, col)
                                piece_obj = create_piece(player_color, piece[1], (row, col))
                                # 获取所有可能的移动，并过滤掉会导致己方被将军的移动
                                valid_moves = [move for move in piece_obj.get_valid_moves(board) 
                                              if board.is_valid_move((row, col), move)]
                                # 如果当前处于将军状态，只允许能解除将军的移动
                                if board.is_in_check(player_color):
                                    valid_moves = [move for move in valid_moves if not board.will_be_in_check_after_move((row, col), move)]
                        else:
                            target_pos = (row, col)
                            if target_pos in valid_moves:
                                board.move_piece(selected_piece, target_pos)
                                selected_piece = None
                                valid_moves = []
                                if board.is_checkmate():
                                    game_state = "menu"
                                    result = "Checkmate! " + ("White" if board.current_turn == "black" else "Black") + " wins!"
                                elif board.is_stalemate():
                                    game_state = "menu"
                                    result = "Stalemate!"
                            else:
                                selected_piece = None
                                valid_moves = []

            if board.current_turn != player_color:
                move = get_best_move(board)
                if move:
                    board.move_piece(move[0], move[1])
                    if board.is_checkmate():
                        game_state = "menu"
                        result = "Checkmate! " + ("White" if board.current_turn == "black" else "Black") + " wins!"
                    elif board.is_stalemate():
                        game_state = "menu"
                        result = "Stalemate!"

            screen.fill((255, 255, 255))
            draw_board(screen, board, selected_piece, valid_moves)
            if board.is_in_check(board.current_turn):
                font = pygame.font.SysFont(None, 36)
                text = font.render("Check!", True, (255, 0, 0))
                screen.blit(text, (10, 10))
            pygame.display.flip()

if __name__ == "__main__":
    main()
