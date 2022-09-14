from pprint import PrettyPrinter
import sys, os
from binance.client import Client
from binance.exceptions import BinanceAPIException
from binance import ThreadedWebsocketManager
from datetime import datetime, date, timedelta
from threading import Thread
from multiprocessing import Process, Pipe
import time

##Local Imports
import Bot_Class
from Helper import Trade_Manager, get_historical, Trade, Trade_Stats, Data_Handler

now = datetime.now()
current_time = now.strftime("%H:%M:%S")
csv_name = f"Logs_{current_time.replace(':','_')}.txt"
DH: [Data_Handler] = []
streams = []  ##store streams allowing the option to start and stop streams if needed
new_candle_flag = 0
Data = {}

## If you are getting a rate limit error on startup this will add a delay for downloading candlesticks to start
RATE_LIMIT_WAIT = False  ## It will not slow down the bot, it will only slow down the startup by about (4 x (number of coins you're trading)) seconds


def listen_pipe(pipe: Pipe):
    global Data, new_candle_flag
    while True:
        Data = pipe.recv()
        new_candle_flag = 1
 

def web_soc_process(pipe: Pipe, twm: ThreadedWebsocketManager):
    global DH, Data, streams
    ##keep process running
    while True:
        ##Check if all coins we are trading have received a new data point
        count = 0
        for data in DH:
            if data.new_data:
                count += 1
            if data.socket_failed:
                try:
                    print(f"Attempting to reset socket for {data.symbol}")
                    twm.stop_socket(streams[data.index])
                    streams[data.index] = twm.start_kline_futures_socket(data.handle_socket_message, symbol=data.symbol)
                    data.socket_failed = False
                    print(f"Reset successful")
                except:
                    print(f"Error in resetting websocket for {data.symbol}")
        ##If they have, Send the updated Data_set to the process handling trading
        if count == len(DH):
            for data in DH:
                data.new_data = False
                Data[data.symbol] = data.next_candle
            pipe.send(Data)


def Check_for_signals(pipe: Pipe, leverage: int, order_Size: float, start_string: str, Interval: str, Max_Number_Of_Trades: int, client: Client,
                      twm: ThreadedWebsocketManager, use_trailing_stop: bool, use_market_orders: bool, trading_threshold: float, trailing_stop_callback: float, symbol: [str], strategy: str,
                      TP_SL_choice: str, SL_mult: float, TP_mult: float):
    global new_candle_flag, Data
    pp = PrettyPrinter()  ## for printing json text cleanly (inspect binance API call returns)
    active_trades: [Trade] = []  ## List of active trades
    new_trades: [[int, [int, float, float]]] = []
    order_Size = round(order_Size/100, 3)
    trading_threshold = round(trading_threshold/100, 3)
    TM = Trade_Manager(client=client, use_trailing_stop=use_trailing_stop, trailing_stop_callback=trailing_stop_callback, use_market=use_market_orders)
    TS = Trade_Stats()
    Bots: [Bot_Class.Bot] = []

    y = client.futures_exchange_info()['symbols']
    coin_info = [[x['pair'], x['pricePrecision'], x['quantityPrecision'], x['filters'][0]['tickSize'], x['filters'][0]['minPrice']] for x in y]

    i = 0
    while i < len(symbol):
        print(f"Starting {symbol[i]} web socket")
        Coin_precision_temp = -99
        Order_precision_temp = -99
        tick_temp = -99
        min_price_temp = -99
        flag = 0
        for x in coin_info:
            if x[0] == symbol[i]:
                print(symbol[i], int(x[2]), int(x[1]))
                Coin_precision_temp = int(x[1])
                Order_precision_temp = int(x[2])
                tick_temp = float(x[3])
                min_price_temp = float(x[4])
                flag = 1
                break
        if flag == 1:
            Bots.append(Bot_Class.Bot(symbol=symbol[i], Open=[], Close=[], High=[], Low=[], Volume=[], Date=[], OP=Order_precision_temp, CP=Coin_precision_temp,
                                      index=i, tick=tick_temp, strategy=strategy, TP_SL_choice=TP_SL_choice, SL_mult=SL_mult, TP_mult=TP_mult))
            i += 1
        else:
            print(f"{symbol.pop(i)} no info found")
            try:
                symbol.pop(i)
                Bots.pop(i)
                twm.stop_socket(streams[i])
                streams.pop(i)
            except:
                pass

    print("Combining Historical and web socket data...")
    i = 0
    while i < len(Bots):
        Date_temp, Open_temp, Close_temp, High_temp, Low_temp, Volume_temp = get_historical(symbol=symbol[i], start_string=start_string, Interval=Interval)
        ##Pop off last candle as it is a duplicate, luki009's suggestion
        Date_temp.pop(-1)
        Open_temp.pop(-1)
        Close_temp.pop(-1)
        High_temp.pop(-1)
        Low_temp.pop(-1)
        Volume_temp.pop(-1)
        if len(Date_temp) < 100:
            print(f"Not enough data for {symbol[i]}, Increase your start_str variable in Config_File so we have a buffer of candles ")
            symbol.pop(i)
            Bots.pop(i)
            streams.pop(i)
        else:
            Bots[i].add_hist(Date_temp=Date_temp, Open_temp=Open_temp, Close_temp=Close_temp, High_temp=High_temp, Low_temp=Low_temp, Volume_temp=Volume_temp)
            i += 1
        if RATE_LIMIT_WAIT:
            time.sleep(2)  ##wait a few second to avoid api rate limit
    print("Finished.")
    AccountBalance = 0
    y = client.futures_account_balance()
    for x in y:
        if x['asset'] == 'USDT':
            AccountBalance = float(x['balance'])
            break
    print("Start Balance:", AccountBalance)

    start = datetime.now().time()
    yesterdate = date.today()
    all_orders = []
    print_flag = 0
    print("Searching for Trade Entries...")
    account_balance = 0
    startup_account_balance = 0
    account_balance_info = client.futures_account_balance()
    for item in account_balance_info:
        if item['asset'] == 'USDT':
            account_balance = float(item['balance'])
            startup_account_balance = float(item['balance'])
            break
    data_thread = Thread(target=listen_pipe, args=(pipe,))  ## thread to listen for new candles
    data_thread.start()
    while True:
        try:
            if new_candle_flag:
                for Bot in Bots:
                    Bot.handle_socket_message(Data[Bot.symbol])
                print_flag = 1
                new_candle_flag = 0

                ##Ensure Bot doesn't interfere with positions opened manually by the user
                open_trades = []
                position_info = client.futures_position_information()
                open_trades = [position['symbol'] for position in position_info if float(position['notional']) != 0.0]

                for i in range(len(Bots)):
                    trade_flag = 0
                    for t in active_trades:
                        if t.index == i:
                            trade_flag = 1
                            break
                    for s in open_trades:
                        if s == Bots[i].symbol:
                            trade_flag = 1
                            break
                    if trade_flag == 0:
                        temp_dec = Bots[i].Make_decision()
                        # print(Data[i].symbol,temp_dec)
                        if temp_dec[0] != -99:
                            new_trades.append([i, temp_dec])  ##[index,[trade_direction,SL,TP]]
            ##Sort out new trades to be opened
            while len(new_trades) > 0 and len(active_trades) < Max_Number_Of_Trades:
                account_balance = 0
                account_balance_info = client.futures_account_balance()
                for item in account_balance_info:
                    if item['asset'] == 'USDT':
                        account_balance = float(item['balance'])
                        break
                [index, [trade_direction, stop_loss, take_profit]] = new_trades.pop(0)

                order_notional = leverage * order_Size * account_balance

                order_id_temp, position_size_temp, entry_price_temp, _ = TM.open_trade(symbol=Bots[index].symbol, trade_direction=trade_direction, order_notional=order_notional,
                                                                  CP=Bots[index].CP, OP=Bots[index].OP, tick_size=Bots[index].tick_size,
                                                                  time=Bots[index].Date[-1], close=Bots[index].Close[-1], trading_threshold=trading_threshold)

                ##Add on the trade which we will later Check on
                if order_id_temp != '':
                    active_trades.append(Trade(index, position_size_temp, take_profit, stop_loss, trade_direction, order_id_temp, Bots[index].symbol))
                    active_trades[-1].entry_price = entry_price_temp
                if len(active_trades) >= Max_Number_Of_Trades:
                    new_trades = []  ##Don't Open any new positions

            ##Clear trades if trade list is full
            if len(active_trades) >= Max_Number_Of_Trades:
                new_trades = []  ##Don't Open any new positions

            rightnow = datetime.now().time()  ##time right now
            timer = timedelta(hours=0, minutes=0, seconds=10)  ##how often to run code below
            if (datetime.combine(date.today(), rightnow) - datetime.combine(yesterdate, start)) > timer:
                start = datetime.now().time()  ##reset start
                yesterdate = date.today()
                all_orders = client.futures_get_all_orders()

                ##Check if we are in a trade set compensation and TPs
                trade_index = 0
                while trade_index < len(active_trades):
                    pop_flag = 0
                    for order in all_orders:
                        if order['symbol'] == active_trades[trade_index].symbol and order['orderId'] == \
                                active_trades[trade_index].order_id and active_trades[trade_index].trade_status == 0 and \
                                order['status'] == 'FILLED':

                            active_trades[trade_index].entry_price = float(client.futures_position_information(symbol=active_trades[trade_index].symbol)[0]['entryPrice'])
                            take_profit_val = 0
                            stop_loss_val = 0
                            if active_trades[trade_index].trade_direction:
                                take_profit_val = active_trades[trade_index].TP_val + active_trades[trade_index].entry_price
                                stop_loss_val = active_trades[trade_index].entry_price - active_trades[trade_index].SL_val
                            else:
                                take_profit_val = active_trades[trade_index].entry_price - active_trades[trade_index].TP_val
                                stop_loss_val = active_trades[trade_index].entry_price + active_trades[trade_index].SL_val

                            ##This position has been opened
                            if active_trades[trade_index].TP_id == '':
                                active_trades[trade_index].TP_id = TM.place_TP(symbol=active_trades[trade_index].symbol, TP=[take_profit_val, active_trades[trade_index].position_size],
                                                                               trade_direction=active_trades[trade_index].trade_direction, CP=Bots[active_trades[trade_index].index].CP,
                                                                               tick_size=Bots[active_trades[trade_index].index].tick_size, time=Bots[trade_index].Date[-1])

                            active_trades[trade_index].SL_id = TM.place_SL(symbol=active_trades[trade_index].symbol, SL=stop_loss_val, trade_direction=active_trades[trade_index].trade_direction,
                                                                           CP=Bots[active_trades[trade_index].index].CP, tick_size=Bots[active_trades[trade_index].index].tick_size, time=Bots[trade_index].Date[-1])
                            active_trades[trade_index].trade_status = 1 ## In a Trade
                            ##Order would trigger immediately so close the position
                            if active_trades[trade_index].SL_id == -1 or active_trades[trade_index].TP_id == -1:
                                TM.close_position(symbol=active_trades[trade_index].symbol,
                                                  trade_direction=active_trades[trade_index].trade_direction,
                                                  total_position_size=active_trades[trade_index].position_size, time=Bots[trade_index].Date[-1])
                                print(f"Closed Trade on {active_trades[trade_index].symbol} as SL OR TP would have thrown a trigger immediately error")
                                pop_flag = 1
                                break

                    if active_trades[trade_index].trade_status == 0 and active_trades[trade_index].waited_time >= active_trades[trade_index].limit_order_wait_time:
                        ## trade hasn't opened yet so check it hasn't gone past threshold
                        order_notional = leverage * order_Size * account_balance
                        _, _, _, active_trades[trade_index].trade_status = TM.open_trade(symbol=active_trades[trade_index].symbol,
                                                                               trade_direction=active_trades[trade_index].trade_direction,
                                                                               order_notional=order_notional,
                                                                               CP=Bots[active_trades[trade_index].index].CP, OP=Bots[active_trades[trade_index].index].OP,
                                                                               tick_size=Bots[active_trades[trade_index].index].tick_size,
                                                                               time=Bots[active_trades[trade_index].index].Date[-1], close=Bots[active_trades[trade_index].index].Close[-1],
                                                                               trading_threshold=trading_threshold, orderID=active_trades[trade_index].order_id,
                                                                               old_entry_price=active_trades[trade_index].entry_price)
                        active_trades[trade_index].waited_time = 0
                        if active_trades[trade_index].trade_status == -99:
                            pop_flag = 1  ## pop off trade as threshold was reached
                    elif active_trades[trade_index].trade_status == 0 and active_trades[trade_index].waited_time < active_trades[trade_index].limit_order_wait_time:
                        active_trades[trade_index].waited_time += 1
                    if pop_flag:
                        active_trades.pop(trade_index)
                    else:
                        trade_index += 1

                ##Check If positions have been closed manually by the user or If trades have hit their TP values or SL value and move SL/Cancel open orders cause the trade is finished
                i = 0
                while i < len(active_trades):
                    position_info = client.futures_position_information(symbol=active_trades[i].symbol)[0]
                    all_orders = client.futures_get_all_orders()
                    if float(position_info['positionAmt']) == 0 and (active_trades[i].trade_status == -99 or active_trades[i].trade_status == 1):
                        try:
                            client.futures_cancel_all_open_orders(symbol=active_trades[i].symbol)  ##Close open orders on that symbol
                        except:
                            pass
                        for order in all_orders:
                            if order['symbol'] == active_trades[i].symbol and order['orderId'] == \
                                    active_trades[i].TP_id and order['status'] == 'FILLED':
                                ##Trading Statistics
                                TS.wins += 1
                                TS.total_number_of_trades += 1
                                account_balance = 0
                                account_balance_info = client.futures_account_balance()
                                for item in account_balance_info:
                                    if item['asset'] == 'USDT':
                                        account_balance = float(item['balance'])
                                        break
                            elif order['symbol'] == active_trades[i].symbol and order['orderId'] == \
                                    active_trades[i].SL_id and order['status'] == 'FILLED':
                                ##Trading Statistics
                                TS.losses += 1
                                TS.total_number_of_trades += 1
                                account_balance = 0
                                account_balance_info = client.futures_account_balance()
                                for item in account_balance_info:
                                    if item['asset'] == 'USDT':
                                        account_balance = float(item['balance'])
                                        break
                        active_trades.pop(i)
                    else:
                        i += 1

            if print_flag:
                account_balance = 0
                account_balance_info = client.futures_account_balance()
                for item in account_balance_info:
                    if item['asset'] == 'USDT':
                        account_balance = float(item['balance'])
                        break
                i = 0
                while i < len(active_trades):
                    if Bots[active_trades[i].index].use_close_pos and not active_trades[i].same_candle:
                        ## Check each interval if the close position was met
                        close_pos = Bots[active_trades[i].index].check_close_pos()
                        if close_pos:
                            TM.close_position(active_trades[i].symbol,
                                              active_trades[i].trade_direction,
                                              active_trades[i].position_size, Bots[active_trades[i].index].Date[-1])
                            close_pos = 0
                            print(f"Closed Trade on {active_trades[i].symbol} as Close Position condition was met")
                            active_trades.pop(i)
                        else:
                            i += 1
                    else:
                        active_trades[i].same_candle = False
                        break
                print_flag = 0
                temp_symbols = [active_trades[t].symbol for t in range(len(active_trades))]
                print(f"Account Balance: {account_balance}, {str(datetime.utcfromtimestamp(round(Bots[0].Date[-1]/1000)))}: Active Trades: {temp_symbols}")
                #Helper.log_info(active_trades, trade_prices, Dates, account_balance, csv_name, indicators)
                try:
                    print(f"wins: {TS.wins}, losses: {TS.losses}, Total Profit: {account_balance - startup_account_balance},"
                          f" Average Trade Profit: ${(account_balance - startup_account_balance) / TS.total_number_of_trades}")
                except:
                    print(
                        f"wins: {TS.wins}, losses: {TS.losses}, Total Profit: {account_balance - startup_account_balance}")


        except BinanceAPIException as e:
            pp.pprint(e)
        except Exception as e:
            print(e)
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)


def run_bot(API_KEY, API_SECRET, leverage, order_Size, buffer, Interval, Max_Number_Of_Trades,
                 use_trailing_stop, trailing_stop_callback, symbol, strategy,
                 TP_choice, SL_choice, SL_mult, TP_mult, Trade_All_Coins, use_market_orders, trading_threshold):
    client = Client(api_key=API_KEY, api_secret=API_SECRET)

    if Trade_All_Coins:
        x = client.futures_ticker()
        symbol = [y['symbol'] for y in x if (('USDT' in y['symbol']) and not('_' in y['symbol']))]

    pp = PrettyPrinter()  ##for printing json text cleanly (inspect binance API call returns)
    twm = ThreadedWebsocketManager(api_key=API_KEY, api_secret=API_SECRET)
    twm.start()  ##start manager

    print("Setting Leverage...")
    i = 0
    while i < len(symbol):
        try:
            client.futures_change_leverage(symbol=symbol[i], leverage=leverage)
            i += 1
        except BinanceAPIException as e:
            if e == 'APIError(code=-4141): Symbol is closed.':
                print(f"Symbol: {symbol[i]}, error: {e}")
                symbol.pop(i)
            else:
                print(f"Error: {e}, removing symbol")
                symbol.pop(i)

    i = 0
    while i < len(symbol):
        try:
            DH.append(Data_Handler(symbol[i], i))
            streams.append(twm.start_kline_futures_socket(callback=DH[i].handle_socket_message, symbol=symbol[i],
                                                          interval=Interval))
            i += 1
        except:
            symbol.pop(i)

    pipe1, pipe2 = Pipe()  ##pipe to communicate between processes
    _thread = Thread(target=web_soc_process, args=(pipe1, twm))
    _thread.start()

    P1 = Process(target=Check_for_signals, args=(pipe2, leverage, order_Size, buffer, Interval, Max_Number_Of_Trades, client, twm, use_trailing_stop, use_market_orders, trading_threshold,
                                                 trailing_stop_callback, symbol, strategy, TP_SL_choice, SL_mult, TP_mult))
    P1.start()
    twm.join()  ##keep websockets running


if __name__ == '__main__':
    ## Still able to run from this script by configuring Config_File.py
    from Config_File import *
    from Config_File import symbol  # explicitly importing to remove a warning

    client = Client(api_key=API_KEY, api_secret=API_SECRET)

    if Trade_All_Coins:
        x = client.futures_ticker()
        symbol = [y['symbol'] for y in x if (('USDT' in y['symbol']) and not ('_' in y['symbol']))]

    pp = PrettyPrinter()  ##for printing json text cleanly (inspect binance API call returns)
    twm = ThreadedWebsocketManager(api_key=API_KEY, api_secret=API_SECRET)
    twm.start()  ##start manager

    print("Setting Leverage...")
    i = 0
    while i < len(symbol):
        try:
            client.futures_change_leverage(symbol=symbol[i], leverage=leverage)
            i += 1
        except BinanceAPIException as e:
            if e == 'APIError(code=-4141): Symbol is closed.':
                print(f"Symbol: {symbol[i]}, error: {e}")
                symbol.pop(i)
            else:
                print(f"Error: {e}, removing symbol")
                symbol.pop(i)

    i = 0
    while i < len(symbol):
        try:
            DH.append(Data_Handler(symbol[i], i))
            streams.append(twm.start_kline_futures_socket(callback=DH[i].handle_socket_message, symbol=symbol[i],
                                                          interval=Interval))
            i += 1
        except:
            symbol.pop(i)

    pipe1, pipe2 = Pipe()  ##pipe to communicate between processes
    _thread = Thread(target=web_soc_process, args=(pipe1, twm))
    _thread.start()

    P1 = Process(target=Check_for_signals, args=(pipe2, leverage, order_Size, buffer, Interval, Max_Number_Of_Trades, client,
                      twm, use_trailing_stop, use_market_orders, trading_threshold, trailing_stop_callback, symbol, strategy,
                      TP_SL_choice, SL_mult, TP_mult))
    P1.start()
    twm.join()  ##keep websockets running
