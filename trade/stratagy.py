import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Generate random price data for demonstration
np.random.seed(42)
price_data = np.random.randn(252) + 10  # 252 trading days
date_index = pd.date_range(start='1/1/2023', periods=252, freq='B')
prices = pd.Series(price_data, index=date_index)
import ipdb ; ipdb.set_trace()

# Define a function to implement the moving average crossover strategy
def moving_average_crossover_strategy(prices, short_window, long_window):
    signals = pd.DataFrame(index=prices.index)
    signals['signal'] = 0.0

    # Create short simple moving average
    signals['short_mavg'] = prices.rolling(window=short_window, min_periods=1, center=False).mean()

    # Create long simple moving average
    signals['long_mavg'] = prices.rolling(window=long_window, min_periods=1, center=False).mean()

    # Create signals
    signals['signal'][short_window:] = np.where(signals['short_mavg'][short_window:] > signals['long_mavg'][short_window:], 1.0, 0.0)

    # Generate trading orders
    signals['positions'] = signals['signal'].diff()

    return signals

# Define short and long windows for the moving averages
short_window = 40
long_window = 100

# Get signals from the moving average crossover strategy
signals = moving_average_crossover_strategy(prices, short_window, long_window)

# Plot the price data with buy and sell signals
fig, ax = plt.subplots(figsize=(12, 8))

ax.plot(prices.index, prices, label='Price')
ax.plot(signals.index, signals['short_mavg'], label=f'Short {short_window} days Mavg')
ax.plot(signals.index, signals['long_mavg'], label=f'Long {long_window} days Mavg')

# Plotting buy signals
ax.plot(signals.loc[signals.positions == 1.0].index,
        signals.short_mavg[signals.positions == 1.0],
        '^', markersize=10, color='g', label='Buy Signal')

# Plotting sell signals
ax.plot(signals.loc[signals.positions == -1.0].index,
        signals.short_mavg[signals.positions == -1.0],
        'v', markersize=10, color='r', label='Sell Signal')

plt.title('Moving Average Crossover Strategy')
plt.xlabel('Date')
plt.ylabel('Price')
plt.legend()
plt.show()