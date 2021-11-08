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
import matplotlib
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
import personal_strats as PS
import download_Data as DD
import API_keys
#data.reset_index(level=0, inplace=True)
matplotlib.use("Agg")

run_on_all_coins_separately = 0 ##flag to run strategy on all coins with seperate account balances or on all coins with one single account
seperate_graphs_for_each_coin = 1 ##If ON we get a graph for each individual coin that is profitable, if off we get a single graph with all the coins that are profitable
if seperate_graphs_for_each_coin:
    run_on_all_coins_separately=1
only_print_profitable_coins = 0 ##flag to decide whether we want to print coins that ended up losing money with our strategy
index = 0 ## used with flag above
test_set = 0  ##If OFF we are only paper trading on in-sample data, if ON the we are paper trading on out of sample data to determine the validity of our strategies results
test_set_length = "1 month ago UTC"  ## valid strings 'x days/weeks/months/years ago UTC'
time_period = 3  ##time_period in same units as test_set_length above
TIME_INTERVAL = 240  ##Candlestick interval in minutes, valid options:1,   3,   5,  15,   30,  60, 120,240,360,480,720, 1440,4320, 10080, 40320
load_data = 1
Strategy_name = 'Test'
STOP=1 ##multiplier for ATR to set stoploss if function calls SetSLTP with Type == 9
TAKE=1.5 ##multiplier for ATR to set takeprofit if function calls SetSLTP with Type == 9
Starting_Account_Size = 1000
OrderSIZE = .02 ##percent in deciaml of Effective_Account_Balance to use per trade where Effective_Account_Balance = Account_Balance*leverage
leverage = 10  ##leverage being used

client = Client(api_key=API_keys.api_key,api_secret=API_keys.api_secret) ##Binance keys needed to get historical data/ Trade on an account

symbol = []
y=client.get_all_coins_info()
for x in y:
    symbol.append(x['coin'] + 'USDT')
High_1min = []
Low_1min = []
Close_1min = []
Open_1min = []
Date_1min = []
Open=[]
High=[]
Low=[]
Close=[]
Volume=[]
Date=[]
signal1=-99
signal2=-99

period_string, time_CAGR = Helper.get_period_String(test_set_length, time_period)
if load_data:
    print("Loading Price Data")
    i=0
    while i<len(symbol):
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
            i+=1
        except:
            try:
                print(f"Data doesnt exist in path: {path}, Downloading Data to specified path now...")
                DD.get_data(TIME_INTERVAL,symbol[i],f"{time_period} {period_string} ago UTC")
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

i=0
while i<len(Close):
    if len(Close[i])<(time_CAGR*365*24*60/TIME_INTERVAL)*.9: ##if the coin is too new to have the historical data requested
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
        i-=1
    i+=1


Date_1min, High_1min, Low_1min, Close_1min, Open_1min, Date, Open, Close, High, Low, Volume = Helper.align_Datasets(
            Date_1min, High_1min, Low_1min, Close_1min, Open_1min, Date, Open, Close, High, Low, Volume, symbol)

trades = deque(maxlen=100000)  ##keep track of shorts/Longs for graphing
cashout = deque(maxlen=100000)  ##keep track of Winning trades/ Losing trades
signals = deque(maxlen=100000)  ##when a siganl occured , NOT IN USE

OpenStream = []
HighStream = []
LowStream = []
CloseStream = []
VolumeStream = []
DateStream = []
Profit = 0  ##Keep track of profit by flipping a single coin
CurrentPos = -99  ##0 for short , 1 for Long
positionPrice = 0  ##Positions entry Price
correct = 0  ##winning trades
Highestprice = 0
profitgraph = []  # for graphing the profit change over time
pp = pprint.PrettyPrinter()
Sleep = 0

# OrderSize = 100
tradeNO = 0  ##number of trades
######### variables used for trading Strats

Type = []
stoplossval = []
takeprofitval = []
CurrentPos = []
positionSize = []
positionPrice = []
PrevPos = []
prediction = []


AccountBalance = []




count = 0
Hold_pos = 0  ##no TP/SL, for strategies that buy and hold turn off otherwise
percent = .01  ##percentage to hold out for

waitflag = 0  ##wait until next candlestick before checking if stoploss/ takeprofit was hit
fee = .00036
Daily_return = []
Trade_count = []
correct = []
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
    profitgraph.append([Starting_Account_Size])
    AccountBalance.append(Starting_Account_Size)
    Daily_return.append([])
    Trade_count.append(0)
    correct.append(0)
print("Symbols:", symbol, "Start Balance:", AccountBalance, "fee:", fee)
break_even = 0  ##whether or not to move the stoploss into profit based of settings below
break_even_flag = 0  ##flag don't change
break_Even_Stage = [.7,1.75]  ##if we reach this point in of profit target move stoploss to corresponding point break_even_Amount
break_even_Amount = [.1, .4]  ##where to move the stop to
originalBalance = AccountBalance[0]
##variables for CAGR calculation
start_equity = AccountBalance

##variables for sharpe ratio
day_start_equity = AccountBalance
month_return = 0
monthly_return = []
print(f"{TIME_INTERVAL} min OHLC Candle Sticks from a period of {time_period} {period_string}")
Strategy = 0
for i in range(len(High_1min[0]) - 1):
    if i % TIME_INTERVAL == 0 and i != 0:
        for j in range(len(High_1min)):
            DateStream[j] = flow.dataStream(DateStream[j], Date[j][int(i / TIME_INTERVAL) - 1], 1, 300)
            OpenStream[j] = flow.dataStream(OpenStream[j], float(Open[j][int(i / TIME_INTERVAL) - 1]), 1, 300)
            CloseStream[j] = flow.dataStream(CloseStream[j], float(Close[j][int(i / TIME_INTERVAL) - 1]), 1, 300)
            HighStream[j] = flow.dataStream(HighStream[j], float(High[j][int(i / TIME_INTERVAL) - 1]), 1, 300)
            LowStream[j] = flow.dataStream(LowStream[j], float(Low[j][int(i / TIME_INTERVAL) - 1]), 1, 300)
            VolumeStream[j] = flow.dataStream(VolumeStream[j], float(Volume[j][int(i / TIME_INTERVAL) - 1]), 1, 300)
    # print(len(OpenStream))
    if len(OpenStream[0]) >= 299:
        if len(OpenStream[0]) == 299:
            pass
            # Strategy = TS.sup_res(CloseStream[0])
            #Strategy = PS.fractal2(x)
        for j in range(len(prediction)):
            if run_on_all_coins_separately:
                    index = j
            else:
                    index = 0
            prev_Account_Bal = copy(AccountBalance[index])
            EffectiveAccountBalance = AccountBalance[index] * leverage
            if (CurrentPos[j] == -99 or Hold_pos):
                if i % TIME_INTERVAL == 0 and (i != 0 or TIME_INTERVAL == 1):
                    break_even_flag = 0
                    # prediction[j],signal1,signal2,Type[j] =TS.StochRSI_RSIMACD(prediction[j],CloseStream[j],signal1,signal2) ###########################################
                    #prediction[j],Type[j] = TS.StochRSIMACD(prediction[j], CloseStream[j],HighStream[j],LowStream[j])  ###########################################
                    #prediction[j], signal1, signal2, Type[j] = TS.tripleEMAStochasticRSIATR(CloseStream[j],signal1,signal2,prediction[j])
                    # prediction[j], signal1, Type[j],loc1,loc1_1,loc2,loc2_2,peaks,RSI = TS.RSIStochEMA(prediction[j],CloseStream[j],HighStream[j],LowStream[j],signal1,CurrentPos[j])
                    #prediction[j],Type[j]=TS.tripleEMA(CloseStream[j],OpenStream[j],prediction[j])
                    # prediction[j], Type[j] = TS.breakout(prediction[j],CloseStream[j],VolumeStream[j],symbol[j])
                    # if prediction[j]==1:
                    #    prediction[j]=-99
                    prediction[j], Type[j] = TS.fakeout(prediction[j], CloseStream[j], VolumeStream[j], symbol[j])
                    '''if loc1!=-99:
                        print("Bearish Divergence found:",DateStream[loc1],"to",DateStream[loc1_1])
                    if loc2!=-99:
                        print("Bullish Divergence found:",DateStream[loc2],"to",DateStream[loc2_2])'''
                    # for x in peaks:
                    #   print("Peak at ",DateStream[x],"RSI:",RSI[x])
                    # prediction[j],Type[j] = TS.Fractal2(CloseStream[j],LowStream[j],HighStream[j],signal1,prediction[j]) ###############################################
                    # prediction[j],Type[j] = TS.stochBB(prediction[j],CloseStream[j])
                    # prediction[j], Type[j] = TS.goldenCross(prediction[j],CloseStream[j])
                    # prediction[j] , Type[j] = TS.candle_wick(prediction,CloseStream[j],OpenStream[j],HighStream[j],LowStream[j])
                    # prediction[j],Close_pos,count,stoplossval[j] = TS.single_candle_swing_pump(prediction[j],CloseStream[j],HighStream[j],LowStream[j],CurrentPos[j],Close_pos,count,stoplossval[j])
                    # Strategy.Check_for_sup_res(CloseStream[j])
                    # prediction[j],Type[j] = Strategy.make_decision(CloseStream[j],OpenStream[j],HighStream[j],LowStream[j])
                    '''prediction[j], stoplossval[j], takeprofitval[j] = Strategy.check_for_pullback(CloseStream[j],
                                                                                                  LowStream[j],
                                                                                                  HighStream[j],
                                                                                                  OpenStream[j],
                                                                                                  VolumeStream[j],
                                                                                                  prediction[j])'''
                    stoplossval[j], takeprofitval[j] = SetSLTP(stoplossval[j], takeprofitval[j], CloseStream[j],HighStream[j], LowStream[j], prediction[j],CurrentPos[j], Type[j],SL=STOP,TP=TAKE)
                    # prediction[j],stoplossval[j],takeprofitval[j],max_pos,min_pos = TS.fibMACD(prediction[j], CloseStream[j], OpenStream[j],HighStream[j],LowStream[j])
                    # if prediction[j]==0 or prediction[j]==1 and CurrentPos[j]==-99:
                    #    print("\nMax:",DateStream[j][max_pos])
                    #    print("Min:",DateStream[j][min_pos])

                    # prediction[j],stoplossval[j],takeprofitval[j] = TS.Fractal(CloseStream[j], LowStream[j], HighStream[j],OpenStream[j],prediction[j])

                    # takeprofitval[j], stoplossval[j], prediction[j], signal1= TS.SARMACD200EMA(stoplossval[j], takeprofitval[j],CloseStream[j],HighStream[j],LowStream[j],prediction[j],CurrentPos[j],signal1)

                    # takeprofitval[j], stoplossval[j], prediction[j], signal1= TS.TripleEMA(stoplossval[j], takeprofitval[j],CloseStream[j],HighStream[j],LowStream[j],prediction[j],CurrentPos[j],signal1)

                    # prediction[j],Highest_lowest,Close_pos = TS.trend_Ride(prediction[j], CloseStream[j], HighStream[j][-1], LowStream[j][-1], percent, CurrentPos[j], Highest_lowest) ##This strategy holds a position until the price dips/rises a certain percentage

                    # prediction[j],Close_pos = TS.RSI_trade(prediction[j],CloseStream[j],CurrentPos[j],Close_pos)
                    # if CurrentPos[j] == -99:
                    #    stoplossval[j], takeprofitval[j] = SetSLTP(stoplossval[j], takeprofitval[j], CloseStream[j],HighStream[j], LowStream[j], prediction[j],CurrentPos[j], 9,SL=STOP,TP=TAKE)



            ##If the trade won't cover the fee & profit something then don't place it
            if (prediction[j] == 1 or prediction[j] == 0) and (.00125 * Close_1min[j][-1] > takeprofitval[j]) and (not Hold_pos):
                prediction[j] = -99
            #################################################################
            #################################################################

            if CurrentPos[j] == -99 and prediction[j] == 0:
                positionPrice[j] = Open_1min[j][i + 1]  ##next open candle #CloseStream[j][len(CloseStream[j]) - 1]
                positionSize[j] = (OrderSIZE * EffectiveAccountBalance) / positionPrice[j]
                CurrentPos[j] = 0
                tradeNO += 1
                Trade_count[j]+=1
                # Highestprice = positionPrice
                # stoplossval = positionPrice * trailing_stoploss
                trades.append({'x': i, 'y': positionPrice[j], 'type': "sell", 'current_price': positionPrice[j]})
                Profit -= Open_1min[j][i + 1] * fee
                AccountBalance[index] -= positionSize[j] * Open_1min[j][i + 1] * fee
                month_return -= positionSize[j] * Open_1min[j][i + 1] * fee
                waitflag = 1
                prediction[j] = -99
            elif CurrentPos[j] == -99 and prediction[j] == 1:
                positionPrice[j] = Open_1min[j][i + 1]  ##next open candle
                positionSize[j] = (OrderSIZE * EffectiveAccountBalance) / positionPrice[j]
                CurrentPos[j] = 1
                tradeNO += 1
                Trade_count[j] += 1
                # Highestprice = positionPrice
                # stoplossval = positionPrice * trailing_stoploss
                trades.append({'x': i, 'y': positionPrice[j], 'type': "buy", 'current_price': positionPrice[j]})
                Profit -= Open_1min[j][i + 1] * fee
                AccountBalance[index] -= positionSize[j] * Open_1min[j][i + 1] * fee
                month_return -= positionSize[j] * Open_1min[j][i + 1] * fee
                waitflag = 1
                prediction[j] = -99
            ############### break-even:
            # if CurrentPos==0 and break_even and positionPrice-CloseStream[-1] > .0025*positionPrice:

            if positionPrice[j] - High_1min[j][i] < -stoplossval[j] and CurrentPos[j] == 0 and (
            not waitflag) and not Hold_pos:
                Profit += -stoplossval[
                    j]  # positionPrice-CloseStream[len(CloseStream) - 1]  ##This will be positive if the price went down
                month_return -= positionSize[j] * stoplossval[j]
                AccountBalance[index] += positionSize[j] * -stoplossval[j]  # (positionPrice-CloseStream[len(CloseStream) - 1])
                positionPrice[j] = Open_1min[j][i + 1]
                Profit -= Open_1min[j][i + 1] * fee
                AccountBalance[index] -= positionSize[j] * Open_1min[j][i + 1] * fee
                month_return -= positionSize[j] * Open_1min[j][i + 1] * fee
                cashout.append({'x': i, 'y': Open_1min[j][i + 1], 'type': "loss", 'position': 'short',
                                'Profit': -stoplossval[j] * positionSize[j]})
                # CurrentPos = -99
                CurrentPos[j] = -99
                stopflag = -99

            elif Low_1min[j][i] - positionPrice[j] < -stoplossval[j] and CurrentPos[j] == 1 and (
            not waitflag) and not Hold_pos:
                Profit += -stoplossval[
                    j]  # CloseStream[len(CloseStream) - 1] - positionPrice ##This will be positive if the price went up
                month_return -= positionSize[j] * stoplossval[j]
                AccountBalance[index] += positionSize[j] * -stoplossval[
                    j]  # (CloseStream[len(CloseStream) - 1] - positionPrice)
                positionPrice[j] = Open_1min[j][i + 1]
                Profit -= Open_1min[j][i + 1] * fee
                AccountBalance[index] -= positionSize[j] * Open_1min[j][i + 1] * fee
                month_return -= positionSize[j] * Open_1min[j][i + 1] * fee
                cashout.append({'x': i, 'y': Open_1min[j][i + 1], 'type': "loss", 'position': 'long',
                                'Profit': -stoplossval[j] * positionSize[j]})
                # CurrentPos = -99
                CurrentPos[j] = -99
                stopflag = -99

            elif positionPrice[j] - Low_1min[j][i] > takeprofitval[j] and CurrentPos[j] == 0 and (
            not waitflag) and not Hold_pos:
                Profit += takeprofitval[j]  # positionPrice - CloseStream[-1]
                month_return += positionSize[j] * takeprofitval[j]
                AccountBalance[index] += positionSize[j] * takeprofitval[
                    j]  # (positionPrice - CloseStream[len(CloseStream) - 1])
                correct[index] += 1
                positionPrice[j] = Open_1min[j][i + 1]
                Profit -= Open_1min[j][i + 1] * fee
                AccountBalance[index] -= positionSize[j] * Open_1min[j][i + 1] * fee
                month_return -= positionSize[j] * Open_1min[j][i + 1] * fee
                cashout.append({'x': i, 'y': Open_1min[j][i + 1], 'type': "win", 'position': 'short',
                                'Profit': takeprofitval[j] * positionSize[j]})
                CurrentPos[j] = -99
                stopflag = -99

            elif High_1min[j][i] - positionPrice[j] > takeprofitval[j] and CurrentPos[j] == 1 and (
            not waitflag) and not Hold_pos:
                Profit += takeprofitval[j]  # CloseStream[-1] - positionPrice
                month_return += positionSize[j] * takeprofitval[j]
                AccountBalance[index] += positionSize[j] * takeprofitval[
                    j]  # (CloseStream[len(CloseStream) - 1] - positionPrice)
                correct[index] += 1
                positionPrice[j] = Open_1min[j][i + 1]
                Profit -= Open_1min[j][i + 1] * fee
                AccountBalance[index] -= positionSize[j] * Open_1min[j][i + 1] * fee
                month_return -= positionSize[j] * Open_1min[j][i + 1] * fee
                cashout.append({'x': i, 'y': Open_1min[j][i + 1], 'type': "win", 'position': 'long',
                                'Profit': takeprofitval[j] * positionSize[j]})
                CurrentPos[j] = -99
                stopflag = -99
            waitflag = 0

            if CurrentPos[j] != PrevPos[j]:
                print(f"\nCurrent Position {symbol[j]}:", CurrentPos[j])
                print("Time:", Date_1min[j][i])
                # print("Time Max",DateStream[max_pos])
                # print("Time Min", DateStream[min_pos])
                try:
                    print("Account Balance: ", AccountBalance[index], "Order Size:", positionSize[j], "PV:",
                          (Profit * 100) / (tradeNO * CloseStream[j][-1]), "Stoploss:", stoplossval[j], "TakeProfit:",
                          takeprofitval[j])
                except Exception as e:
                    pass
                if i % 1440 == 0 and i != 0 and j == 0 and not run_on_all_coins_separately:
                        Daily_return[0].append(AccountBalance[0])  # (day_return/day_start_equity)
                        # day_return=0
                        # day_start_equity=AccountBalance
                elif i == len(High_1min[0]) - 1 and j == 0 and not run_on_all_coins_separately:
                        Daily_return[0].append(AccountBalance[0])  # (day_return/day_start_equity)
                elif i % 1440 == 0 and i != 0 and run_on_all_coins_separately:
                        Daily_return[j].append(AccountBalance[j])  # (day_return/day_start_equity)
                        # day_return=0
                        # day_start_equity=AccountBalance
                elif i == len(High_1min[0]) - 1 and run_on_all_coins_separately:
                        Daily_return[j].append(AccountBalance[j])  # (day_return/day_start_equity)
                if i % 43800 == 0 and i != 0 and ((time_period == 1 and test_set_length[2] == 'y') or (
                        time_period == 12 and test_set_length[3] == 'm') or (time_period == 52 and test_set_length[3] == 'w')) and not run_on_all_coins_separately:
                        monthly_return.append(month_return)
                        month_return = 0
                elif i == len(High_1min[0]) - 1 and ((time_period == 1 and test_set_length[2] == 'y') or (
                        time_period == 12 and test_set_length[3] == 'm') or (time_period == 52 and test_set_length[3] == 'w')) and not run_on_all_coins_separately:
                        monthly_return.append(month_return)
                        month_return = 0
                if prev_Account_Bal != AccountBalance[index] and j == 0 and not run_on_all_coins_separately:
                    profitgraph[index].append(AccountBalance[index])
                elif prev_Account_Bal != AccountBalance[index]:
                    profitgraph[index].append(AccountBalance[index])
                PrevPos = copy(CurrentPos)

lines = []
if run_on_all_coins_separately and seperate_graphs_for_each_coin:
        for j in range(len(symbol)):
            try:
                risk_free_rate = 1.41  ##10 year treasury rate
                df = pd.DataFrame({'Account_Balance': Daily_return[j]})
                df['daily_return'] = df['Account_Balance'].pct_change()
                df['cum_return'] = (1 + df['daily_return']).cumprod()
                df['cum_roll_max'] = df['cum_return'].cummax()
                df['drawdown'] = df['cum_roll_max'] - df['cum_return']
                df['drawdown %'] = df['drawdown'] / df['cum_roll_max']
                max_dd = df['drawdown %'].max() * 100

                CAGR = ((df['cum_return'].iloc[-1]) ** (1 / time_CAGR) - 1) * 100
                vol = (df['daily_return'].std() * np.sqrt(365)) * 100
                neg_vol = (df[df['daily_return'] < 0]['daily_return'].std() * np.sqrt(365)) * 100
                Sharpe_ratio = (CAGR - risk_free_rate) / vol
                sortino_ratio = (CAGR - risk_free_rate) / neg_vol
                calmar_ratio = 0
                if max_dd != 0:
                    calmar_ratio = CAGR / max_dd
                if AccountBalance[j]>originalBalance and only_print_profitable_coins:

                    lines.append(f"Symbol: {symbol[j]} \n \
                                Account Balance: {AccountBalance[j]} \n \
                                % Gain on Account: {((AccountBalance[j] - originalBalance) * 100) / originalBalance} \n \
                                Total Returns: {AccountBalance[j] - start_equity[j]} \n \
                                Annualized Volatility: {round(vol, 4)}%\n \
                                CAGR: {round(CAGR, 4)}%\n \
                                Sharpe Ratio: {round(Sharpe_ratio, 4)}\n \
                                Sortino Ratio: {round(sortino_ratio, 4)}\n \
                                Calmar Ratio: {round(calmar_ratio, 4)}\n \
                                Max Drawdown: {round(max_dd, 4)}%\n \
                                Trades Made: {Trade_count[j]}\n \
                                Successful Trades: {correct[j]} \n \
                                Accuracy: {(correct[j] / Trade_count[j]) * 100} \n\n")
                    with open(f'C:\\Users\\conor\\Desktop\\Strategy_tester\\{Strategy_name}\\{symbol[j]}.txt', 'w') as f:
                        for line in lines:
                            f.write(line)
                            f.write('\n')
                    plt.plot(profitgraph[j])
                    plt.title(f"{symbol[j]}")
                    plt.ylabel('Dollars')
                    plt.xlabel('# Trades')
                    plt.savefig(f'C:\\Users\\conor\\Desktop\\Strategy_tester\\{Strategy_name}\\{symbol[j]}.png', dpi=300,
                                bbox_inches='tight')
                    plt.close()
                elif not only_print_profitable_coins:
                    lines.append(f"Symbol: {symbol[j]} \n \
                                Account Balance: {AccountBalance[j]} \n \
                                % Gain on Account: {((AccountBalance[j] - originalBalance) * 100) / originalBalance} \n \
                                Total Returns: {AccountBalance[j] - start_equity[j]} \n \
                                Annualized Volatility: {round(vol, 4)}%\n \
                                CAGR: {round(CAGR, 4)}%\n \
                                Sharpe Ratio: {round(Sharpe_ratio, 4)}\n \
                                Sortino Ratio: {round(sortino_ratio, 4)}\n \
                                Calmar Ratio: {round(calmar_ratio, 4)}\n \
                                Max Drawdown: {round(max_dd, 4)}%\n \
                                Trades Made: {Trade_count[j]}\n \
                                Successful Trades: {correct[j]} \n \
                                Accuracy: {(correct[j] / Trade_count[j]) * 100} \n\n")
                    with open(f'C:\\Users\\conor\\Desktop\\Strategy_tester\\{Strategy_name}\\{symbol[j]}.txt', 'w') as f:
                        for line in lines:
                            f.write(line)
                            f.write('\n')
                    plt.plot(profitgraph[j])
                    plt.title(f"{symbol[j]}")
                    plt.ylabel('Dollars')
                    plt.xlabel('# Trades')
                    plt.savefig(f'C:\\Users\\conor\\Desktop\\Strategy_tester\\{Strategy_name}\\{symbol[j]}.png',
                                dpi=300, bbox_inches='tight')
                    plt.close()
            except:
                pass

elif run_on_all_coins_separately and only_print_profitable_coins:
        for j in range(len(symbol)):
            try:
                risk_free_rate = 1.41  ##10 year treasury rate
                df = pd.DataFrame({'Account_Balance': Daily_return[j]})
                df['daily_return'] = df['Account_Balance'].pct_change()
                df['cum_return'] = (1 + df['daily_return']).cumprod()
                df['cum_roll_max'] = df['cum_return'].cummax()
                df['drawdown'] = df['cum_roll_max'] - df['cum_return']
                df['drawdown %'] = df['drawdown'] / df['cum_roll_max']
                max_dd = df['drawdown %'].max() * 100

                CAGR = ((df['cum_return'].iloc[-1]) ** (1 / time_CAGR) - 1) * 100
                vol = (df['daily_return'].std() * np.sqrt(365)) * 100
                neg_vol = (df[df['daily_return'] < 0]['daily_return'].std() * np.sqrt(365)) * 100
                Sharpe_ratio = (CAGR - risk_free_rate) / vol
                sortino_ratio = (CAGR - risk_free_rate) / neg_vol
                calmar_ratio = 0
                if max_dd!=0:
                    calmar_ratio = CAGR / max_dd
                if AccountBalance[j]>originalBalance:
                    lines.append(f"Symbol: {symbol[j]} \n \
                                Account Balance: {AccountBalance[j]} \n \
                                % Gain on Account: {((AccountBalance[j] - originalBalance) * 100) / originalBalance} \n \
                                Total Returns: {AccountBalance[j] - start_equity[j]} \n \
                                Annualized Volatility: {round(vol, 4)}%\n \
                                CAGR: {round(CAGR, 4)}%\n \
                                Sharpe Ratio: {round(Sharpe_ratio, 4)}\n \
                                Sortino Ratio: {round(sortino_ratio, 4)}\n \
                                Calmar Ratio: {round(calmar_ratio, 4)}\n \
                                Max Drawdown: {round(max_dd, 4)}%\n \
                                Trades Made: {Trade_count[j]}\n \
                                Successful Trades: {correct[j]} \n \
                                Accuracy: {(correct[j] / Trade_count[j]) * 100} \n\n")
                if AccountBalance[j] > originalBalance:
                    plt.plot(profitgraph[j])
            except:
                pass
        with open(f'C:\\Users\\conor\\Desktop\\Strategy_tester\\{Strategy_name}\\All_coins_profitable.txt', 'w') as f:
            for line in lines:
                f.write(line)
                f.write('\n')
        plt.title("All_coins_profitable")
        plt.ylabel('Dollars')
        plt.xlabel('# Trades')
        plt.savefig(f'C:\\Users\\conor\\Desktop\\Strategy_tester\\{Strategy_name}\\All_coins_profitable.png',
                        dpi=300,
                        bbox_inches='tight')
        plt.close()
elif run_on_all_coins_separately and not only_print_profitable_coins:
    for j in range(len(symbol)):
        try:
            risk_free_rate = 1.41  ##10 year treasury rate
            df = pd.DataFrame({'Account_Balance': Daily_return[j]})
            df['daily_return'] = df['Account_Balance'].pct_change()
            df['cum_return'] = (1 + df['daily_return']).cumprod()
            df['cum_roll_max'] = df['cum_return'].cummax()
            df['drawdown'] = df['cum_roll_max'] - df['cum_return']
            df['drawdown %'] = df['drawdown'] / df['cum_roll_max']
            max_dd = df['drawdown %'].max() * 100

            CAGR = ((df['cum_return'].iloc[-1]) ** (1 / time_CAGR) - 1) * 100
            vol = (df['daily_return'].std() * np.sqrt(365)) * 100
            neg_vol = (df[df['daily_return'] < 0]['daily_return'].std() * np.sqrt(365)) * 100
            Sharpe_ratio = (CAGR - risk_free_rate) / vol
            sortino_ratio = (CAGR - risk_free_rate) / neg_vol
            calmar_ratio = 0
            if max_dd != 0:
                calmar_ratio = CAGR / max_dd
            lines.append(f"Symbol: {symbol[j]} \n \
                        Account Balance: {AccountBalance[j]} \n \
                        % Gain on Account: {((AccountBalance[j] - originalBalance) * 100) / originalBalance} \n \
                        Total Returns: {AccountBalance[j] - start_equity[j]} \n \
                        Annualized Volatility: {round(vol, 4)}%\n \
                        CAGR: {round(CAGR, 4)}%\n \
                        Sharpe Ratio: {round(Sharpe_ratio, 4)}\n \
                        Sortino Ratio: {round(sortino_ratio, 4)}\n \
                        Calmar Ratio: {round(calmar_ratio, 4)}\n \
                        Max Drawdown: {round(max_dd, 4)}%\n \
                        Trades Made: {Trade_count[j]}\n \
                        Successful Trades: {correct[j]} \n \
                        Accuracy: {(correct[j] / Trade_count[j]) * 100} \n\n")
            plt.plot(profitgraph[j])
        except:
            pass
    with open(f'C:\\Users\\conor\\Desktop\\Strategy_tester\\{Strategy_name}\\All_coins.txt','w') as f:
        for line in lines:
            f.write(line)
            f.write('\n')
    plt.title("All Coins")
    plt.ylabel('Dollars')
    plt.xlabel('# Trades')
    plt.savefig(f'C:\\Users\\conor\\Desktop\\Strategy_tester\\{Strategy_name}\\All_coins.png', dpi=300,
                bbox_inches='tight')
    plt.close()

else:
    risk_free_rate = 1.41  ##10 year treasury rate
    df = pd.DataFrame({'Account_Balance': Daily_return[0]})
    df['daily_return'] = df['Account_Balance'].pct_change()
    df['cum_return'] = (1 + df['daily_return']).cumprod()
    df['cum_roll_max'] = df['cum_return'].cummax()
    df['drawdown'] = df['cum_roll_max'] - df['cum_return']
    df['drawdown %'] = df['drawdown'] / df['cum_roll_max']
    max_dd = df['drawdown %'].max() * 100

    CAGR = ((df['cum_return'].iloc[-1]) ** (1 / time_CAGR) - 1) * 100
    vol = (df['daily_return'].std() * np.sqrt(365)) * 100
    neg_vol = (df[df['daily_return'] < 0]['daily_return'].std() * np.sqrt(365)) * 100
    Sharpe_ratio = (CAGR - risk_free_rate) / vol
    sortino_ratio = (CAGR - risk_free_rate) / neg_vol
    calmar_ratio = 0
    if max_dd != 0:
        calmar_ratio = CAGR / max_dd

    lines = [
            f"{symbol}: {TIME_INTERVAL}min from a period of {time_period} {period_string}",
            f"Account Balance: {AccountBalance[0]}",
            f"% Gain on Account: {((AccountBalance[0] - originalBalance) * 100) / originalBalance}",
            f"Total Returns: {AccountBalance[0] - start_equity[0]}", "\n", f"Annualized Volatility: {round(vol, 4)}%",
            f"CAGR: {round(CAGR, 4)}%", f"Sharpe Ratio: {round(Sharpe_ratio, 4)}",
            f"Sortino Ratio: {round(sortino_ratio, 4)}",
            f"Calmar Ratio: {round(calmar_ratio, 4)}", f"Max Drawdown: {round(max_dd, 4)}%",
            f"Trades Made: {len(trades)}", f"Successful Trades: {correct[0]}",
            f"Accuracy: {(correct[0] / len(trades)) * 100}"]

    plt.plot(profitgraph)

    with open(f'C:\\Users\\conor\\Desktop\\Strategy_tester\\{Strategy_name}\\All_coins.txt','w') as f:
        for line in lines:
            f.write(line)
            f.write('\n')
    plt.title("All Coins")
    plt.ylabel('Dollars')
    plt.xlabel('# Trades')
    plt.savefig(f'C:\\Users\\conor\\Desktop\\Strategy_tester\\{Strategy_name}\\All_coins.png',dpi=300, bbox_inches='tight')
    plt.close()