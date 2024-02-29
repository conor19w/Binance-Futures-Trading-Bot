start = "12-09-23"
end = "13-09-23"
buffer = None ## Leave as none to auto-calculate the required buffer,
starting_account_balance = 53  ## Starting account size
fee = .00036 ## .036%
leverage = 10
order_size = 3  ## 1.25% of account balance per trade with 10x leverage the position size would be 12.5%
interval = '15m'  ## valid intervals: 1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h, 1d
max_number_of_positions = 10  ## max amount of trades the bot will have open at any time
slippage = .001  ## .01% recommended to use at least .01% slippage, the more slippage the strategy can survive the better the signals
TP_SL_choice = '%'  ## type of TP/SL used in backtest, list of valid values: '%', 'x (ATR)', 'x (Swing High/Low) level 1', 'x (Swing Close) level 1', 'x (Swing High/Low) level 2', 'x (Swing Close) level 2', 'x (Swing High/Low) level 3', 'x (Swing Close) level 3'
SL_mult = 1.5  ## multiplier for the 'TP_SL_choice' above
TP_mult = 4  ## multiplier for the 'TP_SL_choice' above
trading_strategy = ''  ##name of strategy you want to run
time_change = 1  ## Adjust time for printing based off GMT (This is GMT+1)

use_trailing_stop = False  ## flag to use the trailing stop with callback distance defined below
trailing_stop_callback = 1  ## 1% keep the trailing stop this percent away from the last high/ low
trade_each_symbol_with_separate_balance = True  ## Isolated test will generate graphs for each coin as if it was trading separately from the other coins
only_show_profitable_coins = False  # flag for the below percentage
percent_gain_threshold = 1  ## percentage for 'only_show_profitable_coins' flag, will only show coins at the end of the backtest that have made this amount of profit or more
use_minimum_drawdown = False  ## Flag for minimum drawdown below
minimum_drawdown = 1  ## 1%, Only print coins which have had less than this drawdown when the above flag 'particular_drawdown' is True

symbols_to_trade = ['BTCUSDT', 'BAKEUSDT']  ## list of coins to trade, example: ['ETHUSDT', 'BNBUSDT']
trade_all_symbols = True  ## will test on all coins on exchange if true
coin_exclusion_list = []
'''
 Trade Graphing Settings
'''
graph_buys_and_sells = False
auto_open_graph_images = False ## Set to true to open all the trade graphs on completion (Caution this may use up a lot of memory)
graph_buys_and_sells_window_before = 5 ## graph 5 candles before the trade opened
graph_buys_and_sells_window_after = 5 ## graph 5 candles after the trade opened
graph_folder_location = './'
trade_log_name = "trade_log.csv"

## Variables you probably don't need to change:
trading_on = False  ## Set to false to use the trading start time below, CAUTION ensure trading is withing start and end or you will get errors
start_trading_date = '2023-09-13 10:30:00'  ## Particular time to start trading at not used if trading_on = True
use_multiprocessing_for_downloading_data = True ## use multiprocessing for quicker backtesting

make_decision_options = {'look_back_period': 10, 'volume_mult': 5}
