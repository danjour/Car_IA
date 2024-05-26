import torch
import random
import numpy as np
from collections import deque
from typing import List, Tuple
from game import Jogo
from model import Linear_QNet, QTrainer
from graph import plot

MAX_MEMORY = 100_000
BATCH_SIZE = 1000
LR = 0.001

class Agent:

    def __init__(self)  -> None:
        self.n_games = 0
        self.epsilon = 0
        self.gamma = 0.9 
        self.memory = deque(maxlen=MAX_MEMORY)
        self.model = Linear_QNet(3, 256, 3)
        self.trainer = QTrainer(self.model, lr=LR, gamma=self.gamma)
        self.model_file = r"\model\model.pth"
    
    def load_model(self) -> None:
        self.model.load(self.model_file)

    def get_state(self, obstacle_x1:int, obstacle_y:int, car_x:int,car_y:int,obstacle_x2:int) -> np.ndarray:
        left = 0
        right = 0
        stop = 0

        can_move_left = (car_x > 0 and
                            not (car_x - 10 < obstacle_x1 + 75 and
                                    car_x - 10 + 75 > obstacle_x1 and
                                    car_y < obstacle_y + 120 and
                                    car_y + 120 > obstacle_y) and
                            not (car_x - 10 < obstacle_x2 + 75 and
                                    car_x - 10 + 75 > obstacle_x2 and
                                    car_y < obstacle_y + 120 and
                                    car_y + 120 > obstacle_y))

        can_move_right = (car_x + 75 < 400 and
                            not (car_x + 10 < obstacle_x1 + 75 and
                                car_x + 10 + 75 > obstacle_x1 and
                                car_y < obstacle_y + 120 and
                                car_y + 120 > obstacle_y) and
                            not (car_x + 10 < obstacle_x2 + 75 and
                                car_x + 10 + 75 > obstacle_x2 and
                                car_y < obstacle_y + 120 and
                                car_y + 120 > obstacle_y))

        if can_move_left:
            left = 1
        elif can_move_right:
            right = 1
        else:
            stop = 1

        state = [
            left,
            right,
            stop
        ]

        return np.array(state, dtype=int)


    def remember(self, state: np.ndarray, action: int, reward: float, next_state: np.ndarray, done: bool) -> None:
        self.memory.append((state, action, reward, next_state, done))

    def train_long_memory(self) ->None:
        if len(self.memory) > BATCH_SIZE:
            mini_sample = random.sample(self.memory, BATCH_SIZE) 
        else:
            mini_sample = self.memory
        states, actions, rewards, next_states, dones = zip(*mini_sample)
        self.trainer.train_step(states, actions, rewards, next_states, dones)


    def train_short_memory(self, state:np.ndarray, action:int, reward:int, next_state:np.ndarray, done:bool)->None:
        self.trainer.train_step(state, action, reward, next_state, done)

    def get_action(self, state:np.ndarray)->List[int]:
        self.epsilon = 80 - self.n_games
        final_move = [0,0,0]
        if random.randint(0, 100) < self.epsilon:
            move = random.randint(0, 2)
            final_move[move] = 1
        else:
            state0 = torch.tensor(state, dtype=torch.float)
            prediction = self.model(state0)
            move = torch.argmax(prediction).item()
            final_move[move] = 1

        return final_move

def train()->None:
    count = 0
    plot_scores = []
    plot_mean_scores = []
    total_score = 0
    record = 0
    agent = Agent()
    jogo = Jogo()
    try:
        agent.load_model()
        print("Loaded model.")
    except FileNotFoundError:
        print("Model not found. A new one will be created.")

    while True:
        obstacle_x, obstacle_y, car_x,car_y,obstacle_x2= jogo.run_game()

        state_old = agent.get_state(obstacle_x, obstacle_y, car_x,car_y,obstacle_x2)

        final_move = agent.get_action(state_old)

        count += 1

        reward, done, score = jogo.play_step(final_move)

        state_new = agent.get_state(jogo.car_x,jogo.car_y, jogo.obstacle_x, jogo.obstacle_y,jogo.obstacle_x2)

        agent.train_short_memory(state_old, final_move, reward, state_new, done)

        agent.remember(state_old, final_move, reward, state_new, done)

        if done:
            agent.n_games += 1
            agent.train_long_memory()

            if score > record:
                record = score
                agent.model.save()

            print('Game', agent.n_games, 'Score', score, 'Record:', record)

            plot_scores.append(score)
            total_score += score
            mean_score = total_score / agent.n_games
            plot_mean_scores.append(mean_score)
            plot(plot_scores, plot_mean_scores)


if __name__ == '__main__':
    train()
