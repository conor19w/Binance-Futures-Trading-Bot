from copy import copy
from pprint import PrettyPrinter
from live_trading_config import *
from live_trading_config import symbols_to_trade  # explicitly importing to remove a warning
from Helper import *
from trade_manager import *
from threading import Thread
import multiprocessing
from queue import Queue
import os

os.environ['TYPE_CHECKING'] = 'False'

if __name__ == '__main__':
    pp = PrettyPrinter()  ##for printing json text cleanly (inspect binance API call returns)
    Bots: [Bot_Class.Bot] = []
    signal_queue = None
    print_trades_q = None
    if use_multiprocessing_for_trade_execution:
        signal_queue = multiprocessing.Queue()
        print_trades_q = multiprocessing.Queue()
    else:
        signal_queue = Queue()
        print_trades_q = Queue()

    python_binance_client = Client(api_key=API_KEY, api_secret=API_SECRET)
    client = CustomClient(python_binance_client, print_trades_q)
    if trade_all_symbols:
        symbols_to_trade = client.get_all_symbols()

    client.set_leverage(symbols_to_trade)

    ## Initialize a bot for each coin we're trading
    client.setup_bots(Bots, symbols_to_trade, signal_queue, print_trades_q)

    client.start_websockets(Bots)

    ## Initialize Trade manager for order related tasks
    TM = TradeManager(python_binance_client, signal_queue, print_trades_q)

    ## Thread to ping the server & reconnect websockets
    ping_server_reconnect_sockets_thread = Thread(target=client.ping_server_reconnect_sockets, args=(Bots,))
    ping_server_reconnect_sockets_thread.daemon = True
    ping_server_reconnect_sockets_thread.start()

    ## Combine data collected from websockets with historical data, so we have a buffer of data to calculate signals
    combine_data_thread = Thread(target=client.combine_data, args=(Bots, symbols_to_trade))
    combine_data_thread.daemon = True
    combine_data_thread.start()

    new_trade_loop = None
    if use_multiprocessing_for_trade_execution:
        new_trade_loop = multiprocessing.Process(target=new_trades_loop_multiprocess, args=(python_binance_client, signal_queue))
        new_trade_loop.start()
    else:
        new_trade_loop = Thread(target=TM.new_trades_loop)
        new_trade_loop.daemon = True
        new_trade_loop.start()

    account_balance = TM.get_account_balance()
    startup_account_balance = copy(account_balance)

    log.info(f'Start Balance: {account_balance}')
    print()
    new_trade_loop.join()