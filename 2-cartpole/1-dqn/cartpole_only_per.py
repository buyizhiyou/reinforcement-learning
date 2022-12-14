import sys
import gym
import pylab
import random
import numpy as np
from SumTree import SumTree
from collections import deque
from keras.layers import Dense
from keras.optimizers import Adam
from keras.models import Sequential

EPISODES = 300


#The DQN agent in the cartpole example
class DQNAgent:
    def __init__(self, state_size, action_size):
        self.render = False
        self.load_model = False

        #Define size of state and action
        self.state_size = state_size
        self.action_size = action_size

        # DQN hyperparameter
        self.discount_factor = 0.99
        self.learning_rate = 0.001
        self.epsilon = 1.0
        self.epsilon_decay = 0.999
        self.epsilon_min = 0.01
        self.batch_size = 64
        self.train_start = 2000
        self.memory_size = 2000

        # Replay memory, maximum size 2000
        self.memory = Memory(self.memory_size)

        # Creating model and target model
        self.model = self.build_model()
        self.target_model = self.build_model()

        #Target model initialization
        self.update_target_model()

        if self.load_model:
            self.model.load_weights("./save_model/cartpole_dqn_trained.h5")

    #Generate neural network 
    def build_model(self):
        model = Sequential()
        model.add(Dense(24, input_dim=self.state_size, activation='relu',
                        kernel_initializer='he_uniform'))
        model.add(Dense(24, activation='relu',
                        kernel_initializer='he_uniform'))
        model.add(Dense(self.action_size, activation='linear',
                        kernel_initializer='he_uniform'))
        model.summary()
        model.compile(loss='mse', optimizer=Adam(lr=self.learning_rate))
        return model

    #Update target model to weight of model
    def update_target_model(self):
        self.target_model.set_weights(self.model.get_weights())

    #Select action by Epsilon Greed policy
    def get_action(self, state):
        if np.random.rand() <= self.epsilon:
            return random.randrange(self.action_size)
        else:
            q_value = self.model.predict(state)
            return np.argmax(q_value[0])

    #Store sample <s, a, r, s'> in replay memory
    def append_sample(self, state, action, reward, next_state, done):
        if self.epsilon == 1:
            done = True

        #Obtain TD-error and store it in memory
        target = self.model.predict([state])
        old_val = target[0][action]
        target_val = self.target_model.predict([next_state])
        if done:
            target[0][action] = reward
        else:
            target[0][action] = reward + self.discount_factor * (
                np.amax(target_val[0]))
        error = abs(old_val - target[0][action])

        self.memory.add(error, (state, action, reward, next_state, done))

    #Model learning with batches randomly extracted from replay memory
    def train_model(self):
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay

        # ??????????????? ?????? ???????????? ???????????? ?????? ??????
        mini_batch = self.memory.sample(self.batch_size)

        errors = np.zeros(self.batch_size)
        states = np.zeros((self.batch_size, self.state_size))
        next_states = np.zeros((self.batch_size, self.state_size))
        actions, rewards, dones = [], [], []

        for i in range(self.batch_size):
            states[i] = mini_batch[i][1][0]
            actions.append(mini_batch[i][1][1])
            rewards.append(mini_batch[i][1][2])
            next_states[i] = mini_batch[i][1][3]
            dones.append(mini_batch[i][1][4])

        # ?????? ????????? ?????? ????????? ?????????
        # ?????? ????????? ?????? ?????? ????????? ?????????
        target = self.model.predict(states)
        target_val = self.target_model.predict(next_states)

        # ?????? ?????? ???????????? ????????? ???????????? ??????
        for i in range(self.batch_size):
            old_val = target[i][actions[i]]
            if dones[i]:
                target[i][actions[i]] = rewards[i]
            else:
                target[i][actions[i]] = rewards[i] + self.discount_factor * (
                    np.amax(target_val[i]))
            # TD-error??? ??????
            errors[i] = abs(old_val - target[i][actions[i]])

        # TD-error??? priority ????????????
        for i in range(self.batch_size):
            idx = mini_batch[i][0]
            self.memory.update(idx, errors[i])

        self.model.fit(states, target, batch_size=self.batch_size,
                       epochs=1, verbose=0)


class Memory:  # stored as ( s, a, r, s_ ) in SumTree
    e = 0.01
    a = 0.6

    def __init__(self, capacity):
        self.tree = SumTree(capacity)

    def _getPriority(self, error):
        return (error + self.e) ** self.a

    def add(self, error, sample):
        p = self._getPriority(error)
        self.tree.add(p, sample)

    def sample(self, n):
        batch = []
        segment = self.tree.total() / n

        for i in range(n):
            a = segment * i
            b = segment * (i + 1)

            s = random.uniform(a, b)
            (idx, p, data) = self.tree.get(s)
            batch.append((idx, data))

        return batch

    def update(self, idx, error):
        p = self._getPriority(error)
        self.tree.update(idx, p)


if __name__ == "__main__":
    # CartPole-v1 ??????, ?????? ???????????? ?????? 500
    env = gym.make('CartPole-v1')
    state_size = env.observation_space.shape[0]
    action_size = env.action_space.n

    # DQN ???????????? ??????
    agent = DQNAgent(state_size, action_size)

    scores, episodes = [], []

    step = 0
    for e in range(EPISODES):
        done = False
        score = 0
        # env ?????????
        state = env.reset()
        state = np.reshape(state, [1, state_size])

        while not done:
            if agent.render:
                env.render()
            step += 1
            # ?????? ????????? ????????? ??????
            action = agent.get_action(state)
            # ????????? ???????????? ???????????? ??? ???????????? ??????
            next_state, reward, done, info = env.step(action)
            next_state = np.reshape(next_state, [1, state_size])
            # ??????????????? ????????? ????????? -100 ??????
            r = reward if not done or score+reward == 500 else -10
            # ???????????? ???????????? ?????? <s, a, r, s'> ??????
            agent.append_sample(state, action, r, next_state, done)
            # ??? ?????????????????? ??????
            if step >= agent.train_start:
                agent.train_model()

            score += reward
            state = next_state

            if done:
                # ??? ?????????????????? ?????? ????????? ????????? ???????????? ????????????
                agent.update_target_model()

#                score = score if score == 500 else score + 100
                # ?????????????????? ?????? ?????? ??????
                scores.append(score)
                episodes.append(e)
                pylab.plot(episodes, scores, 'b')
                pylab.savefig("./save_graph/cartpole_dqn.png")
                print("episode:", e, "  score:", score, "  memory length:",
                      step if step <= agent.memory_size else agent.memory_size, "  epsilon:", agent.epsilon)

                # ?????? 10??? ??????????????? ?????? ????????? 490?????? ?????? ?????? ??????
                if np.mean(scores[-min(10, len(scores)):]) > 490:
                    agent.model.save_weights("./save_model/cartpole_dqn.h5")
                    sys.exit()
