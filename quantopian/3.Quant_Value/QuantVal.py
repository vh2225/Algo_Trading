"""
    Trading Strategy using Fundamental Data
    
    1. Filter the top 50 companies by market cap 
    2. Find the top two sectors that have the highest average PE ratio
    3. Every month exit all the positions before entering new ones at the month
    4. Log the positions that we need 
"""

import pandas as pd
import numpy as np
import datetime
from pytz import timezone
from zipline.utils import tradingcalendar as calendar

class EventManager(object):
    def __init__(self, 
                 period=1,
                 max_daily_hits=1,
                 frequency = '1m',
                 trade_timing_func=None):
        
        self.period = period
        self.max_daily_hits = max_daily_hits
        self.remaining_hits = max_daily_hits
        self._trade_timing_func = trade_timing_func
        self.next_event_date = None
        self.market_open = None
        self.market_close = None
        self.frequency = frequency
    
    @property
    def todays_index(self):
        dt = calendar.canonicalize_datetime(get_datetime())
        return calendar.trading_days.searchsorted(dt)
    
    def open_and_close(self, dt):
        return calendar.open_and_closes.T[dt]
        
    def format_datetime(self, dt):
        # if in minute mode, dt is datetime.datetime
        # if in daily mode, dt is datetime.date
        tmp = { 
            '1m': lambda x: x, 
            '1d': lambda x: x.date() if x is not None else x,
        }[self.frequency](dt)
        return tmp
        
    def signal(self, *args, **kwargs):
        '''
        Entry point for the rule_func
        All arguments are passed to rule_func
        '''
        now = get_datetime()
        dt = calendar.canonicalize_datetime(get_datetime())
        if self.next_event_date is None:
            self.next_event_date = dt
            times = self.open_and_close(dt)
            self.market_open = times['market_open'] 
            self.market_close = times['market_close'] 
        if self.format_datetime(now) < self.format_datetime(self.market_open):
            return False
        #print self.format_datetime(now) >= self.format_datetime(self.market_close)
        if (self.frequency == '1m'):
            # decide if it is the entry time for today's trading
            decision = self._trade_timing_func(*args, **kwargs)
            if decision:
                self.remaining_hits -= 1
                self.set_next_event_date()
        elif (self.frequency == '1d'):
            decision = self.format_datetime(now) >= \
                self.format_datetime(self.market_close)
            if decision:
                self.set_next_event_date()
        return decision
    
    def set_next_event_date(self):
        self.remaining_hits = self.max_daily_hits
        tdays = calendar.trading_days
        idx = self.todays_index + self.period
        self.next_event_date = tdays[idx]
        times = self.open_and_close(self.next_event_date)
        self.market_open = times['market_open']
        self.market_close = times['market_close']
        
    

def entry_func(dt):
    '''
    rule_func passed to EventManager for 
    an intraday entry decision.
    '''
    dt = dt.astimezone(timezone('US/Eastern'))
    return dt.hour == 11 and dt.minute <= 30 
    
# Global instance of the EventManager
trade_manager = EventManager(period=252, frequency = '1d', 
                             trade_timing_func=entry_func)

def initialize(context):
    # Dictionary of stocks and their respective weights
    context.stock_weights = {}
    # Count of days before rebalancing
    context.days = 0
    
    # Sector mappings
    context.sector_mappings = {
       101.0: "Basic Materials",
       102.0: "Consumer Cyclical",
       103.0: "Financial Services",
       104.0: "Real Estate",
       205.0: "Consumer Defensive",
       206.0: "Healthcare",
       207.0: "Utilites",
       308.0: "Communication Services",
       309.0: "Energy",
       310.0: "Industrials",
       311.0: "Technology"
    }
    
def rebalance(context, data):
    # Exit all positions before starting new ones
    for stock in context.portfolio.positions:
        if stock not in context.fundamental_df:
            order_target_percent(stock, 0)

    # Create weights for each stock
    weight = create_weights(context, context.stocks)

    # Rebalance all stocks to target weights
    for stock in context.stocks:
        if weight != 0:
            log.info("Ordering %0.0f%% percent of %s" 
                     % (weight * 100, 
                        stock.symbol))
            
        order_target_percent(stock, weight)

    # track how many positions we're holding
    record(num_positions = len(context.stocks))

    
def before_trading_start(context): 
    """
      Called before the start of each trading day. 
      It updates our universe with the
      securities and values found from fetch_fundamentals.
    """
    
    num_stocks = 15
    
    # Setup SQLAlchemy query to screen stocks based on PE ration
    # and industry sector. Then filter results based on 
    # market cap and shares outstanding.
    # We limit the number of results to num_stocks and return the data
    # in descending order.
    fundamental_df = get_fundamentals(
        query(
            # put your query in here by typing "fundamentals."
            fundamentals.valuation_ratios.pe_ratio, fundamentals.valuation_ratios.pb_ratio, fundamentals.operation_ratios.roe, fundamentals.valuation.market_cap, fundamentals.asset_classification.morningstar_sector_code
        )
        .filter(fundamentals.valuation.market_cap > 100e6)
        .filter(fundamentals.valuation.shares_outstanding != None)
        .filter(fundamentals.valuation_ratios.pe_ratio < 12)
        .filter(fundamentals.valuation_ratios.pb_ratio < 2)
       .filter(fundamentals.operation_ratios.roe > 0.15)
        .order_by(fundamentals.valuation.market_cap.desc())
        .limit(num_stocks)
    )

    # Find sectors with the highest average PE
    #print fundamental_df[fundamental_df.columns[0]]
    context.fundamental_df = fundamental_df
    context.stocks = []
    for s in context.fundamental_df:
        context.stocks.append(s)
    #print [s.symbol for s in fundamental_df.columns]
    
    update_universe(context.fundamental_df.columns.values)   
    
    
def create_weights(context, stocks):
    """
        Takes in a list of securities and weights them all equally 
    """
    if len(stocks) == 0:
        return 0 
    else:
        weight = 1.0/len(stocks)
        return weight
        
def handle_data(context, data):
    if trade_manager.signal():
        rebalance(context, data)