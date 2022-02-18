import json,pprint
import logging
import sys, os
from binance.client import Client
from binance.exceptions import BinanceAPIException
from binance.enums import *
from binance import ThreadedWebsocketManager
from datetime import timezone,datetime,date,timedelta
import Helper
import API_keys
from threading import Thread
from copy import copy
from multiprocessing import Pool,Process,Value,Pipe

from Christian_Strats import Data_set

def reset_vars():
    entry_price = -99  ##where we entered our original trade
    orderId = ''
    stop_ID = ''
    Take_ID = []
    comp_ID = []
    Start_Account_Balance = -99
    position_Size = 0
    Trading_index = -99
    Trade_Direction = -99
    wait_count = 0
    retry_attempt = 0
    takeprofitval = -99
    stoplossval = -99

    ############# flags ###################
    in_a_trade = 0  ##flag for when we are in a trade
    attempting_a_trade = 0  ##trying to place order flag
    order_placed = 0  ##flag to stop double order executions
    flag = 0
    start = datetime.now().time()  ##for timer
    yesterdate = date.today()  ##for timer

    return entry_price,orderId,stop_ID,Take_ID,comp_ID,Start_Account_Balance,position_Size,Trading_index,Trade_Direction,wait_count,takeprofitval,stoplossval,in_a_trade,attempting_a_trade,order_placed,flag,start,yesterdate,retry_attempt

def Check_for_signals(pipe:Pipe,leverage,order_Size,client:Client,use_trailing_stop,trailing_stop_percent):
    pp = pprint.PrettyPrinter()  ##for printing json text cleanly (inspect binance API call returns)
    Data = []
    entry_price, orderId, stop_ID, Take_ID, comp_ID, Start_Account_Balance, position_Size, \
    Trading_index, Trade_Direction, wait_count, takeprofitval, stoplossval, in_a_trade, \
    attempting_a_trade, order_placed, flag, start, yesterdate, retry_attempt = reset_vars()
    while True:
        try:
            try:

                Data_temp = pipe.recv()  ##where we will receive from our pipe
                if Data_temp != None:
                    Data = copy(Data_temp)
                    flag = 1


                if flag == 1 and not attempting_a_trade:  
                    flag = 0
                    result = []
                    for x in Data:
                        ##each x should return something of the form [Trade_Direction,Stoplossval,Takeprofitval]
                        result.append(x.Make_decision())
              
                    for i in range(len(result)):
                        if result[i][0] != -99:
                            Trading_index = i  ##set trading index so we can open a trade
                            attempting_a_trade = 1
                            Trade_Direction = result[i][0] ##direction of our trade (Short (0) or Long (1))
                            stoplossval = result[i][1]
                            takeprofitval = result[i][2]
                            break

                if attempting_a_trade and not order_placed:
                    try:
                        print(f"{Data[0].Date[-1]}: Attempting to place order on {Data[Trading_index].symbol}")
                        y = client.futures_account_balance()
                        for x in y:
                            if x['asset'] == 'USDT':
                                Start_Account_Balance = float(x['balance'])
                                break
                        order_book = client.futures_order_book(symbol=Data[Trading_index].symbol)
                        bids = order_book['bids']
                        asks = order_book['asks']
                        ##Using Order Book to pick entry price for orders:
                        #Ideas:
                        # (1) Copy the 15th order // (2) Do some kind of weighted Sum // (3) Use the Average of the bids/asks
                        ##I went for (1) but the others are easy to implement (call pp.pprint(order_book) to see its structure)
                        if Trade_Direction == 1:
                            entry_price = float(bids[6][0])
                        elif Trade_Direction == 0:
                            entry_price = float(asks[6][0])
                        
                        
                        if Data[Trading_index].OP != 0:
                            position_Size = round( ((Start_Account_Balance * leverage) * order_Size) / entry_price,Data[Trading_index].OP)  ##Size of Position we are opening
                        else:
                            position_Size = round(((Start_Account_Balance * leverage) * order_Size) / entry_price)  ##Size of Position we are opening

                        if Trade_Direction == 1:
                            if Data[Trading_index].CP!=0:
                                order1 = client.futures_create_order(
                                    symbol=Data[Trading_index].symbol,
                                    side=SIDE_BUY,
                                    type=FUTURE_ORDER_TYPE_LIMIT,
                                    price=round(entry_price, Data[Trading_index].CP),
                                    timeInForce=TIME_IN_FORCE_GTC,
                                    quantity=position_Size)
                                orderId = order1['orderId']
                            else:
                                order1 = client.futures_create_order(
                                    symbol=Data[Trading_index].symbol,
                                    side=SIDE_BUY,
                                    type=FUTURE_ORDER_TYPE_LIMIT,
                                    price=round(entry_price),
                                    timeInForce=TIME_IN_FORCE_GTC,
                                    quantity=position_Size)
                                orderId = order1['orderId']

                        elif Trade_Direction == 0:
                            if Data[Trading_index].CP!=0:
                                order1 = client.futures_create_order(
                                    symbol=Data[Trading_index].symbol,
                                    side=SIDE_SELL,
                                    type=FUTURE_ORDER_TYPE_LIMIT,
                                    price=round(entry_price, Data[Trading_index].CP),
                                    timeInForce=TIME_IN_FORCE_GTC,
                                    quantity=position_Size)
                                orderId = order1['orderId']
                            else:
                                order1 = client.futures_create_order(
                                    symbol=Data[Trading_index].symbol,
                                    side=SIDE_SELL,
                                    type=FUTURE_ORDER_TYPE_LIMIT,
                                    price=round(entry_price),
                                    timeInForce=TIME_IN_FORCE_GTC,
                                    quantity=position_Size)
                                orderId = order1['orderId']
                        order_placed = 1  ##weve sent our order successfully
                        start = datetime.now().time()
                        yesterdate = date.today()
                    except BinanceAPIException as e:
                        print(f"{Data[0].Date[-1]}: Initial order not placed on {Data[Trading_index].symbol}, error: {e}")

                if attempting_a_trade and order_placed:
                    rightnow = datetime.now().time()  ##time right now
                    timer = timedelta(hours=0, minutes=0, seconds=15)  ##how often to run code below
                    if (datetime.combine(date.today(), rightnow) - datetime.combine(yesterdate, start)) > timer:
                        start = datetime.now().time()  ##reset start
                        yesterdate = date.today()

                        if in_a_trade:
                            y = client.futures_position_information(symbol=Data[Trading_index].symbol)[0]
                            position_Amount = float(y['positionAmt'])
                            if position_Amount == 0:
                                client.futures_cancel_all_open_orders(symbol=Data[Trading_index].symbol)

                                entry_price, orderId, stop_ID, Take_ID, comp_ID, Start_Account_Balance, position_Size, \
                                Trading_index, Trade_Direction, wait_count, takeprofitval, stoplossval, in_a_trade, \
                                attempting_a_trade, order_placed, flag, start, yesterdate, retry_attempt = reset_vars()

                                y = client.futures_account_balance()
                                for x in y:
                                    if x['asset'] == 'USDT':
                                        print(f"{Data[0].Date[-1]}: Trade Finished\n"
                                              f"Account Balance: {x['balance']}")
                                        break

                        ##Check if order placed
                        if not in_a_trade and order_placed:
                            if client.futures_get_all_orders(symbol=Data[Trading_index].symbol,orderId=orderId)[0]['status'] == 'FILLED':
                                print(f"Initial Order Successful on {Data[Trading_index].symbol}")
                                try:
                                    ##place stoploss and takeprofits
                                    if Trade_Direction == 1:
                                        if Data[Trading_index].CP != 0:
                                            order2 = client.futures_create_order(
                                                symbol=Data[Trading_index].symbol,
                                                side=SIDE_SELL,
                                                type=FUTURE_ORDER_TYPE_STOP_MARKET,
                                                stopPrice=round(round((entry_price - stoplossval)/Data[Trading_index].tick_size)*Data[Trading_index].tick_size,Data[Trading_index].CP),
                                                reduceOnly='true',
                                                quantity=position_Size)
                                            stop_ID = order2['orderId']
                                            if not use_trailing_stop:
                                                order3 = client.futures_create_order(
                                                    symbol=Data[Trading_index].symbol,
                                                    side=SIDE_SELL,
                                                    type=FUTURE_ORDER_TYPE_LIMIT,
                                                    price=round(round((entry_price + takeprofitval)/Data[Trading_index].tick_size)*Data[Trading_index].tick_size, Data[Trading_index].CP),
                                                    timeInForce=TIME_IN_FORCE_GTC,
                                                    quantity=position_Size)
                                                Take_ID = order3['orderId']
                                            else:
                                                order3 = client.futures_create_order(
                                                    symbol=Data[Trading_index].symbol,
                                                    side=SIDE_SELL,
                                                    type='TRAILING_STOP_MARKET',
                                                    stopPrice=round(round((entry_price + takeprofitval)/Data[Trading_index].tick_size)*Data[Trading_index].tick_size, Data[Trading_index].CP),
                                                    timeInForce=TIME_IN_FORCE_GTC,
                                                    quantity=position_Size,
                                                    callbackRate = trailing_stop_percent)
                                                Take_ID = order3['orderId']
                                        else:
                                            order2 = client.futures_create_order(
                                                symbol=Data[Trading_index].symbol,
                                                side=SIDE_SELL,
                                                type=FUTURE_ORDER_TYPE_STOP_MARKET,
                                                stopPrice=round(round((entry_price - stoplossval)/Data[Trading_index].tick_size)*Data[Trading_index].tick_size),
                                                reduceOnly='true',
                                                quantity=position_Size)
                                            stop_ID = order2['orderId']
                                            if not use_trailing_stop:
                                                order3 = client.futures_create_order(
                                                    symbol=Data[Trading_index].symbol,
                                                    side=SIDE_SELL,
                                                    type=FUTURE_ORDER_TYPE_LIMIT,
                                                    price=round(round((entry_price + takeprofitval)/Data[Trading_index].tick_size)*Data[Trading_index].tick_size),
                                                    timeInForce=TIME_IN_FORCE_GTC,
                                                    quantity=position_Size)
                                                Take_ID = order3['orderId']
                                            else:
                                                order3 = client.futures_create_order(
                                                    symbol=Data[Trading_index].symbol,
                                                    side=SIDE_SELL,
                                                    type='TRAILING_STOP_MARKET',
                                                    stopPrice=round(round((entry_price + takeprofitval)/Data[Trading_index].tick_size)*Data[Trading_index].tick_size),
                                                    timeInForce=TIME_IN_FORCE_GTC,
                                                    quantity=position_Size,
                                                    callbackRate = trailing_stop_percent)
                                                Take_ID = order3['orderId']
                                    elif Trade_Direction == 0:
                                        if Data[Trading_index].CP != 0:
                                            order2 = client.futures_create_order(
                                                symbol=Data[Trading_index].symbol,
                                                side=SIDE_BUY,
                                                type=FUTURE_ORDER_TYPE_STOP_MARKET,
                                                stopPrice=round(round((entry_price + stoplossval)/Data[Trading_index].tick_size)*Data[Trading_index].tick_size, Data[Trading_index].CP),
                                                reduceOnly='true',
                                                quantity=position_Size)
                                            stop_ID = order2['orderId']
                                            if not use_trailing_stop:
                                                order3 = client.futures_create_order(
                                                    symbol=Data[Trading_index].symbol,
                                                    side=SIDE_BUY,
                                                    type=FUTURE_ORDER_TYPE_LIMIT,
                                                    price=round(round((entry_price - takeprofitval)/Data[Trading_index].tick_size)*Data[Trading_index].tick_size, Data[Trading_index].CP),
                                                    timeInForce=TIME_IN_FORCE_GTC,
                                                    quantity=position_Size)
                                                Take_ID = order3['orderId']
                                            else:
                                                order3 = client.futures_create_order(
                                                    symbol=Data[Trading_index].symbol,
                                                    side=SIDE_BUY,
                                                    type='TRAILING_STOP_MARKET',
                                                    stopPrice=round(round((entry_price - takeprofitval)/Data[Trading_index].tick_size)*Data[Trading_index].tick_size, Data[Trading_index].CP),
                                                    timeInForce=TIME_IN_FORCE_GTC,
                                                    quantity=position_Size,
                                                    callbackRate = trailing_stop_percent)
                                                Take_ID = order3['orderId']
                                        else:
                                            order2 = client.futures_create_order(
                                                symbol=Data[Trading_index].symbol,
                                                side=SIDE_BUY,
                                                type=FUTURE_ORDER_TYPE_STOP_MARKET,
                                                stopPrice=round(round((entry_price + stoplossval)/Data[Trading_index].tick_size)*Data[Trading_index].tick_size),
                                                reduceOnly='true',
                                                quantity=position_Size)
                                            stop_ID = order2['orderId']
                                            if not use_trailing_stop:
                                                order3 = client.futures_create_order(
                                                    symbol=Data[Trading_index].symbol,
                                                    side=SIDE_BUY,
                                                    type=FUTURE_ORDER_TYPE_LIMIT,
                                                    price=round(round((entry_price - takeprofitval)/Data[Trading_index].tick_size)*Data[Trading_index].tick_size),
                                                    timeInForce=TIME_IN_FORCE_GTC,
                                                    quantity=position_Size)
                                                Take_ID = order3['orderId']
                                            else:
                                                order3 = client.futures_create_order(
                                                    symbol=Data[Trading_index].symbol,
                                                    side=SIDE_BUY,
                                                    type='TRAILING_STOP_MARKET',
                                                    stopPrice=round(round((entry_price - takeprofitval)/Data[Trading_index].tick_size)*Data[Trading_index].tick_size),
                                                    timeInForce=TIME_IN_FORCE_GTC,
                                                    quantity=position_Size,
                                                    callbackRate = trailing_stop_percent)
                                                Take_ID = order3['orderId']
                                    in_a_trade = 1  ##safely in a trade with our stoploss

                                except BinanceAPIException as e:
                                    print(f"StopLoss/TakeProfit not placed on {Data[Trading_index].symbol}, error: {e}")

                        ##Order placed cancel if takes too long
                        if not in_a_trade and order_placed:
                            if wait_count >= 3 and retry_attempt < 4:
                                if client.futures_get_all_orders(symbol=Data[Trading_index].symbol,orderId=orderId)[0]['status'] != 'FILLED':
                                    print(f"{Data[0].Date[-1]}: Order wasn't placed so retrying")
                                    client.futures_cancel_all_open_orders(symbol=Data[Trading_index].symbol)
                                    order_placed = 0
                                    retry_attempt += 1
                                    wait_count = 0
                                    y = client.futures_account_balance()
                                    for x in y:
                                        if x['asset'] == 'USDT':
                                            print(f"{Data[0].Date[-1]}: Order Didn't Place\n"
                                                  f"Account Balance: {x['balance']}")
                                            break
                            elif wait_count >= 3 and retry_attempt >= 4:
                                print(f"{Data[0].Date[-1]}: Cancelling Order, Tried 4 times to place order.")
                                if client.futures_get_all_orders(symbol=Data[Trading_index].symbol,orderId=orderId)[0]['status'] != 'FILLED':
                                    client.futures_cancel_all_open_orders(symbol=Data[Trading_index].symbol)
                                    entry_price, orderId, stop_ID, Take_ID, comp_ID, Start_Account_Balance, position_Size, \
                                    Trading_index, Trade_Direction, wait_count, takeprofitval, stoplossval, in_a_trade, \
                                    attempting_a_trade, order_placed, flag, start, yesterdate, retry_attempt = reset_vars()
                                    wait_count -= 1  ##offset the addition below
                                    y = client.futures_account_balance()
                                    for x in y:
                                        if x['asset'] == 'USDT':
                                            print(f"{Data[0].Date[-1]}: Order Didn't Place\n"
                                                  f"Account Balance: {x['balance']}")
                                            break
                            wait_count += 1

            except BinanceAPIException as e:
                pp.pprint(e)
        except Exception as e:
            print(e)
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)


def web_soc_process(pipe:Pipe):
    ##keep process running
    while True:
        ##Check if all coins we are trading have received a new data point
        flag = 1
        for x in Data:
            if x.new_data:
                pass
            else:
                flag = 0
                break
        ##If they have Pipe the updated Data_set to the process handling trading
        if flag:
            pipe.send(Data)
            for x in Data:
                x.new_data = 0
        else:
            pipe.send(None)



if __name__ == '__main__':
    ## settings, these are very strategy dependant ensure you have enough data for your chosen strategy
    start_string = '1 hour'  ##buffer of historical data to download before starting the script, valid format: x hour/day/week
    Interval = '1m'  ##Time interval over which we want to trade, valid Intervals: 1m,3m,5m,15m,30m,1h,2h,4h,6h,8h,12h,1d,3d,1w,1M
    leverage = 10  ##leverage we want to use on the account, *Check valid leverages for coins*
    order_Size = .03  ##percent of Effective account to risk ie. (leverage X Account Balance) X order_size
    use_trailing_stop = 0 ##trailing stoploss
    trailing_stop_percent = .01 ## 1% trailing stop
    use_heikin_ashi = 0

    pp = pprint.PrettyPrinter() ##for printing json text cleanly (inspect binance API call returns)
    client = Client(api_key=API_keys.api_key,api_secret=API_keys.api_secret)  ##Binance keys needed to get historical data/ Trade on an account

    y = client.futures_exchange_info()['symbols']
    # client.futures_cancel_order(symbol='NEARUSDT',orderID=5756767805)
    # pp.pprint(y)
    coin_info = []
    for x in y:
        # z = x['filters'][0]
        coin_info.append([x['pair'], x['pricePrecision'], x['quantityPrecision'], x['filters'][0]['tickSize'],
                          x['filters'][0]['minPrice']])
    twm = ThreadedWebsocketManager(api_key=API_keys.api_key, api_secret=API_keys.api_secret) ##handles websockets
    twm.start() ##start manager
    streams = [] ##store streams allowing the option to start and stop streams if needed
    symbol = []
    ### Run on all symbols:
    '''x = client.futures_ticker()  # [0]
    ##get all symbols
    for y in x:
        symbol.append(y['symbol'])
    symbol = [x for x in symbol if 'USDT' in x] ##filter for usdt futures
    symbol = [x for x in symbol if not '_' in x] ##remove invalid symbols'''

    #### Run on select symbols:
    symbol = ['ROSEUSDT','PEOPLEUSDT','LUNAUSDT']

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
    Data = []
    while i < len(symbol):
        print(f"Starting {symbol[i]} web socket")
        # Coin_precision_temp, Order_precision_temp = Helper.get_coin_attrib(symbol[i])
        Coin_precision_temp = -99
        Order_precision_temp = -99
        tick_temp = -99
        min_price_temp = -99
        flag = 0
        for x in coin_info:
            if x[0] == symbol[i]:
                # symbol_temp = x[0]
                Coin_precision_temp = int(x[1])
                Order_precision_temp = int(x[2])
                tick_temp = float(x[3])
                min_price_temp = float(x[4])
                flag = 1
                break
        '''if Coin_precision_temp != -99:
            ##Class for keeping Data_sets'''
        if flag == 1:
            ##Class for keeping Data_sets and executing Strategy
            Data.append(Data_set(symbol[i], [], [], [], [], [], [], Order_precision_temp, Coin_precision_temp, i,use_heikin_ashi,tick_temp))
            streams.append(twm.start_kline_futures_socket(callback=Data[i].handle_socket_message, symbol=Data[i].symbol,
                                                          interval=Interval))
            i += 1
        else:
            print(f"{symbol.pop(i)} no info found")

    print("Combining Historical and web socket data...")
    for i in range(len(Data)):
        Date_temp, Open_temp, Close_temp, High_temp, Low_temp, Volume_temp = Helper.get_historical(symbol[i],start_string,Interval)
        Data[i].add_hist(Date_temp, Open_temp, Close_temp, High_temp, Low_temp, Volume_temp)
    print("Finished.")
    ##Print Account Balance
    AccountBalance = 0
    y = client.futures_account_balance()
    for x in y:
        if x['asset'] == 'USDT':
            AccountBalance = float(x['balance'])
            break
    print("Start Balance:", AccountBalance)

    pipe1, pipe2 = Pipe() ##pipe to communicate between processes

    _thread = Thread(target=web_soc_process,args=(pipe1,)) ##Thread that checks if we have new candle data and then pipes data to our process below
    _thread.start()

    P1 = Process(target=Check_for_signals,args=(pipe2,leverage,order_Size,client,use_trailing_stop,trailing_stop_percent)) ##Process that handles order execution
    P1.start()

    twm.join() ##keep websockets running
