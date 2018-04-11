import quantopian.algorithm as algo
from quantopian.pipeline import Pipeline
from quantopian.pipeline.data.builtin import USEquityPricing
from quantopian.pipeline.filters import QTradableStocksUS


def initialize(context):
    """
    Called once at the start of the algorithm.
    """
    context.security = symbol('SPY')
    print(context.security)

def handle_data(context, data):
    """
    Called every minute.
    """
    MA1 = data[context.security].mavg(50)
    MA2 = data[context.security].mavg(200)
                                      
    current_price = data[context.security].price
    current_positions = context.portfolio.positions[symbol('SPY')].amount
    cash = context.portfolio.cash
    
    if(MA1 > MA2) and not current_positions:
        number_of_shares = int(cash/current_price)
        order(context.security, number_of_shares)
        log.info('Buying shares')
    elif (MA1 < MA2) and current_positions:
        order_target(context.security, 0)
        log.info('Selling shares')
        
    record(MA1 = MA1, MA2 = MA2, Price = current_price)