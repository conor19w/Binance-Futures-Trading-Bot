from pprint import PrettyPrinter
import sys, os
from binance.client import Client
from binance.exceptions import BinanceAPIException
from binance import ThreadedWebsocketManager
from datetime import datetime, date, timedelta
from threading import Thread
from multiprocessing import Process,Pipe
import time
##Local Imports
from Helper import Trade_Maker,get_historical,Trade,Trade_Stats
from Bot_Class import Bot
from Config_File import *

Data:[Bot] = []
new_candle_flag = 0

def listen_pipe(pipe:Pipe):
    global Data, new_candle_flag
    while True:
        Data = pipe.recv()
        new_candle_flag = 1

def web_soc_process(pipe:Pipe):
    global Data, new_candle_flag
    ##keep process running
    while True:
        ##Check if all coins we are trading have received a new data point
        count = 0
        for x in Data:
            if x.new_data:
                count += 1
        ##If they have, Send the updated Data_set to the process handling trading
        if count > len(Data) * .9:
            for x in Data:
                x.new_data = 0
            pipe.send(Data)


def Check_for_signals(pipe: Pipe,leverage, order_Size,Max_Margin,client:Client,use_trailing_stop,trailing_stop_callback):
    global Data, new_candle_flag
    pp = PrettyPrinter()  ## for printing json text cleanly (inspect binance API call returns)
    active_trades:[Trade] = [] ## List of active trades
    new_trades = []
    Data = []
    margin_used = 0
    TM = Trade_Maker(client,use_trailing_stop,trailing_stop_callback)
    TS = Trade_Stats()
    start = datetime.now().time()
    yesterdate = date.today()
    all_orders = []
    print_flag = 0
    print("Searching for Trade Entries...")
    account_balance = 0
    account_balance_info = client.futures_account_balance()
    for item in account_balance_info:
        if item['asset'] == 'USDT':
            account_balance = float(item['balance'])
            break
    data_thread = Thread(target=listen_pipe, args=(pipe,))  ## thread to listen for new candles
    data_thread.start()
    while True:
        try:
            try:
                if new_candle_flag:
                    print_flag = 1
                    new_candle_flag = 0
                    for i in range(len(Data)):
                        trade_flag = 0
                        for t in active_trades:
                            if t.index == i:
                                trade_flag = 1
                                break
                        if trade_flag == 0 :
                            temp_dec = Data[i].Make_decision()
                            #print(Data[i].symbol,temp_dec)
                            if temp_dec[0]!=-99:
                                new_trades.append([i,temp_dec]) ##[index,[trade_direction,SL,TP]]
                ##Sort out new trades to be opened
                while len(new_trades)>0 and margin_used <= Max_Margin*account_balance:

                    account_balance = 0
                    start_account_balance = 0
                    account_balance_info = client.futures_account_balance()
                    for item in account_balance_info:
                        if item['asset'] == 'USDT':
                            account_balance = float(item['balance'])
                            start_account_balance = float(item['balance'])
                            break
                    [index, [trade_direction,stop_loss,take_profit]] = new_trades.pop(0)
                    order_qty = leverage*order_Size*account_balance/Data[index].Close[-1]
                    margin_used += order_Size*account_balance
                    order_id_temp,position_size_temp,entry_price_temp = TM.open_trade(Data[index].symbol,trade_direction,order_qty,Data[index].OP)
                    take_profit_val = 0
                    stop_loss_val = 0
                    if trade_direction:
                        take_profit_val =  take_profit + entry_price_temp
                        stop_loss_val = entry_price_temp - stop_loss
                    else:
                        take_profit_val = entry_price_temp - take_profit
                        stop_loss_val = entry_price_temp + stop_loss
                    ##Add on the trade which we will later Check on
                    active_trades.append(Trade(index,position_size_temp,[take_profit_val,position_size_temp],stop_loss_val,trade_direction,order_id_temp,Data[index].symbol,start_account_balance))
                if margin_used >= Max_Margin*account_balance:
                    new_trades = [] ##Don't Open any new positions


                rightnow = datetime.now().time()  ##time right now
                timer = timedelta(hours=0, minutes=0, seconds=15)  ##how often to run code below
                if (datetime.combine(date.today(), rightnow) - datetime.combine(yesterdate, start)) > timer:
                    start = datetime.now().time()  ##reset start
                    yesterdate = date.today()
                    all_orders = client.futures_get_all_orders()

                    ##Check if we are in a trade set compensation and TPs
                    for order in all_orders:
                        for t in active_trades:
                            if order['symbol'] == t.symbol and order['orderId'] == t.order_id and t.SL_id=='' and order['status']=='FILLED':
                                ##This position has been opened
                                t.TP_id = TM.place_TP(t.symbol,t.TP_vals,t.trade_direction,Data[t.index].CP,Data[t.index].tick_size)
                                t.SL_id = TM.place_SL(t.symbol,t.SL_val,t.trade_direction,Data[t.index].CP,Data[t.index].tick_size)
                    ##Check If trades have hit their TP values or SL value and move SL/Cancel open orders cause the trade is finished
                    for order in all_orders:
                        trade_index = 0
                        while trade_index < len(active_trades):
                            flag = 0
                            if order['symbol'] == active_trades[trade_index].symbol and order['orderId'] == active_trades[trade_index].TP_id and order['status']=='FILLED':
                                ##Trading Statisti
                                TS.wins+=1
                                TS.total_number_of_trades+=1
                                account_balance = 0
                                account_balance_info = client.futures_account_balance()
                                for item in account_balance_info:
                                    if item['asset'] == 'USDT':
                                        account_balance = float(item['balance'])
                                        break
                                TS.total_profit += (account_balance - active_trades[trade_index].start_account_balance)
                                ##Position Closed so cancel open orders and pop off list
                                client.futures_cancel_all_open_orders(symbol=active_trades[trade_index].symbol)

                                flag = 1 ##position Closed so pop instead of iterating

                            if order['symbol'] == active_trades[trade_index].symbol and order['orderId'] == active_trades[trade_index].SL_id and order['status']=='FILLED' and flag == 0:
                                ##Trading Statistics
                                TS.losses+=1
                                TS.total_number_of_trades += 1
                                account_balance = 0
                                account_balance_info = client.futures_account_balance()
                                for item in account_balance_info:
                                    if item['asset'] == 'USDT':
                                        account_balance = float(item['balance'])
                                        break
                                TS.total_profit += (account_balance - active_trades[trade_index].start_account_balance)

                                ##We've hit our SL so close open orders and pop off list
                                client.futures_cancel_all_open_orders(symbol=active_trades[trade_index].symbol)
                                flag = 1 ##Pop off the list

                            if flag==1:
                                active_trades.pop(trade_index)
                            else:
                                trade_index+=1

                    ##Update the margin used every 15 seconds, done last to avoid slowing down other orders
                    position_info = client.futures_position_information()
                    margin_used = 0
                    for item in position_info:
                        if float(item['notional']) != 0:
                            if float(item['notional'])<0:
                                margin_used -= float(item['notional']) / leverage
                            else:
                                margin_used += float(item['notional']) / leverage

                if print_flag:
                    print_flag=0
                    temp_symbols=[]
                    for t in active_trades:
                        temp_symbols.append(t.symbol)
                    print(f"Account Balance: {account_balance}, {Data[0].Date[-1]}: Active Trades: {temp_symbols}")
                    try:
                        print(f"wins: {TS.wins}, losses: {TS.losses}, Total Profit: {TS.total_profit}, Average Trade Profit: ${TS.total_profit/TS.total_number_of_trades}")
                    except:
                        print(f"wins: {TS.wins}, losses: {TS.losses}, Total Profit: {TS.total_profit}")


            except BinanceAPIException as e:
                pp.pprint(e)
        except Exception as e:
            print(e)
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)


if __name__ == '__main__':
    pp = PrettyPrinter()  ##for printing json text cleanly (inspect binance API call returns)
    #client = Client(api_key=API_keys.api_key,api_secret=API_keys.api_secret)  ##Binance keys needed to get historical data/ Trade on an account
    client = Client(api_key=api_key, api_secret=api_secret)#, requests_params={"timeout": '20'})
    y = client.futures_exchange_info()['symbols']
    coin_info = []
    for x in y:
        # z = x['filters'][0]
        coin_info.append([x['pair'], x['pricePrecision'], x['quantityPrecision'], x['filters'][0]['tickSize'],
                          x['filters'][0]['minPrice']])

    # twm = ThreadedWebsocketManager(api_key=API_keys.api_key, api_secret=API_keys.api_secret)  ##handles websockets
    twm = ThreadedWebsocketManager(api_key=api_key, api_secret=api_secret)
    twm.start()  ##start manager
    streams = []  ##store streams allowing the option to start and stop streams if needed


    if Trade_All_Coins:
        symbol = []
        ##Trade All Coins Default, can also specify a list of coins to trade instead. Example: symbol = ['ETHUSDT','BTCUSDT']
        x = client.futures_ticker()  # [0]
        for y in x:
            symbol.append(y['symbol'])
        symbol = [x for x in symbol if 'USDT' in x]
        symbol = [x for x in symbol if not '_' in x]

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
        print(f"Starting {symbol[i]} web socket")
        Coin_precision_temp = -99
        Order_precision_temp = -99
        tick_temp = -99
        min_price_temp = -99
        flag = 0
        for x in coin_info:
            if x[0] == symbol[i]:
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
        Date_temp, Open_temp, Close_temp, High_temp, Low_temp, Volume_temp = get_historical(symbol[i],start_string,Interval)
        ##Pop off last candle as it is a duplicate, luki009's suggestion
        Date_temp.pop(-1)
        Open_temp.pop(-1)
        Close_temp.pop(-1)
        High_temp.pop(-1)
        Low_temp.pop(-1)
        Volume_temp.pop(-1)
        if len(Date_temp) < 100:
            print(f"Not enough data for {symbol[i]} ")
            symbol.pop(i)
            Data.pop(i)
            twm.stop_socket(streams[i])
        else:
            Data[i].add_hist(Date_temp, Open_temp, Close_temp, High_temp, Low_temp, Volume_temp)
            i += 1
        if RATE_LIMIT_WAIT:
            time.sleep(4)  ##wait a few second to avoid api rate limit
    print("Finished.")
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

    P1 = Process(target=Check_for_signals, args=(pipe2, leverage, order_Size,Max_Margin,client,use_trailing_stop,trailing_stop_callback))
    P1.start()
    twm.join()  ##keep websockets running
