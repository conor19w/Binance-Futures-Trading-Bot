from threading import Thread

from binance import ThreadedWebsocketManager
from binance.client import Client
from binance.enums import SIDE_SELL, SIDE_BUY, FUTURE_ORDER_TYPE_MARKET, FUTURE_ORDER_TYPE_LIMIT, TIME_IN_FORCE_GTC, \
    FUTURE_ORDER_TYPE_STOP_MARKET
from binance.exceptions import BinanceAPIException
from tabulate import tabulate

import TradingStrats
from live_trading_config import *
import time
from Helper import Trade
from logger import *

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
        self.twm = ThreadedWebsocketManager(api_key=API_KEY, api_secret=API_SECRET)
        self.twm.start()
        self.user_socket = self.twm.start_futures_user_socket(callback=self.monitor_trades)
        self.print_trades_q = print_trades_q
        self.log_trades_loop_thread = Thread(target=self.log_trades_loop)
        self.log_trades_loop_thread.daemon = True
        self.log_trades_loop_thread.start()
        self.total_profit = 0
        self.number_of_wins = 0
        self.number_of_losses = 0

    '''
    Loop that constantly runs and opens new trades as they come in
    '''
    def new_trades_loop(self):
        while True:
            [symbol, OP, CP, tick_size, trade_direction, index, stop_loss_val, take_profit_val] = self.new_trades_q.get()
            if symbol not in self.get_all_open_or_pending_trades() and len(self.active_trades) < max_number_of_positions and self.check_margin_sufficient():
                try:
                    order_id, order_qty, entry_price, trade_status = self.open_trade(symbol, trade_direction, OP, tick_size)
                    if TP_SL_choice in custom_tp_sl_functions and trade_status != -99:
                        options = {'position_size': order_qty} ## If you have a need to add additional inputs to calculate_custom_tp_sl() you can do so by adding to this dict
                        stop_loss_val, take_profit_val = calculate_custom_tp_sl(options)
                    if trade_status != -99:
                        self.active_trades.append(Trade(index, entry_price, order_qty, take_profit_val, stop_loss_val, trade_direction, order_id, symbol, CP, tick_size))
                    if trade_status:
                        self.place_tp_sl(symbol, trade_direction, CP, tick_size, entry_price, order_qty, -1)
                    elif trade_status == 0:
                        log.info(f'new_trades_loop() - Order placed on {symbol}, Entry price: {entry_price}, order quantity: {order_qty}, Side: {"Long" if trade_direction else "Short"}')
                except Exception as e:
                    exc_type, exc_obj, exc_tb = sys.exc_info()
                    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                    log.error(f'new_trades_loop() - error occurred, Error Info: {exc_obj, fname, exc_tb.tb_lineno}, Error: {e}')

    '''
    Callback for user socket that places TP and SL and marks completed trades for removal
    Any logic to update trades based on hitting TPs should be performed here example: moving the LS after a TP is hit
    '''
    def monitor_trades(self, msg):
        try:
            trades_to_update = []
            # for i in range(len(self.active_trades)):
            for trade in self.active_trades:
                if msg['e'] == 'ORDER_TRADE_UPDATE' and msg['o']['s'] == trade.symbol and msg['o']['X'] == 'FILLED':
                    i = self.active_trades.index(trade)
                    if float(msg['o']['rp']) > 0 and msg['o']['i'] == trade.TP_id:
                        self.total_profit += float(msg['o']['rp'])
                        self.number_of_wins += 1
                        trades_to_update.append([i, 4])
                    elif float(msg['o']['rp']) < 0 and msg['o']['i'] == trade.SL_id:
                        self.total_profit += float(msg['o']['rp'])
                        self.number_of_losses += 1
                        trades_to_update.append([i, 5])
                    elif msg['o']['i'] == self.active_trades[i].order_id:
                        trades_to_update.append([i, self.place_tp_sl(trade.symbol, trade.trade_direction,
                                                    trade.CP, trade.tick_size,
                                                    trade.entry_price, trade.position_size, i)])
                elif msg['e'] == 'ACCOUNT_UPDATE':
                    i = self.active_trades.index(trade)
                    for position in msg['a']['P']:
                        if position['s'] == trade.symbol and position['pa'] == '0':
                            trades_to_update.append([i, 6])
            for [index, status] in trades_to_update:
                self.active_trades[index].trade_status = status
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            log.error(f'monitor_trades() - error occurred, Error Info: {exc_obj, fname, exc_tb.tb_lineno}, Error: {e}')

    '''
    Opens TP and SL positions
    '''
    def place_tp_sl(self, symbol, trade_direction, CP, tick_size, entry_price, order_qty, index):
        self.active_trades[index].SL_id = self.place_SL(symbol, self.active_trades[index].SL_val, trade_direction, CP, tick_size)
        self.active_trades[index].TP_id = self.place_TP(symbol, [self.active_trades[index].TP_val, order_qty], trade_direction, CP, tick_size)
        if self.active_trades[index].SL_id != -1 and self.active_trades[-1].TP_id != -1:
            log.info(f'new_trades_loop() - Position opened on {symbol}, orderId: {self.active_trades[-1].order_id}, Entry price: {entry_price}, order quantity: {order_qty}, Side: {"Long" if trade_direction else "Short"}\n'
                     f' Take Profit & Stop loss have been placed')
            self.print_trades_q.put(True)
            return 1
        else:
            return 3  ## Signals to close the trade as it doesn't have either a Take Profit or a Stop Loss

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
        while True:
            try:
                time.sleep(5)
                open_trades = self.get_all_open_trades()
                ## Check trading threshold for each trade
                for trade in self.active_trades:
                    if trade.trade_status == 0 and trade.symbol not in open_trades:
                        current_price = float(self.client.futures_symbol_ticker(symbol=trade.symbol)['price'])
                        if (abs(trade.entry_price - current_price) / trade.entry_price) > trading_threshold / 100:
                            trade.current_price = current_price
                            trade.trade_status = 2
                self.cancel_and_remove_trades()
            except Exception as e:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                log.error(f'check_threshold_loop() - error occurred, Error Info: {exc_obj, fname, exc_tb.tb_lineno}, Error: {e}')

    '''
    Function that removes finished trades from the active_trades list
    '''
    def cancel_and_remove_trades(self):
        i = 0
        open_trades = self.get_all_open_trades()
        while i < len(self.active_trades):
            if self.active_trades[i].trade_status == 2:
                try:
                    pop_trade = self.check_position_and_cancel_orders(self.active_trades[i], open_trades)
                    if pop_trade:
                        log.info(f'cancel_and_remove_trades() - orders cancelled on {self.active_trades[i].symbol} as price surpassed the trading threshold set in live_trading_config.py\n '
                                 f'Current Price was: {self.active_trades[i].current_price}, Attempted entry price was: {self.active_trades[i].entry_price}, % moved: {abs(100*(self.active_trades[i].entry_price-self.active_trades[i].current_price)/self.active_trades[i].entry_price)}')
                        self.active_trades.pop(i)
                    else:
                        self.active_trades[i].trade_status = 0
                        i += 1
                except Exception as e:
                    exc_type, exc_obj, exc_tb = sys.exc_info()
                    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                    log.error(f'cancel_and_remove_trades() - error occurred cancelling a trade on {self.active_trades[i].symbol}, Error Info: {exc_obj, fname, exc_tb.tb_lineno}, Error: {e}')
            elif self.active_trades[i].trade_status == 3:
                try:
                    self.close_position(self.active_trades[i].symbol, self.active_trades[i].trade_direction, self.active_trades[i].position_size)
                    if self.active_trades[i].SL_id == -1:
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
            elif self.active_trades[i].trade_status == 6:
                try:
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
                log.error(f'open_trade() - error occurred placing market order on {symbol}, OP: {OP}, trade direction: {trade_direction}, '
                          f'Quantity: {order_qty}, Error Info: {exc_obj, fname, exc_tb.tb_lineno}, Error: {e}')
                return -99, -99, -99, -99
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
                return order_id, order_qty, entry_price, 0
            except Exception as e:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                log.error(f'open_trade() - error occurred placing limit order on {symbol}, OP: {OP}, tick_size: {tick_size} '
                    f'Entry price: {entry_price}, trade direction: {trade_direction}, Quantity: {order_qty}, Error Info: {exc_obj, fname, exc_tb.tb_lineno}, Error: {e}')
                return -99, -99, -99, -99

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
        TP_val = 0
        try:
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
            log.error(f"place_TP() - Error occurred placing TP on {symbol}, price: {TP_val}, amount: {TP[1]}, Error: {e}, {exc_type, fname, exc_tb.tb_lineno}")
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
            log.error(f"place_SL() - Error occurred placing SL on {symbol}, price: {SL}, Error: {e}, {exc_type, fname, exc_tb.tb_lineno}")
            return -1

        return order_ID

    '''
    Function for closing an open position, used when something goes wrong with a trade
    Can also be used to close a position based off a condition met in your strategy
    '''
    def close_position(self, symbol: str, trade_direction: int, total_position_size: float):
        try:
            self.client.futures_cancel_all_open_orders(symbol=symbol)  ##cancel orders for this symbol
        except:
            log.warning(f'close_position() issue cancelling open orders on {symbol} potentially there were no open orders')
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
    def check_position_and_cancel_orders(self, trade: Trade, open_trades: [str]):
        if trade.symbol not in open_trades:
            self.client.futures_cancel_all_open_orders(symbol=trade.symbol)
            return True
        else:
            return False

    '''
        Loop that runs constantly and updates the logs for the user when something happens or when a new candle is received
        '''

    def log_trades_loop(self):
        while True:
            self.print_trades_q.get()
            position_information = [position for position in self.client.futures_position_information() if float(position['notional']) != 0.0]
            win_loss = 'Not available yet'
            if self.number_of_losses != 0:
                win_loss = round(self.number_of_wins / self.number_of_losses, 4)
            if len(position_information) != 0:
                info = {'Symbol': [], 'Position Size': [], 'Direction': [], 'Entry Price': [], 'Market Price': [],
                        'TP': [], 'SL': [], 'Distance to TP (%)': [], 'Distance to SL (%)': [], 'PNL': []}
                orders = self.client.futures_get_open_orders()
                open_orders = {f'{str(order["symbol"]) + "_TP"}': float(order['price']) for order in orders if
                               order['reduceOnly'] is True and order['type'] == 'LIMIT'}
                open_orders_SL = {f'{str(order["symbol"]) + "_SL"}': float(order['stopPrice']) for order in orders if
                                  order['origType'] == 'STOP_MARKET'}
                open_orders.update(open_orders_SL)
                for position in position_information:
                    info['Symbol'].append(position['symbol'])
                    info['Position Size'].append(position['positionAmt'])
                    if float(position['notional']) > 0:
                        info['Direction'].append('LONG')
                    else:
                        info['Direction'].append('SHORT')
                    info['Entry Price'].append(position['entryPrice'])
                    info['Market Price'].append(position['markPrice'])
                    try:
                        info['TP'].append(open_orders[f'{position["symbol"]}_TP'])
                        info['Distance to TP (%)'].append(round(abs(((float(info['Market Price'][-1]) - float(
                            info['TP'][-1])) / float(info['Market Price'][-1])) * 100), 3))
                    except:
                        info['TP'].append('Not opened yet')
                        info['Distance to TP (%)'].append('Not available yet')
                    try:
                        info['SL'].append(open_orders[f'{position["symbol"]}_SL'])
                        info['Distance to SL (%)'].append(round(abs(((float(info['Market Price'][-1]) - float(
                            info['SL'][-1])) / float(info['Market Price'][-1])) * 100), 3))
                    except:
                        info['SL'].append('Not opened yet')
                        info['Distance to SL (%)'].append('Not available yet')
                    info['PNL'].append(float(position['unRealizedProfit']))
                log.info(f'Account Balance: ${round(self.get_account_balance(), 3)}, Total profit: ${round(self.total_profit, 3)}, PNL: ${round(sum(info["PNL"]),3)}, Wins: {self.number_of_wins}, Losses: {self.number_of_losses}, Win/Loss ratio: {win_loss}, Open Positions: {len(info["Symbol"])}\n' + tabulate(
                        info, headers='keys', tablefmt='fancy_grid'))
            else:
                log.info(f'Account Balance: ${round(self.get_account_balance(), 3)}, Total profit: ${round(self.total_profit, 3)}, Wins: {self.number_of_wins}, Losses: {self.number_of_losses}, Win/Loss ratio: {win_loss},  No Open Positions')


def start_new_trades_loop_multiprocess(client: Client, new_trades_q, print_trades_q):
    TM = TradeManager(client, new_trades_q, print_trades_q)
    TM.new_trades_loop()