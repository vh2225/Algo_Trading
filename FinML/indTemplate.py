# indicators.py
# Your code that implements your indicators as functions that operate on dataframes.
# The "main" code in indicators.py should generate the charts that illustrate your indicators in the report.
import util
import numpy as np
import pandas as pd
import datetime as dt
import matplotlib.pyplot as plt

def normalize(data):
    na_ind = np.where(np.isnan(data))[0]
    if na_ind.size !=0 :
        first = na_ind[-1]+1
    else:
        first = 0
    return data/data.iloc[first]

def get_ind_data(symbol, start_date, end_date, lookback=14, momentum_period=14):
    # this function will calculate SMA ratio, Bollinger Bands, RSI, Momentum, and MACD
    date_range = pd.date_range(start_date, end_date)
    ind_df = util.get_data([symbol], date_range)

    # calculate SMA:
    ind_df['SMA'] = pd.rolling_mean(ind_df[symbol],window=lookback, min_periods=lookback)

    # calculate Bollinger Bands %
    ind_df['rolling_std'] = pd.rolling_std(ind_df[symbol],window=lookback, min_periods=lookback)
    ind_df['top_bb'] = ind_df['SMA'] + (2 * ind_df['rolling_std'])
    ind_df['bot_bb'] = ind_df['SMA'] - (2 * ind_df['rolling_std'])
    ind_df['BB%'] = (ind_df[symbol] - ind_df['bot_bb']) / (ind_df['top_bb'] - ind_df['bot_bb'])

    # calculate RSI (relative strength index)
    dUp, dDown = ind_df[symbol].diff(), ind_df[symbol].diff()
    dUp[dUp < 0] = 0
    dDown[dDown > 0] = 0
    RolUp = pd.rolling_mean(dUp, lookback)
    RolDown = pd.rolling_mean(dDown, lookback).abs()
    ind_df['RS'] = RolUp / RolDown
    ind_df['RSI'] = 100 - (100 / (1 + ind_df['RS']))

    # calculate momentum:
    ind_df['momentum'] = (ind_df[symbol] / ind_df[symbol].shift(momentum_period)) - 1
    ind_df['momentum crossover'] = np.where(ind_df['momentum'] > 0, 1, 0)
    ind_df['momentum crossover'] = np.where(ind_df['momentum'] < 0, -1, ind_df['momentum crossover'])
    ind_df['momentum signal'] = (np.sign(ind_df['momentum crossover'] - ind_df['momentum crossover'].shift(1)))

    # normalized below data to 1:
    ind_df['price_norm'] = normalize(ind_df[symbol])
    ind_df['top_bb_norm'] = normalize(ind_df['top_bb'])
    ind_df['bot_bb_norm'] = normalize(ind_df['bot_bb'])
    ind_df['SMA_norm'] = normalize(ind_df['SMA'])
    # ind_df['price/SMA'] = ind_df[symbol] / ind_df['SMA']
    ind_df['price/SMA_norm'] = ind_df['price_norm'] / ind_df['SMA_norm']

    # calculate MACD:
    ind_df['26 ema'] = pd.ewma(ind_df[symbol], span=26)
    ind_df['12 ema'] = pd.ewma(ind_df[symbol], span=12)
    ind_df['MACD'] = (ind_df['12 ema'] - ind_df['26 ema'])
    ind_df['Signal Line'] = pd.ewma(ind_df['MACD'], span=9)
    ind_df['Signal Line Crossover'] = np.where(ind_df['MACD'] > ind_df['Signal Line'], 1, 0)
    ind_df['Signal Line Crossover'] = np.where(ind_df['MACD'] < ind_df['Signal Line'], -1, ind_df['Signal Line Crossover'])
    ind_df['Centerline Crossover'] = np.where(ind_df['MACD'] > 0, 1, 0)
    ind_df['Centerline Crossover'] = np.where(ind_df['MACD'] < 0, -1, ind_df['Centerline Crossover'])
    ind_df['MACD signal'] = (np.sign(ind_df['Signal Line Crossover'] - ind_df['Signal Line Crossover'].shift(1)))

    # Buy/Sell signals: 0:'HOLD', 1:'BUY', -1: 'SELL'
    ind_df['BB% trigger'] = 0
    ind_df['BB% trigger'][ind_df['BB%'] < 0.2] = 1
    ind_df['BB% trigger'][ind_df['BB%'] > 0.8] = -1

    ind_df['RSI trigger'] = 0
    ind_df['RSI trigger'][ind_df['RSI'] < 30] = 1
    ind_df['RSI trigger'][ind_df['RSI'] > 70] = -1

    ind_df['MACD trigger']= 0
    ind_df['MACD trigger'][ind_df['MACD signal']== 1] = 1
    ind_df['MACD trigger'][ind_df['MACD signal'] == -1] = -1

    ind_df['momentum trigger'] = 0
    ind_df['momentum trigger'][ind_df['momentum signal'] == 1] = 1
    ind_df['momentum trigger'][ind_df['momentum signal'] == -1] = -1

    ind_df['trigger'] = (2*ind_df['BB% trigger'] + 2*ind_df['RSI trigger'] + ind_df['MACD signal'] +  ind_df['momentum trigger'])

    return ind_df


if __name__ == "__main__":
    start_date = dt.datetime(2008, 01, 01)
    end_date = dt.datetime(2009, 12, 31)
    symbol = 'JPM'
    lookback = 15
    momentum_period = 20
    df = get_ind_data(symbol, start_date, end_date, lookback, momentum_period)
    # f = plt.figure()
    # plot normalized price
    df.plot(y=['price_norm'], title='normalized adjusted closing price')
    plt.savefig('figure 1_1.pdf')
    # plot SMA
    df.plot(y=['price_norm', 'price/SMA_norm', 'SMA_norm'], title='Price / Simple Moving Average')
    plt.savefig('figure 1_2.pdf')
    # plot BB
    df.plot(y=['price_norm', 'BB%'], title='Bollinger Bands %')
    plt.savefig('figure 1_3.pdf')
    df.plot(y=[symbol, 'top_bb', 'bot_bb'], title='Top and Bottom Bollinger Bands')
    plt.savefig('figure 1_4.pdf')
    df.plot(y=['price_norm', 'top_bb_norm', 'bot_bb_norm'], title='Top and Bottom Bollinger Bands normalized')
    plt.savefig('figure 1_5.pdf')
    # plot RSI
    df.plot(y=[symbol, 'RSI'], title='Relative Strength Index')
    plt.savefig('figure 1_6.pdf')
    # plot momentum
    ax1 = df.plot(y=['price_norm', 'momentum'], title='momentum')
    ax1.axhline(y=0, color='r', linestyle='-')
    for xc in df.index[df['momentum signal'] == 1]:
        ax1.axvline(x=xc, color='g', linestyle='-')
    for xc in df.index[df['momentum signal'] == -1]:
        ax1.axvline(x=xc, color='r', linestyle='-')
    plt.savefig('figure 1_7.pdf')
    # plot MACD
    ax2 = df.plot(y=['MACD', 'Signal Line'], title='MACD & Signal Line')
    for xc in df.index[df['MACD signal'] == 1]:
        ax2.axvline(x=xc, color='g', linestyle='-')
    for xc in df.index[df['MACD signal'] == -1]:
        ax2.axvline(x=xc, color='r', linestyle='-')
    plt.savefig('figure 1_8.pdf')
    # df.plot(y=['Centerline Crossover', 'MACD signal'], title='Signal Line & Centerline Crossovers', ylim=(-1.5, 1.5))
    # plt.savefig('figure 1_9.pdf')
    # plt.show()