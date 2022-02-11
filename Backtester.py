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
import create_trade_graphs
import trade_graph_info
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

from copy import copy
import time
trades = deque(maxlen=100000) ##keep track of shorts/Longs for graphing
cashout = deque(maxlen=100000) ##keep track of Winning trades/ Losing trades
signals= deque(maxlen=100000) ##when a siganl occured , NOT IN USE


symbol = ['RAYUSDT', 'NEARUSDT', 'AUDIOUSDT', 'HNTUSDT', 'DGBUSDT', 'ZRXUSDT', 'BCHUSDT', 'HOTUSDT', 'ARUSDT', 'FLMUSDT',
          'SFPUSDT', 'BELUSDT', 'RENUSDT', 'ADAUSDT', 'STORJUSDT', 'CHRUSDT', 'WAVESUSDT', 'CHZUSDT', 'XRPUSDT',
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
test_set = 0  ##If OFF we are only paper trading on in-sample data, if ON the we are paper trading on out of sample data to determine the validity of our strategies results
time_period_units = 'day' ## day/week/month/year
time_period = 2  ##Number of units
TIME_INTERVAL = '1m'  ##Candlestick interval in minutes, valid options: 1m,3m,5m,15m,30m,1hr,2hr,4ht,6hr,8hr,12hr,1d,3d,1w,1M I think...
load_data = 1 ##load data from a file, download the data using download_Data.py
save_data = 0 ##set to true to overwrite data thats currently in price_data folder
use_trailing_stop = 0 ## DO NOT USE  (Causing rounding error i think)  flag to use trailing stop, If on when the takeprofitval margin is reached a trailing stop will be set with the below percentage distance
trailing_stop_distance = .01 ## 1% trailing stop activated by hitting the takeprofitval for a coin
##################################################################################################################################
##################################################################################################################################
if save_data:
    load_data= 0

#### Trade graph settings ####
graph_trades_and_save_to_folder = 0 ##If true a graph for each of the trades taken by your strategy will be created and saved to a new folder on the desktop
trade_graph_folder = 'trade_graphs' ##Name of folder you want to create and save the graphs in on the desktop

## indicators to graph.
# less is more, the graphs will be messy if too many are used
##If your strategy is lacking try turning on some of these and see if they could improve trades

period_leading_to_signal = 20 ##How many bars before a signal to use for graph
period_after_signal = 20 ##How many bars before a signal to use for graph
use_heikin_ashi = 0
use_emas = 1
use_smas = 0
sma_lengths = [20,50,100] ##length of SMA's should match your strategy
ema_lengths = [5,20,50] ##lengths of the EMA's should match your strategy
###These use the default settings if customization is needed you can do that down further in the script, look at sections starting 'if graph_trades_and_save_to_folder' to customize
use_stochastic = 0
use_stochastic_rsi = 0
use_ease_of_movement = 0
use_rsi = 0
use_macd = 0
use_atr = 0
use_bollinger_bands = 0
use_awesome=1 ##awesome oscillator
use_adx=0
use_cci=0
use_obv=0 ##on balance volume
use_fi=0 ##force index
use_mfi=0 ##money flow index
use_tsi=0 ##True strength index
use_acc_dist = 0 ##Accumulation Distribution
use_vwap = 0##Volume weighted average price
###################################################################################################################################
###################################################################################################################################
###################################################################################################################################

######### flags/variables: #######################
Highest_lowest = 0
Type = -99
stoplossval = -99
takeprofitval = -99
CurrentPos = -99
positionSize = -99
positionPrice = -99
PrevPos = -99
prediction = -99
Trading_index = -99 ##index of coin we are trading
Trade_Stage = 0 ##flag to say in a trade
Close_pos = 0
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
fees_paid = 0
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
trade_data = {}

time_CAGR = Helper.get_CAGR(time_period_units, time_period)

if load_data:
    print("Loading Price Data")
    i = 0
    while i < len(symbol):
        if test_set:
            path = f"{DD.path}price_data\\{symbol[i]}_{TIME_INTERVAL}_{time_period} {time_period_units} ago UTC_test.joblib"
        else:
            path = f"{DD.path}price_data\\{symbol[i]}_{TIME_INTERVAL}_{time_period} {time_period_units} ago UTC.joblib"
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
                print("File not Found, Checking if file exists with old naming convention and renaming if present...")
                if test_set:
                    TIME_INTERVAL_TEMP = Helper.get_TIME_INTERVAL(TIME_INTERVAL)
                    old_path = f"{DD.path}price_data\\{symbol[i]}_{TIME_INTERVAL_TEMP}_{time_period} {time_period_units} ago UTC_test.joblib"
                    new_path = f"{DD.path}price_data\\{symbol[i]}_{TIME_INTERVAL}_{time_period} {time_period_units} ago UTC_test.joblib"
                    #print(old_path,new_path)
                else:
                    TIME_INTERVAL_TEMP = Helper.get_TIME_INTERVAL(TIME_INTERVAL)
                    old_path = f"{DD.path}price_data\\{symbol[i]}_{TIME_INTERVAL_TEMP}_{time_period} {time_period_units} ago UTC.joblib"
                    new_path = f"{DD.path}price_data\\{symbol[i]}_{TIME_INTERVAL}_{time_period} {time_period_units} ago UTC.joblib"
                os.rename(old_path, new_path) ##rename to new convention
                print("Rename Successful, Loading Data...")
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
                    DD.get_data(TIME_INTERVAL,symbol[i],time_period,test_set,time_period_units,DD.path)
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
    try:
        i = 0
        while i < len(symbol):
            Date_temp, Open_temp, Close_temp, High_temp, Low_temp, Volume_temp, High_1min_temp, Low_1min_temp, Close_1min_temp,Open_1min_temp, Date_1min_temp = Helper.get_Klines(TIME_INTERVAL,symbol[i],time_period,test_set,time_period_units,save_data)
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
            i+=1
    except BinanceAPIException as e:
        print(f"Failed to download data for {symbol[i]} removing from data_set, Error: {e}")
        symbol.pop(i)
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
indices = []
for j in range(period_leading_to_signal + period_after_signal):
    indices.append(j)

print("Generating Heikin ashi candles will take a while")
Open_H, Close_H, High_H, Low_H = Helper.get_heikin_ashi(Open, Close, High, Low)
print("Finished")

for i in range(len(symbol)):
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
print(f"{TIME_INTERVAL} OHLC Candle Sticks from a period of {time_period} {time_period_units} ago")
original_time_interval = copy(TIME_INTERVAL)
TIME_INTERVAL = Helper.get_TIME_INTERVAL(TIME_INTERVAL) ##Convert string to an integer for the rest of the script
for i in range(len(High_1min[0])-1):
    #global trailing_stoploss,Highestprice
    if (i%TIME_INTERVAL==0 and i!=0) or TIME_INTERVAL==1:
        for j in range(len(High_1min)):
            DateStream[j].append(Date[j][int(i/TIME_INTERVAL)-1])
            OpenStream[j].append(float(Open[j][int(i/TIME_INTERVAL)-1]))
            CloseStream[j].append(float(Close[j][int(i/TIME_INTERVAL)-1]))
            HighStream[j].append(float(High[j][int(i/TIME_INTERVAL)-1]))
            LowStream[j].append(float(Low[j][int(i/TIME_INTERVAL)-1]))
            VolumeStream[j].append(float(Volume[j][int(i/TIME_INTERVAL)-1]))
            OpenStream_H[j].append(float(Open_H[j][int(i / TIME_INTERVAL)-1]))
            CloseStream_H[j].append(float(Close_H[j][int(i / TIME_INTERVAL)-1]))
            HighStream_H[j].append(float(High_H[j][int(i / TIME_INTERVAL)-1]))
            LowStream_H[j].append(float(Low_H[j][int(i / TIME_INTERVAL)-1]))
    #print(len(OpenStream))
    if len(OpenStream[0])>=300:
        for j in range(len(High_1min)):
            DateStream[j].pop(0)
            OpenStream[j].pop(0)
            CloseStream[j].pop(0)
            HighStream[j].pop(0)
            LowStream[j].pop(0)
            VolumeStream[j].pop(0)
            OpenStream_H[j].pop(0)
            CloseStream_H[j].pop(0)
            HighStream_H[j].pop(0)
            LowStream_H[j].pop(0)

        prev_Account_Bal=copy(AccountBalance)
        EffectiveAccountBalance = AccountBalance*leverage
        if Trade_Stage == 1:
            if positionPrice - Open_1min[Trading_index][i] < -stoplossval and CurrentPos == 0:  # and not Hold_pos:
                Profit += -stoplossval
                month_return -= positionSize * stoplossval
                AccountBalance += positionSize * -stoplossval
                Profit -= Open_1min[Trading_index][i] * fee
                AccountBalance -= positionSize * Open_1min[Trading_index][i] * fee
                month_return -= positionSize * Open_1min[Trading_index][i] * fee
                cashout.append({'x': i, 'y': Open_1min[Trading_index][i], 'type': "loss", 'position': 'short',
                                'Profit': -stoplossval * positionSize})
                profitgraph.append(AccountBalance)
                CurrentPos = -99
                fees_paid += positionSize * Open_1min[Trading_index][i] * fee
                losing_trades.append(Trade_start)
                Trade_Stage = 0
                if graph_trades_and_save_to_folder:
                    trade_data[f'Trade_{tradeNO - 1}']['label'] = 0
                print(f"\nCurrent Position {symbol[Trading_index]}:", CurrentPos)
                print("Time:", Date_1min[Trading_index][i])
                # print("Time Max",DateStream[max_pos])
                # print("Time Min", DateStream[min_pos])
                try:
                    print("Account Balance: ", AccountBalance, "Order Size:", positionSize, "PV:",
                          (Profit * 100) / (tradeNO * CloseStream[Trading_index][-1]), "Stoploss:", stoplossval,
                          "TakeProfit:",
                          takeprofitval)
                except Exception as e:
                    pass
                Trading_index = -99

            elif Open_1min[Trading_index][i] - positionPrice < -stoplossval and CurrentPos == 1:  # and not Hold_pos:
                Profit += -stoplossval
                month_return -= positionSize * stoplossval
                AccountBalance += positionSize * -stoplossval
                Profit -= Open_1min[Trading_index][i] * fee
                AccountBalance -= positionSize * Open_1min[Trading_index][i] * fee
                month_return -= positionSize * Open_1min[Trading_index][i] * fee
                cashout.append({'x': i, 'y': Open_1min[Trading_index][i], 'type': "loss", 'position': 'long',
                                'Profit': -stoplossval * positionSize})
                # CurrentPos = -99
                profitgraph.append(AccountBalance)
                CurrentPos = -99
                fees_paid += positionSize * Open_1min[Trading_index][i] * fee
                losing_trades.append(Trade_start)
                Trade_Stage = 0
                if graph_trades_and_save_to_folder:
                    trade_data[f'Trade_{tradeNO - 1}']['label'] = 0
                print(f"\nCurrent Position {symbol[Trading_index]}:", CurrentPos)
                print("Time:", Date_1min[Trading_index][i])
                # print("Time Max",DateStream[max_pos])
                # print("Time Min", DateStream[min_pos])
                try:
                    print("Account Balance: ", AccountBalance, "Order Size:", positionSize, "PV:",
                          (Profit * 100) / (tradeNO * CloseStream[Trading_index][-1]), "Stoploss:", stoplossval,
                          "TakeProfit:",
                          takeprofitval)
                except Exception as e:
                    pass
                Trading_index = -99

            elif positionPrice - Open_1min[Trading_index][i] > takeprofitval and CurrentPos == 0 and not use_trailing_stop:  # and not Hold_pos:
                Profit += takeprofitval
                month_return += positionSize * takeprofitval
                AccountBalance += positionSize * takeprofitval
                correct += 1
                Profit -= Open_1min[Trading_index][i] * fee
                AccountBalance -= positionSize * Open_1min[Trading_index][i] * fee
                month_return -= positionSize * Open_1min[Trading_index][i] * fee
                cashout.append({'x': i, 'y': Open_1min[Trading_index][i], 'type': "win", 'position': 'short',
                                'Profit': takeprofitval * positionSize})
                CurrentPos = -99
                fees_paid += positionSize * Open_1min[Trading_index][i] * fee
                profitgraph.append(AccountBalance)
                Trade_Stage = 0
                if graph_trades_and_save_to_folder:
                    trade_data[f'Trade_{tradeNO - 1}']['label'] = 1
                print(f"\nCurrent Position {symbol[Trading_index]}:", CurrentPos)
                print("Time:", Date_1min[Trading_index][i])
                # print("Time Max",DateStream[max_pos])
                # print("Time Min", DateStream[min_pos])
                try:
                    print("Account Balance: ", AccountBalance, "Order Size:", positionSize, "PV:",
                          (Profit * 100) / (tradeNO * CloseStream[Trading_index][-1]), "Stoploss:", stoplossval,
                          "TakeProfit:",
                          takeprofitval)
                except Exception as e:
                    pass
                winning_trades.append(Trade_start)
                Trading_index = -99

            elif Open_1min[Trading_index][i] - positionPrice > takeprofitval and CurrentPos == 1 and not use_trailing_stop:  # and not Hold_pos:
                Profit += takeprofitval
                month_return += positionSize * takeprofitval
                AccountBalance += positionSize * takeprofitval
                correct += 1
                Profit -= Open_1min[Trading_index][i] * fee
                AccountBalance -= positionSize * Open_1min[Trading_index][i] * fee
                month_return -= positionSize * Open_1min[Trading_index][i] * fee
                cashout.append({'x': i, 'y': Open_1min[Trading_index][i], 'type': "win", 'position': 'long',
                                'Profit': takeprofitval * positionSize})
                CurrentPos = -99
                fees_paid += positionSize * Open_1min[Trading_index][i] * fee
                profitgraph.append(AccountBalance)
                Trade_Stage = 0
                print(f"\nCurrent Position {symbol[Trading_index]}:", CurrentPos)
                print("Time:", Date_1min[Trading_index][i])
                # print("Time Max",DateStream[max_pos])
                # print("Time Min", DateStream[min_pos])
                if graph_trades_and_save_to_folder:
                    trade_data[f'Trade_{tradeNO - 1}']['label'] = 1
                try:
                    print("Account Balance: ", AccountBalance, "Order Size:", positionSize, "PV:",
                          (Profit * 100) / (tradeNO * CloseStream[Trading_index][-1]), "Stoploss:", stoplossval,
                          "TakeProfit:",
                          takeprofitval)
                except Exception as e:
                    pass
                winning_trades.append(Trade_start)
                Trading_index = -99

            elif Close_pos == 1 and CurrentPos == 1:
                prev_val = copy(AccountBalance)
                prev_Profit = copy(Profit)
                Profit += Open_1min[Trading_index][i] - positionPrice  ##sell at next open candle
                month_return += positionSize * (Open_1min[Trading_index][i] - positionPrice)
                AccountBalance += positionSize * (Open_1min[Trading_index][i] - positionPrice)
                if prev_Profit < Profit:
                    correct += 1
                    winning_trades.append(Trade_start)
                    cashout.append({'x': i, 'y': Open_1min[Trading_index][i], 'type': "win", 'position': 'long',
                                    'Profit': (Open_1min[Trading_index][i] - positionPrice) * positionSize})
                else:
                    losing_trades.append(Trade_start)
                    cashout.append({'x': i, 'y': Open_1min[Trading_index][i], 'type': "loss", 'position': 'long',
                                    'Profit': (Open_1min[Trading_index][i] - positionPrice) * positionSize})
                Profit -= Open_1min[Trading_index][i] * fee
                AccountBalance -= positionSize * Open_1min[Trading_index][i] * fee
                month_return -= positionSize * Open_1min[Trading_index][i] * fee
                fees_paid += positionSize * Open_1min[Trading_index][i] * fee
                CurrentPos = -99
                profitgraph.append(AccountBalance)
                Trade_Stage = 0
                if graph_trades_and_save_to_folder:
                    if prev_val > AccountBalance:
                        trade_data[f'Trade_{tradeNO - 1}']['label'] = 1
                    else:
                        trade_data[f'Trade_{tradeNO - 1}']['label'] = 0
                print(f"\nCurrent Position {symbol[Trading_index]}:", CurrentPos)
                print("Time:", Date_1min[Trading_index][i])
                # print("Time Max",DateStream[max_pos])
                # print("Time Min", DateStream[min_pos])
                try:
                    print("Account Balance: ", AccountBalance, "Order Size:", positionSize, "PV:",
                          (Profit * 100) / (tradeNO * CloseStream[Trading_index][-1]), "Stoploss:", stoplossval,
                          "TakeProfit:",
                          takeprofitval)
                except Exception as e:
                    pass

                Close_pos = 0
                Trading_index = -99

                print("Position Closed")

            elif Close_pos == 1 and CurrentPos == 0:
                prev_val = copy(AccountBalance)
                prev_Profit = copy(Profit)
                Profit += positionPrice - Open_1min[Trading_index][i]
                month_return += positionSize * (positionPrice - Open_1min[Trading_index][i])
                AccountBalance += positionSize * (positionPrice - Open_1min[Trading_index][i])
                if prev_Profit < Profit:
                    correct += 1
                    winning_trades.append(Trade_start)
                    cashout.append({'x': i, 'y': Open_1min[Trading_index][i], 'type': "win", 'position': 'short',
                                    'Profit': (positionPrice - Open_1min[Trading_index][i]) * positionSize})
                else:
                    losing_trades.append(Trade_start)
                    cashout.append({'x': i, 'y': Open_1min[Trading_index][i], 'type': "loss", 'position': 'short',
                                    'Profit': (positionPrice - Open_1min[Trading_index][i]) * positionSize})
                Profit -= Open_1min[Trading_index][i] * fee
                AccountBalance -= positionSize * Open_1min[Trading_index][i] * fee
                month_return -= positionSize * Open_1min[Trading_index][i] * fee
                fees_paid += positionSize * Open_1min[Trading_index][i] * fee
                CurrentPos = -99
                profitgraph.append(AccountBalance)
                Close_pos = 0
                Trade_Stage = 0
                if graph_trades_and_save_to_folder:
                    if prev_val > AccountBalance:
                        trade_data[f'Trade_{tradeNO - 1}']['label'] = 1
                    else:
                        trade_data[f'Trade_{tradeNO - 1}']['label'] = 0
                print(f"\nCurrent Position {symbol[Trading_index]}:", CurrentPos)
                print("Time:", Date_1min[Trading_index][i])
                # print("Time Max",DateStream[max_pos])
                # print("Time Min", DateStream[min_pos])
                try:
                    print("Account Balance: ", AccountBalance, "Order Size:", positionSize, "PV:",
                          (Profit * 100) / (tradeNO * CloseStream[Trading_index][-1]), "Stoploss:", stoplossval,
                          "TakeProfit:",
                          takeprofitval)
                except Exception as e:
                    pass
                Trading_index = -99

                print("Position Closed")

            elif use_trailing_stop and CurrentPos == 0:
                # trailing_stop_value
                if Open_1min[Trading_index][i] < positionPrice - takeprofitval and trailing_stop_value == -99:
                    ##takeprofit reached so set trailing_stop_value
                    trailing_stop_value = (positionPrice - takeprofitval) * (
                                1 + trailing_stop_distance)  ##price at which we will sell if moved up to
                    print("Trailing Stop: ", trailing_stop_value)
                elif Open_1min[Trading_index][i] > trailing_stop_value and trailing_stop_value != -99:
                    prev_val = copy(AccountBalance)
                    ##trailing stop has been hit
                    Profit += positionPrice - trailing_stop_value
                    month_return += positionSize * (positionPrice - trailing_stop_value)
                    AccountBalance += positionSize * (positionPrice - trailing_stop_value)
                    print("Trailing Stop Profit", positionSize * (positionPrice - trailing_stop_value))
                    correct += 1
                    Profit -= trailing_stop_value * fee
                    fees_paid += positionSize * Open_1min[Trading_index][i] * fee
                    AccountBalance -= positionSize * trailing_stop_value * fee
                    month_return -= positionSize * trailing_stop_value * fee
                    cashout.append({'x': i, 'y': trailing_stop_value, 'type': "win", 'position': 'short',
                                    'Profit': positionSize * (positionPrice - trailing_stop_value)})
                    CurrentPos = -99
                    profitgraph.append(AccountBalance)
                    trailing_stop_value = -99
                    winning_trades.append(Trade_start)
                    Trade_Stage = 0
                    if graph_trades_and_save_to_folder:
                        if prev_val>AccountBalance:
                            trade_data[f'Trade_{tradeNO-1}']['label'] = 1
                        else:
                            trade_data[f'Trade_{tradeNO - 1}']['label'] = 0
                elif Open_1min[Trading_index][i] * (
                        1 + trailing_stop_distance) < trailing_stop_value and trailing_stop_value != -99:
                    trailing_stop_value = Open_1min[Trading_index][i] * (
                                1 + trailing_stop_distance)  ##move trailing stop as a new low was reached
                    print("Trailing Stop: ", trailing_stop_value)
            elif use_trailing_stop and CurrentPos == 1:
                # trailing_stop_value
                if Open_1min[Trading_index][i] > positionPrice + takeprofitval and trailing_stop_value == -99:
                    ##takeprofit reached so set trailing_stop_value
                    trailing_stop_value = (positionPrice + takeprofitval) * (
                                1 - trailing_stop_distance)  ##price at which we will sell if moved up to
                    print("Trailing Stop: ", trailing_stop_value)

                elif Open_1min[Trading_index][i] < trailing_stop_value and trailing_stop_value != -99:
                    ##trailing stop has been hit
                    prev_val = copy(AccountBalance)
                    Profit += trailing_stop_value - positionPrice
                    month_return += positionSize * (trailing_stop_value - positionPrice)
                    AccountBalance += positionSize * (trailing_stop_value - positionPrice)
                    print("Trailing Stop Profit", positionSize * (trailing_stop_value - positionPrice))
                    correct += 1
                    Profit -= trailing_stop_value * fee
                    fees_paid += positionSize * Open_1min[Trading_index][i] * fee
                    AccountBalance -= positionSize * trailing_stop_value * fee
                    month_return -= positionSize * trailing_stop_value * fee
                    cashout.append({'x': i, 'y': trailing_stop_value, 'type': "win", 'position': 'short',
                                    'Profit': positionSize * (trailing_stop_value - positionPrice)})
                    CurrentPos = -99
                    profitgraph.append(AccountBalance)
                    trailing_stop_value = -99
                    winning_trades.append(Trade_start)
                    Trade_Stage = 0
                    if graph_trades_and_save_to_folder:
                        if prev_val>AccountBalance:
                            trade_data[f'Trade_{tradeNO-1}']['label'] = 1
                        else:
                            trade_data[f'Trade_{tradeNO - 1}']['label'] = 0
                elif Open_1min[Trading_index][i] * (
                        1 - trailing_stop_distance) > trailing_stop_value and trailing_stop_value != -99:
                    trailing_stop_value = Open_1min[Trading_index][i] * (
                                1 - trailing_stop_distance)  ##move trailing stop as a new high was reached
                    print("Trailing Stop: ", trailing_stop_value)


        elif Trade_Stage==0:
            for j in range(len(symbol)):
                if i%TIME_INTERVAL==0 and (i!=0 or TIME_INTERVAL==1):
                    break_even_flag=0

                    ##Public Strats :) :
                    if CurrentPos==-99:
                        ## These strats require a call to SetSLTP as they return a Type param:
                        #prediction,Type = TS.StochRSIMACD(prediction, CloseStream[j],HighStream[j],LowStream[j])  ###########################################
                        #prediction, signal1, signal2, Type = TS.tripleEMAStochasticRSIATR(CloseStream[j],signal1,signal2,prediction)
                        prediction,Type=TS.tripleEMA(CloseStream[j],OpenStream[j],prediction)
                        
                        #prediction, Type = TS.breakout(prediction,CloseStream[j],VolumeStream[j])
                        #prediction,Type = TS.stochBB(prediction,CloseStream[j])
                        #prediction, Type = TS.goldenCross(prediction,CloseStream[j])
                        #prediction , Type = TS.candle_wick(prediction,CloseStream[j],OpenStream[j],HighStream[j],LowStream[j])
                        #prediction,Close_pos,count,stoplossval = TS.single_candle_swing_pump(prediction,CloseStream[j],HighStream[j],LowStream[j],
                        # CurrentPos,Close_pos,count,stoplossval) ##must be unhighlighted below as it returns the Close_pos var
                        stoplossval, takeprofitval = SetSLTP(stoplossval, takeprofitval, CloseStream[j],HighStream[j], LowStream[j], prediction,CurrentPos, Type)
                        #print(prediction)
                        ##These strats don't require a call to SetSLTP:
                        #prediction,stoplossval,takeprofitval = TS.fibMACD(prediction, CloseStream[j], OpenStream[j],HighStream[j],LowStream[j])
                        #prediction, stoplossval, takeprofitval, Close_pos = TS.heikin_ashi_ema2(CloseStream[j], OpenStream_H[j], HighStream_H[j], LowStream_H[j], CloseStream_H[j], prediction, stoplossval, takeprofitval, CurrentPos, Close_pos)
                        #prediction,stoplossval,takeprofitval,Close_pos = TS.heikin_ashi_ema(CloseStream[j], OpenStream_H[j], CloseStream_H[j], prediction, stoplossval,takeprofitval, CurrentPos, Close_pos)
                    else:
                        ##Must Call these every candle because they return Close_pos var
                        #prediction,Close_pos,count,stoplossval = TS.single_candle_swing_pump(prediction,CloseStream[j],HighStream[j],LowStream[j],CurrentPos,Close_pos,count,stoplossval)
                        #prediction,Highest_lowest,Close_pos = TS.trend_Ride(prediction, CloseStream[j], HighStream[j][-1], LowStream[j][-1], percent, CurrentPos, Highest_lowest) ##This strategy holds a position until the price dips/rises a certain percentage
                        #prediction,Close_pos = TS.RSI_trade(prediction,CloseStream[j],CurrentPos,Close_pos)
                        pass
                        ##########################################################################################################################################################################
                        ##########################################################################################################################################################################
                    ##Non public Strats sorry :( :
                    # prediction, stoplossval, takeprofitval, Close_pos = \
                    #    PS.heikin_ashi_ema(CloseStream[j], OpenStream_H[j], HighStream_H[j], LowStream_H[j], CloseStream_H[j], prediction, stoplossval, takeprofitval, CurrentPos, Close_pos)
                    # if Close_pos:
                    #    Close_pos = 0
                    # prediction, stoplossval[j], takeprofitval[j], Close_pos = \
                    #    PS.meta_candle_heikin_ashi(CloseStream[j],OpenStream_H[j],HighStream_H[j],LowStream_H[j],CloseStream_H[j],prediction[j],stoplossval[j],takeprofitval[j],CurrentPos[j],Close_pos)
                    # prediction,Type = Strategy.Check_for_sup_res(CloseStream[j],OpenStream[j],HighStream[j],LowStream[j]) ##not a strategy ive made public
                    #prediction, stoplossval, takeprofitval = Strategy[j].check_for_pullback(CloseStream[j], LowStream[j], HighStream[j], OpenStream[j],VolumeStream[j],prediction) ##not a strategy ive made public
                    #if prediction[j]==1:
                    #    prediction[j]=-99
                    ##########################################################################################################################################################################
                #Close_pos = Strategy[j].Trade_timer(CurrentPos, Close_pos)

            ##If the trade won't cover the fee & profit something then don't place it
            #if (prediction[j] == 1 or prediction[j] == 0) and (.00125 * Close_1min[j][-1] > takeprofitval[j]) and (not pair_Trading) and (not Hold_pos):
            #    prediction[j] = -99
            #################################################################
            #################################################################


                if CurrentPos == -99 and prediction == 0:
                    Trading_index = j
                    positionPrice = Open_1min[Trading_index][i]##next open candle #CloseStream[j][len(CloseStream[j]) - 1]
                    positionSize= (OrderSIZE*EffectiveAccountBalance)/positionPrice
                    CurrentPos = 0

                    Trade_Stage = 1
                    trades.append({'x':i,'y':positionPrice,'type': "sell",'current_price': positionPrice})
                    Profit -= Open_1min[Trading_index][i] * fee
                    fees_paid += positionSize * Open_1min[Trading_index][i] * fee
                    AccountBalance -= positionSize * Open_1min[Trading_index][i] * fee
                    month_return -= positionSize * Open_1min[Trading_index][i] * fee
                    prediction = -99

                    Trade_start = [symbol[Trading_index], Date_1min[Trading_index][i],CurrentPos]  ##we enter trade on next candle

                    print(f"\nCurrent Position {symbol[Trading_index]}:", CurrentPos)
                    print("Time:", Date_1min[Trading_index][i])
                    # print("Time Max",DateStream[max_pos])
                    # print("Time Min", DateStream[min_pos])
                    try:
                        print("Account Balance: ", AccountBalance, "Order Size:", positionSize, "PV:",
                              (Profit * 100) / (tradeNO * CloseStream[Trading_index][-1]), "Stoploss:", stoplossval,
                              "TakeProfit:",
                              takeprofitval)
                    except Exception as e:
                        pass

                    if graph_trades_and_save_to_folder:
                        trade_data[f'Trade_{tradeNO}'] = {}
                        trade_data[f'Trade_{tradeNO}']['direction'] = CurrentPos
                        trade_data[f'Trade_{tradeNO}']['stop_loss'] = positionPrice+stoplossval
                        trade_data[f'Trade_{tradeNO}']['take_profit'] = positionPrice-takeprofitval
                        trade_data[f'Trade_{tradeNO}']['entry_price'] = positionPrice
                        trade_data[f'Trade_{tradeNO}']['entry_index'] = period_leading_to_signal
                        trade_data[f'Trade_{tradeNO}']['symbol'] = symbol[Trading_index]
                        trade_data[f'Trade_{tradeNO}']['date'] = Date_1min[Trading_index][i]
                        trade_data[f'Trade_{tradeNO}']['indices'] = indices
                        if use_heikin_ashi:
                            trade_data[f'Trade_{tradeNO}']['close'] = Close_H[Trading_index][i-period_leading_to_signal:i+period_after_signal]
                            trade_data[f'Trade_{tradeNO}']['open'] = Open_H[Trading_index][i - period_leading_to_signal:i + period_after_signal]
                            trade_data[f'Trade_{tradeNO}']['low'] = Low_H[Trading_index][i - period_leading_to_signal:i + period_after_signal]
                            trade_data[f'Trade_{tradeNO}']['high'] = High_H[Trading_index][i - period_leading_to_signal:i + period_after_signal]
                        else:
                            trade_data[f'Trade_{tradeNO}']['close'] = Close[Trading_index][i - period_leading_to_signal:i + period_after_signal]
                            trade_data[f'Trade_{tradeNO}']['open'] = Open[Trading_index][i - period_leading_to_signal:i + period_after_signal]
                            trade_data[f'Trade_{tradeNO}']['low'] = Low[Trading_index][i - period_leading_to_signal:i + period_after_signal]
                            trade_data[f'Trade_{tradeNO}']['high'] = High[Trading_index][i - period_leading_to_signal:i + period_after_signal]
                        trade_data[f'Trade_{tradeNO}']['volume'] = Volume[Trading_index][i - period_leading_to_signal:i + period_after_signal]

                        trade_data[f'Trade_{tradeNO}'] = trade_graph_info.create_dict(trade_data[f'Trade_{tradeNO}'],
                                    Trading_index,pd.Series(Volume[Trading_index][i - 300:i + period_after_signal]), pd.Series(High[Trading_index][i - 300:i + period_after_signal]),
                                    pd.Series(Low[Trading_index][i - 300:i + period_after_signal]), pd.Series(Close[Trading_index][i - 300:i + period_after_signal]),
                                    period_leading_to_signal, period_after_signal, use_emas,use_smas,sma_lengths, ema_lengths, use_stochastic, use_stochastic_rsi,
                                    use_ease_of_movement,use_rsi, use_macd, use_atr, use_bollinger_bands, use_awesome, use_adx, use_cci,use_obv, use_fi, use_mfi, use_tsi,use_acc_dist,use_vwap)

                    tradeNO += 1

                    break


                elif CurrentPos == -99 and prediction == 1:
                    Trading_index = j
                    positionPrice = Open_1min[Trading_index][i] ##next open candle
                    positionSize = (OrderSIZE * EffectiveAccountBalance) / positionPrice
                    CurrentPos = 1

                    Trade_Stage = 1
                    trades.append({'x':i,'y':positionPrice, 'type': "buy",'current_price': positionPrice})
                    Profit -= Open_1min[Trading_index][i] * fee
                    fees_paid += positionSize * Open_1min[Trading_index][i] * fee
                    AccountBalance -= positionSize * Open_1min[Trading_index][i] * fee
                    month_return -= positionSize * Open_1min[Trading_index][i] * fee
                    prediction = -99

                    Trade_start = [symbol[Trading_index], Date_1min[Trading_index][i],CurrentPos]  ##we enter trade on next candle

                    print(f"\nCurrent Position {symbol[Trading_index]}:", CurrentPos)
                    print("Time:", Date_1min[Trading_index][i])
                    # print("Time Max",DateStream[max_pos])
                    # print("Time Min", DateStream[min_pos])
                    try:
                        print("Account Balance: ", AccountBalance, "Order Size:", positionSize, "PV:",
                              (Profit * 100) / (tradeNO * CloseStream[Trading_index][-1]), "Stoploss:", stoplossval,
                              "TakeProfit:",
                              takeprofitval)
                    except Exception as e:
                        pass

                    if graph_trades_and_save_to_folder:
                        trade_data[f'Trade_{tradeNO}'] = {}
                        trade_data[f'Trade_{tradeNO}']['direction'] = CurrentPos
                        trade_data[f'Trade_{tradeNO}']['stop_loss'] = positionPrice-stoplossval
                        trade_data[f'Trade_{tradeNO}']['take_profit'] = positionPrice+takeprofitval
                        trade_data[f'Trade_{tradeNO}']['entry_price'] = positionPrice
                        trade_data[f'Trade_{tradeNO}']['entry_index'] = period_leading_to_signal
                        trade_data[f'Trade_{tradeNO}']['symbol'] = symbol[Trading_index]
                        trade_data[f'Trade_{tradeNO}']['date'] = Date_1min[Trading_index][i]
                        trade_data[f'Trade_{tradeNO}']['indices'] = indices
                        if use_heikin_ashi:
                            trade_data[f'Trade_{tradeNO}']['close'] = Close_H[Trading_index][i - period_leading_to_signal:i + period_after_signal]
                            trade_data[f'Trade_{tradeNO}']['open'] = Open_H[Trading_index][i - period_leading_to_signal:i + period_after_signal]
                            trade_data[f'Trade_{tradeNO}']['low'] = Low_H[Trading_index][i - period_leading_to_signal:i + period_after_signal]
                            trade_data[f'Trade_{tradeNO}']['high'] = High_H[Trading_index][i - period_leading_to_signal:i + period_after_signal]
                        else:
                            trade_data[f'Trade_{tradeNO}']['close'] = Close[Trading_index][i - period_leading_to_signal:i + period_after_signal]
                            trade_data[f'Trade_{tradeNO}']['open'] = Open[Trading_index][i - period_leading_to_signal:i + period_after_signal]
                            trade_data[f'Trade_{tradeNO}']['low'] = Low[Trading_index][i - period_leading_to_signal:i + period_after_signal]
                            trade_data[f'Trade_{tradeNO}']['high'] = High[Trading_index][i - period_leading_to_signal:i + period_after_signal]
                        trade_data[f'Trade_{tradeNO}']['volume'] = Volume[Trading_index][i - period_leading_to_signal:i + period_after_signal]

                        trade_data[f'Trade_{tradeNO}'] = trade_graph_info.create_dict(trade_data[f'Trade_{tradeNO}'],Trading_index,
                            pd.Series(Volume[Trading_index][i - 300:i + period_after_signal]), pd.Series(High[Trading_index][i - 300:i + period_after_signal]),
                            pd.Series(Low[Trading_index][i - 300:i + period_after_signal]),pd.Series(Close[Trading_index][i - 300:i + period_after_signal]),
                            period_leading_to_signal,period_after_signal, use_emas,use_smas, sma_lengths,ema_lengths, use_stochastic,use_stochastic_rsi,
                            use_ease_of_movement, use_rsi,use_macd, use_atr,use_bollinger_bands, use_awesome,use_adx, use_cci, use_obv, use_fi,use_mfi, use_tsi,use_acc_dist,use_vwap)

                    tradeNO += 1
                    break

        if i%1440==0 and i!=0:
            Daily_return.append(AccountBalance)#(day_return/day_start_equity)
            #day_return=0
            #day_start_equity=AccountBalance
        elif i==len(High_1min[0])-1:
            Daily_return.append(AccountBalance)#(day_return/day_start_equity)
        if i%43800==0 and i!=0 and ((time_period == 1 and time_period_units == 'year') or (time_period == 12 and time_period_units == 'month') or (time_period==52 and time_period_units == 'week')):
            monthly_return.append(month_return)
            month_return=0
        elif i==len(High_1min[0])-1 and ((time_period == 1 and time_period_units == 'year') or (time_period == 12 and time_period_units == 'month') or (time_period==52 and time_period_units == 'week')):
            monthly_return.append(month_return)
            month_return = 0

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



print("\nSettings:")
print('leverage:',leverage)
print('order_Size:',OrderSIZE)
print('fee:',fee)
print("\nSymbol(s):", symbol, "fee:", fee)
print(f"{original_time_interval} OHLC Candle Sticks from a period of {time_period} {time_period_units} ago")
print("Account Balance:", AccountBalance)
print("% Gain on Account:", ((AccountBalance - originalBalance) * 100) / originalBalance)
print("Total Returns:",AccountBalance-start_equity,"\n")

if len(monthly_return)>0:
    print("Monthly Returns")
    for i in range(len(monthly_return)):
        print(f"Month {i+1}: {monthly_return[i]}")

print(f"Annualized Volatility: {round(vol,4)}%")
print(f"CAGR: {round(CAGR,4)}%")
print("Sharpe Ratio:",round(Sharpe_ratio,4))
print("Sortino Ratio:",round(sortino_ratio,4))
print("Calmar Ratio:",round(calmar_ratio,4))
print(f"Max Drawdown: {round(max_dd,4)}%")

longwins=0
longlosses=0
shortwins=0
shortlosses=0
longCash = 0
shortCash = 0
for trade in cashout:
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

print("Trades Made: ",len(trades))
print("Successful Trades:",correct)
print("Accuracy: ",(correct/len(trades))*100)
print("Win/Loss Ratio: ",{correct/(tradeNO-correct)})
print("Profit before fees: ",shortCash+longCash)
print("Trading fees paid: ",fees_paid)
try:
    print("# Shorts:", shortwins + shortlosses)
    print("Short W/L ratio:",shortwins/shortlosses)
    print("Profit from Shorts:",shortCash)
except Exception as E:
    pass
try:
    print("# Longs:",longwins+longlosses)
    print("Long W/L ratio:", longwins / longlosses)
    print("Profit from Longs:", longCash)
except Exception as E:
    pass
print("Winning Trades: ",winning_trades,"\n","Losing Trades: ",losing_trades)

if graph_trades_and_save_to_folder:
    try:
        os.makedirs(f'{DD.path}{trade_graph_folder}\\winning trades')
        os.makedirs(f'{DD.path}{trade_graph_folder}\\losing trades')
    except:
        pass
    create_trade_graphs.plot(trade_data,trade_graph_folder)
          
plt.plot(profitgraph)
plt.title(f"{symbol}: {original_time_interval} from a period of {time_period} {time_period_units} ago")
plt.ylabel('Dollars')
plt.xlabel('# Trades')
plt.show()


