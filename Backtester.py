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
import download_Data as DD
Coin_precision = -99  ##Precision Coin is measured up to
Order_precision = -99 ##Precision Orders are measured up to
#import personal_strats as PS
#data.reset_index(level=0, inplace=True)
trades = deque(maxlen=100000) ##keep track of shorts/Longs for graphing
cashout = deque(maxlen=100000) ##keep track of Winning trades/ Losing trades
signals= deque(maxlen=100000) ##when a siganl occured , NOT IN USE

symbol = ['RAYUSDT', 'NEARUSDT', 'AUDIOUSDT', 'HNTUSDT', 'DGBUSDT', 'ZRXUSDT', 'BCHUSDT', 'HOTUSDT', 'ARUSDT', 'FLMUSDT',
          'SFPUSDT', 'BELUSDT', 'RENUSDT', 'ADAUSDT', 'STORJUSDT', 'BZRXUSDT', 'CHRUSDT', 'WAVESUSDT', 'CHZUSDT', 'XRPUSDT',
          'SANDUSDT', 'OCEANUSDT', 'ENJUSDT', 'YFIIUSDT', 'GRTUSDT', 'UNIUSDT', 'TLMUSDT', 'XTZUSDT', 'LUNAUSDT', 'EOSUSDT',
          'SKLUSDT', 'GTCUSDT', 'DOTUSDT', '1INCHUSDT', 'UNFIUSDT', 'FTMUSDT', 'RLCUSDT', 'ATOMUSDT', 'BLZUSDT', 'SNXUSDT',
          'SOLUSDT', 'ETCUSDT', 'BNBUSDT', 'CELRUSDT', 'OGNUSDT', 'ETHUSDT', 'NEOUSDT', 'TOMOUSDT', 'CELOUSDT', 'KLAYUSDT',
          'TRBUSDT', 'TRXUSDT', 'EGLDUSDT', 'CRVUSDT', 'BAKEUSDT', 'NUUSDT', 'SRMUSDT', 'ALICEUSDT', 'CTKUSDT', 'ARPAUSDT',
          'MATICUSDT', 'IOTXUSDT', 'DENTUSDT', 'IOSTUSDT', 'OMGUSDT', 'BANDUSDT', 'BTCUSDT', 'NKNUSDT', 'RSRUSDT', 'IOTAUSDT',
          'CVCUSDT', 'REEFUSDT', 'BTSUSDT', 'BTTUSDT', 'ONEUSDT', 'ANKRUSDT', 'SUSHIUSDT', 'ALGOUSDT', 'SCUSDT', 'ONTUSDT',
          'MANAUSDT', 'ATAUSDT', 'MKRUSDT', 'DODOUSDT', 'LITUSDT', 'ICPUSDT', 'ZECUSDT', 'ICXUSDT', 'ZENUSDT', 'DOGEUSDT',
          'ALPHAUSDT', 'SXPUSDT', 'HBARUSDT', 'RVNUSDT', 'CTSIUSDT', 'KAVAUSDT', 'C98USDT', 'THETAUSDT', 'MASKUSDT', 'AAVEUSDT',
          'YFIUSDT', 'AXSUSDT', 'ZILUSDT', 'XEMUSDT', 'COMPUSDT', 'RUNEUSDT', 'AVAXUSDT', 'KNCUSDT', 'LPTUSDT', 'LRCUSDT',
          'MTLUSDT', 'VETUSDT', 'DASHUSDT', 'KEEPUSDT', 'LTCUSDT', 'DYDXUSDT', 'LINAUSDT', 'XLMUSDT', 'LINKUSDT', 'QTUMUSDT',
          'KSMUSDT', 'FILUSDT', 'STMXUSDT', 'BALUSDT', 'GALAUSDT', 'BATUSDT', 'AKROUSDT', 'XMRUSDT', 'COTIUSDT']

###################################################################################################################################
#######################################             SETTINGS            ###########################################################
###################################################################################################################################

EffectiveAccountBalance = -99 ##set later
OrderSIZE = .1 ## Amount of effective account balance to use per trade
AccountBalance = 1000
leverage = 10  ##leverage being used
test_set = 1  ##If OFF we are only paper trading on in-sample data, if ON the we are paper trading on out of sample data to determine the validity of our strategies results
test_set_length = "2 month ago UTC"  ## valid strings 'x days/weeks/months/years ago UTC'
time_period = 2  ##time_period in same units as test_set_length above
TIME_INTERVAL = 15  ##Candlestick interval in minutes, valid options:1,   3,   5,  15,   30,  60, 120,240,360,480,720, 1440,4320, 10080, 40320
load_data = 1 ##load data from a file, download the data using download_Data.py
use_heikin_ashi = 1  ##May take a long time/ will look at speeding up in future
use_trailing_stop = 0 ##   (Causing rounding error i think)  flag to use trailing stop, If on when the takeprofitval margin is reached a trailing stop will be set with the below percentage distance
trailing_stop_distance = .01 ## 1% trailing stop activated by hitting the takeprofitval for a coin







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

###################################################################################################################################
###################################################################################################################################
###################################################################################################################################

######### flags/variables: #######################
Highest_lowest = 0
Type = []
stoplossval = []
takeprofitval = []
CurrentPos = []
positionSize = []
positionPrice = []
PrevPos = []
prediction = []
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
correct=0 ##winning trades
profitgraph=[] #for graphing the profit change over time
pp = pprint.PrettyPrinter()
Sleep=0
tradeNO=0 ##number of trades

High_1min = []
Low_1min = []
Close_1min= []
Open_1min = []
Date_1min = []
profitgraph.append(AccountBalance)
count = 0
percent = .01 ##percentage to hold out for
originalBalance = copy(AccountBalance)
fee = .00036
trailing_stop_value = -99 ##gets set automatically depending on the trailing stop percent, if used above
#####################################################################################################################
#####################################################################################################################

period_string, time_CAGR = Helper.get_period_String(test_set_length, time_period)

if load_data:
    print("Loading Price Data")
    i = 0
    while i < len(symbol):
        if test_set:
            path = f"{DD.path}\\{symbol[i]}_{TIME_INTERVAL}_{time_period} {period_string} ago UTC_test.joblib"
        else:
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
                DD.get_data(TIME_INTERVAL,symbol[i],time_period,test_set,test_set_length)
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
                    print(f"Wrong path specified in download_Data.py,error: {e}")
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
Open_H = []
Close_H = []
High_H = []
Low_H = []
OpenStream_H = []
CloseStream_H = []
HighStream_H = []
LowStream_H = []
if use_heikin_ashi:
    print("Generating Heikin ashi candles will take a while")
    Open_H, Close_H, High_H, Low_H = Helper.get_heikin_ashi(Open, Close, High, Low)
    print("Finished")

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
    OpenStream_H.append([])
    CloseStream_H.append([])
    HighStream_H.append([])
    LowStream_H.append([])


##variables for sharpe ratio
day_start_equity = AccountBalance
month_return = 0
monthly_return = []
Daily_return = []
Strategy = []
Trade_start = []
winning_trades = []
losing_trades = []
print(f"{TIME_INTERVAL} min OHLC Candle Sticks from a period of {time_period} {period_string}")
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
            if use_heikin_ashi:
                OpenStream_H[j] = flow.dataStream(OpenStream_H[j], float(Open_H[j][int(i / TIME_INTERVAL) - 1]), 1, 300)
                CloseStream_H[j] = flow.dataStream(CloseStream_H[j], float(Close_H[j][int(i / TIME_INTERVAL) - 1]), 1, 300)
                HighStream_H[j] = flow.dataStream(HighStream_H[j], float(High_H[j][int(i / TIME_INTERVAL) - 1]), 1, 300)
                LowStream_H[j] = flow.dataStream(LowStream_H[j], float(Low_H[j][int(i / TIME_INTERVAL) - 1]), 1, 300)
    #print(len(OpenStream))
    if len(OpenStream[0])>=100:
        prev_Account_Bal=copy(AccountBalance)
        EffectiveAccountBalance = AccountBalance*leverage

        for j in range(len(prediction)):
            if len(OpenStream[0]) == 100 and not pair_Trading:
                pass
                # Strategy = PS.sup_res(CloseStream[0]) ##not a strategy ive made public
                #Strategy.append(PS.fractal2([1,0,0,1,0,0,0,0,0]))
                #Strategy.append(PS.hidden_fractal([1,1,0,0,1,0,0,0,0]))
                #Strategy.append(TS.pump(DateStream[j], CloseStream[j], VolumeStream[j]))
            if not pair_Trading:
                if CurrentPos[j]==-99 and i%TIME_INTERVAL==0 and (i!=0 or TIME_INTERVAL==1):
                    break_even_flag=0

                    ##Public Strats :) :
                    ## These strats require a call to SetSLTP as they return a Type param:
                    #prediction[j],Type[j] = TS.StochRSIMACD(prediction[j], CloseStream[j],HighStream[j],LowStream[j])  ###########################################
                    #prediction[j], signal1, signal2, Type[j] = TS.tripleEMAStochasticRSIATR(CloseStream[j],signal1,signal2,prediction[j])
                    #prediction[j],Type[j]=TS.tripleEMA(CloseStream[j],OpenStream[j],prediction[j])
                    #prediction[j], Type[j] = TS.breakout(prediction[j],CloseStream[j],VolumeStream[j],symbol[j])
                    #prediction[j],Type[j] = TS.stochBB(prediction[j],CloseStream[j])
                    #prediction[j], Type[j] = TS.goldenCross(prediction[j],CloseStream[j])
                    #prediction[j] , Type[j] = TS.candle_wick(prediction,CloseStream[j],OpenStream[j],HighStream[j],LowStream[j])
                    #prediction[j],Close_pos,count,stoplossval[j] = TS.single_candle_swing_pump(prediction[j],CloseStream[j],HighStream[j],LowStream[j],CurrentPos[j],Close_pos,count,stoplossval[j])
                    #stoplossval[j], takeprofitval[j] = SetSLTP(stoplossval[j], takeprofitval[j], CloseStream[j],HighStream[j], LowStream[j], prediction[j],CurrentPos[j], Type[j],SL=STOP,TP=TAKE)
                    #print(prediction[j])
                    #prediction[j],stoplossval[j], takeprofitval[j] = Strategy[j].make_decision(((OrderSIZE*EffectiveAccountBalance)/Open_1min[j][i])*AccountBalance,CloseStream[j][-1],VolumeStream[j][-1])

                    ##These strats don't require a call to SetSLTP:
                    #prediction[j],stoplossval[j],takeprofitval[j] = TS.fibMACD(prediction[j], CloseStream[j], OpenStream[j],HighStream[j],LowStream[j])
                    #prediction[j],Highest_lowest,Close_pos = TS.trend_Ride(prediction[j], CloseStream[j], HighStream[j][-1], LowStream[j][-1], percent, CurrentPos[j], Highest_lowest) ##This strategy holds a position until the price dips/rises a certain percentage
                    #prediction[j],Close_pos = TS.RSI_trade(prediction[j],CloseStream[j],CurrentPos[j],Close_pos)

                    ##########################################################################################################################################################################
                    ##########################################################################################################################################################################
                    ##Non public Strats sorry :( :
                    # prediction[j],Type[j] = Strategy.Check_for_sup_res(CloseStream[j],OpenStream[j],HighStream[j],LowStream[j]) ##not a strategy ive made public
                    #prediction[j], stoplossval[j], takeprofitval[j] = Strategy[j].check_for_pullback(CloseStream[j], LowStream[j], HighStream[j], OpenStream[j],VolumeStream[j],prediction[j]) ##not a strategy ive made public
                    #if prediction[j]==1:
                    #    prediction[j]=-99
                    ##########################################################################################################################################################################

                    ##Ensure we only trade one coin at a time:
                    if prediction[j]!=-99:
                        for q in CurrentPos:
                            if q!=-99:
                                prediction[j]=-99
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

            #Close_pos = Strategy[j].Trade_timer(CurrentPos[j], Close_pos)

            ##If the trade won't cover the fee & profit something then don't place it
            #if (prediction[j] == 1 or prediction[j] == 0) and (.00125 * Close_1min[j][-1] > takeprofitval[j]) and (not pair_Trading) and (not Hold_pos):
            #    prediction[j] = -99
    #################################################################
        #################################################################
            if positionPrice[j] - Open_1min[j][i] < -stoplossval[j] and CurrentPos[j] == 0:# and not Hold_pos:
                Profit +=-stoplossval[j]
                month_return-=positionSize[j] *stoplossval[j]
                AccountBalance += positionSize[j] * -stoplossval[j]
                Profit -= Open_1min[j][i] * fee
                AccountBalance-= positionSize[j] * Open_1min[j][i] * fee
                month_return -= positionSize[j] * Open_1min[j][i] * fee
                cashout.append({'x': i, 'y': Open_1min[j][i], 'type': "loss",'position':'short','Profit': -stoplossval[j]*positionSize[j]})
                profitgraph.append(AccountBalance)
                CurrentPos[j] = -99
                losing_trades.append(Trade_start)

            elif Open_1min[j][i] - positionPrice[j] < -stoplossval[j] and CurrentPos[j] == 1:# and not Hold_pos:
                Profit +=-stoplossval[j]
                month_return -= positionSize[j] *stoplossval[j]
                AccountBalance += positionSize[j]* -stoplossval[j]
                Profit -= Open_1min[j][i] * fee
                AccountBalance -= positionSize[j] * Open_1min[j][i] * fee
                month_return -= positionSize[j] * Open_1min[j][i] * fee
                cashout.append({'x': i, 'y': Open_1min[j][i], 'type': "loss",'position':'long','Profit': -stoplossval[j]*positionSize[j]})
                # CurrentPos = -99
                profitgraph.append(AccountBalance)
                CurrentPos[j] = -99
                losing_trades.append(Trade_start)

            elif positionPrice[j] - Open_1min[j][i] > takeprofitval[j] and CurrentPos[j] == 0 and not use_trailing_stop:# and not Hold_pos:
                Profit += takeprofitval[j]
                month_return += positionSize[j] *takeprofitval[j]
                AccountBalance += positionSize[j] *  takeprofitval[j]
                correct += 1
                Profit -= Open_1min[j][i] * fee
                AccountBalance -= positionSize[j] * Open_1min[j][i] * fee
                month_return -= positionSize[j] * Open_1min[j][i] * fee
                cashout.append({'x': i, 'y': Open_1min[j][i], 'type': "win",'position':'short','Profit': takeprofitval[j]*positionSize[j]})
                CurrentPos[j] = -99
                profitgraph.append(AccountBalance)
                winning_trades.append(Trade_start)

            elif Open_1min[j][i] - positionPrice[j] > takeprofitval[j] and CurrentPos[j] == 1 and not use_trailing_stop:# and not Hold_pos:
                Profit +=  takeprofitval[j]
                month_return += positionSize[j] *takeprofitval[j]
                AccountBalance += positionSize[j] *  takeprofitval[j]
                correct += 1
                Profit -= Open_1min[j][i] * fee
                AccountBalance -= positionSize[j] * Open_1min[j][i] * fee
                month_return -= positionSize[j] * Open_1min[j][i] * fee
                cashout.append({'x': i, 'y': Open_1min[j][i], 'type': "win",'position':'long','Profit': takeprofitval[j]*positionSize[j]})
                CurrentPos[j] = -99
                profitgraph.append(AccountBalance)
                winning_trades.append(Trade_start)

            elif Close_pos==1 and CurrentPos[j] == 1:
                prev_Profit = copy(Profit)
                Profit += Open_1min[j][i] - positionPrice[j] ##sell at next open candle
                month_return += positionSize[j] * (Open_1min[j][i]-positionPrice[j])
                AccountBalance += positionSize[j] * (Open_1min[j][i]-positionPrice[j])
                if prev_Profit<Profit:
                    correct += 1
                    winning_trades.append(Trade_start)
                    cashout.append({'x': i, 'y': Open_1min[j][i], 'type': "win", 'position': 'long',
                                    'Profit': (Open_1min[j][i]- positionPrice[j]) * positionSize[j]})
                else:
                    losing_trades.append(Trade_start)
                    cashout.append({'x': i, 'y': Open_1min[j][i], 'type': "loss", 'position': 'long',
                                    'Profit': (Open_1min[j][i] - positionPrice[j]) * positionSize[j]})
                Profit -= Open_1min[j][i] * fee
                AccountBalance -= positionSize[j] * Open_1min[j][i] * fee
                month_return -= positionSize[j] * Open_1min[j][i] * fee
                CurrentPos[j] = -99
                profitgraph.append(AccountBalance)
                Close_pos = 0

                print("Position Closed")

            elif Close_pos == 1 and CurrentPos[j] == 0:
                prev_Profit = copy(Profit)
                Profit += positionPrice[j] - Open_1min[j][i]
                month_return += positionSize[j] * (positionPrice[j] - Open_1min[j][i])
                AccountBalance += positionSize[j] *  (positionPrice[j] - Open_1min[j][i])
                if prev_Profit<Profit:
                    correct += 1
                    winning_trades.append(Trade_start)
                    cashout.append({'x': i, 'y': Open_1min[j][i], 'type': "win", 'position': 'short',
                                    'Profit': (positionPrice[j] - Open_1min[j][i]) * positionSize[j]})
                else:
                    losing_trades.append(Trade_start)
                    cashout.append({'x': i, 'y': Open_1min[j][i], 'type': "loss", 'position': 'short',
                                    'Profit': (positionPrice[j] - Open_1min[j][i]) * positionSize[j]})
                Profit -= Open_1min[j][i] * fee
                AccountBalance -= positionSize[j] * Open_1min[j][i] * fee
                month_return -= positionSize[j] * Open_1min[j][i] * fee
                CurrentPos[j] = -99
                profitgraph.append(AccountBalance)
                Close_pos=0

                print("Position Closed")

            elif use_trailing_stop and CurrentPos[j] == 0:
                #trailing_stop_value
                if Open_1min[j][i] < positionPrice[j] - takeprofitval[j] and trailing_stop_value ==-99:
                    ##takeprofit reached so set trailing_stop_value
                    trailing_stop_value = (positionPrice[j] - takeprofitval[j])*(1 + trailing_stop_distance) ##price at which we will sell if moved up to
                    print("Trailing Stop: ", trailing_stop_value)
                elif Open_1min[j][i] > trailing_stop_value and trailing_stop_value!=-99:
                    ##trailing stop has been hit
                    Profit += positionPrice[j] - trailing_stop_value
                    month_return += positionSize[j] * (positionPrice[j] - trailing_stop_value)
                    AccountBalance += positionSize[j] * (positionPrice[j] - trailing_stop_value)
                    print("Trailing Stop Profit", positionSize[j] * (positionPrice[j] - trailing_stop_value))
                    correct += 1
                    Profit -= trailing_stop_value * fee
                    AccountBalance -= positionSize[j] * trailing_stop_value * fee
                    month_return -= positionSize[j] * trailing_stop_value * fee
                    cashout.append({'x': i, 'y': trailing_stop_value, 'type': "win", 'position': 'short',
                                    'Profit': positionSize[j] * (positionPrice[j] - trailing_stop_value)})
                    CurrentPos[j] = -99
                    profitgraph.append(AccountBalance)
                    trailing_stop_value = -99
                    winning_trades.append(Trade_start)

                elif Open_1min[j][i]*(1 + trailing_stop_distance) < trailing_stop_value and trailing_stop_value!=-99:
                    trailing_stop_value = Open_1min[j][i]*(1 + trailing_stop_distance) ##move trailing stop as a new low was reached
                    print("Trailing Stop: ", trailing_stop_value)
            elif use_trailing_stop and CurrentPos[j] ==1:
                # trailing_stop_value
                if Open_1min[j][i] > positionPrice[j] + takeprofitval[j] and trailing_stop_value == -99:
                    ##takeprofit reached so set trailing_stop_value
                    trailing_stop_value = (positionPrice[j] + takeprofitval[j]) * (1 - trailing_stop_distance)  ##price at which we will sell if moved up to
                    print("Trailing Stop: ",trailing_stop_value)

                elif Open_1min[j][i] < trailing_stop_value and trailing_stop_value != -99:
                    ##trailing stop has been hit
                    Profit += trailing_stop_value - positionPrice[j]
                    month_return += positionSize[j] * (trailing_stop_value - positionPrice[j])
                    AccountBalance += positionSize[j] * (trailing_stop_value - positionPrice[j])
                    print("Trailing Stop Profit",positionSize[j] * (trailing_stop_value - positionPrice[j]))
                    correct += 1
                    Profit -= trailing_stop_value * fee
                    AccountBalance -= positionSize[j] * trailing_stop_value * fee
                    month_return -= positionSize[j] * trailing_stop_value * fee
                    cashout.append({'x': i, 'y': trailing_stop_value, 'type': "win", 'position': 'short',
                                    'Profit': positionSize[j] * (trailing_stop_value - positionPrice[j])})
                    CurrentPos[j] = -99
                    profitgraph.append(AccountBalance)
                    trailing_stop_value = -99
                    winning_trades.append(Trade_start)

                elif Open_1min[j][i]*(1 - trailing_stop_distance) > trailing_stop_value and trailing_stop_value!=-99:
                    trailing_stop_value = Open_1min[j][i]*(1 - trailing_stop_distance) ##move trailing stop as a new high was reached
                    print("Trailing Stop: ", trailing_stop_value)

            if CurrentPos[j] == -99 and prediction[j] == 0:
                positionPrice[j] = Open_1min[j][i]##next open candle #CloseStream[j][len(CloseStream[j]) - 1]
                positionSize[j]= (OrderSIZE*EffectiveAccountBalance)/positionPrice[j]
                CurrentPos[j] = 0
                tradeNO+=1
                trades.append({'x':i,'y':positionPrice[j],'type': "sell",'current_price': positionPrice[j]})
                Profit -= Open_1min[j][i] * fee
                AccountBalance -= positionSize[j] * Open_1min[j][i] * fee
                month_return -= positionSize[j] * Open_1min[j][i] * fee
                prediction[j] = -99

                Trade_start = [symbol[j], Date_1min[j][i],CurrentPos[j]]  ##we enter trade on next candle

            elif CurrentPos[j] == -99 and prediction[j] == 1:
                positionPrice[j] = Open_1min[j][i] ##next open candle
                positionSize[j] = (OrderSIZE * EffectiveAccountBalance) / positionPrice[j]
                CurrentPos[j] = 1
                tradeNO += 1
                trades.append({'x':i,'y':positionPrice[j], 'type': "buy",'current_price': positionPrice[j]})
                Profit -= Open_1min[j][i] * fee
                AccountBalance -= positionSize[j] * Open_1min[j][i] * fee
                month_return -= positionSize[j] * Open_1min[j][i] * fee
                prediction[j] = -99

                Trade_start = [symbol[j], Date_1min[j][i],CurrentPos[j]]  ##we enter trade on next candle



            if CurrentPos[j] != PrevPos[j]:
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
print("Winning Trades: ",winning_trades,"\n","Losing Trades: ",losing_trades)


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
