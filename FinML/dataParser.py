# import
import bs4 as bs
import pickle
import requests
import os
import datetime as dt
import pandas as pd
import pandas_datareader as web

# get sp500
def save_sp500_tickers():
    resp = requests.get('https://en.wikipedia.org/wiki/List_of_S%26P_500_companies')
    soup = bs.BeautifulSoup(resp.text, 'lxml')
    table = soup.find('table', {'class':'wikitable sortable'})
    tickers = []
    for row in table.findAll('tr')[1:]:
        ticker = row.findAll('td')[0].text
        tickers.append(ticker)

    with open('sp500tickers.pickle','wb') as f:
        pickle.dump(tickers,f)

    return tickers

# save_sp500_tickers()

def get_data_from_Yahoo(firstN=500, reload_sp500=False):
    if reload_sp500:
        tickers = save_sp500_tickers()
    else:
        with open('sp500tickers.pickle','rb') as f:
            tickers = pickle.load(f)

    if not os.path.exists('stock_dfs'):
        os.makedirs('stock_dfs')

    start = dt.datetime(2000,1,1)
    end = dt.datetime(2016,12,31)
    firstN = min(firstN, len(tickers))
    # iterate and save all data
    for ticker in tickers[:firstN]:
        # print(ticker)
        if not os.path.exists('stock_dfs/{}.csv'.format(ticker)):
            df = web.DataReader(ticker, 'yahoo', start, end)
            df.to_csv('stock_dfs/{}.csv'.format(ticker))
        else:
            print('{} data already exist'.format(ticker))


# get_data_from_Yahoo(10)

def compile_data():
    with open('sp500tickers.pickle', 'rb') as f:
        tickers = pickle.load(f)

    main_df = pd.DataFrame()
    for ind,ticker in enumerate(tickers):
        file_path = 'stock_dfs/{}.csv'.format(ticker)
        if os.path.exists(file_path):
            df = pd.read_csv(file_path)
            df.set_index('Date', inplace=True)
            df.rename(columns={'Adj Close': ticker}, inplace=True)
            df.drop(['Open', 'High', 'Low', 'Close', 'Volume'], 1, inplace=True)
            main_df = df if main_df.empty else main_df.join(df, how='outer')

    main_df.to_csv('sample_sp500_closes.csv')

# get_data_from_Yahoo()
# compile_data()