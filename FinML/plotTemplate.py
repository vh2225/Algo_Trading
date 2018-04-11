# import
import datetime as dt
import matplotlib.pyplot as plt
from matplotlib import style
from matplotlib.finance import candlestick_ohlc
import matplotlib.dates as mdates
import pandas as pd
import pandas_datareader.data as web

# style
style.use('ggplot')

# time
# start = dt.datetime(2000, 1, 1)
# end = dt.datetime(2016, 12, 31)

# df -> csv
# symbol = 'TSLA'
# source = 'yahoo'
# df = web.DataReader(symbol, source, start, end)
# df.to_csv(symbol + '.csv')
# df.head(n=5): Return the first n rows, default 5

# csv -> df
symbol = 'TSLA'
df = pd.read_csv(symbol + '.csv', parse_dates=True, index_col=0) # index_col=0: row label
# print(df[['Open', 'High']].head())

# candle
period = '10D'
df_ohlc = df['Adj Close'].resample(period).ohlc() # open-high-low-close for candle
df_volume = df['Volume'].resample(period).sum()
df_ohlc.reset_index(inplace=True)
df_ohlc['Date'] = df_ohlc['Date'].map(mdates.date2num)
# print(df_ohlc.head())

# 100ma
# -----------------------------------
# df['100ma'] = df['Adj Close'].rolling(window=100).mean()
# df.dropna(inplace=True )
# -----------------------------------
# df['100ma'] = df['Adj Close'].rolling(window=100, min_periods=0).mean()

# plot
# -----------------------------------
# df['Adj Close'].plot()
# plt.show()
# -----------------------------------
ax1 = plt.subplot2grid((6,1), (0,0), rowspan=5, colspan=1)
ax2 = plt.subplot2grid((6,1), (5,0), rowspan=1, colspan=1, sharex=ax1)
ax1.xaxis_date()
# ax1.plot(df.index, df['Adj Close'])
# ax1.plot(df.index, df['100ma'])
# ax2.bar(df.index, df['Volume'])
candlestick_ohlc(ax1, df_ohlc.values, width=2, colorup='g', colordown='r')
ax2.fill_between(df_volume.index.map(mdates.date2num), df_volume.values, 0)
plt.show()
