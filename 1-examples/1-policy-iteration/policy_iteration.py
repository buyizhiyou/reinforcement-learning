# -*- coding: utf-8 -*-
import random
from environment import GraphicDisplay, Env


class PolicyIteration:
    def __init__(self, env):
        self.env = env
        # 2-d list for the value function
        self.value_table = [[0.0] * env.width for _ in range(env.height)]#值函数表
        # list of random policy (same probability of up, down, left, right)
        self.policy_table = [[[0.25, 0.25, 0.25, 0.25]] * env.width
                                    for _ in range(env.height)]#每一状态的动作策略表，一开始向四方运动是相同概率的
        # setting terminal state
        self.policy_table[2][2] = []#吸收态，终止
        self.discount_factor = 0.9

    def policy_evaluation(self):#策略估计
        next_value_table = [[0.00] * self.env.width
                                    for _ in range(self.env.height)]

        # Bellman Expectation Equation for the every states
        for state in self.env.get_all_states():
            value = 0.0
            # keep the value function of terminal states as 0(吸收态赋０)
            if state == [2, 2]:
                next_value_table[state[0]][state[1]] = value
                continue

            for action in self.env.possible_actions:#计算所有可能动作,根据贝尔曼方程更新value
                next_state = self.env.state_after_action(state, action)
                reward = self.env.get_reward(state, action)
                next_value = self.get_value(next_state)
                value += (self.get_policy(state)[action] *
                          (reward + self.discount_factor * next_value))

            next_value_table[state[0]][state[1]] = round(value, 2)

        self.value_table = next_value_table

    def policy_improvement(self):#策略改进
        next_policy = self.policy_table
        for state in self.env.get_all_states():
            if state == [2, 2]:
                continue
            value = -99999
            max_index = []
            result = [0.0, 0.0, 0.0, 0.0]  # initialize the policy

            # for every actions, calculate　计算所有可能动作,保留取得最大值函数的动作
            # [reward + (discount factor) * (next state value function)]
            for index, action in enumerate(self.env.possible_actions):
                next_state = self.env.state_after_action(state, action)
                reward = self.env.get_reward(state, action)
                next_value = self.get_value(next_state)
                temp = reward + self.discount_factor * next_value

                # We normally can't pick multiple actions in greedy policy.
                # but here we allow multiple actions with same max values　允许多个取最大值函数的动作存在
                if temp == value:
                    max_index.append(index)
                elif temp > value:
                    value = temp
                    max_index.clear()
                    max_index.append(index)

            # probability of action
            prob = 1 / len(max_index)

            for index in max_index:
                result[index] = prob

            next_policy[state[0]][state[1]] = result#更新策略表

        self.policy_table = next_policy

    # get action according to the current policy
    def get_action(self, state):
        random_pick = random.randrange(100) / 100

        policy = self.get_policy(state)
        policy_sum = 0.0
        # return the action in the index
        for index, value in enumerate(policy):
            policy_sum += value
            if random_pick < policy_sum:
                return index

    # get policy of specific state
    def get_policy(self, state):
        if state == [2, 2]:
            return 0.0
        return self.policy_table[state[0]][state[1]]

    def get_value(self, state):
        return round(self.value_table[state[0]][state[1]], 2)

if __name__ == "__main__":
    import pdb; pdb.set_trace()
    env = Env()
    policy_iteration = PolicyIteration(env)
    grid_world = GraphicDisplay(policy_iteration)
    grid_world.mainloop()
