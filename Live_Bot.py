import json, pprint
import sys, os
import pandas as pd
from binance.client import Client
from binance.exceptions import BinanceAPIException
from binance.enums import *
from binance import ThreadedWebsocketManager
from datetime import timezone, datetime, date, timedelta

import API_keys
import github.Helper as Helper
from threading import Thread
from copy import copy
from multiprocessing import Process,Pipe
from github.Bot_Class import Bot


# noinspection PyTypeChecker
class Trade_Maker:
    def __init__(self,client:Client):
        self.client = client
    def open_trade(self, symbol,side,order_qty,OP):
        try:
            try:
                order = ['']
                if OP==0:
                    order_qty=round(order_qty)
                else:
                    order_qty = round(order_qty,OP)

                ##Could Make limit orders but for now the entry is a market
                if side == 0:
                    order = self.client.futures_create_order(
                        symbol=symbol,
                        side=SIDE_SELL,
                        type=FUTURE_ORDER_TYPE_MARKET,
                        quantity=order_qty)

                if side == 1:
                    order = self.client.futures_create_order(
                        symbol=symbol,
                        side=SIDE_BUY,
                        type=FUTURE_ORDER_TYPE_MARKET,
                        quantity=order_qty)

                entry = float(self.client.futures_position_information(symbol=symbol)[0]['entryPrice'])


                return order['orderId'],order_qty,entry

            except BinanceAPIException as e:
                print("Error in open_trade(), Error: ",e)

        except Exception as e:
            print(e)
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)

    def place_TP(self, symbol, TP, side, CP, tick_size):
        try:
            try:
                TP_IDs = []
                TP_val = 0
                for x in TP:
                    if CP == 0:
                        TP_val = round(x[0])
                    else:
                        TP_val = round(round(x[0] / tick_size) * tick_size, CP)
                    if side==1:
                        order = self.client.futures_create_order(
                            symbol=symbol,
                            side=SIDE_SELL,
                            type=FUTURE_ORDER_TYPE_LIMIT,
                            price=TP_val,
                            timeInForce=TIME_IN_FORCE_GTC,
                            quantity=x[1])
                    else:
                        order = self.client.futures_create_order(
                            symbol=symbol,
                            side=SIDE_BUY,
                            type=FUTURE_ORDER_TYPE_LIMIT,
                            price=TP_val,
                            timeInForce=TIME_IN_FORCE_GTC,
                            quantity=x[1])
                    TP_IDs.append(order['orderId'])

                return TP_IDs

            except BinanceAPIException as e:
                print("\nError in place_TP(), Error: ", e)
                print(f"symbol: {symbol} TP: {TP}\n")
        except Exception as e:
            print(e)
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)

    def place_SL(self, symbol, SL, side, CP,tick_size):
        try:
            try:
                if CP==0:
                    SL = round(SL)
                else:
                    SL = round(round(SL/tick_size)*tick_size,CP)
                order_ID = ''
                if side == 1:
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

                return order_ID

            except BinanceAPIException as e:
                print("Error in place_SL(), Error: ", e)
                print(f"symbol: {symbol} SL: {SL}\n")
        except Exception as e:
            print(e)
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)

def Check_for_signals(pipe: Pipe,leverage, order_Size,Max_Margin,client:Client):
    pp = pprint.PrettyPrinter()  ##for printing json text cleanly (inspect binance API call returns)
    active_trades = [] ##[index,position_size,TP_vals,SL_val,trade_direction,order_id,TP_ids,SL_id]
    new_trades = []
    Data = []
    margin_used = 0
    TM = Trade_Maker(client)
    start = datetime.now().time()
    yesterdate = date.today()
    all_trades = []
    print_flag = 0
    print("Searching for Trade Entries...")
    AccountBalance = 0
    y = client.futures_account_balance()
    for x in y:
        if x['asset'] == 'USDT':
            AccountBalance = float(x['balance'])
            break
    while True:
        try:
            try:
                ##Data Comes in
                Data_temp = pipe.recv()  ##where we will receive from our pipe
                if Data_temp != None:
                    print_flag = 1
                    Data = copy(Data_temp)
                    for i in range(len(Data)):
                        trade_flag = 0
                        for x in active_trades:
                            if x[0] == i:
                                trade_flag = 1
                                break
                        if trade_flag == 0 :
                            temp_dec = Data[i].Make_decision()
                            #print(Data[i].symbol,temp_dec)
                            if temp_dec[0]!=-99:
                                new_trades.append([i,temp_dec]) ##[index,[side,SL,TP]]
                ##Sort out new trades to be opened
                while len(new_trades)>0 and margin_used <= Max_Margin*AccountBalance:

                    AccountBalance = 0
                    y = client.futures_account_balance()
                    for x in y:
                        if x['asset'] == 'USDT':
                            AccountBalance = float(x['balance'])
                            break

                    [index, [side,stop_loss,take_profit]] = new_trades.pop(0)
                    order_qty = leverage*order_Size*AccountBalance/Data[index].Close[-1]
                    margin_used += order_Size*AccountBalance
                    order_id_temp,position_size_temp,entry_price_temp = TM.open_trade(Data[index].symbol,side,order_qty,Data[index].OP)
                    take_profit_val = 0
                    stop_loss_val = 0
                    if side:
                        take_profit_val =  take_profit + entry_price_temp
                        stop_loss_val = entry_price_temp - stop_loss
                    else:
                        take_profit_val = entry_price_temp - take_profit
                        stop_loss_val = entry_price_temp + stop_loss
                    ##Add on the trade which we will later Check on
                    ##[ index (0) ,position_size (1) ,TP_vals (2) ,SL val(3) ,trade_direction (4) ,order_id (5) ,TP_ids (6) ,SL_id (7)]
                    ##Could provide multiple TP vals, but default is to sell whole position at specified price

                    active_trades.append([index,position_size_temp,[[take_profit_val,position_size_temp]],stop_loss_val,side,order_id_temp,[],''])
                if margin_used >= Max_Margin*AccountBalance:
                    new_trades = [] ##Don't Open any new positions


                rightnow = datetime.now().time()  ##time right now
                timer = timedelta(hours=0, minutes=0, seconds=15)  ##how often to run code below
                if (datetime.combine(date.today(), rightnow) - datetime.combine(yesterdate, start)) > timer:
                    start = datetime.now().time()  ##reset start
                    yesterdate = date.today()
                    all_trades = client.futures_get_all_orders()

                    ##Check if we are in a trade set compensation and TPs
                    for x in all_trades:
                        for y in active_trades:
                            if x['symbol'] == Data[y[0]].symbol and x['orderId'] == y[5] and y[7]=='' and x['status']=='FILLED':
                                ##This position has been opened
                                y[6] = TM.place_TP(Data[y[0]].symbol,y[2],y[4],Data[y[0]].CP,Data[y[0]].tick_size)
                                y[7] = TM.place_SL(Data[y[0]].symbol,y[3],y[4],Data[y[0]].CP,Data[y[0]].tick_size)
                    ##Check If trades have hit their TP values or SL value and move SL/Cancel open orders cause the trade is finished
                    for x in all_trades:
                        q = 0
                        while q < len(active_trades):
                            flag = 0
                            if x['symbol'] == Data[active_trades[q][0]].symbol and x['orderId'] == active_trades[q][6][0] and x['status']=='FILLED':
                                ##Position Closed so cancel open orders and pop off list
                                client.futures_cancel_all_open_orders(symbol=Data[active_trades[q][0]].symbol)
                                flag = 1 ##position Closed so pop instead of iterating

                            if x['symbol'] == Data[active_trades[q][0]].symbol and x['orderId'] == active_trades[q][7] and x['status']=='FILLED' and flag == 0:
                                ##We've hit our SL so close open orders and pop off list
                                client.futures_cancel_all_open_orders(symbol=Data[active_trades[q][0]].symbol)
                                flag = 1 ##Pop off the list
                                break

                            if flag==1:
                                active_trades.pop(q)
                            else:
                                q+=1

                    ##Update the margin used every 15 seconds, done last to avoid slowing down other orders
                    position_info = client.futures_position_information()
                    margin_used = 0
                    for x in position_info:
                        if float(x['notional']) != 0:
                            if float(x['notional'])<0:
                                margin_used -= float(x['notional']) / leverage
                            else:
                                margin_used += float(x['notional']) / leverage

                if print_flag:
                    print_flag=0
                    temp_symbols=[]
                    for x in active_trades:
                        temp_symbols.append(Data[x[0]].symbol)
                    print(f"{Data[0].Date[-1]}: Active Trades: {temp_symbols}")


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
            for x in Data:
                x.new_data = 0
            pipe.send(Data)
        else:
            pipe.send(None)


if __name__ == '__main__':
    ################## settings, these are very strategy dependant ensure you have enough data for your chosen strategy ##################################
    order_Size = .02
    leverage = 10
    fee = .00036
    start_string = '4 hour ago'
    Interval = '1m' ##candle sticks you want to trade
    Max_Margin = 0  ## Set to zero to hold only a single position at a time, Margin allowed to be used up by opening positions
    use_heikin_ashi = 0 ## Create heikin ashi candles that can be referenced in Bot_Class.Bot.make_decision()

    ######################################################################################################################################################

    pp = pprint.PrettyPrinter()  ##for printing json text cleanly (inspect binance API call returns)
    #client = Client(api_key=API_keys.api_key,api_secret=API_keys.api_secret)  ##Binance keys needed to get historical data/ Trade on an account
    client = Client(api_key=API_keys.api_key, api_secret=API_keys.api_secret)#, requests_params={"timeout": '20'})
    y = client.futures_exchange_info()['symbols']
    coin_info = []
    for x in y:
        # z = x['filters'][0]
        coin_info.append([x['pair'], x['pricePrecision'], x['quantityPrecision'], x['filters'][0]['tickSize'],
                          x['filters'][0]['minPrice']])

    # twm = ThreadedWebsocketManager(api_key=API_keys.api_key, api_secret=API_keys.api_secret)  ##handles websockets
    twm = ThreadedWebsocketManager(api_key=API_keys.api_key, api_secret=API_keys.api_secret)
    twm.start()  ##start manager
    streams = []  ##store streams allowing the option to start and stop streams if needed

    ##Trade All Coins Default, can also specify a list of coins to trade instead. Example: symbol = ['ETHUSDT','BTCUSDT']
    symbol = []
    x = client.futures_ticker()  # [0]
    for y in x:
        symbol.append(y['symbol'])
    symbol = [x for x in symbol if 'USDT' in x]
    symbol = [x for x in symbol if not '_' in x]

    # print(len(symbol))
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
        if flag == 1:
            Data.append(Bot(symbol[i], [], [], [], [], [], [],  Order_precision_temp, Coin_precision_temp,  i, use_heikin_ashi, tick=tick_temp))
            streams.append(twm.start_kline_futures_socket(callback=Data[i].handle_socket_message, symbol=Data[i].symbol,interval=Interval))
            i += 1
        else:
            print(f"{symbol.pop(i)} no info found")

    print("Combining Historical and web socket data...")
    i = 0
    while i < len(Data):
        Date_temp, Open_temp, Close_temp, High_temp, Low_temp, Volume_temp = Helper.get_historical(symbol[i],start_string,Interval)
        if len(Date_temp) < 100:
            print(f"Not enough data for {symbol[i]} ")
            symbol.pop(i)
            Data.pop(i)
            twm.stop_socket(streams[i])
        else:
            Data[i].add_hist(Date_temp, Open_temp, Close_temp, High_temp, Low_temp, Volume_temp)
            i += 1
    print("Finished.")
    ##Print Account Balance
    AccountBalance = 0
    y = client.futures_account_balance()
    for x in y:
        if x['asset'] == 'USDT':
            AccountBalance = float(x['balance'])
            break
    print("Start Balance:", AccountBalance)

    pipe1, pipe2 = Pipe()  ##pipe to communicate between processes
    for x in Data:
        x.new_data = 0
    _thread = Thread(target=web_soc_process, args=(pipe1,))
    _thread.start()

    P1 = Process(target=Check_for_signals, args=(pipe2, leverage, order_Size,Max_Margin,client,))
    P1.start()
    twm.join()  ##keep websockets running