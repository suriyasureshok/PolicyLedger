from src.shared.env import EnergySlotEnv

env = EnergySlotEnv(seed=42)

state = env.reset()
done = False
total_reward = 0

while not done:
    action = 0  # always SAVE
    state, reward, done = env.step(action)
    total_reward += reward

print("Total reward:", total_reward)
print("Final state:", state)
