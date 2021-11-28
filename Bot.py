import math
from collections import deque
import json,pprint
import asyncio
import time
from joblib import load, dump
import websockets
import Data_flow as flow
import sys, os
from binance.client import Client
import matplotlib.pyplot as plt
from copy import copy
import TradingStrats as TS
from TradingStrats import SetSLTP
from binance.exceptions import BinanceAPIException
from binance.enums import *
from binance import ThreadedWebsocketManager,AsyncClient
import pandas as pd
import numpy as np
from datetime import timezone,datetime,date,timedelta
import Helper
import API_keys
#import personal_strats as PS
import download_Data as DD
Coin_precision = -99  ##Precision Coin is measured up to
Order_precision = -99 ##Precision Orders are measured up to

#data.reset_index(level=0, inplace=True)
trades = deque(maxlen=100000) ##keep track of shorts/Longs for graphing
cashout = deque(maxlen=100000) ##keep track of Winning trades/ Losing trades
signals= deque(maxlen=100000) ##when a siganl occured , NOT IN USE
Open=[]
High=[]
Low=[]
Close=[]
Volume=[]
Date=[]
OpenStream=[]
HighStream=[]
LowStream=[]
CloseStream=[]
VolumeStream=[]
DateStream = []
Profit=0 ##Keep track of profit by flipping a single coin
CurrentPos=-99 ##0 for short , 1 for Long
positionPrice=0 ##Positions entry Price
stoplossval = 1000 ##stoploss this is set by each individual strategy in TradingStrats.py
correct=0 ##winning trades
Highestprice=0
trailing_stoploss=.2 ##not used
profitgraph=[] #for graphing the profit change over time
pp = pprint.PrettyPrinter()
#profitgraphy=[0]
Sleep=0
#print(symbol)
#print(30)
client = Client(api_key=API_keys.api_key,api_secret=API_keys.api_secret) ##Binance keys needed to get historical data/ Trade on an account
twm = ThreadedWebsocketManager(api_key=API_keys.api_key,api_secret=API_keys.api_secret)
twm.start()

#OrderSize = 100
tradeNO=0 ##number of trades
######### variables used for trading Strats
signal =-99
stoplossval=0
takeprofitval=0
signal1=-99
signal2=-99
prediction=-99
HighestUlt=50
Highestval=-99
PrevPos=-999
prevsignal1=-999
prevsignal2=-999
prediction2=-99
Highest=-999



AccountBalance=-99 ##Start amount for paper trading
EffectiveAccountBalance = -99
positionSize = 0 ##altered later and sent as the orderQTY
Stop_ID=''
Limit_ID=''
Order_ID=''
current_date = datetime.now(timezone.utc)
current_date = current_date.replace(tzinfo=timezone.utc)
current_date = round(float(current_date.timestamp()*1000-.5))
successful_Trades=0
prevProfit = 0
minuteFlag = 0

### Settings ###############
Market_Orders = 1 ##Allow Market Orders if limit is not filled
Trading=0 ##Actually trade on Binance, If Trading==1 then we are trading a strategy using the api keys specified above
          ## If Trading==0 then we are paper trading a strategy on historical data
leverage=35 ##leverage being used
OrderSIZE = .02 ##how much of account to use per trade in Decimal, not correct as leverage is used and depends on the stoploss settings used
break_even = 0 ##Set a new stop once in profit to cover the trading fee and breakeven
break_Even_Stage = [.4,.6] ##at what percentage (In decimal)
                                    # of take profit to set new stop which corresponds to break_even_Amount
                                    # Note:setting 1.5 makes that stage disabled as trades
                                     # will never reach 150% of takeprofit
break_even_Amount = [.1,.2]  ##what to set the new stop loss at
min_profit_accepted = .0015
Order_Type = 'GTC' ##'IOC' ##not currently used
start_string = '1 day ago UTC' ##buffer of historical data to download before starting the script
Interval = '1m' ##Time interval over which we want to trade, valid Intervals: 1m,3m,5m,15m,30m,1h,2h,4h,6h,8h,12h,1d,3d,1w

##Different coins we can trade, can add more in Helper.py
symbol="BTCUSDT"
#symbol="ETHUSDT"
#symbol="LTCUSDT"
#symbol="SOLUSDT"
#symbol="BNBUSDT"
#symbol="ADAUSDT"
#symbol="DOGEUSDT"
#symbol="BAKEUSDT"
#symbol="SUSHIUSDT"
#symbol="DOTUSDT"
#symbol = "ALPHAUSDT"
#symbol="XRPUSDT"
#symbol = "OMGUSDT"

Coin_precision,Order_precision = Helper.get_coin_attrib(symbol)

start = datetime.now().time()
yesterdate = date.today()
Start = 1
Profit = 0
tradeNO = 0
CurrentPos = -99
positionPrice = 0
current_stoplossval = 0
current_takeprofitval = 0
if Trading: ## Trade on Binance with above api key and secret key
    print("Symbol:", symbol, "Start Balance:", AccountBalance)
    def runWS():
        global Sleep,Date,Open, Close, High, Low, Volume,Profit,tradeNO,CurrentPos,positionPrice,\
            AccountBalance,EffectiveAccountBalance,positionSize,Highestprice,prediction, signal1, signal2, HighestUlt, Highest, \
            stoplossval, takeprofitval,prevsignal1,prevsignal2,PrevPos,Stop_ID,Order_ID,Limit_ID,prevProfit,minuteFlag,Start,start,yesterdate, \
        current_takeprofitval,current_stoplossval
        break_Even_Flag=0


        Date,Open,Close,High,Low,Volume = Helper.get_historical(symbol,start_string,Interval)

        y = client.futures_account_balance()
        for x in y:
            if x['asset'] == 'USDT':
                AccountBalance = float(x['balance'])

        EffectiveAccountBalance = AccountBalance * leverage

        try:
            if client.futures_position_information(symbol=symbol)[0]['positionAmt']!=0:
                y = client.futures_get_all_orders(symbol=symbol)
                Order_ID = y[-3]['orderId']
                Stop_ID = y[-2]['orderId']
                Limit_ID = y[-1]['orderId']
        except:
            pass
        ## setup websocket:
        if Interval == '1m' and Start:
            twm.start_kline_futures_socket(callback=handle_socket_message, symbol=symbol,
                                           interval=KLINE_INTERVAL_1MINUTE)
            Start = 0
        elif Interval == '3m' and Start:
            twm.start_kline_futures_socket(callback=handle_socket_message, symbol=symbol,
                                           interval=KLINE_INTERVAL_3MINUTE)
            Start = 0
        elif Interval == '5m' and Start:
            twm.start_kline_futures_socket(callback=handle_socket_message, symbol=symbol,
                                           interval=KLINE_INTERVAL_5MINUTE)
            Start = 0
        elif Interval == '15m' and Start:
            twm.start_kline_futures_socket(callback=handle_socket_message, symbol=symbol,
                                           interval=KLINE_INTERVAL_15MINUTE)
            Start = 0
        elif Interval == '30m' and Start:
            twm.start_kline_futures_socket(callback=handle_socket_message, symbol=symbol,
                                           interval=KLINE_INTERVAL_30MINUTE)
            Start = 0
        elif Interval == '1h' and Start:
            twm.start_kline_futures_socket(callback=handle_socket_message, symbol=symbol,
                                           interval=KLINE_INTERVAL_1HOUR)
            Start = 0
        elif Interval == '2h' and Start:
            twm.start_kline_futures_socket(callback=handle_socket_message, symbol=symbol,
                                           interval=KLINE_INTERVAL_2HOUR)
            Start = 0
        elif Interval == '4h' and Start:
            twm.start_kline_futures_socket(callback=handle_socket_message, symbol=symbol,
                                           interval=AsyncClient.KLINE_INTERVAL_4HOUR)
            Start = 0
        elif Interval == '6h' and Start:
            twm.start_kline_futures_socket(callback=handle_socket_message, symbol=symbol,
                                           interval=KLINE_INTERVAL_6HOUR)
            Start = 0
        elif Interval == '8h' and Start:
            twm.start_kline_futures_socket(callback=handle_socket_message, symbol=symbol,
                                           interval=KLINE_INTERVAL_8HOUR)
            Start = 0
        elif Interval == '12h' and Start:
            twm.start_kline_futures_socket(callback=handle_socket_message, symbol=symbol,
                                           interval=KLINE_INTERVAL_12HOUR)
            Start = 0
        elif Interval == '1d' and Start:
            twm.start_kline_futures_socket(callback=handle_socket_message, symbol=symbol,
                                           interval=KLINE_INTERVAL_1DAY)
            Start = 0
        elif Interval == '3d' and Start:
            twm.start_kline_futures_socket(callback=handle_socket_message, symbol=symbol,
                                           interval=KLINE_INTERVAL_3DAY)
            Start = 0
        elif Interval == '1w' and Start:
            twm.start_kline_futures_socket(callback=handle_socket_message, symbol=symbol,
                                           interval=KLINE_INTERVAL_1WEEK)
            Start = 0
        while True:
            #########################################################################################
            ######################## Runs every 30 seconds ##########################################
            rightnow = datetime.now().time()
            sec = timedelta(hours=0, minutes=0, seconds=30)
            if (datetime.combine(date.today(), rightnow) - datetime.combine(yesterdate, start)) > sec:
                start = datetime.now().time()
                yesterdate = date.today()
                if Order_ID!='':

                    if client.futures_get_all_orders(symbol=symbol, orderId=Order_ID)[-1]['status'] == 'PARTIALLY FILLED':
                        client.futures_cancel_order(symbol=symbol,orderId=Order_ID)  ##cancel leftover order

                    y = client.futures_position_information(symbol=symbol)[0]
                    if float(y['positionAmt']) == 0:
                        CurrentPos = -99  ##Check if we are in a trade, if not reinitialize CurrentPos
                        break_Even_Flag = 0  ##reinitialize
                        Order_ID = ''
                        Limit_ID = ''
                        Stop_ID = ''
                        client.futures_cancel_all_open_orders(symbol=symbol)  ##cancel open orders also

                    elif float(y['positionAmt']) < 0:
                        CurrentPos = 0  ##in a short
                        ##Check that stoploss and takeprofit are set:
                        try:
                            if Stop_ID == '':
                                # print("Z1: Stop Order not sent, trying again Attempting Stop Price:",round(float(x['entryPrice']) + current_stoplossval + (5 * math.pow(10, -Coin_precision - 1)),Coin_precision))
                                order2 = client.futures_create_order(
                                    symbol=symbol,
                                    side=SIDE_BUY,
                                    type=FUTURE_ORDER_TYPE_STOP_MARKET,
                                    quantity=-1 * float(y['positionAmt']),
                                    stopPrice=round(float(y['entryPrice']) + current_stoplossval + (
                                                5 * math.pow(10, -Coin_precision - 1)), Coin_precision))
                                Stop_ID = order2['orderId']
                            if Limit_ID == '':
                                # print("Z1: Limit Order not sent, trying again Attempting Limit Price:",round(float(x['entryPrice']) - current_takeprofitval, Coin_precision))
                                order3 = client.futures_create_order(
                                    symbol=symbol,
                                    side=SIDE_BUY,
                                    type=FUTURE_ORDER_TYPE_LIMIT,
                                    price=round(float(y['entryPrice']) - current_takeprofitval, Coin_precision),
                                    timeInForce=TIME_IN_FORCE_GTC,
                                    quantity=-1 * float(y['positionAmt']))
                                Limit_ID = order3['orderId']
                        except BinanceAPIException as d:
                            pass
                            if d.message == 'Order would immediately trigger.':
                                print(
                                    "Order would immediately Trigger, Cancelling and sleeping for 5 minutes")
                                order4 = client.futures_create_order(
                                    symbol=symbol,
                                    side=SIDE_BUY,
                                    type=FUTURE_ORDER_TYPE_MARKET,
                                    quantity=-1 * float(y['positionAmt']))
                                time.sleep(300)  ##sleep for 5 minutes
                                Sleep = 1
                                break
                    elif float(y['positionAmt']) > 0:
                        CurrentPos = 1  ##in a long
                        ##Check that stoploss and takeprofit are set:
                        try:
                            if Stop_ID == '':
                                # print("Z2: Stop Order not sent, trying again Attempting Stop Price:",round(float(x['entryPrice']) - current_stoplossval - (5 * math.pow(10, -Coin_precision - 1)),Coin_precision))
                                ##stoploss
                                order2 = client.futures_create_order(
                                    symbol=symbol,
                                    side=SIDE_SELL,
                                    type=FUTURE_ORDER_TYPE_STOP_MARKET,
                                    quantity=float(y['positionAmt']),
                                    stopPrice=round(float(y['entryPrice']) - current_stoplossval - (
                                                5 * math.pow(10, -Coin_precision - 1)), Coin_precision))
                                Stop_ID = order2['orderId']
                                ##takeprofit:
                            if Limit_ID == '':
                                # print("Z2: Limit Order not sent, trying again Attempting Limit Price:",round(float(x['entryPrice']) + current_takeprofitval, Coin_precision))
                                order3 = client.futures_create_order(
                                    symbol=symbol,
                                    side=SIDE_SELL,
                                    type=FUTURE_ORDER_TYPE_LIMIT,
                                    price=round(float(y['entryPrice']) + current_takeprofitval,
                                                Coin_precision),
                                    timeInForce=TIME_IN_FORCE_GTC,
                                    quantity=float(y['positionAmt']))
                                Limit_ID = order3['orderId']
                        except BinanceAPIException as d:
                            pass
                            if d.message == 'Order would immediately trigger.':
                                print("Order would immediately Trigger, Cancelling and sleeping for 5 minutes")
                                order4 = client.futures_create_order(
                                    symbol=symbol,
                                    side=SIDE_SELL,
                                    type=FUTURE_ORDER_TYPE_MARKET,
                                    quantity=float(y['positionAmt']))
                                time.sleep(300)  ##sleep for 5 minutes
                                Sleep = 1
                                break
                ##Check every 30 seconds that limit/stop hasn't been hit
                if Limit_ID!='' or Stop_ID!='':
                    y = client.futures_position_information(symbol=symbol)[0]
                    if float(y['positionAmt'])==0:
                        CurrentPos = -99  ##Check if we are in a trade, if not reinitialize CurrentPos
                        break_Even_Flag = 0  ##reinitialize
                        Order_ID = ''
                        Limit_ID = ''
                        Stop_ID = ''
                        client.futures_cancel_all_open_orders(symbol=symbol)  ##cancel open orders also
                        print("No Open Position Cancelling Stop/Limit")
                ##Check if Order was made but not hit, then maybe place market order
                elif Order_ID!='' and Market_Orders==1:
                    y = client.futures_position_information(symbol=symbol)[0]

                    if float(y['positionAmt']) == 0 and CurrentPos==0: ##No position was opened so place market order
                        client.futures_cancel_order(symbol=symbol)  ##cancel Orders
                        if Order_precision != 0:
                            Order(round(positionSize,Order_precision),0,symbol,
                                        current_stoplossval,current_takeprofitval,
                                        Coin_precision,Market=1)
                        else:
                            Order(round(positionSize), 0, symbol,
                                        current_stoplossval, current_takeprofitval,
                                        Coin_precision, Market=1)

                    elif float(y['positionAmt']) == 0 and CurrentPos == 1:  ##No position was opened so place market order
                        client.futures_cancel_order(symbol=symbol)  ##cancel Orders
                        if Order_precision != 0:
                            Order(round(positionSize,Order_precision), 1, symbol,
                                        current_stoplossval, current_takeprofitval,
                                        Coin_precision, Market=1)
                        else:
                            Order(round(positionSize), 1, symbol,
                                        current_stoplossval, current_takeprofitval,
                                        Coin_precision, Market=1)
            ###############################################################################################################
            ###############################################################################################################

            if minuteFlag: ##new OHLC data
                y = client.futures_account_balance()
                for x in y:
                    if x['asset'] == 'USDT':
                        AccountBalance = float(x['balance'])
                EffectiveAccountBalance = AccountBalance * leverage

                minuteFlag = 0 ##switch off flag
                prediction=-99 ##reinitialize

                ######################## These are some trading strategies I have coded up as functions, found in TradingStrats.py #######################################

                #prediction,Type = TS.MovingAverage(Close,prediction)
                #prediction,signal1,signal2,Type =TS.StochRSI_RSIMACD(prediction,Close,signal1,signal2)
                prediction, Type = TS.breakout(prediction, Close, Volume, symbol)
                #prediction, signal1, signal2, Type = TS.tripleEMAStochasticRSIATR(Close,signal1,signal2,prediction)
                #prediction,stoplossval,takeprofitval = TS.Fractal(Close,Low,High,prediction)
                #prediction, stoplossval, takeprofitval = TS.fibMACD(prediction,Close,Open)
                #prediction, signal1, Type = TS.RSIStochEMA(prediction, Close, High, Low,signal1, CurrentPos)
                #prediction, signal1, signal2, HighestUlt, Highest, Type = TS.UltOscMACD(prediction,Close,High, Low,signal1, signal2,HighestUlt, Highest)
                #prediction, signal1, Type = TS.RSIStochEMA200(prediction,Close,High,Low,signal1,signal2,CurrentPos)
                #prediction,Type = TS.Fractal2(Close,Low,High,signal1,prediction)

                #prediction, Type = stochBB(prediction, Close)

                stoplossval, takeprofitval = SetSLTP(stoplossval, takeprofitval, Close, High,Low, prediction, CurrentPos, Type) ##This function sets the stoploss and takeprofit based off the Type variable returned by the above functions

                ##These trading strategies have custom stoploss & takeprofits:
                #takeprofitval, stoplossval, prediction, signal1= TS.SARMACD200EMA(stoplossval, takeprofitval,Close,High,Low,prediction,CurrentPos,signal1)
                #takeprofitval, stoplossval, prediction, signal1= TS.TripleEMA(stoplossval, takeprofitval,Close,High,Low,prediction,CurrentPos,signal1)

                if (prediction == 1 or prediction == 0) and (min_profit_accepted * Close[-1] > takeprofitval):
                    prediction = -99

                y = client.futures_position_information(symbol=symbol)[0]

                if float(y['positionAmt']) < 0:
                    CurrentPos = 0  ##in a short
                    if break_even and break_Even_Flag==0:
                        if float(y['entryPrice']) - Close[-1] >break_Even_Stage[0]*current_takeprofitval:
                            ###### Set new Stop if we are in profit to breakeven
                            ##Set new Stop in Profit:
                            try:
                                order2 = client.futures_create_order(
                                    symbol=symbol,
                                    side=SIDE_BUY,
                                    type=FUTURE_ORDER_TYPE_STOP_MARKET,
                                    quantity=-1 * float(y['positionAmt']),
                                    stopPrice=round(float(y['entryPrice']) - break_even_Amount[0] * current_takeprofitval + 5 * math.pow(10, -Coin_precision - 1), Coin_precision))
                                if order2['status']=="NEW":
                                    client.futures_cancel_order(symbol=symbol,orderId=Stop_ID)
                                    print(f"New Stop placed at {break_even_Amount[0]}x(take profit)")
                                    break_Even_Flag = 1
                                    Stop_ID=order2['orderId']
                            except BinanceAPIException as d:
                                if d.message=='Order would immediately trigger.':
                                    print("New Stop not placed as order would trigger immediately")#, LastPrice:",LastPrice)

                    if break_even and break_Even_Flag<=1:
                        if float(y['entryPrice']) - Close[-1] >break_Even_Stage[1]*current_takeprofitval:
                            ###### Set new Stop if we are in profit to breakeven
                            ##Set new Stop in Profit:
                            try:
                                order2 = client.futures_create_order(
                                    symbol=symbol,
                                    side=SIDE_BUY,
                                    type=FUTURE_ORDER_TYPE_STOP_MARKET,
                                    quantity=-1 * float(y['positionAmt']),
                                    stopPrice=round(float(y['entryPrice']) - break_even_Amount[1] * current_takeprofitval + 5 * math.pow(10, -Coin_precision - 1), Coin_precision))
                                if order2['status']=="NEW":
                                    client.futures_cancel_order(symbol=symbol, orderId=Stop_ID)
                                    print(f"New Stop placed at {break_even_Amount[1]}x(takeprofit)")
                                    break_Even_Flag = 2
                                    Stop_ID=order2['orderId']
                            except BinanceAPIException as d:
                                if d.message=='Order would immediately trigger.':
                                    print("New Stop not placed as order would trigger immediately")#, LastPrice:",LastPrice)

                elif float(y['positionAmt']) > 0:
                    CurrentPos = 1  ##in a long
                    if break_even and break_Even_Flag==0:
                        if Close[-1] - float(y['entryPrice']) >break_Even_Stage[0]*takeprofitval:
                            ###### Set new Stop if we are in profit to breakeven
                            ##Set new Stop in Profit:
                            try:
                                order2 = client.futures_create_order(
                                    symbol=symbol,
                                    side=SIDE_SELL,
                                    type=FUTURE_ORDER_TYPE_STOP_MARKET,
                                    quantity=float(y['positionAmt']),
                                    stopPrice=round(float(y['entryPrice']) + break_even_Amount[0] * current_takeprofitval - 5 * math.pow(10, -Coin_precision - 1), Coin_precision))
                                if order2['status']=="NEW":
                                    client.futures_cancel_order(symbol=symbol,orderId=Stop_ID)  ##cancel open orders also
                                    print(f"New Stop placed at {break_even_Amount[0]}x(take profit)")
                                    break_Even_Flag = 1
                                    Stop_ID=order2['orderId']
                            except BinanceAPIException as d:
                                if d.message=='Order would immediately trigger.':
                                    print("New Stop not placed as order would trigger immediately")#, LastPrice:",LastPrice)

                    if break_even and break_Even_Flag<=1:
                        if Close[-1] - float(y['entryPrice']) >break_Even_Stage[1]*takeprofitval:
                            ###### Set new Stop if we are in profit to breakeven
                            ##Set new Stop in Profit:
                            try:
                                order2 = client.futures_create_order(
                                    symbol=symbol,
                                    side=SIDE_SELL,
                                    type=FUTURE_ORDER_TYPE_STOP_MARKET,
                                    quantity=float(y['positionAmt']),
                                    stopPrice=round(float(y['entryPrice']) + current_takeprofitval * break_even_Amount[1] - 5 * math.pow(10, -Coin_precision - 1), Coin_precision))
                                if order2['status']=="NEW":
                                    client.futures_cancel_order(symbol=symbol,orderId=Stop_ID)  ##cancel open orders also
                                    print(f"New Stop placed at {break_even_Amount[1]}x(takeprofit)")
                                    break_Even_Flag = 2
                                    Stop_ID=order2['orderId']
                            except BinanceAPIException as d:
                                if d.message=='Order would immediately trigger.':
                                    print("New Stop not placed as order would trigger immediately")#, LastPrice:",LastPrice)

                if CurrentPos == -99 and prediction == 0:  ##not in a trade but want to enter a short position
                    LP = float(client.get_ticker(symbol=symbol)['lastPrice'])
                    positionPrice = LP
                    positionSize = (OrderSIZE * EffectiveAccountBalance) / positionPrice ##work out OrderQTY
                    #print(positionSize)
                    CurrentPos = 0
                    Highestprice = positionPrice
                    ##Stoploss and takeprofit in case the stop/limit order isn't filled
                    current_stoplossval = copy(stoplossval)
                    current_takeprofitval = copy(takeprofitval)

                    ##Create Order on Binance
                    if Order_precision!=0:
                        Order(round(positionSize,Order_precision), 0, symbol,stoplossval,takeprofitval,Coin_precision,Market_Orders)
                    else:
                        Order(round(positionSize), 0, symbol, stoplossval, takeprofitval, Coin_precision,Market_Orders)

                elif CurrentPos == -99 and prediction == 1: ##not in a trade but want to enter a Long position
                    LP = float(client.get_ticker(symbol=symbol)['lastPrice'])
                    positionPrice = LP
                    positionSize = (OrderSIZE * EffectiveAccountBalance) / positionPrice ##work out OrderQTY
                    CurrentPos = 1
                    Highestprice = positionPrice
                    ##Stoploss and takeprofit in case the stop/limit order isn't filled
                    current_stoplossval = copy(stoplossval)
                    current_takeprofitval = copy(takeprofitval)

                    ##Create Order on Binance
                    if Order_precision!=0:
                        Order(round(positionSize,Order_precision), 1, symbol,stoplossval,takeprofitval,Coin_precision,Market_Orders)
                    else:
                        Order(round(positionSize), 1, symbol, stoplossval, takeprofitval,Coin_precision,Market_Orders)

                if CurrentPos != PrevPos:
                    if PrevPos!=-99:
                        tradeNO+=1
                    bnb = float(client.get_ticker(symbol="BNBUSDT")['lastPrice'])
                    signal1 = -99
                    signal2 = -99
                    print("Current Position:", CurrentPos)
                    try:
                        prevProfit = printProfit(symbol, bnb,prevProfit)
                    except Exception as e:
                        pass
                PrevPos = copy(CurrentPos)


    def handle_socket_message(msg):
        global minuteFlag,Open,Close,High,Low,Volume
        # print(msg)
        payload = msg['k']
        if payload['x'] and msg['ps'] == symbol:
            Date = flow.dataStream(Date, datetime.utcfromtimestamp(round(float(payload['t'])/1000)), 1, 300)
            Open = flow.dataStream(Open, float(payload['o']), 1, 300)
            Close = flow.dataStream(Close, float(payload['c']), 1, 300)
            High = flow.dataStream(High, float(payload['h']), 1, 300)
            Low = flow.dataStream(Low, float(payload['l']), 1, 300)
            Volume = flow.dataStream(Volume, float(payload['q']), 1, 300)
            minuteFlag = 1

    def printProfit(S,bnb,previous_Profit):
        global Profit,tradeNO,stoplossval,takeprofitval,Close,AccountBalance,successful_Trades
        data = client.futures_account_trades(symbol=S)
        commissionbnb = []
        comission = []
        PNL = []
        # pp.pprint(data)
        for j in data:
            if float(j['time']) > float(current_date):
                # print(i)
                if j['commissionAsset'] == 'BNB':
                    commissionbnb.append(j['commission'])
                else:
                    comission.append(j['commission'])
                PNL.append(j['realizedPnl'])
        for x in commissionbnb:
            Profit -= (float(x) * bnb)
        for x in comission:
            Profit -= float(x)
        for x in PNL:
            Profit += float(x)
        if Profit>previous_Profit:
            successful_Trades+=1
        print("Account Balance: ", AccountBalance, "Profit:", Profit)
        try:
            print("PV:", (Profit * 100) / (tradeNO * Close[-1]),"Stoploss:",stoplossval, "TakeProfit:", takeprofitval,"Successful Trades:",successful_Trades,"Trades lost:",tradeNO-successful_Trades,"W/L ratio:",successful_Trades/tradeNO)
        except:
            pass
        previous_Profit = copy(Profit)
        Profit=0
        return previous_Profit

    def Order(q, side1, s,stoploss,takeprofit,CP,Market):
        global Stop_ID,Limit_ID,Order_ID
        try:
            try:
                if side1 and Market==0: ##Long
                    PP = float(client.get_ticker(symbol=s)['lastPrice']) * 1.0007  ##So last price more likely to fill
                    ##Place the Long
                    order1 = client.futures_create_order(
                        symbol=s,
                        side=SIDE_BUY,
                        type=FUTURE_ORDER_TYPE_LIMIT,
                        price= round(PP,CP),
                        timeInForce=TIME_IN_FORCE_GTC,
                        quantity=q)
                    Order_ID=order1['orderId']
                    x = client.futures_get_all_orders(symbol=s, orderId=Order_ID)
                    ##stoploss
                    order2 = client.futures_create_order(symbol=s,
                        side=SIDE_SELL,
                        type=FUTURE_ORDER_TYPE_STOP_MARKET,
                        quantity=float(x[-1]['executedQty']),
                        stopPrice=round((float(x[-1]['avgPrice']))-stoploss-(5*math.pow(10,-CP-1)),CP))
                    Stop_ID=order2['orderId']
                    ##takeprofit:
                    order3 = client.futures_create_order(
                        symbol=s,
                        side=SIDE_SELL,
                        type=FUTURE_ORDER_TYPE_LIMIT,
                        price=round((float(x[-1]['avgPrice'])) + takeprofit, CP),
                        timeInForce=TIME_IN_FORCE_GTC,
                        quantity=float(x[-1]['executedQty']))
                    Limit_ID=order3['orderId']

                elif side1==0 and Market==0: ##Short
                    PP = float(client.get_ticker(symbol=s)['lastPrice']) * .9993  ##So last price more likely to fill
                    ##Place the short
                    order1 = client.futures_create_order(
                        symbol=s,
                        side=SIDE_SELL,
                        type=FUTURE_ORDER_TYPE_LIMIT,
                        price=round(PP,CP),
                        timeInForce=TIME_IN_FORCE_GTC,
                        quantity=q)
                    Order_ID = order1['orderId']
                    x = client.futures_get_all_orders(symbol=s, orderId=Order_ID)
                    #print("x[-1]['status']:",x[-1]['status'])
                    #if x[-1]['status'] == 'FILLED':
                        #print("avPrice:", (float(x[-1]['avgPrice'])))
                        #print("attempted Stoploss:",round((float(x[-1]['avgPrice'])) + stoploss + 5 * math.pow(10, -CP - 1), CP))
                        #print("attempted Takeprofit:", round(round((float(x[-1]['avgPrice'])) - takeprofit, CP)))
                    order2 = client.futures_create_order(
                        symbol=s,
                        side=SIDE_BUY,
                        type=FUTURE_ORDER_TYPE_STOP_MARKET,
                        quantity=float(x[-1]['executedQty']),
                        stopPrice=round((float(x[-1]['avgPrice'])) + stoploss + (5 * math.pow(10, -CP - 1)), CP))
                    Stop_ID=order2['orderId']
                    order3 = client.futures_create_order(
                        symbol=s,
                        side=SIDE_BUY,
                        type=FUTURE_ORDER_TYPE_LIMIT,
                        price=round((float(x[-1]['avgPrice'])) - takeprofit, CP),
                        timeInForce=TIME_IN_FORCE_GTC,
                        quantity=float(x[-1]['executedQty']))
                    Limit_ID=order3['orderId']
                elif side1 and Market:
                    client.futures_cancel_all_open_orders(symbol=s)  ##cancel open orders
                    ##Market order so we don't miss the move
                    order1 = client.futures_create_order(
                        symbol=s,
                        side=SIDE_BUY,
                        type=FUTURE_ORDER_TYPE_MARKET,
                        quantity=q)
                    Order_ID=order1['orderId']
                    x = client.futures_get_all_orders(symbol=s, orderId=order1['orderId'])
                    ##stoploss:
                    order2 = client.futures_create_order(
                        symbol=s,
                        side=SIDE_SELL,
                        type=FUTURE_ORDER_TYPE_STOP_MARKET,
                        quantity=float(x[-1]['executedQty']),
                        stopPrice=round((float(x[-1]['avgPrice'])) - stoploss - (5 * math.pow(10, -CP - 1)), CP))
                    Stop_ID=order2['orderId']
                    ##takeprofit:
                    order3 = client.futures_create_order(
                        symbol=s,
                        side=SIDE_SELL,
                        type=FUTURE_ORDER_TYPE_LIMIT,
                        price=round((float(x[-1]['avgPrice'])) + takeprofit, CP),
                        timeInForce=TIME_IN_FORCE_GTC,
                        quantity=float(x[-1]['executedQty']))
                    Limit_ID=order3['orderId']

                elif side1==0 and Market:
                    client.futures_cancel_all_open_orders(symbol=s)  ##cancel open orders
                    ##Market order so we don't miss the move
                    order1 = client.futures_create_order(
                        symbol=s,
                        side=SIDE_SELL,
                        type=FUTURE_ORDER_TYPE_MARKET,
                        quantity=q)
                    Order_ID=order1['orderId']
                    x = client.futures_get_all_orders(symbol=s, orderId=order1['orderId'])
                    ##Stoploss
                    order2 = client.futures_create_order(
                        symbol=s,
                        side=SIDE_BUY,
                        type=FUTURE_ORDER_TYPE_STOP_MARKET,
                        quantity=float(x[-1]['executedQty']),
                        stopPrice=round((float(x[-1]['avgPrice'])) + stoploss + 5 * math.pow(10, -CP - 1), CP))
                    Stop_ID=order2['orderId']
                    ##takeprofit
                    order3 = client.futures_create_order(
                        symbol=s,
                        side=SIDE_BUY,
                        type=FUTURE_ORDER_TYPE_LIMIT,
                        price=round((float(x[-1]['avgPrice'])) - takeprofit, CP),
                        timeInForce=TIME_IN_FORCE_GTC,
                        quantity=float(x[-1]['executedQty']))
                    Limit_ID=order3['orderId']
            except BinanceAPIException as e:
                print(e.status_code)
                print(e.message)
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)



    def run():
        try:
            runWS()
        except Exception as e:
            #print("Error:",e)
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)
            print("Error in websocket, Restarting")
            time.sleep(1)
            bnb = float(client.get_ticker(symbol="BNBUSDT")['lastPrice'])
            printProfit(symbol, bnb, 0)
            run()

    run()

    if Sleep == 1:
        Sleep = 0
        print("Done Sleeping")
        run()
elif Trading==0:       ## Paper Trading, exact same as above but simulated trading with graphs
    High_1min = []
    Low_1min = []
    Close_1min= []
    Open_1min = []
    Date_1min = []
    symbol = ["BTCUSDT"]
    #symbol=["ETHUSDT"]
    #symbol = ["DOGEUSDT"]
    #symbol = ['ADAUSDT']
    #symbol = ["OMGUSDT"]
    #symbol = ['XRPUSDT','SOLUSDT'] ###############################
    #symbol = ['MATICUSDT'] #############################
    #symbol = ["XRPUSDT"]
    #symbol=['BAKEUSDT']
    #symbol=['BNBUSDT']
    #symbol= ['SUSHIUSDT']
    #symbol = ["DOTUSDT"]
    #symbol = ["ALPHAUSDT"]
    #symbol = ['BATUSDT']
    #symbol = ["DOGEUSDT",'SOLUSDT']
    #symbol = ['DOGEUSDT', 'SOLUSDT','OMGUSDT','ADAUSDT','XRPUSDT','ETHUSDT','BTCUSDT','MATICUSDT','BNBUSDT','BAKEUSDT']#,'OMGUSDT']#,'ADAUSDT']#,'BTCUSDT']#,"BNBUSDT","XRPUSDT"]
    #symbol = ['SANDUSDT']

    OrderSIZE = .02
    AccountBalance = 2335
    leverage = 35  ##leverage being used
    test_set = 0  ##If OFF we are only paper trading on in-sample data, if ON the we are paper trading on out of sample data to determine the validity of our strategies results
    test_set_length = "1 month ago UTC"  ## valid strings 'x days/weeks/months/years ago UTC'
    time_period = 8  ##time_period in same units as test_set_length above
    TIME_INTERVAL = 240  ##Candlestick interval in minutes, valid options:1,   3,   5,  15,   30,  60, 120,240,360,480,720, 1440,4320, 10080, 40320
    load_data = 1 ##load data from a file, download the data using download_Data.py

    ############################## pairTrading ##############################################
    pair_Trading = 0  ##Switch to backtest the pairtrading Long-Short strategy, switch off for any other strategy
    TPSL = 0 ## type of take profit for pair trading
    percent_TP = .08 ##percent to takeprofit if TPSL switched on
    percent_SL = .01 ##percent to stoploss if TPSL switched on
    log = 0 ###log prices, not recommended as implementation may be wrong, something i'm working on understanding better
    Close_pos = 0 ##flag to close the position on next open if pair trading
    if pair_Trading:
        symbol = ['RENUSDT','ATOMUSDT']
    #################################################################################################################
    STOP = 1  ##If strategy SLTP of type 9 multiplier for stoploss using ATR
    TAKE = 2.5 ##If strategy SLTP of type 9 multiplier for takeprofit using ATR

    Highest_lowest = 0
    Type = []
    stoplossval = []
    takeprofitval = []
    CurrentPos = []
    positionSize = []
    positionPrice = []
    PrevPos = []
    prediction = []
    profitgraph.append(AccountBalance)

    count = 0
    Hold_pos = 0 ##no TP/SL, for strategies that buy and hold turn off otherwise
    percent = .01 ##percentage to hold out for

    originalBalance = copy(AccountBalance)
    waitflag = 0  ##wait until next candlestick before checking if stoploss/ takeprofit was hit
    fee = .00036

    ##trailing stop variables
    break_even = 0  ##whether or not to move the stoploss into profit based of settings below
    break_even_flag = 0  ##flag don't change
    break_Even_Stage = [.7,1.75]  ##if we reach this point in of profit target move stoploss to corresponding point break_even_Amount
    break_even_Amount = [.1, .4]  ##where to move the stop to

    period_string, time_CAGR = Helper.get_period_String(test_set_length, time_period)

    if load_data:
        print("Loading Price Data")
        i = 0
        while i < len(symbol):
            path = f"{DD.path}\\{symbol[i]}_{TIME_INTERVAL}_{time_period} {period_string} ago UTC.joblib"
            try:
                price_data = load(path)
                Date.append(price_data['Date'])
                Open.append(price_data['Open'])
                Close.append(price_data['Close'])
                High.append(price_data['High'])
                Low.append(price_data['Low'])
                Volume.append(price_data['Volume'])
                High_1min.append(price_data['High_1min'])
                Low_1min.append(price_data['Low_1min'])
                Close_1min.append(price_data['Close_1min'])
                Open_1min.append(price_data['Open_1min'])
                Date_1min.append(price_data['Date_1min'])
                i += 1
            except:
                try:
                    print(f"Data doesnt exist in path: {path}, Downloading Data to specified path now...")
                    DD.get_data(TIME_INTERVAL, symbol[i], f"{time_period} {period_string} ago UTC")
                    price_data = load(path)
                    Date.append(price_data['Date'])
                    Open.append(price_data['Open'])
                    Close.append(price_data['Close'])
                    High.append(price_data['High'])
                    Low.append(price_data['Low'])
                    Volume.append(price_data['Volume'])
                    High_1min.append(price_data['High_1min'])
                    Low_1min.append(price_data['Low_1min'])
                    Close_1min.append(price_data['Close_1min'])
                    Open_1min.append(price_data['Open_1min'])
                    Date_1min.append(price_data['Date_1min'])
                    print("Download Successful, Loading Data now")
                    i += 1
                except BinanceAPIException as e:
                    if str(e) == 'APIError(code=-1121): Invalid symbol.':
                        print(f"Invalid Symbol: {symbol[i]}, removing from data set")
                        symbol.pop(i)
                    else:
                        print("Wrong path specified in download_Data.py")
                        symbol.pop(i)
                        print("Fix path issue or else turn off load_data")
                        print("Contact me if still stuck @ wconor539@gmail.com")


    else:
        for i in range(len(symbol)):
            Date_temp, Open_temp, Close_temp, High_temp, Low_temp, Volume_temp, High_1min_temp, Low_1min_temp, Close_1min_temp,Open_1min_temp, Date_1min_temp = Helper.get_Klines(symbol[i], TIME_INTERVAL,time_period,test_set,test_set_length)
            Date.append(Date_temp)
            Open.append(Open_temp)
            Close.append(Close_temp)
            High.append(High_temp)
            Low.append(Low_temp)
            Volume.append(Volume_temp)
            High_1min.append(High_1min_temp)
            Low_1min.append(Low_1min_temp)
            Close_1min.append(Close_1min_temp)
            Open_1min.append(Open_1min_temp)
            Date_1min.append(Date_1min_temp)
    print("Symbols:", symbol, "Start Balance:", AccountBalance,"fee:",fee)

    ##variables for CAGR calculation
    start_equity = AccountBalance

    i = 0
    while i < len(Close):
        if len(Close[i]) == 0:
            Date.pop(i)
            Open.pop(i)
            Close.pop(i)
            High.pop(i)
            Low.pop(i)
            Volume.pop(i)
            High_1min.pop(i)
            Low_1min.pop(i)
            Close_1min.pop(i)
            Open_1min.pop(i)
            Date_1min.pop(i)
            print(f"Not enough candleStick data for {symbol[i]} removing from dataset...")
            symbol.pop(i)
            i -= 1
        i += 1
    print("Aligning Data Sets... This may take a few minutes")
    Date_1min, High_1min, Low_1min, Close_1min, Open_1min, Date, Open, Close, High, Low, Volume = Helper.align_Datasets(
        Date_1min, High_1min, Low_1min, Close_1min, Open_1min, Date, Open, Close, High, Low, Volume, symbol)

    for i in range(len(symbol)):
        Type.append(-99)
        stoplossval.append(0)
        takeprofitval.append(0)
        CurrentPos.append(-99)
        positionSize.append(0)
        positionPrice.append(0)
        PrevPos.append(-99)
        prediction.append(-99)
        CloseStream.append([])
        OpenStream.append([])
        HighStream.append([])
        LowStream.append([])
        VolumeStream.append([])
        DateStream.append([])


    ##variables for sharpe ratio
    day_start_equity = AccountBalance
    month_return = 0
    monthly_return = []
    Daily_return = []

    print(f"{TIME_INTERVAL} min OHLC Candle Sticks from a period of {time_period} {period_string}")
    Strategy = 0
    for i in range(len(High_1min[0])-1):
        #global trailing_stoploss,Highestprice
        if i%TIME_INTERVAL==0 and i!=0:
            for j in range(len(High_1min)):
                DateStream[j] = flow.dataStream(DateStream[j], Date[j][int(i/TIME_INTERVAL)-1], 1, 300)
                OpenStream[j] = flow.dataStream(OpenStream[j], float(Open[j][int(i/TIME_INTERVAL)-1]), 1, 300)
                CloseStream[j] = flow.dataStream(CloseStream[j], float(Close[j][int(i/TIME_INTERVAL)-1]), 1, 300)
                HighStream[j] = flow.dataStream(HighStream[j], float(High[j][int(i/TIME_INTERVAL)-1]), 1, 300)
                LowStream[j] = flow.dataStream(LowStream[j], float(Low[j][int(i/TIME_INTERVAL)-1]), 1, 300)
                VolumeStream[j] = flow.dataStream(VolumeStream[j], float(Volume[j][int(i/TIME_INTERVAL)-1]), 1, 300)
        #print(len(OpenStream))
        if len(OpenStream[0])>=299:
            prev_Account_Bal=copy(AccountBalance)
            EffectiveAccountBalance = AccountBalance*leverage
            if len(OpenStream[0])==299 and not pair_Trading:
                pass
                #Strategy = PS.sup_res(CloseStream[0]) ##not a strategy ive made public
                #Strategy = PS.fractal2([0,0,0,1,0,0,0,0,0])
            for j in range(len(prediction)):
                if (CurrentPos[j]== -99 or Hold_pos) and not pair_Trading:
                    if i%TIME_INTERVAL==0 and (i!=0 or TIME_INTERVAL==1):
                        break_even_flag=0

                        ##Public Strats :) :
                        ## These strats require a call to SetSLTP as they return a Type param:

                        #prediction[j],signal1,signal2,Type[j] =TS.StochRSI_RSIMACD(prediction[j],CloseStream[j],signal1,signal2) ###########################################
                        #prediction[j],Type[j] = TS.StochRSIMACD(prediction[j], CloseStream[j],HighStream[j],LowStream[j])  ###########################################
                        #prediction[j], signal1, signal2, Type[j] = TS.tripleEMAStochasticRSIATR(CloseStream[j],signal1,signal2,prediction[j])
                        #prediction[j], signal1, Type[j] = TS.RSIStochEMA(prediction[j],CloseStream[j],HighStream[j],LowStream[j],signal1,CurrentPos[j])
                        prediction[j],Type[j]=TS.tripleEMA(CloseStream[j],OpenStream[j],prediction[j])
                        #prediction[j], Type[j] = TS.breakout(prediction[j],CloseStream[j],VolumeStream[j],symbol[j])
                        #prediction[j],Type[j] = TS.Fractal2(CloseStream[j],LowStream[j],HighStream[j],signal1,prediction[j]) ###############################################
                        #prediction[j],Type[j] = TS.stochBB(prediction[j],CloseStream[j])
                        #prediction[j], Type[j] = TS.goldenCross(prediction[j],CloseStream[j])
                        #prediction[j] , Type[j] = TS.candle_wick(prediction,CloseStream[j],OpenStream[j],HighStream[j],LowStream[j])
                        #prediction[j],Close_pos,count,stoplossval[j] = TS.single_candle_swing_pump(prediction[j],CloseStream[j],HighStream[j],LowStream[j],CurrentPos[j],Close_pos,count,stoplossval[j])
                        stoplossval[j], takeprofitval[j] = SetSLTP(stoplossval[j], takeprofitval[j], CloseStream[j],HighStream[j], LowStream[j], prediction[j],CurrentPos[j], Type[j],SL=STOP,TP=TAKE)


                        ##These strats don't require a call to SetSLTP:

                        #prediction[j],stoplossval[j],takeprofitval[j] = TS.fibMACD(prediction[j], CloseStream[j], OpenStream[j],HighStream[j],LowStream[j])
                        #prediction[j],stoplossval[j],takeprofitval[j] = TS.Fractal(CloseStream[j], LowStream[j], HighStream[j],OpenStream[j],prediction[j])
                        # takeprofitval[j], stoplossval[j], prediction[j], signal1= TS.SARMACD200EMA(stoplossval[j], takeprofitval[j],CloseStream[j],HighStream[j],LowStream[j],prediction[j],CurrentPos[j],signal1)
                        # takeprofitval[j], stoplossval[j], prediction[j], signal1= TS.TripleEMA(stoplossval[j], takeprofitval[j],CloseStream[j],HighStream[j],LowStream[j],prediction[j],CurrentPos[j],signal1)
                        #prediction[j],Highest_lowest,Close_pos = TS.trend_Ride(prediction[j], CloseStream[j], HighStream[j][-1], LowStream[j][-1], percent, CurrentPos[j], Highest_lowest) ##This strategy holds a position until the price dips/rises a certain percentage
                        #prediction[j],Close_pos = TS.RSI_trade(prediction[j],CloseStream[j],CurrentPos[j],Close_pos)

                        ##########################################################################################################################################################################
                        ##########################################################################################################################################################################
                        ##Non public Strats sorry :( :
                        # prediction[j],Type[j] = Strategy.Check_for_sup_res(CloseStream[j],OpenStream[j],HighStream[j],LowStream[j]) ##not a strategy ive made public
                        #prediction[j], stoplossval[j], takeprofitval[j] = Strategy.check_for_pullback(CloseStream[j], LowStream[j], HighStream[j], OpenStream[j],VolumeStream[j],prediction[j]) ##not a strategy ive made public
                        ##########################################################################################################################################################################

                elif not pair_Trading:
                    prediction[j]=-99

                elif pair_Trading and CurrentPos[0]==CurrentPos[1]==prediction[0]==prediction[1]==-99:
                    ##Pair Trading


                    if not TPSL:
                        prediction, Type = TS.pairTrading(prediction, CloseStream[0], CloseStream[1], log, TPSL, percent_TP,percent_SL)
                        stoplossval[0], takeprofitval[0] = SetSLTP(stoplossval[0], takeprofitval[0], CloseStream[0],HighStream[0], LowStream[0], prediction[0],CurrentPos[0], 9, SL=STOP, TP=TAKE)
                        stoplossval[1], takeprofitval[1] = SetSLTP(stoplossval[1], takeprofitval[1], CloseStream[1],HighStream[1], LowStream[1], prediction[1],CurrentPos[1], 9, SL=STOP, TP=TAKE)
                    else:
                        prediction, Type, takeprofitval[0], takeprofitval[1],stoplossval[0],stoplossval[1] = TS.pairTrading(prediction,CloseStream[0],CloseStream[1],log, TPSL,percent_TP, percent_SL)


                ##If the trade won't cover the fee & profit something then don't place it
                if (prediction[j] == 1 or prediction[j] == 0) and (.00125 * Close_1min[j][-1] > takeprofitval[j]) and (not pair_Trading) and (not Hold_pos):
                    prediction[j] = -99
        #################################################################
            #################################################################

                if CurrentPos[j] == -99 and prediction[j] == 0:
                    positionPrice[j] = Open_1min[j][i+1]##next open candle #CloseStream[j][len(CloseStream[j]) - 1]
                    positionSize[j]= (OrderSIZE*EffectiveAccountBalance)/positionPrice[j]
                    CurrentPos[j] = 0
                    tradeNO+=1
                    #Highestprice = positionPrice
                   #stoplossval = positionPrice * trailing_stoploss
                    trades.append({'x':i,'y':positionPrice[j],'type': "sell",'current_price': positionPrice[j]})
                    Profit -= Open_1min[j][i+1] * fee
                    AccountBalance -= positionSize[j] * Open_1min[j][i+1] * fee
                    month_return -= positionSize[j] * Open_1min[j][i+1] * fee
                    waitflag = 1
                    prediction[j] = -99
                elif CurrentPos[j] == -99 and prediction[j] == 1:
                    positionPrice[j] = Open_1min[j][i+1] ##next open candle
                    positionSize[j] = (OrderSIZE * EffectiveAccountBalance) / positionPrice[j]
                    CurrentPos[j] = 1
                    tradeNO += 1
                    #Highestprice = positionPrice
                    #stoplossval = positionPrice * trailing_stoploss
                    trades.append({'x':i,'y':positionPrice[j], 'type': "buy",'current_price': positionPrice[j]})
                    Profit -= Open_1min[j][i+1] * fee
                    AccountBalance -= positionSize[j] * Open_1min[j][i+1] * fee
                    month_return -= positionSize[j] * Open_1min[j][i+1] * fee
                    waitflag = 1
                    prediction[j] = -99
                ############### break-even:
                #if CurrentPos==0 and break_even and positionPrice-CloseStream[-1] > .0025*positionPrice:


                if positionPrice[j] - High_1min[j][i] < -stoplossval[j] and CurrentPos[j] == 0 and (not waitflag) and not Hold_pos:
                    Profit +=-stoplossval[j] #positionPrice-CloseStream[len(CloseStream) - 1]  ##This will be positive if the price went down
                    month_return-=positionSize[j] *stoplossval[j]
                    AccountBalance += positionSize[j] * -stoplossval[j] # (positionPrice-CloseStream[len(CloseStream) - 1])
                    positionPrice[j] = Close_1min[j][i]
                    Profit -= Close_1min[j][i] * fee
                    AccountBalance-= positionSize[j] * Close_1min[j][i] * fee
                    month_return -= positionSize[j] * Close_1min[j][i] * fee
                    cashout.append({'x': i, 'y': Close_1min[j][i], 'type': "loss",'position':'short','Profit': -stoplossval[j]*positionSize[j]})
                    # CurrentPos = -99
                    CurrentPos[j] = -99
                    stopflag = -99

                elif Low_1min[j][i] - positionPrice[j] < -stoplossval[j] and CurrentPos[j] == 1 and (not waitflag) and not Hold_pos:
                    Profit +=-stoplossval[j] #CloseStream[len(CloseStream) - 1] - positionPrice ##This will be positive if the price went up
                    month_return -= positionSize[j] *stoplossval[j]
                    AccountBalance += positionSize[j]* -stoplossval[j] #(CloseStream[len(CloseStream) - 1] - positionPrice)
                    positionPrice[j] = Close_1min[j][i]
                    Profit -= Close_1min[j][i] * fee
                    AccountBalance -= positionSize[j] * Close_1min[j][i] * fee
                    month_return -= positionSize[j] * Close_1min[j][i] * fee
                    cashout.append({'x': i, 'y': Close_1min[j][i], 'type': "loss",'position':'long','Profit': -stoplossval[j]*positionSize[j]})
                    # CurrentPos = -99
                    CurrentPos[j] = -99
                    stopflag = -99

                elif positionPrice[j] - Low_1min[j][i] > takeprofitval[j] and CurrentPos[j] == 0 and (not waitflag) and not Hold_pos:
                    Profit += takeprofitval[j] #positionPrice - CloseStream[-1]
                    month_return += positionSize[j] *takeprofitval[j]
                    AccountBalance += positionSize[j] *  takeprofitval[j] #(positionPrice - CloseStream[len(CloseStream) - 1])
                    correct += 1
                    positionPrice[j] = Close_1min[j][i]
                    Profit -= Close_1min[j][i] * fee
                    AccountBalance -= positionSize[j] * Close_1min[j][i] * fee
                    month_return -= positionSize[j] * Close_1min[j][i] * fee
                    cashout.append({'x': i, 'y': Close_1min[j][i], 'type': "win",'position':'short','Profit': takeprofitval[j]*positionSize[j]})
                    CurrentPos[j] = -99
                    stopflag = -99

                elif High_1min[j][i] - positionPrice[j] > takeprofitval[j] and CurrentPos[j] == 1 and (not waitflag) and not Hold_pos:
                    Profit +=  takeprofitval[j] #CloseStream[-1] - positionPrice
                    month_return += positionSize[j] *takeprofitval[j]
                    AccountBalance += positionSize[j] *  takeprofitval[j] #(CloseStream[len(CloseStream) - 1] - positionPrice)
                    correct += 1
                    positionPrice[j] = Close_1min[j][i]
                    Profit -= Close_1min[j][i] * fee
                    AccountBalance -= positionSize[j] * Close_1min[j][i] * fee
                    month_return -= positionSize[j] * Close_1min[j][i] * fee
                    cashout.append({'x': i, 'y': Close_1min[j][i], 'type': "win",'position':'long','Profit': takeprofitval[j]*positionSize[j]})
                    CurrentPos[j] = -99
                    stopflag = -99
                elif (pair_Trading or Hold_pos) and (not waitflag) and Close_pos==1 and CurrentPos[j] == 1:
                    prev_Profit = copy(Profit)
                    Profit += Open_1min[j][i+1] - positionPrice[j] ##sell at next open candle
                    month_return += positionSize[j] * (Open_1min[j][i+1]-positionPrice[j])
                    AccountBalance += positionSize[j] * (Open_1min[j][i+1]-positionPrice[j])
                    if prev_Profit<Profit:
                        correct += 1
                        cashout.append({'x': i, 'y': Open_1min[j][i + 1], 'type': "win", 'position': 'long',
                                        'Profit': (Open_1min[j][i + 1]- positionPrice[j]) * positionSize[j]})
                    else:
                        cashout.append({'x': i, 'y': Open_1min[j][i + 1], 'type': "loss", 'position': 'long',
                                        'Profit': (Open_1min[j][i + 1] - positionPrice[j]) * positionSize[j]})
                    positionPrice[j] = Open_1min[j][i + 1]
                    Profit -= Open_1min[j][i+1] * fee
                    AccountBalance -= positionSize[j] * Open_1min[j][i+1] * fee
                    month_return -= positionSize[j] * Open_1min[j][i+1] * fee
                    CurrentPos[j] = -99
                    stopflag = -99
                    Close_pos = 0
                elif (pair_Trading or Hold_pos) and (not waitflag) and Close_pos == 1 and CurrentPos[j] == 0:
                    prev_Profit = copy(Profit)
                    Profit += positionPrice[j] - Open_1min[j][i+1]
                    month_return += positionSize[j] * (positionPrice[j] - Open_1min[j][i+1])
                    AccountBalance += positionSize[j] *  (positionPrice[j] - Open_1min[j][i+1])
                    if prev_Profit<Profit:
                        correct += 1
                        cashout.append({'x': i, 'y': Open_1min[j][i + 1], 'type': "win", 'position': 'short',
                                        'Profit': (positionPrice[j] - Open_1min[j][i+1]) * positionSize[j]})
                    else:
                        cashout.append({'x': i, 'y': Open_1min[j][i + 1], 'type': "loss", 'position': 'short',
                                        'Profit': (positionPrice[j] - Open_1min[j][i+1]) * positionSize[j]})
                    positionPrice[j] = Open_1min[j][i+1]
                    Profit -= Open_1min[j][i+1] * fee
                    AccountBalance -= positionSize[j] * Open_1min[j][i+1] * fee
                    month_return -= positionSize[j] * Open_1min[j][i+1] * fee
                    CurrentPos[j] = -99
                    stopflag = -99
                    Close_pos=0

                #########################################################################################################################
                ###########################   Trailing Stop Loss Logic:   ###############################################################
                if CurrentPos[j] ==0 and break_even and break_even_flag == 0:
                    if positionPrice[j] - Close_1min[j][i] > break_Even_Stage[0] * takeprofitval[j]:
                        ###### Set new Stop if we are in profit to breakeven
                        ##Set new Stop in Profit:
                        #stoplossval = -break_even_Amount[0]*takeprofitval
                        stoplossval[j]*=break_even_Amount[0]
                        break_even_flag+=1
                elif CurrentPos[j] ==1 and break_even and break_even_flag == 0:
                    if Close_1min[j][i] - positionPrice[j] > break_Even_Stage[0] * takeprofitval[j]:
                        ###### Set new Stop if we are in profit to breakeven
                        ##Set new Stop in Profit:
                        #stoplossval = -break_even_Amount[0]*takeprofitval
                        stoplossval[j] *= break_even_Amount[0]
                        break_even_flag += 1
                if CurrentPos[j] ==0 and break_even and break_even_flag <= 1:
                    # LastPrice = float(client.get_ticker(symbol=symbol)['lastPrice'])
                    if positionPrice[j] - Close_1min[j][i] > break_Even_Stage[1] * takeprofitval[j]:
                        ###### Set new Stop if we are in profit to breakeven
                        ##Set new Stop in Profit:
                        #stoplossval = -break_even_Amount[1] * takeprofitval
                        stoplossval[j] *= break_even_Amount[1]
                        break_even_flag += 1
                elif CurrentPos[j] ==1 and break_even and break_even_flag <=1:
                    if Close_1min[j][i] - positionPrice[j] > break_Even_Stage[1] * takeprofitval[j]:
                        ###### Set new Stop if we are in profit to breakeven
                        ##Set new Stop in Profit:
                        #stoplossval = -break_even_Amount[1]*takeprofitval
                        stoplossval[j] *= break_even_Amount[1]
                        break_even_flag += 1
                ################################################################################################################################
                ################################################################################################################################

                waitflag=0

                if CurrentPos[j] != PrevPos[j]:
                    signal1 = -99
                    signal2 = -99
                    print(f"\nCurrent Position {symbol[j]}:", CurrentPos[j])
                    print("Time:", Date_1min[j][i])
                    # print("Time Max",DateStream[max_pos])
                    # print("Time Min", DateStream[min_pos])
                    try:
                        print("Account Balance: ", AccountBalance, "Order Size:", positionSize[j], "PV:",
                              (Profit * 100) / (tradeNO * CloseStream[j][-1]), "Stoploss:", stoplossval[j], "TakeProfit:",
                              takeprofitval[j])
                    except Exception as e:
                        pass
            if i%1440==0 and i!=0:
                Daily_return.append(AccountBalance)#(day_return/day_start_equity)
                #day_return=0
                #day_start_equity=AccountBalance
            elif i==len(High_1min[0])-1:
                Daily_return.append(AccountBalance)#(day_return/day_start_equity)
            if i%43800==0 and i!=0 and ((time_period == 1 and test_set_length[2] == 'y') or (time_period == 12 and test_set_length[3] == 'm') or (time_period==52 and test_set_length[3] == 'w')):
                monthly_return.append(month_return)
                month_return=0
            elif i==len(High_1min[0])-1 and ((time_period == 1 and test_set_length[2] == 'y') or (time_period == 12 and test_set_length[3] == 'm') or (time_period==52 and test_set_length[3] == 'w')):
                monthly_return.append(month_return)
                month_return = 0
            if prev_Account_Bal!=AccountBalance:
                profitgraph.append(AccountBalance)
            PrevPos=copy(CurrentPos)

    risk_free_rate = 1.41  ##10 year treasury rate
    df=pd.DataFrame({'Account_Balance':Daily_return})
    df['daily_return'] = df['Account_Balance'].pct_change()
    df['cum_return'] = (1+df['daily_return']).cumprod()
    df['cum_roll_max'] = df['cum_return'].cummax()
    df['drawdown'] = df['cum_roll_max'] - df['cum_return']
    df['drawdown %'] = df['drawdown']/df['cum_roll_max']
    max_dd = df['drawdown %'].max()*100

    CAGR = ((df['cum_return'].iloc[-1])**(1/time_CAGR)-1)*100
    vol = (df['daily_return'].std() * np.sqrt(365))*100
    neg_vol = (df[df['daily_return']<0]['daily_return'].std()* np.sqrt(365))*100
    Sharpe_ratio = (CAGR-risk_free_rate)/vol
    sortino_ratio = (CAGR - risk_free_rate)/neg_vol
    calmar_ratio = CAGR/max_dd


    if pair_Trading and TPSL:
        print(f"Pair Trading {symbol}: {TIME_INTERVAL}min from a period of {time_period} {period_string} SL={percent_SL},TP={percent_TP}")
    else:
        print("\nSymbol(s):", symbol, "fee:", fee, "Order Size:", OrderSIZE, "Stoploss:", STOP, "Takeprofit:", TAKE)
    if break_even:
        print("Moving Stoploss ON")
    print(f"{TIME_INTERVAL} min OHLC Candle Sticks from a period of {time_period} {period_string}")
    print("Account Balance:", AccountBalance)
    print("% Gain on Account:", ((AccountBalance - originalBalance) * 100) / originalBalance)
    print("Total Returns:",AccountBalance-start_equity,"\n")
    month=0
    if len(monthly_return)>0:
        print("Monthly Returns")
    for x in ["month 1","month 2","month 3","month 4","month 5","month 6","month 7","month 8","month 9","month 10","month 11","month 12"]:
        try:
            print(f"{x}: {monthly_return[month]}")
            month+=1
        except:
            pass

    print(f"Annualized Volatility: {round(vol,4)}%")
    print(f"CAGR: {round(CAGR,4)}%")
    print("Sharpe Ratio:",round(Sharpe_ratio,4))
    print("Sortino Ratio:",round(sortino_ratio,4))
    print("Calmar Ratio:",round(calmar_ratio,4))
    print(f"Max Drawdown: {round(max_dd,4)}%")
    #ax1 = plt.subplot2grid((6, 1), (0, 0), rowspan=5, colspan=1)
    #ax2 = plt.subplot2grid((6, 1), (5, 0), rowspan=1, colspan=1)
    '''for trade in trades:
        #trade_date = mpl_dates.date2num([pd.to_datetime(trade['Date'])])[0]
        if trade['type'] == 'buy':
            ax1.scatter(trade['x'],trade['y']-.08, c='green', label='green', s=120, edgecolors='none',marker="^")
        else:
            ax1.scatter(trade['x'],trade['y']+.08, c='red', label='red', s=120, edgecolors='none', marker="v")'''
    longwins=0
    longlosses=0
    shortwins=0
    shortlosses=0
    longCash = 0
    shortCash = 0
    for trade in cashout:
        #trade_date = mpl_dates.date2num([pd.to_datetime(trade['Date'])])[0]
        '''if trade['type'] == 'win':
            ax1.scatter(trade['x'],trade['y']-.08, c='green', label='green', s=80, edgecolors='none',marker=".") ##green dot for successful trade
        else:
            ax1.scatter(trade['x'],trade['y']+.08, c='red', label='red', s=80, edgecolors='none', marker=".") ##red dot for unsuccessful trade'''

        if trade['position']=='long' and trade['type'] == 'win':
            longwins+=1
        elif trade['position']=='long' and trade['type'] == 'loss':
            longlosses+=1
        elif trade['position']=='short' and trade['type'] == 'win':
            shortwins+=1
        elif trade['position']=='short' and trade['type'] == 'loss':
            shortlosses+=1

        if trade['position'] == 'long':
            longCash+=float(trade['Profit'])
        else:
            shortCash+=float(trade['Profit'])
    '''for trade in signals:
        #trade_date = mpl_dates.date2num([pd.to_datetime(trade['Date'])])[0]
        if trade['type'] == 'signal1-0':
            ax1.scatter(trade['x'],trade['y']-.08, c='red', label='green', s=80, edgecolors='none',marker="|")
        elif trade['type'] == 'signal1-1':
            ax1.scatter(trade['x'],trade['y']+.08, c='green', label='red', s=80, edgecolors='none', marker="|")
        elif trade['type'] == 'signal2-1':
            ax1.scatter(trade['x'], trade['y'] + .08, c='green', label='red', s=80, edgecolors='none', marker="1")
        elif trade['type'] == 'signal2-0':
            ax1.scatter(trade['x'], trade['y'] + .08, c='red', label='red', s=80, edgecolors='none', marker="1")'''

    #ax1.plot(Close,label="Price",color="blue")
    print("Trades Made: ",len(trades))
    print("Successful Trades:",correct)
    print("Accuracy: ",(correct/len(trades))*100)
    try:
        print("# Shorts:", shortwins + shortlosses)
        print("Short W/L:",shortwins/shortlosses)
        print("Profit from Shorts:",shortCash)
    except Exception as E:
        pass
    try:
        print("# Longs:",longwins+longlosses)
        print("Long W/L:", longwins / longlosses)
        print("Profit from Longs:", longCash)
    except Exception as E:
        pass
    #Close1=data['Close']

    #xs = [x[0] for x in profitgraph]
    #ys = [x[1] for x in profitgraph]
    #x, y = zip(*profitgraph)
    #ax2.plot(profitgraphx, profitgraphy)
    plt.plot(profitgraph)
    #ax2.plot(profitgraph)
    #plt.plot(Close)
    if not pair_Trading:
        plt.title(f"{symbol}: {TIME_INTERVAL}min from a period of {time_period} {period_string} SL={STOP},TP={TAKE}")
    else:
        if not TPSL:
            plt.title(f"Pair Trading {symbol}: {TIME_INTERVAL}min from a period of {time_period} {period_string} SL={STOP},TP={TAKE}")
        else:
            plt.title(f"Pair Trading {symbol}: {TIME_INTERVAL}min from a period of {time_period} {period_string} SL={percent_SL},TP={percent_TP}")
    plt.ylabel('Dollars')
    plt.xlabel('# Trades')
    #plt.legend(loc=2)
    plt.show()
#time.sleep(60) ##don't close for 1 min
