import math
from collections import deque
import json,pprint
import asyncio
import time
import websockets
import Data_flow as flow
import sys, os
from binance.client import Client
import matplotlib.pyplot as plt
from copy import copy
import TradingStrats as TS
from TradingStrats import stochBB
from TradingStrats import SetSLTP
from binance.exceptions import BinanceAPIException
from binance.enums import *
import pandas as pd
from datetime import timezone,datetime,date,timedelta
from requests import exceptions
Coin_precision = -99  ##Precision Coin is measured up to
Order_precision = -99 ##Precision Orders are measured up to


##Different coins we can trade,
# kline_15m - OHLC for 15 min intervals, Change accordingly

PRICES = "wss://stream.binance.com:9443/ws/btcusdt@ticker"
SOCKET = "wss://stream.binance.com:9443/ws/btcusdt@kline_1m"
symbol="BTCUSDT"

PRICES = "wss://stream.binance.com:9443/ws/ethusdt@ticker"
SOCKET = "wss://stream.binance.com:9443/ws/ethusdt@kline_1m"
symbol="ETHUSDT"

#SOCKET = "wss://stream.binance.com:9443/ws/ltcusdt@kline_15m"
#symbol="LTCUSDT"

PRICES = "wss://stream.binance.com:9443/ws/solusdt@ticker"
SOCKET = "wss://stream.binance.com:9443/ws/solusdt@kline_1m"
symbol="SOLUSDT"

PRICES = "wss://stream.binance.com:9443/ws/bnbusdt@ticker"
SOCKET = "wss://stream.binance.com:9443/ws/bnbusdt@kline_1m"
symbol="BNBUSDT"


#SOCKET = "wss://stream.binance.com:9443/ws/adausdt@kline_15m"
#symbol="ADAUSDT"

#PRICES = "wss://stream.binance.com:9443/ws/dogeusdt@ticker"
#SOCKET = "wss://stream.binance.com:9443/ws/dogeusdt@kline_1m"
#symbol="DOGEUSDT"

#PRICES = "wss://stream.binance.com:9443/ws/maticusdt@ticker"
#SOCKET = "wss://stream.binance.com:9443/ws/maticusdt@kline_1m" ##############Price not increased by tick size error
#symbol="MATICUSDT"

#PRICES = "wss://stream.binance.com:9443/ws/bakeusdt@ticker"
#SOCKET = "wss://stream.binance.com:9443/ws/bakeusdt@kline_1m"
#symbol="BAKEUSDT"

#PRICES = "wss://stream.binance.com:9443/ws/sushiusdt@ticker"
#SOCKET = "wss://stream.binance.com:9443/ws/sushiusdt@kline_1m"
#symbol="SUSHIUSDT"

#PRICES = "wss://stream.binance.com:9443/ws/xrpusdt@ticker"
#SOCKET = "wss://stream.binance.com:9443/ws/xrpusdt@kline_1m"
#symbol="XRPUSDT"

#PRICES = "wss://stream.binance.com:9443/ws/dotusdt@ticker"
#SOCKET = "wss://stream.binance.com:9443/ws/dotusdt@kline_1m"
#symbol="DOTUSDT"

#PRICES = "wss://stream.binance.com:9443/ws/alphausdt@ticker"
#SOCKET = "wss://stream.binance.com:9443/ws/alphausdt@kline_1m"
#symbol = "ALPHAUSDT"


#PRICES = "wss://stream.binance.com:9443/ws/1000shibusdt@ticker"
#SOCKET = "wss://stream.binance.com:9443/ws/1000shibusdt@kline_1m"
#symbol = "1000SHIBUSDT"


if symbol=='BTCUSDT':
    Coin_precision = 2
    Order_precision = 2

elif symbol == 'ETHUSDT':
    Coin_precision = 2
    Order_precision = 2

elif symbol == 'LTCUSDT':
    Coin_precision = 2
    Order_precision = 3

elif symbol == 'SOLUSDT':
    Coin_precision = 3
    Order_precision = 0

elif symbol == 'BNBUSDT':
    Coin_precision = 2
    Order_precision = 2

elif symbol == 'ADAUSDT':
    Coin_precision = 4
    Order_precision = 0

elif symbol == 'DOGEUSDT':
    Coin_precision = 5
    Order_precision = 0

elif symbol == 'MATICUSDT':
    Coin_precision = 4
    Order_precision = 0

elif symbol == "BAKEUSDT":
    Coin_precision = 4
    Order_precision = 0

elif symbol =="SHIBUSDT":
    Coin_precision = 5
    Order_precision = 0

elif symbol =="XRPUSDT":
    Coin_precision = 4
    Order_precision = 1

elif symbol == "SUSHIUSDT":
    Coin_precision = 3
    Order_precision = 0

elif symbol == "DOTUSDT":
    Coin_precision = 3
    Order_precision = 1

elif symbol =="ALPHAUSDT":
    Coin_precision = 4
    Order_precision = 0

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
profitgraph=[0] #for graphing the profit change over time
pp = pprint.PrettyPrinter()
#profitgraphy=[0]
Sleep=0
#print(symbol)
#print(30)
client = Client(api_key='',api_secret='') ##Binance keys needed to get historical data/ Trade on an account


#OrderSize = 100
tradeNO=0 ##number of trades
######### variables used for trading Strats
signal =-99
stoplossval=0
takeprofitval=0
signal1=-99
signal2=-99
prediction1=-99
HighestUlt=50
Highestval=-99
PrevPos=-999
prevsignal1=-999
prevsignal2=-999
prediction2=-99
Highest=-999


leverage=35 ##leverage being used
AccountBalance=1000 ##Start amount for paper trading
EffectiveAccountBalance = AccountBalance*leverage
OriginalAccountSize=copy(AccountBalance)
OrderSIZE = .005 ##how much of account to use per trade in Decimal
positionSize = 0 ##altered later and sent as the orderQTY
break_even = 1 ##Set a new stop once in profit to cover the trading fee and breakeven
min_profit_accepted = .005
Order_Type = 'GTC' ##'IOC'
Stop_ID=''
Limit_ID=''
Order_ID=''
current_date = datetime.now(timezone.utc)
current_date = current_date.replace(tzinfo=timezone.utc)
current_date = round(float(current_date.timestamp()*1000-.5))
Market_Orders = 0 ##Allow Market Orders if limit is not filled
Trading=1 ##Actually trade on Binance, If Trading==1 then we are trading a strategy using the api keys specified above
          ## If Trading==0 then we are paper trading a strategy on historical data
#print(client.futures_get_all_orders(symbol=symbol)[-3])
#x = client.futures_get_all_orders(symbol=symbol)
'''order1 = client.futures_create_order(
                            symbol=symbol,
                            side=SIDE_BUY,
                            type=FUTURE_ORDER_TYPE_LIMIT,
                            timeInForce='GTC',
                            price=.01,
                            quantity=5000)
print(order1)
x = client.futures_get_all_orders(symbol=symbol, orderId=order1['orderId'])
print(x)
print(x[-1])'''
#x = client.futures_get_all_orders(symbol=symbol)
#print(x)
#client.get_ticker(symbol=symbol)
#print(client.futures_get_all_orders(symbol=symbol))
#print(client.futures_position_information(symbol=symbol)[0])
if Trading: ## Trade on Binance with above api key and secret key
    print("Symbol:", symbol, "Start Balance:", AccountBalance)
    async def runWS():
        async with websockets.connect(SOCKET) as websocket:
            global Sleep,Open, Close, High, Low, Volume,Profit,tradeNO,CurrentPos,positionPrice,\
                AccountBalance,EffectiveAccountBalance,positionSize,Highestprice,prediction1, signal1, signal2, HighestUlt, Highest, \
                stoplossval, takeprofitval,prevsignal1,prevsignal2,PrevPos,Stop_ID,Order_ID,Limit_ID
            Profit = 0
            tradeNO = 0
            CurrentPos = -99
            positionPrice = 0
            minuteFlag = 0 ##flag to signal new incoming kline
            current_stoplossval = 0
            current_takeprofitval = 0
            TimeCount=0
            TTC = 0
            timer = 0
            break_even_flag=0
            #print(client.futures_get_all_orders(symbol=symbol))
            #print(order1)
            start = datetime.now().time()
            yesterdate = date.today()

            for kline in client.get_historical_klines_generator(symbol, Client.KLINE_INTERVAL_1MINUTE,start_str="1 day ago UTC"):  ## get KLines with 15 minute intervals for the last month
                # print(kline)
                Date.append(datetime.utcfromtimestamp(int(kline[0]) / 1000))
                Open.append(float(kline[1]))
                Close.append(float(kline[4]))
                High.append(float(kline[2]))
                Low.append(float(kline[3]))
                Volume.append(float(kline[7]))

            y = client.futures_account_balance()
            AccountBalance = float(y[1]['balance'])

            '''try:
                bnb = await getBNBfee()
                printProfit(symbol, bnb)
            except Exception as e:
                pass'''

            while True:
                try:
                    try:
                        #pp.pprint(x)
                        #print(client.futures_position_information(symbol=symbol)[0])

                        message = await asyncio.create_task(websocket.recv()) ##pull klines
                        json_message = json.loads(message)
                        payload = json_message['k']



                        #########################################################################################
                        ######################## Runs every 30 seconds ##########################################
                        rightnow = datetime.now().time()
                        sec = timedelta(hours=0, minutes=0, seconds=30)
                        if (datetime.combine(date.today(), rightnow) - datetime.combine(yesterdate, start)) > sec:
                            start = datetime.now().time()
                            yesterdate = date.today()
                            ##Check every 30 seconds that limit/stop hasn't been hit
                            if Limit_ID!='' or Stop_ID!='':
                                x = client.futures_position_information(symbol=symbol)[0]
                                if float(x['positionAmt'])==0:
                                    CurrentPos = -99  ##Check if we are in a trade, if not reinitialize CurrentPos
                                    break_even_flag = 0  ##reinitialize
                                    Order_ID = ''
                                    Limit_ID = ''
                                    Stop_ID = ''
                                    client.futures_cancel_all_open_orders(symbol=symbol)  ##cancel open orders also
                                    print("No Open Position Cancelling Stop/Limit")

                            ##Check if Order was made but not hit, then maybe place market order
                            elif Order_ID!='' and Market_Orders==1:
                                x = client.futures_position_information(symbol=symbol)[0]

                                if float(x['positionAmt']) == 0 and CurrentPos==0: ##No position was opened so place market order
                                    client.futures_cancel_order(symbol=symbol)  ##cancel Orders
                                    if Order_precision != 0:
                                        await Order(round(positionSize,Order_precision),0,symbol,
                                                    current_stoplossval,current_takeprofitval,
                                                    Coin_precision,Market=1)
                                    else:
                                        await Order(round(positionSize), 0, symbol,
                                                    current_stoplossval, current_takeprofitval,
                                                    Coin_precision, Market=1)

                                elif float(x['positionAmt']) == 0 and CurrentPos == 1:  ##No position was opened so place market order
                                    client.futures_cancel_order(symbol=symbol)  ##cancel Orders
                                    if Order_precision != 0:
                                        await Order(round(positionSize,Order_precision), 1, symbol,
                                                    current_stoplossval, current_takeprofitval,
                                                    Coin_precision, Market=1)
                                    else:
                                        await Order(round(positionSize), 1, symbol,
                                                    current_stoplossval, current_takeprofitval,
                                                    Coin_precision, Market=1)
                        ###############################################################################################################
                        ###############################################################################################################

                        if payload['x']: ##if payload['x']==1 then it is a new kline we have received => new OHLC data
                            Open = flow.dataStream(Open, float(payload['o']), 1, 300)
                            Close = flow.dataStream(Close, float(payload['c']), 1, 300)
                            High = flow.dataStream(High, float(payload['h']), 1, 300)
                            Low = flow.dataStream(Low, float(payload['l']), 1, 300)
                            Volume = flow.dataStream(Volume, float(payload['q']), 1, 300)
                            minuteFlag = 1 ##new OHLC data so check Strategy for signals of entry points

                        if minuteFlag: ##new OHLC data

                            y = client.futures_account_balance()
                            AccountBalance = float(y[1]['balance'])
                            EffectiveAccountBalance = AccountBalance*leverage ##Get Account Balance when multiplied by leverage to use for deciding positionSize based of OrderSIZE above

                            minuteFlag = 0 ##switch off flag


                            ######################## These are some trading strategies I have coded up as functions, found in TradingStrats.py #######################################

                            #prediction1,Type1 = TS.MovingAverage(Close,prediction1)
                            #prediction1,signal1,signal2,Type1 =TS.StochRSIMACD(prediction1,Close,signal1,signal2)
                            #prediction1, signal1, signal2, Type1 = TS.tripleEMAStochasticRSIATR(Close,signal1,signal2,prediction1)
                            prediction1,stoplossval,takeprofitval = TS.Fractal(Close,Low,High,prediction1)
                            #prediction1, signal1, signal2, HighestUlt, Highest, Type1 = TS.UltOscMACD(prediction1,Close,High, Low,signal1, signal2,HighestUlt, Highest)
                            #prediction1, signal1, Type1 = TS.RSIStochEMA200(prediction1,Close,High,Low,signal1,signal2,CurrentPos)
                            #prediction1,Type1 = TS.Fractal2(Close,Low,High,signal1,prediction1)

                            #prediction1, Type1 = stochBB(prediction1, Close)

                            #stoplossval, takeprofitval = SetSLTP(stoplossval, takeprofitval, Close, High,Low, prediction1, CurrentPos, Type1) ##This function sets the stoploss and takeprofit based off the Type1 variable returned by the above functions

                            ##These trading strategies have custom stoploss & takeprofits:
                            #takeprofitval, stoplossval, prediction1, signal1= TS.SARMACD200EMA(stoplossval, takeprofitval,Close,High,Low,prediction1,CurrentPos,signal1)
                            #takeprofitval, stoplossval, prediction1, signal1= TS.TripleEMA(stoplossval, takeprofitval,Close,High,Low,prediction1,CurrentPos,signal1)

                            if (prediction1 == 1 or prediction1 == 0) and (min_profit_accepted * Close[-1] > takeprofitval):
                                prediction1 = -99

                            x = client.futures_position_information(symbol=symbol)[0]

                            #print("position Amount:",x)
                            #time.sleep(5)
                            if float(x['positionAmt']) == 0:
                                CurrentPos = -99  ##Check if we are in a trade, if not reinitialize CurrentPos
                                break_even_flag = 0 ##reinitialize
                                Order_ID=''
                                Limit_ID=''
                                Stop_ID=''
                                client.futures_cancel_all_open_orders(symbol=symbol)  ##cancel open orders also

                            elif float(x['positionAmt']) < 0:
                                CurrentPos = 0  ##in a short
                                ##Check that stoploss and takeprofit are set:
                                try:
                                    if Stop_ID=='':
                                        #print("Z1: Stop Order not sent, trying again Attempting Stop Price:",round(float(x['entryPrice']) + current_stoplossval + (5 * math.pow(10, -Coin_precision - 1)),Coin_precision))
                                        order2 = client.futures_create_order(
                                            symbol=symbol,
                                            side=SIDE_BUY,
                                            type=FUTURE_ORDER_TYPE_STOP_MARKET,
                                            quantity=-1*float(x['positionAmt']),
                                            stopPrice=round(float(x['entryPrice']) + current_stoplossval + (5 * math.pow(10, -Coin_precision - 1)),Coin_precision))
                                        Stop_ID = order2['orderId']
                                    if Limit_ID=='':
                                        #print("Z1: Limit Order not sent, trying again Attempting Limit Price:",round(float(x['entryPrice']) - current_takeprofitval, Coin_precision))
                                        order3 = client.futures_create_order(
                                            symbol=symbol,
                                            side=SIDE_BUY,
                                            type=FUTURE_ORDER_TYPE_LIMIT,
                                            price=round(float(x['entryPrice']) - current_takeprofitval, Coin_precision),
                                            timeInForce=TIME_IN_FORCE_GTC,
                                            quantity=-1*float(x['positionAmt']))
                                        Limit_ID = order3['orderId']
                                except BinanceAPIException as d:
                                    pass
                                    if d.message=='Order would immediately trigger.':
                                        print("Order would immediately Trigger, Cancelling and sleeping for 5 minutes")
                                        order4= client.futures_create_order(
                                            symbol=symbol,
                                            side=SIDE_BUY,
                                            type=FUTURE_ORDER_TYPE_MARKET,
                                            quantity=-1*float(x['positionAmt']))
                                        time.sleep(300)  ##sleep for 5 minutes
                                        Sleep=1
                                        break

                                if break_even and break_even_flag==0:
                                    LastPrice = float(client.get_ticker(symbol=symbol)['lastPrice'])
                                    if float(x['entryPrice']) - LastPrice >.5*current_takeprofitval:
                                        ###### Set new Stop if we are in profit to breakeven
                                        ##Set new Stop in Profit:
                                        try:
                                            order2 = client.futures_create_order(
                                                symbol=symbol,
                                                side=SIDE_BUY,
                                                type=FUTURE_ORDER_TYPE_STOP_MARKET,
                                                quantity=-1 * float(x['positionAmt']),
                                                stopPrice=round(float(x['entryPrice']) + 5 * math.pow(10, -Coin_precision - 1), Coin_precision))
                                            if order2['status']=="NEW":
                                                client.futures_cancel_order(symbol=symbol,orderId=Stop_ID)
                                                print("New Stop placed at .1x(takeprofit)")
                                                break_even_flag = 1
                                                Stop_ID=order2['orderId']
                                        except BinanceAPIException as d:
                                            if d.message=='Order would immediately trigger.':
                                                print("New Stop not placed as order would trigger immediately, LastPrice:",LastPrice)

                                if break_even and break_even_flag<=1:
                                    LastPrice = float(client.get_ticker(symbol=symbol)['lastPrice'])
                                    if float(x['entryPrice']) - LastPrice >.7*current_takeprofitval:
                                        ###### Set new Stop if we are in profit to breakeven
                                        ##Set new Stop in Profit:
                                        try:
                                            order2 = client.futures_create_order(
                                                symbol=symbol,
                                                side=SIDE_BUY,
                                                type=FUTURE_ORDER_TYPE_STOP_MARKET,
                                                quantity=-1 * float(x['positionAmt']),
                                                stopPrice=round(float(x['entryPrice'])-.4*current_takeprofitval + 5 * math.pow(10, -Coin_precision - 1), Coin_precision))
                                            if order2['status']=="NEW":
                                                client.futures_cancel_order(symbol=symbol, orderId=Stop_ID)
                                                print("New Stop placed at .4x(takeprofit)")
                                                break_even_flag = 2
                                                Stop_ID=order2['orderId']
                                        except BinanceAPIException as d:
                                            if d.message=='Order would immediately trigger.':
                                                print("New Stop not placed as order would trigger immediately, LastPrice:",LastPrice)


                                if break_even and break_even_flag<=2:
                                    if float(x['entryPrice']) - LastPrice >.85*takeprofitval:
                                        ###### Set new Stop if we are in profit to breakeven
                                        ##Set new Stop in Profit:
                                        try:
                                            order2 = client.futures_create_order(
                                                symbol=symbol,
                                                side=SIDE_BUY,
                                                type=FUTURE_ORDER_TYPE_STOP_MARKET,
                                                quantity=-1 * float(x['positionAmt']),
                                                stopPrice=round(float(x['entryPrice']) -.6*current_takeprofitval + 5 * math.pow(10, -Coin_precision - 1), Coin_precision))
                                            if order2['status']=="NEW":
                                                client.futures_cancel_order(symbol=symbol,orderId=Stop_ID)
                                                print("New Stop placed at .7x(takeprofit)")
                                                break_even_flag = 3
                                                Stop_ID=order2['orderId']
                                        except BinanceAPIException as d:
                                            if d.message=='Order would immediately trigger.':
                                                print("New Stop not placed as order would trigger immediately, LastPrice:",LastPrice)

                            elif float(x['positionAmt']) > 0:
                                CurrentPos = 1  ##in a long
                                ##Check that stoploss and takeprofit are set:
                                try:
                                    if Stop_ID=='':
                                        #print("Z2: Stop Order not sent, trying again Attempting Stop Price:",round(float(x['entryPrice']) - current_stoplossval - (5 * math.pow(10, -Coin_precision - 1)),Coin_precision))
                                        ##stoploss
                                        order2 = client.futures_create_order(
                                            symbol=symbol,
                                            side=SIDE_SELL,
                                            type=FUTURE_ORDER_TYPE_STOP_MARKET,
                                            quantity=float(x['positionAmt']),
                                            stopPrice=round(float(x['entryPrice']) - current_stoplossval - (5 * math.pow(10, -Coin_precision - 1)),Coin_precision))
                                        Stop_ID=order2['orderId']
                                        ##takeprofit:
                                    if Limit_ID=='':
                                        #print("Z2: Limit Order not sent, trying again Attempting Limit Price:",round(float(x['entryPrice']) + current_takeprofitval, Coin_precision))
                                        order3 = client.futures_create_order(
                                            symbol=symbol,
                                            side=SIDE_SELL,
                                            type=FUTURE_ORDER_TYPE_LIMIT,
                                            price=round(float(x['entryPrice']) + current_takeprofitval, Coin_precision),
                                            timeInForce=TIME_IN_FORCE_GTC,
                                            quantity=float(x['positionAmt']))
                                        Limit_ID=order3['orderId']
                                except BinanceAPIException as d:
                                    pass
                                    if d.message=='Order would immediately trigger.':
                                        print("Order would immediately Trigger, Cancelling and sleeping for 5 minutes")
                                        order4= client.futures_create_order(
                                            symbol=symbol,
                                            side=SIDE_SELL,
                                            type=FUTURE_ORDER_TYPE_MARKET,
                                            quantity=float(x['positionAmt']))
                                        time.sleep(300) ##sleep for 5 minutes
                                        Sleep = 1
                                        break

                                if break_even and break_even_flag==0:
                                    LastPrice = float(client.get_ticker(symbol=symbol)['lastPrice'])
                                    if LastPrice - float(x['entryPrice']) >.5*takeprofitval:
                                        ###### Set new Stop if we are in profit to breakeven
                                        ##Set new Stop in Profit:
                                        try:
                                            order2 = client.futures_create_order(
                                                symbol=symbol,
                                                side=SIDE_SELL,
                                                type=FUTURE_ORDER_TYPE_STOP_MARKET,
                                                quantity=float(x['positionAmt']),
                                                stopPrice=round(float(x['entryPrice']) - 5 * math.pow(10, -Coin_precision - 1), Coin_precision))
                                            if order2['status']=="NEW":
                                                client.futures_cancel_order(symbol=symbol,orderId=Stop_ID)  ##cancel open orders also
                                                print("New Stop placed at .4x(takeprofit)")
                                                break_even_flag = 1
                                                Stop_ID=order2['orderId']
                                        except BinanceAPIException as d:
                                            if d.message=='Order would immediately trigger.':
                                                print("New Stop not placed as order would trigger immediately, LastPrice:",LastPrice)

                                if break_even and break_even_flag<=1:
                                    LastPrice = float(client.get_ticker(symbol=symbol)['lastPrice'])

                                    if LastPrice - float(x['entryPrice']) >.7*takeprofitval:
                                        ###### Set new Stop if we are in profit to breakeven
                                        ##Set new Stop in Profit:
                                        try:
                                            order2 = client.futures_create_order(
                                                symbol=symbol,
                                                side=SIDE_SELL,
                                                type=FUTURE_ORDER_TYPE_STOP_MARKET,
                                                quantity=float(x['positionAmt']),
                                                stopPrice=round(float(x['entryPrice']) + current_takeprofitval*.4 - 5 * math.pow(10, -Coin_precision - 1), Coin_precision))
                                            if order2['status']=="NEW":
                                                client.futures_cancel_order(symbol=symbol,orderId=Stop_ID)  ##cancel open orders also
                                                print("New Stop placed at .4x(takeprofit)")
                                                break_even_flag = 2
                                                Stop_ID=order2['orderId']
                                        except BinanceAPIException as d:
                                            if d.message=='Order would immediately trigger.':
                                                print("New Stop not placed as order would trigger immediately, LastPrice:",LastPrice)

                                if break_even and break_even_flag<=2:
                                    LastPrice = float(client.get_ticker(symbol=symbol)['lastPrice'])
                                    if LastPrice - float(x['entryPrice']) >.85*takeprofitval:
                                        ###### Set new Stop if we are in profit to breakeven
                                        ##Set new Stop in Profit:
                                        try:
                                            order2 = client.futures_create_order(
                                                symbol=symbol,
                                                side=SIDE_SELL,
                                                type=FUTURE_ORDER_TYPE_STOP_MARKET,
                                                quantity=float(x['positionAmt']),
                                                stopPrice=round(float(x['entryPrice'])+current_takeprofitval*.6 - 5 * math.pow(10, -Coin_precision - 1), Coin_precision))
                                            if order2['status']=="NEW":
                                                client.futures_cancel_order(symbol=symbol,orderId=Stop_ID)  ##cancel open orders also
                                                print("New Stop placed at .7x(takeprofit)")
                                                break_even_flag = 3
                                                Stop_ID=order2['orderId']
                                        except BinanceAPIException as d:
                                            if d.message=='Order would immediately trigger.':
                                                print("New Stop not placed as order would trigger immediately, LastPrice:",LastPrice)
                                                ##get rid of partially filled orders

                            if Order_ID!='':
                                if client.futures_get_all_orders(symbol=symbol, orderId=Order_ID)[-1]['status'] == 'PARTIALLY FILLED':
                                    client.futures_cancel_order(symbol=symbol,orderId=Order_ID)  ##cancel leftover order


                            if CurrentPos == -99 and prediction1 == 0:  ##not in a trade but want to enter a short position
                                LP = float(client.get_ticker(symbol=symbol)['lastPrice'])
                                positionPrice = LP
                                positionSize = (OrderSIZE * EffectiveAccountBalance) / positionPrice ##work out OrderQTY
                                #print(positionSize)
                                CurrentPos = 0
                                tradeNO += 1
                                Highestprice = positionPrice
                                # stoplossval = positionPrice * trailing_stoploss
                                #trades.append({'x': i, 'y': positionPrice, 'type': "sell",'current_price': positionPrice})
                                ##Stoploss and takeprofit in case the stop/limit order isn't filled
                                current_stoplossval = copy(stoplossval)
                                current_takeprofitval = copy(takeprofitval)

                                ##Create Order on Binance
                                if Order_precision!=0:
                                    await Order(round(positionSize,Order_precision), 0, symbol,stoplossval,takeprofitval,Coin_precision)
                                else:
                                    await Order(round(positionSize), 0, symbol, stoplossval, takeprofitval, Coin_precision)

                            elif CurrentPos == -99 and prediction1 == 1: ##not in a trade but want to enter a Long position
                                LP = float(client.get_ticker(symbol=symbol)['lastPrice'])
                                positionPrice = LP
                                positionSize = (OrderSIZE * EffectiveAccountBalance) / positionPrice ##work out OrderQTY
                                CurrentPos = 1
                                tradeNO += 1
                                Highestprice = positionPrice
                                # stoplossval = positionPrice * trailing_stoploss
                                #trades.append({'x': i, 'y': positionPrice, 'type': "buy",'current_price': positionPrice})
                                ##Stoploss and takeprofit in case the stop/limit order isn't filled
                                current_stoplossval = copy(stoplossval)
                                current_takeprofitval = copy(takeprofitval)

                                ##Create Order on Binance
                                if Order_precision!=0:
                                    await Order(round(positionSize,Order_precision), 1, symbol,stoplossval,takeprofitval,Coin_precision)
                                else:
                                    await Order(round(positionSize), 1, symbol, stoplossval, takeprofitval,Coin_precision)



                            if CurrentPos != PrevPos:
                                bnb = float(client.get_ticker(symbol="BNBUSDT")['lastPrice'])
                                signal1 = -99
                                signal2 = -99
                                print("Current Position:", CurrentPos)
                                #print("Margin:", positionPrice - Close[-1])
                                # print("Date:",DateStream[-1])
                                try:
                                    printProfit(symbol, bnb)
                                except Exception as e:
                                    pass
                            # if prevProfit!=Profit:
                            #profitgraph.append(Profit)
                            PrevPos = copy(CurrentPos)

                    except BinanceAPIException as e:  # BinanceAPIException
                        print(e.status_code)
                        print(e.message)

                except Exception as e:  # Check for Errors in Code
                    print(e)
                    exc_type, exc_obj, exc_tb = sys.exc_info()
                    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                    print(exc_type, fname, exc_tb.tb_lineno)


    def printProfit(S,bnb):
        global Profit,tradeNO,stoplossval,takeprofitval,Close,AccountBalance
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
        print("Account Balance: ", AccountBalance, "Profit:", Profit)
        print("PV:", (Profit * 100) / (tradeNO * Close[-1]),"Stoploss:",stoplossval, "TakeProfit:", takeprofitval)
        Profit=0

    async def Order(q, side1, s,stoploss,takeprofit,CP,Market=0):
        global Stop_ID,Limit_ID,Order_ID
        try:
            try:
                PP = float(client.get_ticker(symbol=symbol)['lastPrice'])
                if side1 and Market==0: ##Long
                    ##Place the Long
                    order1 = client.futures_create_order(
                        symbol=s,
                        side=SIDE_BUY,
                        type=FUTURE_ORDER_TYPE_LIMIT,
                        price= PP,
                        timeInForce=TIME_IN_FORCE_GTC,
                        quantity=q)
                    Order_ID=order1['orderId']
                    x = client.futures_get_all_orders(symbol=symbol, orderId=Order_ID)
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
                    ##Place the short
                    order1 = client.futures_create_order(
                        symbol=s,
                        side=SIDE_SELL,
                        type=FUTURE_ORDER_TYPE_LIMIT,
                        price=PP,
                        timeInForce=TIME_IN_FORCE_GTC,
                        quantity=q)
                    Order_ID = order1['orderId']
                    x = client.futures_get_all_orders(symbol=symbol, orderId=Order_ID)
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
                    client.futures_cancel_all_open_orders(symbol=symbol)  ##cancel open orders
                    ##Market order so we don't miss the move
                    order1 = client.futures_create_order(
                        symbol=s,
                        side=SIDE_BUY,
                        type=FUTURE_ORDER_TYPE_MARKET,
                        quantity=q)
                    Order_ID=order1['orderId']
                    x = client.futures_get_all_orders(symbol=symbol, orderId=order1['orderId'])
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
                    client.futures_cancel_all_open_orders(symbol=symbol)  ##cancel open orders
                    ##Market order so we don't miss the move
                    order1 = client.futures_create_order(
                        symbol=s,
                        side=SIDE_SELL,
                        type=FUTURE_ORDER_TYPE_MARKET,
                        quantity=q)
                    Order_ID=order1['orderId']
                    x = client.futures_get_all_orders(symbol=symbol, orderId=order1['orderId'])
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
            asyncio.get_event_loop().run_until_complete(runWS())
        except Exception as e:
            #print("Error:",e)
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)
            print("Error in websocket, retrying")
            time.sleep(1)
            run()


    run()

    if Sleep == 1:
        Sleep = 0
        print("Done Sleeping")
        run()
elif Trading==0:       ## Paper Trading, exact same as above but simulated trading with graphs
    leverage = 35  ##leverage being used
    AccountBalance = 2185
    originalBalance=copy(AccountBalance)
    trailing_stop = .001  ##if market dips we sell/buy
    trailing_execution = .5  ##when to start the trailing stoploss
    trail_start = 0
    Use_trail_stop=0 ##turn on or off trailing stop
    stopflag=-99
    stops_executed=0
    symbol = "BTCUSDT"
    #symbol="ETHUSDT"
    #symbol='SHIBUSDT'
    #symbol='ADAUSDT'
    #symbol='BAKEUSDT'
    #symbol='BNBUSDT'
    #symbol= 'SUSHIUSDT'
    #symbol = 'SOLUSDT' ###############################
    #symbol = 'MATICUSDT' #############################
    #symbol = 'DOGEUSDT'
    #symbol = "XRPUSDT"
    #symbol = "DOTUSDT"
    #symbol = "ALPHAUSDT"
    print("Symbol:", symbol, "Start Balance:", AccountBalance)
    for kline in client.get_historical_klines_generator(symbol, Client.KLINE_INTERVAL_1MINUTE,start_str="1 month ago UTC"):  ## get KLines with 15 minute intervals for the last month
        # print(kline)
        Date.append(datetime.datetime.utcfromtimestamp(int(kline[0]) / 1000))
        Open.append(float(kline[1]))
        Close.append(float(kline[4]))
        High.append(float(kline[2]))
        Low.append(float(kline[3]))
        Volume.append(float(kline[7]))
    for i in range(len(Close)):
        #global trailing_stoploss,Highestprice
        #DateStream = flow.dataStream(DateStream, Date[i], 1, 300)
        OpenStream = flow.dataStream(OpenStream, Open[i], 1, 300)
        CloseStream = flow.dataStream(CloseStream, Close[i], 1, 300)
        HighStream = flow.dataStream(HighStream, High[i], 1, 300)
        LowStream = flow.dataStream(LowStream, Low[i], 1, 300)
        VolumeStream = flow.dataStream(VolumeStream, Volume[i], 1, 300)
        #print(len(OpenStream))
        if len(OpenStream)>=299:
            prevProfit=copy(Profit)
            EffectiveAccountBalance = AccountBalance*leverage
            if CurrentPos== -99:
                #prediction1,Type = TS.MovingAverage(CloseStream,prediction1)
                #prediction1,signal1,signal2,Type =TS.StochRSIMACD(prediction1,CloseStream,signal1,signal2) ###########################################
                #prediction1, signal1, signal2, Type = TS.tripleEMAStochasticRSIATR(CloseStream,signal1,signal2,prediction1)
                #prediction1,signal1,signal2,HighestUlt,Highest,Type = TS.UltOscMACD(prediction1,CloseStream,HighStream,LowStream,signal1,signal2,HighestUlt,Highest)
                #prediction1, signal1, Type = TS.RSIStochEMA200(prediction1,CloseStream,HighStream,LowStream,signal1,signal2,CurrentPos)
                #prediction1,Type = TS.Fractal2(CloseStream,LowStream,HighStream,signal1,prediction1) ###############################################
                #prediction1,Type = TS.stochBB(prediction1,CloseStream)

                #stoplossval, takeprofitval = TS.SetSLTP(stoplossval, takeprofitval,CloseStream,HighStream,LowStream,prediction1,CurrentPos,Type)

                prediction1,stoplossval,takeprofitval = TS.Fractal(CloseStream, LowStream, HighStream,prediction1)
                #takeprofitval, stoplossval, prediction1, signal1= TS.SARMACD200EMA(stoplossval, takeprofitval,CloseStream,HighStream,LowStream,prediction1,CurrentPos,signal1)
                #takeprofitval, stoplossval, prediction1, signal1= TS.TripleEMA(stoplossval, takeprofitval,CloseStream,HighStream,LowStream,prediction1,CurrentPos,signal1)

                ##If the trade won't cover the fee & profit something then don't place it
                if (prediction1 == 1 or prediction1 == 0) and (.005 * Close[-1] > takeprofitval):
                    prediction1 = -99
        #################################################################
            #################################################################

            if CurrentPos == -99 and prediction1 == 0:
                positionPrice = CloseStream[len(CloseStream) - 1]
                positionSize= (OrderSIZE*EffectiveAccountBalance)/positionPrice
                CurrentPos = 0
                tradeNO+=1
                #Highestprice = positionPrice
               #stoplossval = positionPrice * trailing_stoploss
                trades.append({'x':i,'y':positionPrice,'type': "sell",'current_price': positionPrice})
                Profit -= CloseStream[len(CloseStream) - 1] * .0004
                AccountBalance -= positionSize * CloseStream[-1] * .0004
                trail_start = trailing_execution*takeprofitval
                stopflag = -99
            elif CurrentPos == -99 and prediction1 == 1:
                positionPrice = CloseStream[len(CloseStream) - 1]
                positionSize = (OrderSIZE * EffectiveAccountBalance) / positionPrice
                CurrentPos = 1
                tradeNO += 1
                #Highestprice = positionPrice
                #stoplossval = positionPrice * trailing_stoploss
                trades.append({'x':i,'y':positionPrice, 'type': "buy",'current_price': positionPrice})
                Profit -= CloseStream[len(CloseStream) - 1] * .0004
                AccountBalance -= positionSize * CloseStream[-1] * .0004
                trail_start = trailing_execution * takeprofitval
                stopflag = -99

            ############### break-even:
            #if CurrentPos==0 and break_even and positionPrice-CloseStream[-1] > .0025*positionPrice:



            if positionPrice - HighStream[ - 1] < -stoplossval and CurrentPos == 0:
                Profit +=-stoplossval #positionPrice-CloseStream[len(CloseStream) - 1]  ##This will be positive if the price went down
                AccountBalance += positionSize * -stoplossval # (positionPrice-CloseStream[len(CloseStream) - 1])
                positionPrice = CloseStream[len(CloseStream) - 1]
                Profit -= CloseStream[-1] * .0004
                AccountBalance-= positionSize*CloseStream[-1] * .0004
                cashout.append({'x': i, 'y': CloseStream[-1], 'type': "loss",'position':'short','Profit': -stoplossval*positionSize})
                # CurrentPos = -99
                CurrentPos = -99
                stopflag = -99

                Profit -= CloseStream[len(CloseStream) - 1] * .0004
            elif LowStream[- 1] - positionPrice < -stoplossval and CurrentPos == 1:
                Profit +=-stoplossval #CloseStream[len(CloseStream) - 1] - positionPrice ##This will be positive if the price went up
                AccountBalance += positionSize* -stoplossval #(CloseStream[len(CloseStream) - 1] - positionPrice)
                positionPrice = CloseStream[len(CloseStream) - 1]
                Profit -= CloseStream[-1] * .0004
                AccountBalance -= positionSize * CloseStream[-1] * .0004
                cashout.append({'x': i, 'y': CloseStream[-1], 'type': "loss",'position':'long','Profit': -stoplossval*positionSize})
                # CurrentPos = -99
                CurrentPos = -99
                stopflag = -99

                Profit -= CloseStream[len(CloseStream) - 1] * .0004
            elif positionPrice - LowStream[-1] > takeprofitval and CurrentPos == 0 and (not Use_trail_stop):
                Profit += takeprofitval #positionPrice - CloseStream[-1]
                AccountBalance += positionSize *  takeprofitval #(positionPrice - CloseStream[len(CloseStream) - 1])
                correct += 1
                positionPrice = CloseStream[-1]
                Profit -= CloseStream[-1] * .0004
                AccountBalance -= positionSize * CloseStream[-1] * .0004
                cashout.append({'x': i, 'y': CloseStream[-1], 'type': "win",'position':'short','Profit': takeprofitval*positionSize})
                CurrentPos = -99
                stopflag = -99

            elif HighStream[-1] - positionPrice > takeprofitval and CurrentPos == 1 and (not Use_trail_stop):
                Profit +=  takeprofitval #CloseStream[-1] - positionPrice
                AccountBalance += positionSize *  takeprofitval #(CloseStream[len(CloseStream) - 1] - positionPrice)
                correct += 1
                positionPrice = CloseStream[-1]
                Profit -= CloseStream[-1] * .0004
                AccountBalance -= positionSize * CloseStream[-1] * .0004
                cashout.append({'x': i, 'y': CloseStream[-1], 'type': "win",'position':'long','Profit': takeprofitval*positionSize})
                CurrentPos = -99
                stopflag = -99
            #########################################################################################################################
            ###########################   Trailing Stop Loss Logic:   ###############################################################
            if positionPrice - CloseStream[-1] > trail_start and CurrentPos == 0 and Use_trail_stop:
                ##trailing stoploss started
                Stopflag=0

            elif CloseStream[-1] - positionPrice > trail_start and CurrentPos == 1 and Use_trail_stop:
                ##trailing stoploss started
                Stopflag = 1
            if stopflag ==0 and ((CloseStream[-1]-positionPrice-trail_start)/trail_start)>trailing_stop and Use_trail_stop:
                stops_executed += 1
                Profit += trail_start*(1-trailing_stop)#positionPrice - CloseStream[-1]
                AccountBalance += positionSize*trail_start*(1-trailing_stop)#positionPrice - CloseStream[-1]
                correct += 1
                positionPrice = CloseStream[-1]
                Profit -= CloseStream[-1] * .00036
                AccountBalance -= positionSize * CloseStream[-1] * .00036
                cashout.append({'x': i, 'y': CloseStream[-1], 'type': "win", 'position': 'short','Profit': takeprofitval * positionSize})
                CurrentPos = -99
                stopflag = -99
            elif stopflag ==1 and ((trail_start+positionPrice-CloseStream[-1])/trail_start)<-trailing_stop and Use_trail_stop:
                #print("Trailing stop executed")
                stops_executed+=1
                Profit += trail_start*(1-trailing_stop) #CloseStream[-1] - positionPrice
                AccountBalance +=positionSize*trail_start*(1-trailing_stop) #(CloseStream[len(CloseStream) - 1] - positionPrice)
                correct += 1
                positionPrice = CloseStream[-1]
                Profit -= CloseStream[-1] * .00036
                AccountBalance -= positionSize * CloseStream[-1] * .00036
                cashout.append({'x': i, 'y': CloseStream[-1], 'type': "win", 'position': 'long','Profit': takeprofitval * positionSize})
                CurrentPos = -99
                stopflag = -99
            if stopflag==0 and CloseStream[-1] < positionPrice - trail_start and Use_trail_stop:
                trail_start = positionPrice - CloseStream[-1]
            elif stopflag ==1 and CloseStream[-1]>positionPrice + trail_start and Use_trail_stop:
                trail_start = CloseStream[-1] - positionPrice
            ################################################################################################################################
            ################################################################################################################################

            if CurrentPos == 0 and CloseStream[-1] < Highestprice:
                pass
                #Highestprice = CloseStream[-1]
                #stoplossval = Highestprice * trailing_stoploss
            elif CurrentPos == 1 and CloseStream[-1] > Highestprice:
                pass
                #Highestprice = CloseStream[-1]
                #stoplossval = Highestprice * trailing_stoploss
            '''if CurrentPos == 0 and LowStream[-1] < Highestprice:
                #pass
                Highestprice = LowStream[-1]
                stoplossval = Highestprice * trailing_stoploss
            elif CurrentPos == 1 and HighStream[-1] > Highestprice:
                #pass
                Highestprice = HighStream[-1]
                stoplossval = Highestprice * trailing_stoploss'''


            if CurrentPos!=PrevPos:
                signal1=-99
                signal2=-99
                print("Current Position:",CurrentPos,"\n")
                print("Margin:",positionPrice-CloseStream[-1])
                #print("Date:",DateStream[-1])
                try:
                    print("Account Balance: ", AccountBalance,"Order Size:",positionSize,"PV:",(Profit * 100) / (tradeNO * CloseStream[-1]),"Stoploss:",stoplossval,"TakeProfit:",takeprofitval)
                except Exception as e:
                    pass
            #if prevProfit!=Profit:
            profitgraph.append(Profit)
            PrevPos=copy(CurrentPos)
    print("Symbol:",symbol)
    print("Account Balance:", AccountBalance)
    print("% Gain on Account:", ((AccountBalance - originalBalance) * 100) / originalBalance)
    print("Stops Executed:",stops_executed)
    ax1 = plt.subplot2grid((6, 1), (0, 0), rowspan=5, colspan=1)
    ax2 = plt.subplot2grid((6, 1), (5, 0), rowspan=1, colspan=1)
    for trade in trades:
        #trade_date = mpl_dates.date2num([pd.to_datetime(trade['Date'])])[0]
        if trade['type'] == 'buy':
            ax1.scatter(trade['x'],trade['y']-.08, c='green', label='green', s=120, edgecolors='none',marker="^")
        else:
            ax1.scatter(trade['x'],trade['y']+.08, c='red', label='red', s=120, edgecolors='none', marker="v")
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

    '''High1=np.array(High)
    Low1 = np.array(Low)
    SAR=ta.SAR(High1,Low1,acceleration=.02,maximum=.2)
    x=[]
    for i in range(len(SAR)):
        x.append(i)
    x=np.array(x)
    ax1.scatter(x,SAR, c='black', s=80, edgecolors='none',marker=".")'''

    ax1.plot(Close,label="Price",color="blue")
    print("Trades Made: ",len(trades))
    print("Successful Trades:",correct)
    print("Accuracy: ",(correct/len(trades))*100)
    try:
        print("Short W/L:",shortwins/shortlosses)
        print("Profit from Shorts:",shortCash)
    except Exception as E:
        pass
    try:
        print("Long W/L:", longwins / longlosses)
        print("Profit from Longs:", longCash)
    except Exception as E:
        pass
    #Close1=data['Close']

    #xs = [x[0] for x in profitgraph]
    #ys = [x[1] for x in profitgraph]
    #x, y = zip(*profitgraph)
    #ax2.plot(profitgraphx, profitgraphy)
    #plt.plot(profitgraph[:])
    #ax2.plot(profitgraph)
    #plt.plot(Close)
    #plt.ylabel('Dollars')
    #plt.xlabel('Time')
    #plt.legend(loc=2)
    #plt.show()
time.sleep(60) ##don't close for 1 min
