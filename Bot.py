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
from binance.exceptions import BinanceAPIException
from binance.enums import *
import datetime

Coin_precision = -99  ##Precision Coin is measured up to
Order_precision = -99 ##Precision Orders are measured up to


##Different coins we can trade,
# kline_15m - OHLC for 15 min intervals, Change accordingly

#PRICES = "wss://stream.binance.com:9443/ws/btcusdt@depth10"
SOCKET = "wss://stream.binance.com:9443/ws/btcusdt@kline_15m"
symbol="BTCUSDT"

#SOCKET = "wss://stream.binance.com:9443/ws/ethusdt@kline_15m"
#symbol="ETHUSDT"

#SOCKET = "wss://stream.binance.com:9443/ws/ltcusdt@kline_15m"
#symbol="LTCUSDT"


#SOCKET = "wss://stream.binance.com:9443/ws/solusdt@kline_15m"
#symbol="SOLUSDT"


#SOCKET = "wss://stream.binance.com:9443/ws/bnbusdt@kline_15m"
#symbol="BNBUSDT"


#SOCKET = "wss://stream.binance.com:9443/ws/adausdt@kline_15m"
#symbol="ADAUSDT"


#SOCKET = "wss://stream.binance.com:9443/ws/dogeusdt@kline_15m"
#symbol="DOGEUSDT"


#SOCKET = "wss://stream.binance.com:9443/ws/maticusdt@kline_15m"
#symbol="MATICUSDT"


if symbol=='BTCUSDT':
    Coin_precision = 3
    Order_precision = 2

elif symbol == 'ETHUSDT':
    Coin_precision = 3
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

#symbol="BTCUSDT"
#symbol="ETHUSDT"
#symbol='SHIBUSDT'
#symbol='ADAUSDT'
#symbol='BAKEUSDT'
#symbol='BNBUSDT'
#symbol= 'SUSHIUSDT'
#symbol = 'SOLUSDT' ###############################
#symbol = 'MATICUSDT' #############################
#print(symbol)
#print(30)
client = Client(api_key="",api_secret="") ##Binance keys needed to get historical data/ Trade on an account
for kline in client.get_historical_klines_generator(symbol, Client.KLINE_INTERVAL_15MINUTE, start_str="1 months ago UTC"):  ## get KLines with 15 minute intervals for the last month
    # print(kline)
    Date.append(datetime.datetime.utcfromtimestamp(int(kline[0])/1000))
    Open.append(float(kline[1]))
    Close.append(float(kline[4]))
    High.append(float(kline[2]))
    Low.append(float(kline[3]))
    Volume.append(float(kline[7]))

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


leverage=125 ##leverage used on binance just for console display
AccountBalance=617*leverage  ## $617 from binance account balance multiplied by leverage used x125
OriginalAccountSize=copy(AccountBalance)
OrderSIZE = .02 ##how much of account to use per trade in Decimal
positionSize = 0 ##altered later and sent as the orderQTY


Trading=0 ##Actually trade on Binance, If Trading==1 then we are trading a strategy using the api keys specified above
          ## If Trading==0 then we are paper trading a strategy on historical data
print("Symbol:",symbol,"Start Balance:",AccountBalance/leverage)
if Trading: ## Trade on Binance with above api key and secret key
    async def runWS():
        async with websockets.connect(SOCKET) as websocket:
            global Open, Close, High, Low, Volume,Profit,tradeNO,CurrentPos,positionPrice,\
                AccountBalance,positionSize,Highestprice,prediction1, signal1, signal2, HighestUlt, Highest, \
                stoplossval, takeprofitval,prevsignal1,prevsignal2,PrevPos
            Profit = 0
            tradeNO = 0
            CurrentPos = -99
            positionPrice = 0
            minuteFlag = 0 ##flag to signal new incoming kline
            TimeCount=0
            TTC = 0
            timer = 0
            while True:
                try:
                    try:
                        # print("hello")
                        message = await websocket.recv() ##pull klines
                        json_message = json.loads(message)
                        payload = json_message['k']
                        if payload['x']: ##if payload['x']==1 then it is a new kline we have received => new OHLC data
                            Open = flow.dataStream(Open, float(payload['o']), 1, 300)
                            Close = flow.dataStream(Close, float(payload['c']), 1, 300)
                            High = flow.dataStream(High, float(payload['h']), 1, 300)
                            Low = flow.dataStream(Low, float(payload['l']), 1, 300)
                            Volume = flow.dataStream(Volume, float(payload['q']), 1, 300)
                            minuteFlag = 1 ##new OHLC data so check Strategy for signals of entry points
                        ############ Check if stoploss or takeprofit was met/Filled, if so cancel the open orders for this coin before moving on, & to find out if we are currently in a trade
                        if TimeCount==100:
                            TimeCount=0
                            if CurrentPos != -99: ##we might be in a trade
                                x = client.futures_get_all_orders(symbol=symbol)
                                ##stoploss
                                if x[-2]['status'] == 'FILLED':
                                    if x[-2]['side'] == 'SELL':  ##stoploss was a sell so we were Long
                                        Profit += float(x[-2][
                                                            'stopPrice']) - positionPrice  ##This will be positive if the price went up
                                        AccountBalance += positionSize * (float(x[-2]['stopPrice']) - positionPrice)
                                        positionPrice = float(x[-2]['stopPrice'])
                                        Profit -= float(x[-2]['stopPrice']) * .00036
                                        AccountBalance -= positionSize * float(x[-2]['stopPrice']) * .00036
                                        # cashout.append({'x': i, 'y': CloseStream[-1], 'type': "loss", 'position': 'long'})
                                        CurrentPos = -99 ##order filled so we are not in a trade

                                    elif x[-2]['side'] == 'BUY':  ##stoploss was a buy so we were Short
                                        Profit += positionPrice - float(
                                            x[-2]['stopPrice'])  ##This will be positive if the price went down
                                        AccountBalance += positionSize * (positionPrice - float(x[-2]['stopPrice']))
                                        positionPrice = float(x[-2]['stopPrice'])
                                        Profit -= float(x[-2]['stopPrice']) * .00036
                                        AccountBalance -= positionSize * float(x[-2]['stopPrice']) * .00036
                                        # cashout.append({'x': i, 'y': CloseStream[-1], 'type': "loss", 'position': 'short'})
                                        CurrentPos = -99 ##order filled so we are not in a trade
                                    client.futures_cancel_all_open_orders(symbol=symbol)
                                ##takeprofit
                                elif x[-1]['status'] == 'FILLED':
                                    if x[-2]['side'] == 'SELL':  ##takeprofit was a sell so we were Long
                                        Profit += float(
                                            x[-2]['price']) - positionPrice  ##This will be positive if the price went up
                                        AccountBalance += positionSize * (float(x[-2]['price']) - positionPrice)
                                        positionPrice = float(x[-2]['price'])
                                        Profit -= float(x[-2]['price']) * .00036
                                        AccountBalance -= positionSize * float(x[-2]['price']) * .00036
                                        # cashout.append({'x': i, 'y': CloseStream[-1], 'type': "loss", 'position': 'long'})
                                        CurrentPos = -99 ##order filled so we are not in a trade
                                    elif x[-2]['side'] == 'BUY':  ##takeprofit was a buy so we were Short
                                        Profit += positionPrice - float(
                                            x[-2]['price'])  ##This will be positive if the price went down
                                        AccountBalance += positionSize * (positionPrice - float(x[-2]['price']))
                                        positionPrice = float(x[-2]['price'])
                                        Profit -= float(x[-2]['price']) * .00036
                                        AccountBalance -= positionSize * float(x[-2]['price']) * .00036
                                        # cashout.append({'x': i, 'y': CloseStream[-1], 'type': "loss", 'position': 'short'})
                                        CurrentPos = -99 ##order filled so we are not in a trade
                                    client.futures_cancel_all_open_orders(symbol=symbol)
                        ####################################################################################################################
                        TimeCount+=1
                        if minuteFlag: ##new OHLC data
                            y = client.futures_account_balance()
                            AccountBalance = float(y[1]['balance'])*leverage  ##Get Account Balance when multiplied by leverage to use for deciding positionSize based of OrderSIZE above
                            minuteFlag = 0 ##switch off flag


                            ######################## These are some trading strategies I have coded up as functions, found in TradingStrats.py #######################################

                            #prediction1,Type1 = TS.MovingAverage(Close,prediction1)
                            #prediction1,signal1,signal2,Type1 =TS.StochRSIMACD(prediction1,Close,signal1,signal2)
                            #prediction1, signal1, signal2, Type1 = TS.tripleEMAStochasticRSIATR(Close,signal1,signal2,prediction1)
                            #prediction1,Type1 = TS.Fractal(Close,Low,High,signal1,prediction1)
                            #prediction1, signal1, signal2, HighestUlt, Highest, Type1 = TS.UltOscMACD(prediction1,Close,High, Low,signal1, signal2,HighestUlt, Highest)
                            prediction1, signal1, Type1 = TS.RSIStochEMA200(prediction1,Close,High,Low,signal1,signal2,CurrentPos)
                            #prediction1,Type1 = TS.Fractal2(Close,Low,High,signal1,prediction1)


                            stoplossval, takeprofitval = TS.SetSLTP(stoplossval, takeprofitval, Close, High,Low, prediction1, CurrentPos, Type1) ##This function sets the stoploss and takeprofit based off the Type1 variable returned by the above functions

                            ##These trading strategies have custom stoploss & takeprofits:
                            #takeprofitval, stoplossval, prediction1, signal1= TS.SARMACD200EMA(stoplossval, takeprofitval,Close,High,Low,prediction1,CurrentPos,signal1)
                            #takeprofitval, stoplossval, prediction1, signal1= TS.TripleEMA(stoplossval, takeprofitval,Close,High,Low,prediction1,CurrentPos,signal1)



                            if CurrentPos == -99 and prediction1 == 0:  ##not in a trade but want to enter a short position
                                positionPrice = Close[-1]
                                positionSize = (OrderSIZE * AccountBalance) / positionPrice ##work out OrderQTY
                                #print(positionSize)
                                CurrentPos = 0
                                tradeNO += 1
                                Highestprice = positionPrice
                                # stoplossval = positionPrice * trailing_stoploss
                                #trades.append({'x': i, 'y': positionPrice, 'type': "sell",'current_price': positionPrice})
                                Profit -= positionSize*Close[-1] * .00036 ##trading fee
                                AccountBalance -= positionSize * Close[-1] * .00036 ##trading fee
                                ##Create Order on Binance
                                if Coin_precision!=0:
                                    Order(round(positionSize,Coin_precision), 0, symbol,stoplossval,takeprofitval,positionPrice,Order_precision)
                                else:
                                    Order(round(positionSize), 0, symbol, stoplossval, takeprofitval,positionPrice, Order_precision)

                            elif CurrentPos == -99 and prediction1 == 1: ##not in a trade but want to enter a Long position
                                positionPrice = Close[-1]
                                positionSize = (OrderSIZE * AccountBalance) / positionPrice ##work out OrderQTY
                                CurrentPos = 1
                                tradeNO += 1
                                Highestprice = positionPrice
                                # stoplossval = positionPrice * trailing_stoploss
                                #trades.append({'x': i, 'y': positionPrice, 'type': "buy",'current_price': positionPrice})
                                Profit -= positionSize*Close[-1] * .00036 ##trading fee
                                AccountBalance -= positionSize * Close[-1] * .00036 ##trading fee
                                #print(stoplossval,takeprofitval)
                                ##Create Order on Binance
                                if Coin_precision!=0:
                                    Order(round(positionSize,Coin_precision), 1, symbol,stoplossval,takeprofitval,positionPrice,Order_precision)
                                else:
                                    Order(round(positionSize), 1, symbol, stoplossval, takeprofitval, positionPrice,Order_precision)

                            if CurrentPos != PrevPos:
                                prevsignal1 = -999
                                prevsignal2 = -999
                                print("Current Position:", CurrentPos, "\n")
                                print("Margin:", positionPrice - Close[-1])
                                # print("Date:",DateStream[-1])
                                try:
                                    print("Account Balance: ",AccountBalance,"Profit:",Profit,"PV:", (Profit * 100) / (tradeNO * Close[-1]), "Stoploss:",
                                          stoplossval, "TakeProfit:", takeprofitval)
                                except Exception as e:
                                    pass
                            # if prevProfit!=Profit:
                            #profitgraph.append(Profit)
                            PrevPos = copy(CurrentPos)

                    except BinanceAPIException as e:  # BinanceAPIException
                        print(e.status_code)
                        print(e.message)

                except Exception as e:  # Check for Errors in Code
                    exc_type, exc_obj, exc_tb = sys.exc_info()
                    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                    print(exc_type, fname, exc_tb.tb_lineno)


    def Order(q, side1, s,stoploss,takeprofit,PP,OP):
        if side1: ##Long
            ##Place the Long
            order1 = client.futures_create_order(
                symbol=s,
                side=SIDE_BUY,
                type=ORDER_TYPE_MARKET,
                quantity=q)
            #print(order1)
            if OP!=0:
                ##Place the stoploss
                order2 = client.futures_create_order(
                    symbol=s,
                    side=SIDE_SELL,
                    type=FUTURE_ORDER_TYPE_STOP_MARKET,
                    stopPrice=round(PP-stoploss,OP),
                    quantity=q)
                #Place the take profit
                order3 = client.futures_create_order(
                    symbol=s,
                    side=SIDE_SELL,
                    type=FUTURE_ORDER_TYPE_LIMIT,
                    price=round(PP+takeprofit,OP),
                    timeInForce='GTC',
                    quantity=q)
            else:
                ##Place the stoploss
                order2 = client.futures_create_order(
                    symbol=s,
                    side=SIDE_SELL,
                    type=FUTURE_ORDER_TYPE_STOP_MARKET,
                    stopPrice=round(PP - stoploss),
                    quantity=q)
                # Place the take profit
                order3 = client.futures_create_order(
                    symbol=s,
                    side=SIDE_SELL,
                    type=FUTURE_ORDER_TYPE_LIMIT,
                    price=round(PP + takeprofit),
                    timeInForce='GTC',
                    quantity=q)
        else: ##Short
            ##Place the short
            order1 = client.futures_create_order(
                symbol=s,
                side=SIDE_SELL,
                type=ORDER_TYPE_MARKET,
                # timeInForce=TIME_IN_FORCE_GTC,
                quantity=q)

            # price='0.00001')
            if OP!=0:
                ##Place the stoploss
                order2 = client.futures_create_order(
                    symbol=s,
                    side=SIDE_BUY,
                    type=FUTURE_ORDER_TYPE_STOP_MARKET,
                    stopPrice=round(PP+stoploss,OP),
                    quantity=q)
                ##Place the take profit
                order3 = client.futures_create_order(
                    symbol=s,
                    side=SIDE_BUY,
                    type=FUTURE_ORDER_TYPE_LIMIT,
                    timeInForce='GTC',
                    price=round(PP-takeprofit,OP),
                    quantity=q)
            else:
                ##Place the stoploss
                order2 = client.futures_create_order(
                    symbol=s,
                    side=SIDE_BUY,
                    type=FUTURE_ORDER_TYPE_STOP_MARKET,
                    stopPrice=round(PP + stoploss),
                    quantity=q)
                ##Place the take profit
                order3 = client.futures_create_order(
                    symbol=s,
                    side=SIDE_BUY,
                    type=FUTURE_ORDER_TYPE_LIMIT,
                    timeInForce='GTC',
                    price=round(PP - takeprofit),
                    quantity=q)


    def run():
        try:
            asyncio.get_event_loop().run_until_complete(runWS())
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)
            print("Error in websocket, retrying")
            time.sleep(1)
            run()


    run()
else:       ## Paper Trading, exact same as above but simulated trading with graphs
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

            #prediction1,Type = TS.MovingAverage(CloseStream,prediction1)
            #prediction1,signal1,signal2,Type =TS.StochRSIMACD(prediction1,CloseStream,signal1,signal2)
            #prediction1, signal1, signal2, Type = TS.tripleEMAStochasticRSIATR(CloseStream,signal1,signal2,prediction1)
            #prediction1,Type = TS.Fractal(CloseStream,LowStream,HighStream,signal1,prediction1)
            #prediction1,signal1,signal2,HighestUlt,Highest,Type = TS.UltOscMACD(prediction1,CloseStream,HighStream,LowStream,signal1,signal2,HighestUlt,Highest)
            prediction1, signal1, Type = TS.RSIStochEMA200(prediction1,CloseStream,HighStream,LowStream,signal1,signal2,CurrentPos)
            #prediction1,Type = TS.Fractal2(CloseStream,LowStream,HighStream,signal1,prediction1)
            stoplossval, takeprofitval = TS.SetSLTP(stoplossval, takeprofitval,CloseStream,HighStream,LowStream,prediction1,CurrentPos,Type)

            #takeprofitval, stoplossval, prediction1, signal1= TS.SARMACD200EMA(stoplossval, takeprofitval,CloseStream,HighStream,LowStream,prediction1,CurrentPos,signal1)
            #takeprofitval, stoplossval, prediction1, signal1= TS.TripleEMA(stoplossval, takeprofitval,CloseStream,HighStream,LowStream,prediction1,CurrentPos,signal1)

        #################################################################
            #################################################################

            if CurrentPos == -99 and prediction1 == 0:
                positionPrice = CloseStream[len(CloseStream) - 1]
                positionSize= (OrderSIZE*AccountBalance)/positionPrice
                CurrentPos = 0
                tradeNO+=1
                Highestprice = positionPrice
               #stoplossval = positionPrice * trailing_stoploss
                trades.append({'x':i,'y':positionPrice,'type': "sell",
                               'current_price': positionPrice})
                Profit -= CloseStream[len(CloseStream) - 1] * .00036
                AccountBalance -= positionSize * CloseStream[-1] * .00036
            elif CurrentPos == -99 and prediction1 == 1:
                positionPrice = CloseStream[len(CloseStream) - 1]
                positionSize = (OrderSIZE * AccountBalance) / positionPrice
                CurrentPos = 1
                tradeNO += 1
                Highestprice = positionPrice
                #stoplossval = positionPrice * trailing_stoploss
                trades.append({'x':i,'y':positionPrice, 'type': "buy",
                                    'current_price': positionPrice})
                Profit -= CloseStream[len(CloseStream) - 1] * .00036
                AccountBalance -= positionSize * CloseStream[-1] * .00036

            if Highestprice - LowStream[ - 1] < -stoplossval and CurrentPos == 0:
                Profit +=-stoplossval #positionPrice-CloseStream[len(CloseStream) - 1]  ##This will be positive if the price went down
                AccountBalance += positionSize * -stoplossval # (positionPrice-CloseStream[len(CloseStream) - 1])
                positionPrice = CloseStream[len(CloseStream) - 1]
                Profit -= CloseStream[-1] * .00036
                AccountBalance-= positionSize*CloseStream[-1] * .00036
                cashout.append({'x': i, 'y': CloseStream[-1], 'type': "loss",'position':'short'})
                # CurrentPos = -99
                CurrentPos = -99

                Profit -= CloseStream[len(CloseStream) - 1] * .00036
            elif HighStream[- 1] - Highestprice < -stoplossval and CurrentPos == 1:
                Profit +=-stoplossval #CloseStream[len(CloseStream) - 1] - positionPrice ##This will be positive if the price went up
                AccountBalance += positionSize* -stoplossval #(CloseStream[len(CloseStream) - 1] - positionPrice)
                positionPrice = CloseStream[len(CloseStream) - 1]
                Profit -= CloseStream[-1] * .00036
                AccountBalance -= positionSize * CloseStream[-1] * .00036
                cashout.append({'x': i, 'y': CloseStream[-1], 'type': "loss",'position':'long'})
                # CurrentPos = -99
                CurrentPos = -99

                Profit -= CloseStream[len(CloseStream) - 1] * .00036
            elif positionPrice - CloseStream[-1] > takeprofitval and CurrentPos == 0:
                Profit += takeprofitval #positionPrice - CloseStream[-1]
                AccountBalance += positionSize *  takeprofitval #(positionPrice - CloseStream[len(CloseStream) - 1])
                correct += 1
                positionPrice = CloseStream[-1]
                Profit -= CloseStream[-1] * .00036
                AccountBalance -= positionSize * CloseStream[-1] * .00036
                cashout.append({'x': i, 'y': CloseStream[-1], 'type': "win",'position':'short'})
                CurrentPos = -99

            elif CloseStream[-1] - positionPrice > takeprofitval and CurrentPos == 1:
                Profit +=  takeprofitval #CloseStream[-1] - positionPrice
                AccountBalance += positionSize *  takeprofitval #(CloseStream[len(CloseStream) - 1] - positionPrice)
                correct += 1
                positionPrice = CloseStream[-1]
                Profit -= CloseStream[-1] * .00036
                AccountBalance -= positionSize * CloseStream[-1] * .00036
                cashout.append({'x': i, 'y': CloseStream[-1], 'type': "win",'position':'long'})
                CurrentPos = -99

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
                prevsignal1=-999
                prevsignal2=-999
                print("Current Position:",CurrentPos,"\n")
                print("Margin:",positionPrice-CloseStream[-1])
                #print("Date:",DateStream[-1])
                try:
                    print("Profit: ", Profit, "PV:", (Profit * 100) / (tradeNO * CloseStream[-1]),"Stoploss:",stoplossval,"TakeProfit:",takeprofitval)
                except Exception as e:
                    pass
            #if prevProfit!=Profit:
            profitgraph.append(Profit)
            PrevPos=copy(CurrentPos)
            if AccountBalance<0:
                print("Negative account balance, No Equity")
                break
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
    for trade in cashout:
        #trade_date = mpl_dates.date2num([pd.to_datetime(trade['Date'])])[0]
        if trade['type'] == 'win':
            ax1.scatter(trade['x'],trade['y']-.08, c='green', label='green', s=80, edgecolors='none',marker=".")
        else:
            ax1.scatter(trade['x'],trade['y']+.08, c='red', label='red', s=80, edgecolors='none', marker=".")
        if trade['position']=='long' and trade['type'] == 'win':
            longwins+=1
        elif trade['position']=='long' and trade['type'] == 'loss':
            longlosses+=1
        elif trade['position']=='short' and trade['type'] == 'win':
            shortwins+=1
        elif trade['position']=='short' and trade['type'] == 'loss':
            shortlosses+=1
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
    except Exception as E:
        pass
    try:
        print("Long W/L:", longwins / longlosses)
    except Exception as E:
        pass
    print("Account Balance:",AccountBalance/leverage)
    print("% Gain on Account:",((AccountBalance-OriginalAccountSize)*100)/OriginalAccountSize)
    #Close1=data['Close']

    #xs = [x[0] for x in profitgraph]
    #ys = [x[1] for x in profitgraph]
    #x, y = zip(*profitgraph)
    #ax2.plot(profitgraphx, profitgraphy)
    #plt.plot(profitgraph[:])
    ax2.plot(profitgraph)

    plt.ylabel('Dollars')
    plt.xlabel('Time')
    #plt.legend(loc=2)
    plt.show()