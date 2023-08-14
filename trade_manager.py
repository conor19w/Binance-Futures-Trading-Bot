from threading import Thread

from binance.client import Client
from binance.enums import SIDE_SELL, SIDE_BUY, FUTURE_ORDER_TYPE_MARKET, FUTURE_ORDER_TYPE_LIMIT, TIME_IN_FORCE_GTC, \
    FUTURE_ORDER_TYPE_STOP_MARKET
from binance.exceptions import BinanceAPIException

import TradingStrats
from live_trading_config import *
import time
from Helper import Trade
from logger import *

active_trades_multiprocess: [Trade] = []


def new_trades_loop_multiprocess(client: Client, new_trades_q):
    global active_trades_multiprocess
    check_threshold_thread = Thread(target=check_threshold_loop_multiprocess)
    check_threshold_thread.daemon = True
    while True:
        [symbol, OP, CP, tick_size, trade_direction, stop_loss_val, take_profit_val] = new_trades_q.get()
        try:
            pass

            if not check_threshold_thread.is_alive():
                check_threshold_thread.start()  ## Start this thread after a trade executes
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            log.error(f'new_trades_loop() - error occurred, Error Info: {exc_obj, fname, exc_tb.tb_lineno}, Error: {e}')


def check_threshold_loop_multiprocess():
    global active_trades_multiprocess
    ## This loop will only be active while we have trades in status 0
    try:
        while True:
            time.sleep(10)
            unopened_trades = [t.trade_status for t in active_trades_multiprocess if t.trade_status == 0]
            if len(unopened_trades) == 0:
                break
            ## Check trading threshold for each trade

    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        log.error(f'check_threshold_loop() - error occurred, Error Info: {exc_obj, fname, exc_tb.tb_lineno}, Error: {e}')


'''
Function for custom TP SL values that need trade information before calculating, may be needed depending on your TP SL Function
Otherwise you can go the usual route and configure a TP SL function in Bot_Class.Bot.update_TP_SL() & TradingStrats.SetSLTP()
'''
def calculate_custom_tp_sl(options):
    stop_loss_val = -99
    take_profit_val = -99
    match TP_SL_choice:
        case 'USDT':
            stop_loss_val, take_profit_val = TradingStrats.USDT_SL_TP(options)

    return stop_loss_val, take_profit_val


class TradeManager:
    def __init__(self, client: Client, new_trades_q, print_trades_q):
        self.client = client
        self.active_trades: [Trade] = []
        self.use_trailing_stop = use_trailing_stop
        self.trailing_stop_callback = trailing_stop_callback
        self.use_market_orders = use_market_orders
        self.new_trades_q = new_trades_q
        self.check_threshold_thread = Thread(target=self.check_threshold_loop)
        self.check_threshold_thread.daemon = True
        self.check_threshold_thread.start()
        self.place_tp_sl_thread = Thread(target=self.place_tp_sl_loop)
        self.place_tp_sl_thread.daemon = True
        self.place_tp_sl_thread.start()
        self.monitor_tp_sl_thread = Thread(target=self.monitor_tp_sl_loop)
        self.monitor_tp_sl_thread.daemon = True
        self.monitor_tp_sl_thread.start()
        self.print_trades_q = print_trades_q

    '''
    Loop that constantly runs and opens new trades as they come in
    '''
    def new_trades_loop(self):
        while True:
            [symbol, OP, CP, tick_size, trade_direction, index, stop_loss_val, take_profit_val] = self.new_trades_q.get()
            if symbol not in self.get_all_open_or_pending_trades() and len(self.active_trades) < max_number_of_positions and self.check_margin_sufficient():
                try:
                    order_id, order_qty, entry_price, trade_status = self.open_trade(symbol, trade_direction, OP, tick_size)
                    if TP_SL_choice in custom_tp_sl_functions:
                        options = {'position_size': order_qty} ## If you have a need to add additional inputs to calculate_custom_tp_sl() you can do so by adding to this dict
                        stop_loss_val, take_profit_val = calculate_custom_tp_sl(options)
                    self.active_trades.append(Trade(index, entry_price, order_qty, take_profit_val, stop_loss_val, trade_direction, order_id, symbol, CP, tick_size))
                    if trade_status:
                        self.place_tp_sl(symbol, trade_direction, CP, tick_size, entry_price, order_qty)
                    elif trade_status == 0:
                        log.info(f'new_trades_loop() - Order placed on {symbol}, Entry price: {entry_price}, order quantity: {order_qty}, Side: {"Long" if trade_direction else "Short"}')
                except Exception as e:
                    exc_type, exc_obj, exc_tb = sys.exc_info()
                    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                    log.error(f'new_trades_loop() - error occurred, Error Info: {exc_obj, fname, exc_tb.tb_lineno}, Error: {e}')

    '''
    Opens TP and SL positions
    '''
    def place_tp_sl(self, symbol, trade_direction, CP, tick_size, entry_price, order_qty):
        self.active_trades[-1].SL_id = self.place_SL(symbol, self.active_trades[-1].SL_val, trade_direction, CP, tick_size)
        self.active_trades[-1].TP_id = self.place_TP(symbol, [self.active_trades[-1].TP_val, order_qty], trade_direction, CP, tick_size)
        if self.active_trades[-1].SL_id != -99 and self.active_trades[-1].TP_id != -99:
            self.active_trades[-1].trade_status = 1
            log.info(f'new_trades_loop() - Position opened on {symbol}, Entry price: {entry_price}, order quantity: {order_qty}, Side: {"Long" if trade_direction else "Short"}\n'
                     f' Take Profit & Stop loss have been placed')
            self.print_trades_q.put(True)
        else:
            self.active_trades[-1].trade_status = 3  ## Signals to close the trade as it doesn't have either a Take Profit or a Stop Loss

    '''
    Gets all opened trades, User opened positions + Bot opened trades + Pending Bot trades
    '''
    def get_all_open_or_pending_trades(self):
        open_trades_symbols = [position['symbol'] for position in self.client.futures_position_information() if float(position['notional']) != 0.0]  ## All open Trades
        active_trade_symbols = [trade.symbol for trade in self.active_trades]
        return open_trades_symbols + active_trade_symbols

    '''
    Gets all opened trades from binance
    '''
    def get_all_open_trades(self):
        return [position['symbol'] for position in self.client.futures_position_information() if float(position['notional']) != 0.0]

    '''
    Checks if we have sufficient margin remaining to open a new trade
    '''
    def check_margin_sufficient(self):
        account_info = self.client.futures_account()
        return float(account_info['totalMarginBalance']) > (float(account_info['totalWalletBalance']) * (1 - order_size / 100)) / leverage

    '''
    Checks if any trades have gone past our specified threshold in live_trading_config.py
    '''
    def check_threshold_loop(self):
        count = 0
        while True:
            try:
                time.sleep(5)
                ## Check trading threshold for each trade
                for trade in self.active_trades:
                    if trade.trade_status == 0:
                        current_price = float(self.client.futures_symbol_ticker(symbol=trade.symbol)['price'])
                        if (abs(trade.entry_price - current_price) / trade.entry_price) > trading_threshold / 100:
                            trade.trade_status = 2
                ## clean up task for completed trades
                if count == 2:
                    self.cancel_and_remove_trades()
                    count = 0
                count += 1
            except Exception as e:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                log.error(f'check_threshold_loop() - error occurred, Error Info: {exc_obj, fname, exc_tb.tb_lineno}, Error: {e}')

    '''
    Function that removes finished trades from the active_trades list
    '''
    def cancel_and_remove_trades(self):
        i = 0
        while i < len(self.active_trades):
            if self.active_trades[i].trade_status == 2:
                try:
                    pop_trade = self.check_position_and_cancel_orders(self.active_trades[i])
                    if pop_trade:
                        log.info(f'cancel_and_remove_trades() - orders cancelled on {self.active_trades[i].symbol} as price surpassed the trading threshold set in live_trading_config.py')
                        self.active_trades.pop(i)
                    else:
                        self.active_trades[i].trade_status = 1
                        i += 1
                except Exception as e:
                    exc_type, exc_obj, exc_tb = sys.exc_info()
                    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                    log.error(f'cancel_and_remove_trades() - error occurred cancelling a trade on {self.active_trades[i].symbol}, Error Info: {exc_obj, fname, exc_tb.tb_lineno}, Error: {e}')
            elif self.active_trades[i].trade_status == 3:
                try:
                    self.close_position(self.active_trades[i].symbol, self.active_trades[i].trade_direction, self.active_trades[i].position_size)
                    if self.active_trades[i].SL_id == -99:
                        log.info(f'cancel_and_remove_trades() - orders cancelled on {self.active_trades[i].symbol} as there was an issue placing the Stop loss')
                    else:
                        log.info(f'cancel_and_remove_trades() - orders cancelled on {self.active_trades[i].symbol} as there was an issue placing the Take Profit')
                    self.active_trades.pop(i)
                except Exception as e:
                    exc_type, exc_obj, exc_tb = sys.exc_info()
                    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                    log.error(f'cancel_and_remove_trades() - error occurred cancelling a trade on {self.active_trades[i].symbol}, Error Info: {exc_obj, fname, exc_tb.tb_lineno}, Error: {e}')
            elif self.active_trades[i].trade_status == 4:
                try:
                    self.client.futures_cancel_all_open_orders(symbol=self.active_trades[i].symbol)
                    log.info(f'cancel_and_remove_trades() - orders cancelled on {self.active_trades[i].symbol} as Take Profit was hit')
                    self.active_trades.pop(i)
                except Exception as e:
                    exc_type, exc_obj, exc_tb = sys.exc_info()
                    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                    log.error(f'cancel_and_remove_trades() - error occurred closing open orders on {self.active_trades[i].symbol}, Error Info: {exc_obj, fname, exc_tb.tb_lineno}, Error: {e}')
            elif self.active_trades[i].trade_status == 5:
                try:
                    self.client.futures_cancel_all_open_orders(symbol=self.active_trades[i].symbol)
                    log.info(f'cancel_and_remove_trades() - orders cancelled on {self.active_trades[i].symbol} as Stop loss was hit')
                    self.active_trades.pop(i)
                except Exception as e:
                    exc_type, exc_obj, exc_tb = sys.exc_info()
                    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                    log.error(f'cancel_and_remove_trades() - error occurred closing open orders on {self.active_trades[i].symbol}, Error Info: {exc_obj, fname, exc_tb.tb_lineno}, Error: {e}')
            elif self.active_trades[i].trade_status == 1:
                try:
                    if self.active_trades[i].symbol not in self.get_all_open_trades():
                        self.client.futures_cancel_all_open_orders(symbol=self.active_trades[i].symbol)
                        log.info(f'cancel_and_remove_trades() - orders cancelled on {self.active_trades[i].symbol} as trade was closed, possibly by the user')
                        self.active_trades.pop(i)
                except Exception as e:
                    exc_type, exc_obj, exc_tb = sys.exc_info()
                    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                    log.error(f'cancel_and_remove_trades() - error occurred cancelling a trade on {self.active_trades[i].symbol}, Error Info: {exc_obj, fname, exc_tb.tb_lineno}, Error: {e}')
            else:
                i += 1

    '''
    Loop that constantly runs and places TP / SL positions when we enter a new position
    '''
    def place_tp_sl_loop(self):
        while True:
            try:
                time.sleep(5)
                unopened_trades = [t for t in self.active_trades if t.trade_status == 0]
                unopened_order_symbols = [t.symbol for t in unopened_trades]
                filled_orders = [[order['symbol'], order['orderId']] for order in self.client.futures_get_all_orders() if (order['symbol'] in unopened_order_symbols and order['status'] == 'FILLED')]
                ## Check if trade was entered
                for trade in self.active_trades:
                    if trade.trade_status == 0:
                        for [symbol, ID] in filled_orders:
                            if symbol == trade.symbol and ID == trade.order_id:
                                trade.SL_id = self.place_SL(trade.symbol, trade.SL_val, trade.trade_direction, trade.CP, trade.tick_size)
                                trade.TP_id = self.place_TP(trade.symbol, [trade.TP_val, trade.position_size], trade.trade_direction, trade.CP, trade.tick_size)
                                if trade.SL_id != -99 and trade.TP_id != -99:
                                    trade.trade_status = 1
                                    log.info(f'place_tp_sl_loop() - Order filled on {symbol}, Entry price: {trade.entry_price}, order quantity: {trade.position_size}, Side: {"Long" if trade.trade_direction else "Short"}\n'
                                        f' Take Profit & Stop loss have been placed')
                                    self.print_trades_q.put(True)
                                else:
                                    self.active_trades[-1].trade_status = 3
            except Exception as e:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                log.error(f'place_tp_sl_loop() - error occurred, Error Info: {exc_obj, fname, exc_tb.tb_lineno}, Error: {e}')

    '''
    Loop that constantly runs and updates the status of trades for removal based on TP & SL
    '''
    def monitor_tp_sl_loop(self):
        while True:
            time.sleep(10)
            opened_trades = [t for t in self.active_trades if t.trade_status == 1]
            opened_order_symbols = [t.symbol for t in opened_trades]
            filled_orders = [[order['symbol'], order['orderId']] for order in self.client.futures_get_all_orders() if (order['symbol'] in opened_order_symbols and order['status'] == 'FILLED')]
            for trade in self.active_trades:
                for [symbol, ID] in filled_orders:
                    if symbol == trade.symbol and ID == trade.TP_id:
                        trade.trade_status = 4 ## successful trade marking for removal
                    elif symbol == trade.symbol and ID == trade.SL_id:
                        trade.trade_status = 5  ## unsuccessful trade marking for removal

    '''
    Function to open a new trade
    '''
    def open_trade(self, symbol, trade_direction, OP, tick_size):
        order_book = None
        order_id = ''
        try:
            order_book = self.client.futures_order_book(symbol=symbol)
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            log.error(f'open_trade() - error occurred getting order book, Error Info: {exc_obj, fname, exc_tb.tb_lineno}, Error: {e}')

        bids = order_book['bids']
        asks = order_book['asks']
        entry_price = 0
        if trade_direction == 1:
            entry_price = float(bids[0][0])
        elif trade_direction == 0:
            entry_price = float(asks[0][0])
        account_balance = self.get_account_balance()
        order_notional = leverage * account_balance * (order_size/100)
        order_qty = order_notional / entry_price
        if OP == 0:
            order_qty = round(order_qty)
        else:
            order_qty = round(order_qty, OP)
        if self.use_market_orders:
            try:
                ##Could Make limit orders but for now the entry is a market
                if trade_direction == 0:
                    order = self.client.futures_create_order(
                        symbol=symbol,
                        side=SIDE_SELL,
                        type=FUTURE_ORDER_TYPE_MARKET,
                        quantity=order_qty)
                    order_id = order['orderId']
                if trade_direction == 1:
                    order = self.client.futures_create_order(
                        symbol=symbol,
                        side=SIDE_BUY,
                        type=FUTURE_ORDER_TYPE_MARKET,
                        quantity=order_qty)
                    order_id = order['orderId']
                market_entry_price = float(self.client.futures_position_information(symbol=symbol)[0]['entryPrice'])
                return order_id, order_qty, market_entry_price, 1
            except Exception as e:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                log.error(f'open_trade() - error occurred placing market order on {symbol}, OP: {OP}, trade direction: {trade_direction},\n'
                          f'Quantity: {order_qty}, Error Info: {exc_obj, fname, exc_tb.tb_lineno}, Error: {e}')
        else:
            try:
                if trade_direction == 0:
                    order = self.client.futures_create_order(
                        symbol=symbol,
                        side=SIDE_SELL,
                        type=FUTURE_ORDER_TYPE_LIMIT,
                        price=entry_price,
                        timeInForce=TIME_IN_FORCE_GTC,
                        quantity=order_qty)
                    order_id = order['orderId']
                if trade_direction == 1:
                    order = self.client.futures_create_order(
                        symbol=symbol,
                        side=SIDE_BUY,
                        type=FUTURE_ORDER_TYPE_LIMIT,
                        price=entry_price,
                        timeInForce=TIME_IN_FORCE_GTC,
                        quantity=order_qty)
                    order_id = order['orderId']
            except Exception as e:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                log.error(f'open_trade() - error occurred placing limit order on {symbol}, OP: {OP}, tick_size: {tick_size}\n'
                    f'Entry price: {entry_price}, trade direction: {trade_direction}, Quantity: {order_qty},\n Error Info: {exc_obj, fname, exc_tb.tb_lineno}, Error: {e}')
            return order_id, order_qty, entry_price, 0

    '''
    Function that returns the USDT balance of the account
    '''
    def get_account_balance(self):
        try:
            account_balance_info = self.client.futures_account_balance()
            for x in account_balance_info:
                if x['asset'] == 'USDT':
                    return float(x['balance'])
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            log.error(f'get_account_balance() - error getting account balance, Error Info: {exc_obj, fname, exc_tb.tb_lineno}, Error: {e}')

    '''
    Function that places a new TP order
    '''
    def place_TP(self, symbol: str, TP: [float, float], trade_direction: int, CP: int, tick_size: float):
        TP_ID = ''
        try:
            TP_val = 0
            order = ''
            order_side = ''
            if CP == 0:
                TP_val = round(TP[0])
            else:
                TP_val = round(round(TP[0] / tick_size) * tick_size, CP)
            if trade_direction == 1:
                order_side = SIDE_SELL
            elif trade_direction == 0:
                order_side = SIDE_BUY
            if not self.use_trailing_stop:
                order = self.client.futures_create_order(
                    symbol=symbol,
                    side=order_side,
                    type=FUTURE_ORDER_TYPE_LIMIT,
                    price=TP_val,
                    timeInForce=TIME_IN_FORCE_GTC,
                    reduceOnly='true',
                    quantity=TP[1])
                TP_ID = order['orderId']
            else:
                order = self.client.futures_create_order(
                    symbol=symbol,
                    side=order_side,
                    type='TRAILING_STOP_MARKET',
                    ActivationPrice=TP_val,
                    callbackRate=self.trailing_stop_callback,
                    quantity=TP[1])
                TP_ID = order['orderId']
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            log.error(f"place_TP() - Error occurred placing TP on {symbol}, Error: {e}, {exc_type, fname, exc_tb.tb_lineno}")
            return -1

        return TP_ID

    '''
    Function that places a new SL order
    '''
    def place_SL(self, symbol: str, SL: float, trade_direction: int, CP: int, tick_size: float):
        order_ID = ''
        try:
            if CP == 0:
                SL = round(SL)
            else:
                SL = round(round(SL / tick_size) * tick_size, CP)

            if trade_direction == 1:
                order = self.client.futures_create_order(
                    symbol=symbol,
                    side=SIDE_SELL,
                    type=FUTURE_ORDER_TYPE_STOP_MARKET,
                    stopPrice=SL,
                    closePosition='true')
                order_ID = order['orderId']
            else:
                order = self.client.futures_create_order(
                    symbol=symbol,
                    side=SIDE_BUY,
                    type=FUTURE_ORDER_TYPE_STOP_MARKET,
                    stopPrice=SL,
                    closePosition='true')
                order_ID = order['orderId']
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            log.error(f"place_SL() - Error occurred placing SL on {symbol}, Error: {e}, {exc_type, fname, exc_tb.tb_lineno}")
            return -1

        return order_ID

    '''
    Function for closing an open position, used when something goes wrong with a trade
    Can also be used to close a position based off a condition met in your strategy
    '''
    def close_position(self, symbol: str, trade_direction: int, total_position_size: float):
        self.client.futures_cancel_all_open_orders(symbol=symbol)  ##cancel orders for this symbol
        if trade_direction == 0:
            self.client.futures_create_order(
                symbol=symbol,
                side=SIDE_BUY,
                type=FUTURE_ORDER_TYPE_MARKET,
                quantity=total_position_size)
        if trade_direction == 1:
            self.client.futures_create_order(
                symbol=symbol,
                side=SIDE_SELL,
                type=FUTURE_ORDER_TYPE_MARKET,
                quantity=total_position_size)

    '''
    Function that checks we haven't entered a position before cancelling it
    '''
    def check_position_and_cancel_orders(self, trade: Trade):
        open_trades = self.get_all_open_trades()
        if trade.symbol not in open_trades:
            self.client.futures_cancel_all_open_orders(symbol=trade.symbol)
            return True
        else:
            return False


