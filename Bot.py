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

from multiprocessing import Pool,Process,Value,Pipe

from Data_Set import Data_set


def Check_for_signals(pipe,leverage,order_Size):
    client_trade = Client(api_key=API_keys.api_key,api_secret=API_keys.api_secret)

    ############## Vars used to keep track of orders ###################
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
    takeprofitval = -99
    stoplossval = -99

    ############# flags ###################
    in_a_trade = 0  ##flag for when we are in a trade
    attempting_a_trade = 0  ##trying to place order flag
    order_placed = 0  ##flag to stop double order executions
    flag = 0

    start = datetime.now().time()  ##for timer
    yesterdate = date.today()  ##for timer

    while True:
        try:
            try:

                Data = pipe.recv() ##where we will receive from our pipe
                if Data!=None:
                    flag = 1


                if flag == 1 and not attempting_a_trade:  
                    flag = 0
                    result = []
                    for x in Data:
                        ##each x should be of the form [Trade_Direction,Stoplossval,Takeprofitval]
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
                        print(f"{Data[Trading_index].Date[-1]}: Attempting to place order on {Data[Trading_index].symbol}")
                        y = client_trade.futures_account_balance()
                        for x in y:
                            if x['asset'] == 'USDT':
                                Start_Account_Balance = float(x['balance'])
                                break
                        order_book = client_trade.futures_order_book(symbol=Data[Trading_index].symbol)
                        bids = order_book['bids']
                        asks = order_book['asks']
                        ##Using Order Book to pick entry price for orders:
                        #Ideas:
                        # (1) Copy the 15th order // (2) Do some kind of weighted Sum // (3) Use the Average of the bids/asks
                        ##I went for (1) but the others are easy to implement (call pp.pprint(order_book) to see its structure)
                        if Trade_Direction == 1:
                            entry_price = float(bids[15][0])
                        elif Trade_Direction == 0:
                            entry_price = float(asks[15][0])
                        
                        
                        if Data[Trading_index].OP != 0:
                            position_Size = round( ((Start_Account_Balance * leverage) * order_Size) / entry_price,Data[Trading_index].OP)  ##Size of Position we are opening
                        else:
                            position_Size = round(((Start_Account_Balance * leverage) * order_Size) / entry_price)  ##Size of Position we are opening

                        if Trade_Direction == 1:
                            if Data[Trading_index].CP!=0:
                                order1 = client_trade.futures_create_order(
                                    symbol=Data[Trading_index].symbol,
                                    side=SIDE_BUY,
                                    type=FUTURE_ORDER_TYPE_LIMIT,
                                    price=round(entry_price, Data[Trading_index].CP),
                                    timeInForce=TIME_IN_FORCE_GTC,
                                    quantity=position_Size)
                                orderId = order1['orderId']
                            else:
                                order1 = client_trade.futures_create_order(
                                    symbol=Data[Trading_index].symbol,
                                    side=SIDE_BUY,
                                    type=FUTURE_ORDER_TYPE_LIMIT,
                                    price=round(entry_price),
                                    timeInForce=TIME_IN_FORCE_GTC,
                                    quantity=position_Size)
                                orderId = order1['orderId']

                        elif Trade_Direction == 0:
                            if Data[Trading_index].CP!=0: 
                                order1 = client_trade.futures_create_order(
                                    symbol=Data[Trading_index].symbol,
                                    side=SIDE_SELL,
                                    type=FUTURE_ORDER_TYPE_LIMIT,
                                    price=round(entry_price, Data[Trading_index].CP),
                                    timeInForce=TIME_IN_FORCE_GTC,
                                    quantity=position_Size)
                                orderId = order1['orderId']
                            else:
                                order1 = client_trade.futures_create_order(
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
                        print(f"{Data[Trading_index].Date[-1]}: Initial order not placed on {Data[Trading_index].symbol}, error: {e}")

                if attempting_a_trade and order_placed:
                    rightnow = datetime.now().time()  ##time right now
                    timer = timedelta(hours=0, minutes=0, seconds=15)  ##how often to run code below
                    if (datetime.combine(date.today(), rightnow) - datetime.combine(yesterdate, start)) > timer:
                        start = datetime.now().time()  ##reset start
                        yesterdate = date.today()

                        if in_a_trade:
                            y = client_trade.futures_position_information(symbol=Data[Trading_index].symbol)[0]
                            position_Amount = float(y['positionAmt'])
                            if position_Amount == 0:
                                client_trade.futures_cancel_all_open_orders(symbol=Data[Trading_index].symbol)
                                ############## Vars used to keep track of orders ###################
                                entry_price = -99  ##where we entered our original trade
                                orderId = ''
                                stop_ID = ''
                                Take_ID = ''
                                Start_Account_Balance = -99
                                position_Size = 0
                                Trading_index = -99
                                Trade_Direction = -99
                                wait_count = 0
                                takeprofitval = -99
                                stoplossval = -99

                                ############# flags ###################
                                in_a_trade = 0  ##flag for when we are in a trade
                                attempting_a_trade = 0  ##trying to place order flag
                                order_placed = 0  ##flag to stop double order executions
                                flag = 0

                                start = datetime.now().time()  ##for timer
                                yesterdate = date.today()  ##for timer

                                y = client_trade.futures_account_balance()
                                for x in y:
                                    if x['asset'] == 'USDT':
                                        print(f"{Data[Trading_index].Date[-1]}: Trade Finished\n"
                                              f"Account Balance: {x['balance']}")
                                        break

                        ##Check if order placed
                        if not in_a_trade:
                            if client_trade.futures_get_all_orders(symbol=Data[Trading_index].symbol,orderId=orderId)[0]['status'] != 'FILLED':
                                print(f"Initial Order Successful on {Data[Trading_index].symbol}")
                                try:
                                    ##place stoploss and takeprofits
                                    if Trade_Direction == 1:
                                        if Data[Trading_index].CP != 0:
                                            order2 = client_trade.futures_create_order(
                                                symbol=Data[Trading_index].symbol,
                                                side=SIDE_SELL,
                                                type=FUTURE_ORDER_TYPE_STOP_MARKET,
                                                stopPrice=round(entry_price - stoplossval,Data[Trading_index].CP),
                                                reduceOnly='true',
                                                quantity=position_Size)
                                            stop_ID = order2['orderId']
    
                                            order3 = client_trade.futures_create_order(
                                                symbol=Data[Trading_index].symbol,
                                                side=SIDE_SELL,
                                                type=FUTURE_ORDER_TYPE_LIMIT,
                                                price=round(entry_price + takeprofitval, Data[Trading_index].CP),
                                                timeInForce=TIME_IN_FORCE_GTC,
                                                quantity=position_Size)
                                            Take_ID = order3['orderId']
                                        else:
                                            order2 = client_trade.futures_create_order(
                                                symbol=Data[Trading_index].symbol,
                                                side=SIDE_SELL,
                                                type=FUTURE_ORDER_TYPE_STOP_MARKET,
                                                stopPrice=round(entry_price - stoplossval),
                                                reduceOnly='true',
                                                quantity=position_Size)
                                            stop_ID = order2['orderId']

                                            order3 = client_trade.futures_create_order(
                                                symbol=Data[Trading_index].symbol,
                                                side=SIDE_SELL,
                                                type=FUTURE_ORDER_TYPE_LIMIT,
                                                price=round(entry_price + takeprofitval),
                                                timeInForce=TIME_IN_FORCE_GTC,
                                                quantity=position_Size)
                                            Take_ID = order3['orderId']

                                    elif Trade_Direction == 0:
                                        if Data[Trading_index].CP != 0:
                                            order2 = client_trade.futures_create_order(
                                                symbol=Data[Trading_index].symbol,
                                                side=SIDE_BUY,
                                                type=FUTURE_ORDER_TYPE_STOP_MARKET,
                                                stopPrice=round(entry_price + stoplossval, Data[Trading_index].CP),
                                                reduceOnly='true',
                                                quantity=position_Size)
                                            stop_ID = order2['orderId']
    
                                            order3 = client_trade.futures_create_order(
                                                symbol=Data[Trading_index].symbol,
                                                side=SIDE_BUY,
                                                type=FUTURE_ORDER_TYPE_LIMIT,
                                                price=round(entry_price - takeprofitval, Data[Trading_index].CP),
                                                timeInForce=TIME_IN_FORCE_GTC,
                                                quantity=position_Size)
                                            Take_ID = order3['orderId']
                                        else:
                                            order2 = client_trade.futures_create_order(
                                                symbol=Data[Trading_index].symbol,
                                                side=SIDE_BUY,
                                                type=FUTURE_ORDER_TYPE_STOP_MARKET,
                                                stopPrice=round(entry_price + stoplossval),
                                                reduceOnly='true',
                                                quantity=position_Size)
                                            stop_ID = order2['orderId']

                                            order3 = client_trade.futures_create_order(
                                                symbol=Data[Trading_index].symbol,
                                                side=SIDE_BUY,
                                                type=FUTURE_ORDER_TYPE_LIMIT,
                                                price=round(entry_price - takeprofitval),
                                                timeInForce=TIME_IN_FORCE_GTC,
                                                quantity=position_Size)
                                            Take_ID = order3['orderId']
                                    in_a_trade = 1  ##safely in a trade with our stoploss

                                except BinanceAPIException as e:
                                    print(f"StopLoss/TakeProfit not placed on {Data[Trading_index].symbol}, error: {e}")

                        ##Order placed cancel if takes too long
                        if not in_a_trade:  ################################################################ deadlock
                            wait_count += 1
                            if wait_count >= 3:
                                print("Order wasn't placed in 45 seconds so cancelling")
                                client_trade.futures_cancel_all_open_orders(symbol=Data[Trading_index].symbol)
                                ############## Vars used to keep track of orders ###################
                                entry_price = -99  ##where we entered our original trade
                                orderId = ''
                                stop_ID = ''
                                Take_ID = ''
                                Start_Account_Balance = -99
                                position_Size = 0
                                Trading_index = -99
                                Trade_Direction = -99
                                wait_count = 0
                                takeprofitval = -99
                                stoplossval = -99

                                ############# flags ###################
                                in_a_trade = 0  ##flag for when we are in a trade
                                attempting_a_trade = 0  ##trying to place order flag
                                order_placed = 0  ##flag to stop double order executions
                                flag = 0

                                start = datetime.now().time()  ##for timer
                                yesterdate = date.today()  ##for timer

                                y = client_trade.futures_account_balance()
                                for x in y:
                                    if x['asset'] == 'USDT':
                                        print(f"{Data[Trading_index].Date[-1]}: Trade Timer Up\n"
                                              f"Account Balance: {x['balance']}")
                                        break

            except BinanceAPIException as e:
                pp.pprint(e)
        except Exception as e:
            print(e)
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)


def web_soc_process(pipe):
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


    pp = pprint.PrettyPrinter() ##for printing json text cleanly (inspect binance API call returns)
    client = Client(api_key=API_keys.api_key,api_secret=API_keys.api_secret)  ##Binance keys needed to get historical data/ Trade on an account

    ##list of all coins at current time
    symbol = ['RAYUSDT', 'NEARUSDT', 'AUDIOUSDT', 'HNTUSDT', 'DGBUSDT', 'ZRXUSDT', 'BCHUSDT', 'HOTUSDT', 'ARUSDT',
              'FLMUSDT', 'SFPUSDT', 'BELUSDT', 'RENUSDT', 'ADAUSDT', 'STORJUSDT', 'BZRXUSDT', 'CHRUSDT', 'WAVESUSDT',
              'CHZUSDT', 'XRPUSDT','SANDUSDT', 'OCEANUSDT', 'ENJUSDT', 'YFIIUSDT', 'GRTUSDT', 'UNIUSDT', 'TLMUSDT',
              'XTZUSDT', 'LUNAUSDT','EOSUSDT','SKLUSDT', 'GTCUSDT', 'DOTUSDT', '1INCHUSDT', 'UNFIUSDT', 'FTMUSDT',
              'RLCUSDT', 'ATOMUSDT', 'BLZUSDT','SNXUSDT','SOLUSDT', 'ETCUSDT', 'BNBUSDT', 'CELRUSDT', 'OGNUSDT',
              'ETHUSDT', 'NEOUSDT', 'TOMOUSDT', 'CELOUSDT','KLAYUSDT','TRBUSDT', 'TRXUSDT', 'EGLDUSDT', 'CRVUSDT',
              'BAKEUSDT', 'NUUSDT', 'SRMUSDT', 'ALICEUSDT', 'CTKUSDT','ARPAUSDT','MATICUSDT', 'IOTXUSDT', 'DENTUSDT',
              'IOSTUSDT', 'OMGUSDT', 'BANDUSDT', 'BTCUSDT', 'NKNUSDT', 'RSRUSDT','IOTAUSDT','CVCUSDT', 'REEFUSDT',
              'BTSUSDT', 'BTTUSDT', 'ONEUSDT', 'ANKRUSDT', 'SUSHIUSDT', 'ALGOUSDT', 'SCUSDT','ONTUSDT','MANAUSDT',
              'ATAUSDT', 'MKRUSDT', 'DODOUSDT', 'LITUSDT', 'ICPUSDT', 'ZECUSDT', 'ICXUSDT', 'ZENUSDT','DOGEUSDT',
              'ALPHAUSDT', 'SXPUSDT', 'HBARUSDT', 'RVNUSDT', 'CTSIUSDT', 'KAVAUSDT', 'C98USDT', 'THETAUSDT', 'MASKUSDT',
              'AAVEUSDT','YFIUSDT', 'AXSUSDT', 'ZILUSDT', 'XEMUSDT', 'COMPUSDT', 'RUNEUSDT', 'AVAXUSDT', 'KNCUSDT',
              'LPTUSDT','LRCUSDT','MTLUSDT', 'VETUSDT', 'DASHUSDT', 'KEEPUSDT', 'LTCUSDT', 'DYDXUSDT', 'LINAUSDT',
              'XLMUSDT', 'LINKUSDT','QTUMUSDT','KSMUSDT', 'FILUSDT', 'STMXUSDT',
              'BALUSDT', 'GALAUSDT', 'BATUSDT', 'AKROUSDT', 'XMRUSDT', 'COTIUSDT']

    twm = ThreadedWebsocketManager(api_key=API_keys.api_key, api_secret=API_keys.api_secret) ##handles websockets
    twm.start() ##start manager
    streams = [] ##store streams allowing the option to start and stop streams if needed
    print(f"Coins Tradeable : {symbol}")

    i=0
    Data = []
    while i < len(symbol):
        print(f"Starting {symbol[i]} web socket")
        Coin_precision_temp, Order_precision_temp = Helper.get_coin_attrib(symbol[i])

        if Coin_precision_temp != -99:
            ##Class for keeping Data_sets
            Data.append(Data_set(symbol[i], [], [], [], [], [], [], Order_precision_temp, Coin_precision_temp, i))
            streams.append(twm.start_kline_futures_socket(callback=Data[i].handle_socket_message, symbol=Data[i].symbol,interval=Interval))
            i += 1
        else:
            print(f"Removing {symbol[i]} as you need to add the coin in Helper.py -> get_coin_attrib() or check the coin information is valid")
            symbol.pop(i)  ##not enough data available so remove symbol
    print("Setting Leverage...")
    for x in symbol:
        client.futures_change_leverage(symbol=x,leverage=leverage)
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

    _thread = Thread(target=web_soc_process,args=(pipe1,))
    _thread.start()

    P1 = Process(target=Check_for_signals,args=(pipe2,leverage,order_Size))
    P1.start()

    twm.join() ##keep websockets running
