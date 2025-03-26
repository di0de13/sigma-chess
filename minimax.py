import chess
import numpy as np
import random

class ChessEnvironment:
    def __init__(self):
        self.board = chess.Board()
        self.reset()
    
    def reset(self):
        self.board.reset()
        return self._get_state()
    
    def step(self, action):
        # 执行动作，返回下一个状态、奖励和是否结束
        move = self._action_to_move(action)
        
        if move not in self.board.legal_moves:
            return self._get_state(), -10, True, {}
        
        self.board.push(move)
        
        # 计算奖励
        reward = self._calculate_reward()
        
        done = self.board.is_game_over()
        
        return self._get_state(), reward, done, {}
    
    def _get_state(self):
        # 将棋盘转换为特征向量
        return self._board_to_feature_vector()
    
    def _board_to_feature_vector(self):
        # 简单的棋盘特征表示
        # 这里只是一个示例，实际应用需要更复杂的特征工程
        piece_map = self.board.piece_map()
        feature_vector = np.zeros(64)
        
        for square, piece in piece_map.items():
            piece_value = self._get_piece_value(piece)
            feature_vector[square] = piece_value
        
        return feature_vector
    
    def _get_piece_value(self, piece):
        piece_values = {
            chess.PAWN: 1,
            chess.KNIGHT: 3,
            chess.BISHOP: 3,
            chess.ROOK: 5,
            chess.QUEEN: 9,
            chess.KING: 0
        }
        
        # 根据颜色给予正负值
        value = piece_values[piece.piece_type]
        return value if piece.color == chess.WHITE else -value
    
    def _action_to_move(self, action):
        # 将动作索引转换为实际的棋步
        moves = list(self.board.legal_moves)
        return moves[action % len(moves)]
    
    def _calculate_reward(self):
        # 简单的奖励设计
        if self.board.is_checkmate():
            return 100 if self.board.turn == chess.BLACK else -100
        
        if self.board.is_stalemate():
            return 0
        
        # 根据当前局面给予小的奖励/惩罚
        current_eval = self._evaluate_board()
        return current_eval
    
    def _evaluate_board(self):
        # 简单的局面评估
        piece_values = {
            chess.PAWN: 1,
            chess.KNIGHT: 3,
            chess.BISHOP: 3,
            chess.ROOK: 5,
            chess.QUEEN: 9,
            chess.KING: 0
        }
        
        white_value = sum(piece_values[piece.piece_type] for piece in self.board.piece_map().values() if piece.color == chess.WHITE)
        black_value = sum(piece_values[piece.piece_type] for piece in self.board.piece_map().values() if piece.color == chess.BLACK)
        
        return white_value - black_value

class SimpleChessAgent:
    def __init__(self, state_size, action_size):
        self.state_size = state_size
        self.action_size = action_size
        
        # 简单的Q-Learning
        self.q_table = np.zeros((state_size, action_size))
        
        self.epsilon = 1.0  # 探索率
        self.epsilon_decay = 0.995
        self.epsilon_min = 0.01
        
        self.gamma = 0.99  # 折扣因子
        self.learning_rate = 0.1
    
    def choose_action(self, state):
        # 探索与利用
        if np.random.rand() <= self.epsilon:
            return random.randrange(self.action_size)
        
        # 利用已学习的Q值
        state_index = self._discretize_state(state)
        return np.argmax(self.q_table[state_index])
    
    def learn(self, state, action, reward, next_state, done):
        state_index = self._discretize_state(state)
        next_state_index = self._discretize_state(next_state)
        
        # Q-Learning更新
        best_next_action = np.argmax(self.q_table[next_state_index])
        
        td_target = reward + self.gamma * self.q_table[next_state_index][best_next_action] * (not done)
        td_error = td_target - self.q_table[state_index][action]
        
        self.q_table[state_index][action] += self.learning_rate * td_error
        
        # 衰减探索率
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay
    
    def _discretize_state(self, state):
        # 将连续状态离散化
        # 这里是一个非常简单的实现，实际应用需要更复杂的状态表示
        return int(np.sum(state) % 1000)

def train_chess_ai(episodes=1000):
    env = ChessEnvironment()
    agent = SimpleChessAgent(state_size=1000, action_size=218)  # 218是棋步的大致数量
    
    for episode in range(episodes):
        state = env.reset()
        done = False
        total_reward = 0
        
        while not done:
            action = agent.choose_action(state)
            next_state, reward, done, _ = env.step(action)
            
            agent.learn(state, action, reward, next_state, done)
            
            state = next_state
            total_reward += reward
        
        print(f"Episode {episode}, Total Reward: {total_reward}, Epsilon: {agent.epsilon}")

if __name__ == "__main__":
    train_chess_ai()