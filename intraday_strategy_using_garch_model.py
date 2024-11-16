# -*- coding: utf-8 -*-
"""Intraday Strategy Using GARCH Model.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1x65-YxKOaW6RZ_9vT3pzhs3VuqidL1YA

Using simulated daily data and intraday 5-min data.

1.  Load Daily and 5-minute data.

2.  Define function to fit GARCH model on the daily data and predict 1-day ahead
volatility in a rolling window.

3.  Calculate prediction premium and form a daily signal from it.

4.    Merge with intraday data and calculate intraday indicators to form the intraday signal.

5.  Generate the position entry and hold until the end of the day.

6. Calculate final strategy returns.

## 1. Load Simulated Daily and Simulated 5-minute data.
We are loading both datasets, set the indexes and calculate daily log returns.
"""

!pip install arch

!pip install pandas_ta

import matplotlib.pyplot as plt
from arch import arch_model
import pandas_ta
import pandas as pd
import numpy as np
import os

# Define file paths for both data files
daily_data_file = '/content/simulated_daily_data.csv'
intraday_data_file = '/content/simulated_5min_data.csv'

# Load and clean the daily data
daily_df = pd.read_csv(daily_data_file)

# Drop any unnamed columns that might be automatically added
daily_df = daily_df.loc[:, ~daily_df.columns.str.contains('^Unnamed')]
daily_df['Date'] = pd.to_datetime(daily_df['Date'], errors='coerce')
daily_df = daily_df.dropna(subset=['Date'])  # Drop rows with invalid dates
daily_df = daily_df.set_index('Date')

# Display the daily data (for debugging/confirmation)
print("Daily DataFrame head:")
print(daily_df.head())

# Load and clean the intraday 5-minute data
intraday_5min_df = pd.read_csv(intraday_data_file)

# Drop any unnamed columns that might be automatically added
intraday_5min_df = intraday_5min_df.loc[:, ~intraday_5min_df.columns.str.contains('^Unnamed')]

# Convert 'datetime' to a datetime format, handling parsing errors
intraday_5min_df['datetime'] = pd.to_datetime(intraday_5min_df['datetime'], errors='coerce')

# Drop rows where 'datetime' could not be parsed (NaT entries)
intraday_5min_df = intraday_5min_df.dropna(subset=['datetime'])

# Set 'datetime' as the index
intraday_5min_df = intraday_5min_df.set_index('datetime')

# Create a 'date' column for grouping purposes
intraday_5min_df['date'] = pd.to_datetime(intraday_5min_df.index.date)

# Display the intraday 5-minute data (for debugging/confirmation)
print("Intraday 5-Minute DataFrame head:")
print(intraday_5min_df.head())

# Additional analysis or plotting can follow here, using daily_df and intraday_5min_df

"""## 2. Define function to fit GARCH model and predict 1-day ahead volatility in a rolling window.
We are first calculating the 6-month rolling variance and then we are creating a function in a 6-month rolling window to fit a garch model and predict the next day variance.
"""

daily_df['log_ret'] = np.log(daily_df['Adj Close']).diff()

daily_df['variance'] = daily_df['log_ret'].rolling(180).var()

daily_df = daily_df['2020':]

def predict_volatility(x):

    best_model = arch_model(y=x,
                            p=1,
                            q=3).fit(update_freq=5,
                                     disp='off')

    variance_forecast = best_model.forecast(horizon=1).variance.iloc[-1,0]

    print(x.index[-1])

    return variance_forecast

daily_df['predictions'] = daily_df['log_ret'].rolling(180).apply(lambda x: predict_volatility(x))

daily_df = daily_df.dropna()

daily_df

# @title Distribution of Daily Log Returns

import matplotlib.pyplot as plt

plt.figure(figsize=(10, 6))
plt.hist(daily_df['log_ret'], bins=50, edgecolor='black')
plt.title('Distribution of Daily Log Returns')
plt.xlabel('Log Return')
_ = plt.ylabel('Frequency')

# @title Open

from matplotlib import pyplot as plt
daily_df['Open'].plot(kind='hist', bins=20, title='Open')
plt.gca().spines[['top', 'right',]].set_visible(False)

print(daily_df.columns)

# Replace 'correct_column_name' with the actual column name you found
daily_df['log_ret'].plot(kind='hist', bins=30, alpha=0.7, color='skyblue', edgecolor='black')
plt.title('Distribution of Daily Signals')
plt.xlabel('Signal Value')
plt.ylabel('Frequency')
plt.show()

import matplotlib.pyplot as plt

# Define the columns to visualize, including 'predictions'
columns_to_plot = ['Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume', 'log_ret', 'variance', 'predictions']

# Set up a grid layout for the plots (3 rows, 3 columns to fit 9 plots)
fig, axes = plt.subplots(nrows=3, ncols=3, figsize=(18, 15))
fig.suptitle('Histograms of Financial Data Columns', fontsize=16)

# Loop through columns and plot each one
for ax, column in zip(axes.flatten(), columns_to_plot):
    daily_df[column].plot(kind='hist', bins=30, alpha=0.7, color='skyblue', edgecolor='black', ax=ax)
    ax.set_title(f'{column} Distribution')
    ax.set_xlabel(column)
    ax.set_ylabel('Frequency')

# Hide any empty subplots if columns don't fill all axes
for ax in axes.flatten()[len(columns_to_plot):]:
    ax.set_visible(False)

plt.tight_layout(rect=[0, 0, 1, 0.96])  # Adjust layout to make space for the title
plt.show()

"""## 4. Merge with intraday data and calculate intraday indicators to form the intraday signal.
Calculate all intraday indicators and intraday signal.
"""

import pandas_ta
import numpy as np

# Define the column names for clarity
DATE_COLUMN = 'date'
DATE_COLUMN_DAILY = 'Date'
RSI_LENGTH = 20
BBANDS_LENGTH = 20

# Check if 'signal_daily' exists in the daily_df DataFrame
if 'signal_daily' not in daily_df.columns:
    # Example logic for creating the 'signal_daily' column
    daily_df['signal_daily'] = np.where(daily_df['Close'] > daily_df['Open'], 1, -1)

# Merge intraday and daily data
final_df = intraday_5min_df.reset_index()\
                            .merge(daily_df[['signal_daily']].reset_index(),
                                   left_on=DATE_COLUMN,
                                   right_on=DATE_COLUMN_DAILY)\
                            .drop([DATE_COLUMN, DATE_COLUMN_DAILY], axis=1)\
                            .set_index('datetime')

# Calculate RSI
final_df['rsi'] = pandas_ta.rsi(close=final_df['close'], length=RSI_LENGTH)

# Calculate Bollinger Bands (lower and upper bands)
final_df['lband'] = pandas_ta.bbands(close=final_df['close'], length=BBANDS_LENGTH).iloc[:, 0]
final_df['uband'] = pandas_ta.bbands(close=final_df['close'], length=BBANDS_LENGTH).iloc[:, 2]

# Generate trading signals (1 for buy, -1 for sell, NaN for no trade)
final_df['signal_intraday'] = final_df.apply(
    lambda x: 1 if (x['rsi'] > 70) & (x['close'] > x['uband'])
              else (-1 if (x['rsi'] < 30) & (x['close'] < x['lband'])
                    else np.nan),
    axis=1
)

# Calculate log returns
final_df['return'] = np.log(final_df['close']).diff()

# Display the final DataFrame
print(final_df.head())

"""## 4. Merge with intraday data and calculate intraday indicators to form the intraday signal.
Calculate all intraday indicators and intraday signal.
"""

final_df = intraday_5min_df.reset_index()\
                            .merge(daily_df[['signal_daily']].reset_index(),
                                   left_on='date',
                                   right_on='Date')\
                            .drop(['date','Date'], axis=1)\
                            .set_index('datetime')

final_df['rsi'] = pandas_ta.rsi(close=final_df['close'],
                                length=20)

final_df['lband'] = pandas_ta.bbands(close=final_df['close'],
                                     length=20).iloc[:,0]

final_df['uband'] = pandas_ta.bbands(close=final_df['close'],
                                     length=20).iloc[:,2]

final_df['signal_intraday'] = final_df.apply(lambda x: 1 if (x['rsi']>70)&
                                                            (x['close']>x['uband'])
                                             else (-1 if (x['rsi']<30)&
                                                         (x['close']<x['lband']) else np.nan),
                                             axis=1)

final_df['return'] = np.log(final_df['close']).diff()

final_df

from matplotlib import pyplot as plt
final_df['open'].plot(kind='hist', bins=20, title='open')
plt.gca().spines[['top', 'right',]].set_visible(False)

from matplotlib import pyplot as plt
final_df['open'].plot(kind='line', figsize=(8, 4), title='open')
plt.gca().spines[['top', 'right']].set_visible(False)

from matplotlib import pyplot as plt
final_df.plot(kind='scatter', x='open', y='low', s=32, alpha=.8)
plt.gca().spines[['top', 'right',]].set_visible(False)

from matplotlib import pyplot as plt
final_df.plot(kind='scatter', x='close', y='volume', s=32, alpha=.8)
plt.gca().spines[['top', 'right',]].set_visible(False)

"""## 5. Generate the position entry and hold until the end of the day.

"""

final_df['return_sign'] = final_df.apply(lambda x: -1 if (x['signal_daily']==1)&(x['signal_intraday']==1)
                                        else (1 if (x['signal_daily']==-1)&(x['signal_intraday']==-1) else np.nan),
                                        axis=1)

final_df['return_sign'] = final_df.groupby(pd.Grouper(freq='D'))['return_sign']\
                                  .transform(lambda x: x.ffill())

final_df['forward_return'] = final_df['return'].shift(-1)

final_df['strategy_return'] = final_df['forward_return']*final_df['return_sign']

daily_return_df = final_df.groupby(pd.Grouper(freq='D'))['strategy_return'].sum()

"""## 6. Calculate final strategy returns.

"""

import matplotlib.ticker as mtick

strategy_cumulative_return = np.exp(np.log1p(daily_return_df).cumsum()).sub(1)

strategy_cumulative_return.plot(figsize=(16,6))

plt.title('Intraday Strategy Returns')

plt.gca().yaxis.set_major_formatter(mtick.PercentFormatter(1))

plt.ylabel('Return')

plt.show()