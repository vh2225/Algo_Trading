"""
This is a template algorithm on Quantopian for you to adapt and fill in.
"""
import quantopian.algorithm as algo
from quantopian.pipeline import Pipeline
from quantopian.pipeline.data.builtin import USEquityPricing
from quantopian.pipeline.filters import QTradableStocksUS


def initialize(context):
    """
    Called once at the start of the algorithm.
    """
    # Rebalance every day, 1 hour after market open.
    context.limit = 10


def before_trading_start(context, data):
    """
    Called every day before market open.
    """
    context.fundamentals = get_fundamentals(
        query(
            fundamentals.valuation_ratios.pb_ratio.
            fundamentals.valuation_ratios.pe_ratio.
        )
        .filter(
            fundamentals.valuation_ratios.pe_ratio < 14
        )
        .filter(
            fundamentals.valuation_ratios.pb_ratio < 2
        )
        .order_by(
            fundamentals.valuation.market_cap.desc()
        )
        .limit(context.limit)
    )
    
    update_universe(context.fundamentals.columns.values)

    # These are the securities that we are interested in trading each day.
    context.security_list = context.output.index


def handle_data(context, data):
    """
    Called every minute.
    """
    cash = context.portfolio.cash
    current_position = context.portfolio.positions
    for stock in data:
        current_position = context.portfolio.positions[stock].amount
        stock_price = data[stock].price
        plausible_investment = cash/10.0
        share_amount = int(plausible_investment/stock_price)
        
        try:
            if stock_price < plausible_investment:
                if not current_position:
                    if context.fundamentals[stock]['pe_ratio']<11:
                        order(stock, share_amount)
        except Exception as e:
            print(str(e))