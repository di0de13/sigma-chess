from core_components.chess_board import ChessBoard
from core_components.move_operations import generate_legal_moves, string_to_move
from ui_interface.pygame_chess_ui import PygameChessUI
import pygame

def main():
    try:
        # 初始化棋盘和UI
        board = ChessBoard()
        ui = PygameChessUI()
        error_message = ""
        
        # 游戏主循环
        clock = pygame.time.Clock()
        running = True
        
        while running and not board.is_game_over():
            # 处理事件
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    break
                    
                if event.type == pygame.MOUSEBUTTONDOWN:
                    move_str = ui.handle_mouse_click(event)
                    if move_str:
                        move = string_to_move(board.board, move_str)
                        if move in generate_legal_moves(board.board):
                            board.make_move(move)
                            error_message = ""
                        else:
                            error_message = "无效的走法！请重新选择。"
            
            # 更新显示
            ui.draw_board(board.board, error_message)
            clock.tick(60)  # 限制帧率为60FPS

        # 游戏结束，显示结果
        if board.is_game_over():
            ui.show_game_over(board.get_result())
            pygame.time.wait(2000)  # 显示结果2秒
        
    except Exception as e:
        print(f"发生错误: {e}")
    finally:
        # 清理资源
        ui.cleanup()
        pygame.quit()

if __name__ == "__main__":
    main()