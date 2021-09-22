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
import Helper
Coin_precision = -99  ##Precision Coin is measured up to
Order_precision = -99 ##Precision Orders are measured up to


##Different coins we can trade,
# kline_15m - OHLC for 15 min intervals, Change accordingly

PRICES = "wss://stream.binance.com:9443/ws/btcusdt@ticker"
SOCKET = "wss://stream.binance.com:9443/ws/btcusdt@kline_1m"
symbol="BTCUSDT"

#PRICES = "wss://stream.binance.com:9443/ws/ethusdt@ticker"
#SOCKET = "wss://stream.binance.com:9443/ws/ethusdt@kline_1m"
#symbol="ETHUSDT"

#PRICES = "wss://stream.binance.com:9443/ws/ltcusdt@ticker"
#SOCKET = "wss://stream.binance.com:9443/ws/ltcusdt@kline_3m"
#symbol="LTCUSDT"

PRICES = "wss://stream.binance.com:9443/ws/solusdt@ticker"
SOCKET = "wss://stream.binance.com:9443/ws/solusdt@kline_5m"
symbol="SOLUSDT"

#PRICES = "wss://stream.binance.com:9443/ws/bnbusdt@ticker"
#SOCKET = "wss://stream.binance.com:9443/ws/bnbusdt@kline_3m"
#symbol="BNBUSDT"

#PRICES = "wss://stream.binance.com:9443/ws/adausdt@ticker"
#SOCKET = "wss://stream.binance.com:9443/ws/adausdt@kline_30m"
#symbol="ADAUSDT"

#PRICES = "wss://stream.binance.com:9443/ws/dogeusdt@ticker"
#SOCKET = "wss://stream.binance.com:9443/ws/dogeusdt@kline_1m"
#symbol="DOGEUSDT"

#PRICES = "wss://stream.binance.com:9443/ws/maticusdt@ticker"
#SOCKET = "wss://stream.binance.com:9443/ws/maticusdt@kline_1m" ##############Price not increased by tick size error
#symbol="MATICUSDT"

#PRICES = "wss://stream.binance.com:9443/ws/bakeusdt@ticker"
#SOCKET = "wss://stream.binance.com:9443/ws/bakeusdt@kline_15m"
#symbol="BAKEUSDT"

#PRICES = "wss://stream.binance.com:9443/ws/sushiusdt@ticker"
#SOCKET = "wss://stream.binance.com:9443/ws/sushiusdt@kline_1m"
#symbol="SUSHIUSDT"



#PRICES = "wss://stream.binance.com:9443/ws/dotusdt@ticker"
#SOCKET = "wss://stream.binance.com:9443/ws/dotusdt@kline_1m"
#symbol="DOTUSDT"

#PRICES = "wss://stream.binance.com:9443/ws/alphausdt@ticker"
#SOCKET = "wss://stream.binance.com:9443/ws/alphausdt@kline_1m"
#symbol = "ALPHAUSDT"

#PRICES = "wss://stream.binance.com:9443/ws/xrpusdt@ticker"
#SOCKET = "wss://stream.binance.com:9443/ws/xrpusdt@kline_1m"
#symbol="XRPUSDT"

#PRICES = "wss://stream.binance.com:9443/ws/1000shibusdt@ticker"
#SOCKET = "wss://stream.binance.com:9443/ws/1000shibusdt@kline_3m"
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
prediction=-99
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
break_even = 0 ##Set a new stop once in profit to cover the trading fee and breakeven
break_Even_Stage = [.4,.6,1.5,1.5] ##at what percentage of take profit to set new stop which corresponds to break_even_Amount
break_even_Amount = [.1,.2,.4,.65]  ##what to set the new stop loss at
min_profit_accepted = .0075
Order_Type = 'GTC' ##'IOC'
Stop_ID=''
Limit_ID=''
Order_ID=''
current_date = datetime.now(timezone.utc)
current_date = current_date.replace(tzinfo=timezone.utc)
current_date = round(float(current_date.timestamp()*1000-.5))
Market_Orders = 1 ##Allow Market Orders if limit is not filled
Trading=0 ##Actually trade on Binance, If Trading==1 then we are trading a strategy using the api keys specified above
          ## If Trading==0 then we are paper trading a strategy on historical data
successful_Trades=0
prevProfit = 0
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
                AccountBalance,EffectiveAccountBalance,positionSize,Highestprice,prediction, signal1, signal2, HighestUlt, Highest, \
                stoplossval, takeprofitval,prevsignal1,prevsignal2,PrevPos,Stop_ID,Order_ID,Limit_ID,prevProfit
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

            for kline in client.get_historical_klines_generator(symbol, Client.KLINE_INTERVAL_5MINUTE,start_str="2 day ago UTC"):  ## get KLines with 15 minute intervals for the last month
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
                            if Order_ID!='':

                                if client.futures_get_all_orders(symbol=symbol, orderId=Order_ID)[-1]['status'] == 'PARTIALLY FILLED':
                                    client.futures_cancel_order(symbol=symbol,orderId=Order_ID)  ##cancel leftover order

                                x = client.futures_position_information(symbol=symbol)[0]
                                if float(x['positionAmt']) == 0:
                                    CurrentPos = -99  ##Check if we are in a trade, if not reinitialize CurrentPos
                                    break_even_flag = 0  ##reinitialize
                                    Order_ID = ''
                                    Limit_ID = ''
                                    Stop_ID = ''
                                    client.futures_cancel_all_open_orders(symbol=symbol)  ##cancel open orders also

                                elif float(x['positionAmt']) < 0:
                                    CurrentPos = 0  ##in a short
                                    ##Check that stoploss and takeprofit are set:
                                    try:
                                        if Stop_ID == '':
                                            # print("Z1: Stop Order not sent, trying again Attempting Stop Price:",round(float(x['entryPrice']) + current_stoplossval + (5 * math.pow(10, -Coin_precision - 1)),Coin_precision))
                                            order2 = client.futures_create_order(
                                                symbol=symbol,
                                                side=SIDE_BUY,
                                                type=FUTURE_ORDER_TYPE_STOP_MARKET,
                                                quantity=-1 * float(x['positionAmt']),
                                                stopPrice=round(float(x['entryPrice']) + current_stoplossval + (
                                                            5 * math.pow(10, -Coin_precision - 1)), Coin_precision))
                                            Stop_ID = order2['orderId']
                                        if Limit_ID == '':
                                            # print("Z1: Limit Order not sent, trying again Attempting Limit Price:",round(float(x['entryPrice']) - current_takeprofitval, Coin_precision))
                                            order3 = client.futures_create_order(
                                                symbol=symbol,
                                                side=SIDE_BUY,
                                                type=FUTURE_ORDER_TYPE_LIMIT,
                                                price=round(float(x['entryPrice']) - current_takeprofitval,Coin_precision),
                                                timeInForce=TIME_IN_FORCE_GTC,
                                                quantity=-1 * float(x['positionAmt']))
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
                                                quantity=-1 * float(x['positionAmt']))
                                            time.sleep(300)  ##sleep for 5 minutes
                                            Sleep = 1
                                            break
                                elif float(x['positionAmt']) > 0:
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
                                                quantity=float(x['positionAmt']),
                                                stopPrice=round(float(x['entryPrice']) - current_stoplossval - (
                                                            5 * math.pow(10, -Coin_precision - 1)), Coin_precision))
                                            Stop_ID = order2['orderId']
                                            ##takeprofit:
                                        if Limit_ID == '':
                                            # print("Z2: Limit Order not sent, trying again Attempting Limit Price:",round(float(x['entryPrice']) + current_takeprofitval, Coin_precision))
                                            order3 = client.futures_create_order(
                                                symbol=symbol,
                                                side=SIDE_SELL,
                                                type=FUTURE_ORDER_TYPE_LIMIT,
                                                price=round(float(x['entryPrice']) + current_takeprofitval,
                                                            Coin_precision),
                                                timeInForce=TIME_IN_FORCE_GTC,
                                                quantity=float(x['positionAmt']))
                                            Limit_ID = order3['orderId']
                                    except BinanceAPIException as d:
                                        pass
                                        if d.message == 'Order would immediately trigger.':
                                            print(
                                                "Order would immediately Trigger, Cancelling and sleeping for 5 minutes")
                                            order4 = client.futures_create_order(
                                                symbol=symbol,
                                                side=SIDE_SELL,
                                                type=FUTURE_ORDER_TYPE_MARKET,
                                                quantity=float(x['positionAmt']))
                                            time.sleep(300)  ##sleep for 5 minutes
                                            Sleep = 1
                                            break
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
                            prediction=-99 ##reinitialize

                            ######################## These are some trading strategies I have coded up as functions, found in TradingStrats.py #######################################

                            #prediction,Type1 = TS.MovingAverage(Close,prediction)
                            #prediction, signal1, signal2, Type1 = TS.tripleEMAStochasticRSIATR(Close,signal1,signal2,prediction)
                            prediction,stoplossval,takeprofitval = TS.Fractal(Close,Low,High,prediction)
                            #prediction, stoplossval, takeprofitval = TS.fibMACD(prediction,Close,Open)
                            #prediction, signal1, Type1 = TS.RSIStochEMA(prediction, Close, High, Low,signal1, CurrentPos)
                            #prediction, signal1, signal2, HighestUlt, Highest, Type1 = TS.UltOscMACD(prediction,Close,High, Low,signal1, signal2,HighestUlt, Highest)
                            #prediction, signal1, Type1 = TS.RSIStochEMA200(prediction,Close,High,Low,signal1,signal2,CurrentPos)
                            #prediction,Type1 = TS.Fractal2(Close,Low,High,signal1,prediction)

                            #prediction, Type1 = stochBB(prediction, Close)

                            stoplossval, takeprofitval = SetSLTP(stoplossval, takeprofitval, Close, High,Low, prediction, CurrentPos, Type1) ##This function sets the stoploss and takeprofit based off the Type1 variable returned by the above functions

                            ##These trading strategies have custom stoploss & takeprofits:
                            #takeprofitval, stoplossval, prediction, signal1= TS.SARMACD200EMA(stoplossval, takeprofitval,Close,High,Low,prediction,CurrentPos,signal1)
                            #takeprofitval, stoplossval, prediction, signal1= TS.TripleEMA(stoplossval, takeprofitval,Close,High,Low,prediction,CurrentPos,signal1)

                            if (prediction == 1 or prediction == 0) and (min_profit_accepted * Close[-1] > takeprofitval):
                                prediction = -99

                            x = client.futures_position_information(symbol=symbol)[0]

                            #print("position Amount:",x)
                            #time.sleep(5)
                            if float(x['positionAmt']) < 0:
                                CurrentPos = 0  ##in a short
                                if break_even and break_even_flag==0:
                                    #LastPrice = float(client.get_ticker(symbol=symbol)['lastPrice'])
                                    if float(x['entryPrice']) - Close[-1] >break_Even_Stage[0]*current_takeprofitval:
                                        ###### Set new Stop if we are in profit to breakeven
                                        ##Set new Stop in Profit:
                                        try:
                                            order2 = client.futures_create_order(
                                                symbol=symbol,
                                                side=SIDE_BUY,
                                                type=FUTURE_ORDER_TYPE_STOP_MARKET,
                                                quantity=-1 * float(x['positionAmt']),
                                                stopPrice=round(float(x['entryPrice']) -break_even_Amount[0]*current_takeprofitval + 5 * math.pow(10, -Coin_precision - 1), Coin_precision))
                                            if order2['status']=="NEW":
                                                client.futures_cancel_order(symbol=symbol,orderId=Stop_ID)
                                                print(f"New Stop placed at {break_even_Amount[0]}x(take profit)")
                                                break_even_flag = 1
                                                Stop_ID=order2['orderId']
                                        except BinanceAPIException as d:
                                            if d.message=='Order would immediately trigger.':
                                                print("New Stop not placed as order would trigger immediately")#, LastPrice:",LastPrice)

                                if break_even and break_even_flag<=1:
                                    #LastPrice = float(client.get_ticker(symbol=symbol)['lastPrice'])
                                    if float(x['entryPrice']) - Close[-1] >break_Even_Stage[1]*current_takeprofitval:
                                        ###### Set new Stop if we are in profit to breakeven
                                        ##Set new Stop in Profit:
                                        try:
                                            order2 = client.futures_create_order(
                                                symbol=symbol,
                                                side=SIDE_BUY,
                                                type=FUTURE_ORDER_TYPE_STOP_MARKET,
                                                quantity=-1 * float(x['positionAmt']),
                                                stopPrice=round(float(x['entryPrice'])-break_even_Amount[1]*current_takeprofitval + 5 * math.pow(10, -Coin_precision - 1), Coin_precision))
                                            if order2['status']=="NEW":
                                                client.futures_cancel_order(symbol=symbol, orderId=Stop_ID)
                                                print(f"New Stop placed at {break_even_Amount[1]}x(takeprofit)")
                                                break_even_flag = 2
                                                Stop_ID=order2['orderId']
                                        except BinanceAPIException as d:
                                            if d.message=='Order would immediately trigger.':
                                                print("New Stop not placed as order would trigger immediately")#, LastPrice:",LastPrice)

                                if break_even and break_even_flag<=2:

                                    if float(x['entryPrice']) - Close[-1] >break_Even_Stage[2]*takeprofitval:
                                        ###### Set new Stop if we are in profit to breakeven
                                        ##Set new Stop in Profit:
                                        try:
                                            order2 = client.futures_create_order(
                                                symbol=symbol,
                                                side=SIDE_BUY,
                                                type=FUTURE_ORDER_TYPE_STOP_MARKET,
                                                quantity=-1 * float(x['positionAmt']),
                                                stopPrice=round(float(x['entryPrice']) -break_even_Amount[2]*current_takeprofitval + 5 * math.pow(10, -Coin_precision - 1), Coin_precision))
                                            if order2['status']=="NEW":
                                                client.futures_cancel_order(symbol=symbol,orderId=Stop_ID)
                                                print(f"New Stop placed at {break_even_Amount[2]}x(takeprofit)")
                                                break_even_flag = 3
                                                Stop_ID=order2['orderId']
                                        except BinanceAPIException as d:
                                            if d.message=='Order would immediately trigger.':
                                                print("New Stop not placed as order would trigger immediately")#, LastPrice:",LastPrice)

                                if break_even and break_even_flag<=3:

                                    if float(x['entryPrice']) - Close[-1] >break_Even_Stage[3]*takeprofitval:
                                        ###### Set new Stop if we are in profit to breakeven
                                        ##Set new Stop in Profit:
                                        try:
                                            order2 = client.futures_create_order(
                                                symbol=symbol,
                                                side=SIDE_BUY,
                                                type=FUTURE_ORDER_TYPE_STOP_MARKET,
                                                quantity=-1 * float(x['positionAmt']),
                                                stopPrice=round(float(x['entryPrice']) -break_even_Amount[3]*current_takeprofitval + 5 * math.pow(10, -Coin_precision - 1), Coin_precision))
                                            if order2['status']=="NEW":
                                                client.futures_cancel_order(symbol=symbol,orderId=Stop_ID)
                                                print(f"New Stop placed at {break_even_Amount[3]}x(takeprofit)")
                                                break_even_flag = 4
                                                Stop_ID=order2['orderId']
                                        except BinanceAPIException as d:
                                            if d.message=='Order would immediately trigger.':
                                                print("New Stop not placed as order would trigger immediately")#, LastPrice:",LastPrice)

                            elif float(x['positionAmt']) > 0:
                                CurrentPos = 1  ##in a long
                                if break_even and break_even_flag==0:
                                    #LastPrice = float(client.get_ticker(symbol=symbol)['lastPrice'])
                                    if Close[-1] - float(x['entryPrice']) >break_Even_Stage[0]*takeprofitval:
                                        ###### Set new Stop if we are in profit to breakeven
                                        ##Set new Stop in Profit:
                                        try:
                                            order2 = client.futures_create_order(
                                                symbol=symbol,
                                                side=SIDE_SELL,
                                                type=FUTURE_ORDER_TYPE_STOP_MARKET,
                                                quantity=float(x['positionAmt']),
                                                stopPrice=round(float(x['entryPrice']) +break_even_Amount[0]*current_takeprofitval - 5 * math.pow(10, -Coin_precision - 1), Coin_precision))
                                            if order2['status']=="NEW":
                                                client.futures_cancel_order(symbol=symbol,orderId=Stop_ID)  ##cancel open orders also
                                                print(f"New Stop placed at {break_even_Amount[0]}x(take profit)")
                                                break_even_flag = 1
                                                Stop_ID=order2['orderId']
                                        except BinanceAPIException as d:
                                            if d.message=='Order would immediately trigger.':
                                                print("New Stop not placed as order would trigger immediately")#, LastPrice:",LastPrice)

                                if break_even and break_even_flag<=1:
                                    #LastPrice = float(client.get_ticker(symbol=symbol)['lastPrice'])

                                    if Close[-1] - float(x['entryPrice']) >break_Even_Stage[1]*takeprofitval:
                                        ###### Set new Stop if we are in profit to breakeven
                                        ##Set new Stop in Profit:
                                        try:
                                            order2 = client.futures_create_order(
                                                symbol=symbol,
                                                side=SIDE_SELL,
                                                type=FUTURE_ORDER_TYPE_STOP_MARKET,
                                                quantity=float(x['positionAmt']),
                                                stopPrice=round(float(x['entryPrice']) + current_takeprofitval*break_even_Amount[1] - 5 * math.pow(10, -Coin_precision - 1), Coin_precision))
                                            if order2['status']=="NEW":
                                                client.futures_cancel_order(symbol=symbol,orderId=Stop_ID)  ##cancel open orders also
                                                print(f"New Stop placed at {break_even_Amount[1]}x(takeprofit)")
                                                break_even_flag = 2
                                                Stop_ID=order2['orderId']
                                        except BinanceAPIException as d:
                                            if d.message=='Order would immediately trigger.':
                                                print("New Stop not placed as order would trigger immediately")#, LastPrice:",LastPrice)

                                if break_even and break_even_flag<=2:
                                    #LastPrice = float(client.get_ticker(symbol=symbol)['lastPrice'])

                                    if Close[-1] - float(x['entryPrice']) >break_Even_Stage[2]*takeprofitval:
                                        ###### Set new Stop if we are in profit to breakeven
                                        ##Set new Stop in Profit:
                                        try:
                                            order2 = client.futures_create_order(
                                                symbol=symbol,
                                                side=SIDE_SELL,
                                                type=FUTURE_ORDER_TYPE_STOP_MARKET,
                                                quantity=float(x['positionAmt']),
                                                stopPrice=round(float(x['entryPrice']) + current_takeprofitval*break_even_Amount[2] - 5 * math.pow(10, -Coin_precision - 1), Coin_precision))
                                            if order2['status']=="NEW":
                                                client.futures_cancel_order(symbol=symbol,orderId=Stop_ID)  ##cancel open orders also
                                                print(f"New Stop placed at {break_even_Amount[2]}x(takeprofit)")
                                                break_even_flag = 3
                                                Stop_ID=order2['orderId']
                                        except BinanceAPIException as d:
                                            if d.message=='Order would immediately trigger.':
                                                print("New Stop not placed as order would trigger immediately")#, LastPrice:",LastPrice)

                                if break_even and break_even_flag<=3:
                                    #LastPrice = float(client.get_ticker(symbol=symbol)['lastPrice'])
                                    if Close[-1] - float(x['entryPrice']) >break_Even_Stage[3]*takeprofitval:
                                        ###### Set new Stop if we are in profit to breakeven
                                        ##Set new Stop in Profit:
                                        try:
                                            order2 = client.futures_create_order(
                                                symbol=symbol,
                                                side=SIDE_SELL,
                                                type=FUTURE_ORDER_TYPE_STOP_MARKET,
                                                quantity=float(x['positionAmt']),
                                                stopPrice=round(float(x['entryPrice'])+current_takeprofitval*break_even_Amount[3] - 5 * math.pow(10, -Coin_precision - 1), Coin_precision))
                                            if order2['status']=="NEW":
                                                client.futures_cancel_order(symbol=symbol,orderId=Stop_ID)  ##cancel open orders also
                                                print(f"New Stop placed at {break_even_Amount[3]}x(takeprofit)")
                                                break_even_flag = 4
                                                Stop_ID=order2['orderId']
                                        except BinanceAPIException as d:
                                            if d.message=='Order would immediately trigger.':
                                                print("New Stop not placed as order would trigger immediately")#, LastPrice:",LastPrice)
                                                ##get rid of partially filled orders


                            if CurrentPos == -99 and prediction == 0:  ##not in a trade but want to enter a short position
                                LP = float(client.get_ticker(symbol=symbol)['lastPrice'])
                                positionPrice = LP
                                positionSize = (OrderSIZE * EffectiveAccountBalance) / positionPrice ##work out OrderQTY
                                #print(positionSize)
                                CurrentPos = 0
                                Highestprice = positionPrice
                                # stoplossval = positionPrice * trailing_stoploss
                                #trades.append({'x': i, 'y': positionPrice, 'type': "sell",'current_price': positionPrice})
                                ##Stoploss and takeprofit in case the stop/limit order isn't filled
                                current_stoplossval = copy(stoplossval)
                                current_takeprofitval = copy(takeprofitval)

                                ##Create Order on Binance
                                if Order_precision!=0:
                                    await Order(round(positionSize,Order_precision), 0, symbol,stoplossval,takeprofitval,Coin_precision,Market_Orders)
                                else:
                                    await Order(round(positionSize), 0, symbol, stoplossval, takeprofitval, Coin_precision,Market_Orders)

                            elif CurrentPos == -99 and prediction == 1: ##not in a trade but want to enter a Long position
                                LP = float(client.get_ticker(symbol=symbol)['lastPrice'])
                                positionPrice = LP
                                positionSize = (OrderSIZE * EffectiveAccountBalance) / positionPrice ##work out OrderQTY
                                CurrentPos = 1
                                Highestprice = positionPrice
                                # stoplossval = positionPrice * trailing_stoploss
                                #trades.append({'x': i, 'y': positionPrice, 'type': "buy",'current_price': positionPrice})
                                ##Stoploss and takeprofit in case the stop/limit order isn't filled
                                current_stoplossval = copy(stoplossval)
                                current_takeprofitval = copy(takeprofitval)

                                ##Create Order on Binance
                                if Order_precision!=0:
                                    await Order(round(positionSize,Order_precision), 1, symbol,stoplossval,takeprofitval,Coin_precision,Market_Orders)
                                else:
                                    await Order(round(positionSize), 1, symbol, stoplossval, takeprofitval,Coin_precision,Market_Orders)



                            if CurrentPos != PrevPos:
                                if PrevPos!=-99:
                                    tradeNO+=1
                                bnb = float(client.get_ticker(symbol="BNBUSDT")['lastPrice'])
                                signal1 = -99
                                signal2 = -99
                                print("Current Position:", CurrentPos)
                                #print("Margin:", positionPrice - Close[-1])
                                # print("Date:",DateStream[-1])
                                try:
                                    prevProfit = printProfit(symbol, bnb,prevProfit)
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
        if Profit<previous_Profit:
            successful_Trades+=1
        print("Account Balance: ", AccountBalance, "Profit:", Profit)
        print("PV:", (Profit * 100) / (tradeNO * Close[-1]),"Stoploss:",stoplossval, "TakeProfit:", takeprofitval,"Successful Trades:",successful_Trades,"Trades lost:",tradeNO-successful_Trades,"W/L ratio:",successful_Trades/tradeNO)
        previous_Profit = copy(Profit)
        Profit=0
        return previous_Profit

    async def Order(q, side1, s,stoploss,takeprofit,CP,Market):
        global Stop_ID,Limit_ID,Order_ID
        try:
            try:
                if side1 and Market==0: ##Long
                    PP = float(client.get_ticker(symbol=symbol)['lastPrice']) * 1.0007  ##So last price more likely to fill
                    ##Place the Long
                    order1 = client.futures_create_order(
                        symbol=s,
                        side=SIDE_BUY,
                        type=FUTURE_ORDER_TYPE_LIMIT,
                        price= round(PP,CP),
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
                    PP = float(client.get_ticker(symbol=symbol)['lastPrice']) * .9993  ##So last price more likely to fill
                    ##Place the short
                    order1 = client.futures_create_order(
                        symbol=s,
                        side=SIDE_SELL,
                        type=FUTURE_ORDER_TYPE_LIMIT,
                        price=round(PP,CP),
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

    waitflag=0 ##wait until next candlestick before checking if stoploss/ takeprofit was hit
    fee = .00036

    High_1min = []
    Low_1min = []

    #symbol = "BTCUSDT"
    #symbol="ETHUSDT"
    #symbol='SHIBUSDT'
    #symbol='ADAUSDT'
    #symbol='BAKEUSDT'
    #symbol='BNBUSDT'
    #symbol= 'SUSHIUSDT'
    symbol = 'SOLUSDT' ###############################
    #symbol = 'MATICUSDT' #############################
    #symbol = 'DOGEUSDT'
    #symbol = "XRPUSDT"
    #symbol = "DOTUSDT"
    #symbol = "ALPHAUSDT"
    print("Symbol:", symbol, "Start Balance:", AccountBalance,"fee:",fee)
    time_period = "5 month ago UTC"
    TIME_INTERVAL = 5 ##Candlestick interval in minutes, valid options:1,   3,   5,  15,   30,  60, 120,240,360,480,720, 1440,4320, 10080, 40320
                                                                  ##1min,3min,5min,15min,30min,1hr,2hr,4hr,6hr,8hr,12hr,1day,3days,1week,1month
    break_even=0 ##whether or not to move the stoploss into profit based of settings below
    break_even_flag=0 ##flag don't change
    break_Even_Stage = [.7,1.75] ##if we reach this point in of profit target move stoploss to corresponding point break_even_Amount
    break_even_Amount = [.1,.4] ##where to move the stop to
    Date,Open,Close,High,Low,Volume,High_1min,Low_1min,Close_1min = Helper.get_Klines(symbol,TIME_INTERVAL,time_period)
    print(f"{TIME_INTERVAL} min OHLC Candle Sticks from {time_period}")
    for i in range(len(High_1min)):
        #global trailing_stoploss,Highestprice
        if i%TIME_INTERVAL==0 and i!=0:
            DateStream = flow.dataStream(DateStream, Date[int(i/TIME_INTERVAL)-1], 1, 300)
            OpenStream = flow.dataStream(OpenStream, Open[int(i/TIME_INTERVAL)-1], 1, 300)
            CloseStream = flow.dataStream(CloseStream, Close[int(i/TIME_INTERVAL)-1], 1, 300)
            HighStream = flow.dataStream(HighStream, High[int(i/TIME_INTERVAL)-1], 1, 300)
            LowStream = flow.dataStream(LowStream, Low[int(i/TIME_INTERVAL)-1], 1, 300)
            VolumeStream = flow.dataStream(VolumeStream, Volume[int(i/TIME_INTERVAL)-1], 1, 300)
        #print(len(OpenStream))
        if len(OpenStream)>=299:
            prevProfit=copy(Profit)
            EffectiveAccountBalance = AccountBalance*leverage
            if CurrentPos== -99:
                if i%TIME_INTERVAL==0 and (i!=0 or TIME_INTERVAL==1):
                    break_even_flag=0
                    prediction=-99
                    #prediction,signal1,signal2,Type =TS.StochRSI_RSIMACD(prediction,CloseStream,signal1,signal2) ###########################################
                    # prediction,Type = TS.StochRSIMACD(prediction, CloseStream,HighStream,LowStream)  ###########################################
                    # prediction, signal1, signal2, Type = TS.tripleEMAStochasticRSIATR(CloseStream,signal1,signal2,prediction)
                    # prediction,signal1,signal2,HighestUlt,Highest,Type = TS.UltOscMACD(prediction,CloseStream,HighStream,LowStream,signal1,signal2,HighestUlt,Highest)
                    # prediction, signal1, Type,loc1,loc1_1,loc2,loc2_2,peaks,RSI = TS.RSIStochEMA(prediction,CloseStream,HighStream,LowStream,signal1,CurrentPos)
                    # prediction,Type=TS.tripleEMA(CloseStream,OpenStream,prediction)
                    '''if loc1!=-99:
                        print("Bearish Divergence found:",DateStream[loc1],"to",DateStream[loc1_1])
                    if loc2!=-99:
                        print("Bullish Divergence found:",DateStream[loc2],"to",DateStream[loc2_2])'''
                    # for x in peaks:
                    #   print("Peak at ",DateStream[x],"RSI:",RSI[x])
                    # prediction,Type = TS.Fractal2(CloseStream,LowStream,HighStream,signal1,prediction) ###############################################
                    # prediction,Type = TS.stochBB(prediction,CloseStream)
                    # prediction, Type = TS.goldenCross(prediction,CloseStream)

                    #stoplossval, takeprofitval = TS.SetSLTP(stoplossval, takeprofitval, CloseStream, HighStream,LowStream, prediction, CurrentPos, Type)

                    prediction,stoplossval,takeprofitval,max_pos,min_pos = TS.fibMACD(prediction, CloseStream, OpenStream,HighStream,LowStream)
                    # if prediction==0 or prediction==1 and CurrentPos==-99:
                    #    print("\nMax:",DateStream[max_pos])
                    #    print("Min:",DateStream[min_pos])

                    #prediction,stoplossval,takeprofitval = TS.Fractal(CloseStream, LowStream, HighStream,OpenStream,prediction)

                    # takeprofitval, stoplossval, prediction, signal1= TS.SARMACD200EMA(stoplossval, takeprofitval,CloseStream,HighStream,LowStream,prediction,CurrentPos,signal1)

                    # takeprofitval, stoplossval, prediction, signal1= TS.TripleEMA(stoplossval, takeprofitval,CloseStream,HighStream,LowStream,prediction,CurrentPos,signal1)

                else:
                    prediction=-99



                ##If the trade won't cover the fee & profit something then don't place it
                if (prediction == 1 or prediction == 0) and (.00125 * Close[-1] > takeprofitval):
                    prediction = -99
        #################################################################
            #################################################################

            if CurrentPos == -99 and prediction == 0:
                positionPrice = CloseStream[len(CloseStream) - 1]
                positionSize= (OrderSIZE*EffectiveAccountBalance)/positionPrice
                CurrentPos = 0
                tradeNO+=1
                #Highestprice = positionPrice
               #stoplossval = positionPrice * trailing_stoploss
                trades.append({'x':i,'y':positionPrice,'type': "sell",'current_price': positionPrice})
                Profit -= CloseStream[len(CloseStream) - 1] * fee
                AccountBalance -= positionSize * CloseStream[-1] * fee
                waitflag = 1
            elif CurrentPos == -99 and prediction == 1:
                positionPrice = CloseStream[len(CloseStream) - 1]
                positionSize = (OrderSIZE * EffectiveAccountBalance) / positionPrice
                CurrentPos = 1
                tradeNO += 1
                #Highestprice = positionPrice
                #stoplossval = positionPrice * trailing_stoploss
                trades.append({'x':i,'y':positionPrice, 'type': "buy",'current_price': positionPrice})
                Profit -= CloseStream[len(CloseStream) - 1] * fee
                AccountBalance -= positionSize * CloseStream[-1] * fee
                waitflag = 1
            ############### break-even:
            #if CurrentPos==0 and break_even and positionPrice-CloseStream[-1] > .0025*positionPrice:



            if positionPrice - High_1min[i] < -stoplossval and CurrentPos == 0 and (not waitflag):
                Profit +=-stoplossval #positionPrice-CloseStream[len(CloseStream) - 1]  ##This will be positive if the price went down
                AccountBalance += positionSize * -stoplossval # (positionPrice-CloseStream[len(CloseStream) - 1])
                positionPrice = CloseStream[len(CloseStream) - 1]
                Profit -= CloseStream[-1] * fee
                AccountBalance-= positionSize*CloseStream[-1] * fee
                cashout.append({'x': i, 'y': CloseStream[-1], 'type': "loss",'position':'short','Profit': -stoplossval*positionSize})
                # CurrentPos = -99
                CurrentPos = -99
                stopflag = -99

            elif Low_1min[i] - positionPrice < -stoplossval and CurrentPos == 1 and (not waitflag):
                Profit +=-stoplossval #CloseStream[len(CloseStream) - 1] - positionPrice ##This will be positive if the price went up
                AccountBalance += positionSize* -stoplossval #(CloseStream[len(CloseStream) - 1] - positionPrice)
                positionPrice = CloseStream[len(CloseStream) - 1]
                Profit -= CloseStream[-1] * fee
                AccountBalance -= positionSize * CloseStream[-1] * fee
                cashout.append({'x': i, 'y': CloseStream[-1], 'type': "loss",'position':'long','Profit': -stoplossval*positionSize})
                # CurrentPos = -99
                CurrentPos = -99
                stopflag = -99

            elif positionPrice - Low_1min[i] > takeprofitval and CurrentPos == 0 and (not waitflag):
                Profit += takeprofitval #positionPrice - CloseStream[-1]
                AccountBalance += positionSize *  takeprofitval #(positionPrice - CloseStream[len(CloseStream) - 1])
                correct += 1
                positionPrice = CloseStream[-1]
                Profit -= CloseStream[-1] * fee
                AccountBalance -= positionSize * CloseStream[-1] * fee
                cashout.append({'x': i, 'y': CloseStream[-1], 'type': "win",'position':'short','Profit': takeprofitval*positionSize})
                CurrentPos = -99
                stopflag = -99

            elif High_1min[i] - positionPrice > takeprofitval and CurrentPos == 1 and (not waitflag):
                Profit +=  takeprofitval #CloseStream[-1] - positionPrice
                AccountBalance += positionSize *  takeprofitval #(CloseStream[len(CloseStream) - 1] - positionPrice)
                correct += 1
                positionPrice = CloseStream[-1]
                Profit -= CloseStream[-1] * fee
                AccountBalance -= positionSize * CloseStream[-1] * fee
                cashout.append({'x': i, 'y': CloseStream[-1], 'type': "win",'position':'long','Profit': takeprofitval*positionSize})
                CurrentPos = -99
                stopflag = -99
            #########################################################################################################################
            ###########################   Trailing Stop Loss Logic:   ###############################################################
            if CurrentPos ==0 and break_even and break_even_flag == 0:
                if positionPrice - Close_1min[i] > break_Even_Stage[0] * takeprofitval:
                    ###### Set new Stop if we are in profit to breakeven
                    ##Set new Stop in Profit:
                    #stoplossval = -break_even_Amount[0]*takeprofitval
                    stoplossval*=break_even_Amount[0]
                    break_even_flag+=1
            elif CurrentPos ==1 and break_even and break_even_flag == 0:
                if Close_1min[i] - positionPrice > break_Even_Stage[0] * takeprofitval:
                    ###### Set new Stop if we are in profit to breakeven
                    ##Set new Stop in Profit:
                    #stoplossval = -break_even_Amount[0]*takeprofitval
                    stoplossval *= break_even_Amount[0]
                    break_even_flag += 1
            if CurrentPos ==0 and break_even and break_even_flag <= 1:
                # LastPrice = float(client.get_ticker(symbol=symbol)['lastPrice'])
                if positionPrice - Close_1min[i] > break_Even_Stage[1] * takeprofitval:
                    ###### Set new Stop if we are in profit to breakeven
                    ##Set new Stop in Profit:
                    #stoplossval = -break_even_Amount[1] * takeprofitval
                    stoplossval *= break_even_Amount[1]
                    break_even_flag += 1
            elif CurrentPos ==1 and break_even and break_even_flag <=1:
                if Close_1min[i] - positionPrice > break_Even_Stage[1] * takeprofitval:
                    ###### Set new Stop if we are in profit to breakeven
                    ##Set new Stop in Profit:
                    #stoplossval = -break_even_Amount[1]*takeprofitval
                    stoplossval *= break_even_Amount[1]
                    break_even_flag += 1
            ################################################################################################################################
            ################################################################################################################################

            waitflag=0
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
                print("\nCurrent Position:",CurrentPos)
                print("Time:",DateStream[-1])
                #print("Time Max",DateStream[max_pos])
                #print("Time Min", DateStream[min_pos])
                try:
                    print("Account Balance: ", AccountBalance,"Order Size:",positionSize,"PV:",(Profit * 100) / (tradeNO * CloseStream[-1]),"Stoploss:",stoplossval,"TakeProfit:",takeprofitval)
                except Exception as e:
                    pass
            #if prevProfit!=Profit:
            profitgraph.append(Profit)
            PrevPos=copy(CurrentPos)
    print("\nSymbol:",symbol,"fee:",fee)
    if break_even:
        print("Moving Stoploss ON")
    print(f"{TIME_INTERVAL} min OHLC Candle Sticks from {time_period}")
    print("Account Balance:", AccountBalance)
    print("% Gain on Account:", ((AccountBalance - originalBalance) * 100) / originalBalance)
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
