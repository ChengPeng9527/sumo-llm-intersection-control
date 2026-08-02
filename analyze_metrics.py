import pandas as pd

df = pd.read_csv("baseline_records.csv")

# throughput
vehicles = df["vehicle"].nunique()

# stop count
stops = (df["speed"] < 0.1).sum()

# average speed
avg_speed = df["speed"].mean()

print("=== Baseline Metrics ===")
print(f"Vehicles passed: {vehicles}")
print(f"Total stop events: {stops}")
print(f"Average speed: {avg_speed:.2f}")