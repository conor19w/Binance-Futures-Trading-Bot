from collections import deque
import pprint
from joblib import load
from binance.client import Client
import matplotlib.pyplot as plt
from binance.exceptions import BinanceAPIException
import pandas as pd
import numpy as np
import Helper
from Config_File import api_key,api_secret
from copy import copy
import TradingStrats as TS
trades = deque(maxlen=100000) ##keep track of shorts/Longs for graphing
cashout = deque(maxlen=100000) ##keep track of Winning trades/ Losing trades
signals= deque(maxlen=100000) ##when a signal occured , NOT IN USE


symbol = ['RAYUSDT', 'NEARUSDT', 'AUDIOUSDT']
'''[, 'HNTUSDT', 'DGBUSDT', 'ZRXUSDT', 'BCHUSDT', 'HOTUSDT', 'ARUSDT', 'FLMUSDT',
          'SFPUSDT', 'BELUSDT', 'RENUSDT', 'ADAUSDT', 'STORJUSDT', 'CHRUSDT', 'WAVESUSDT', 'CHZUSDT', 'XRPUSDT',
          'SANDUSDT', 'OCEANUSDT', 'ENJUSDT', 'GRTUSDT', 'UNIUSDT', 'TLMUSDT', 'XTZUSDT', 'LUNAUSDT', 'EOSUSDT',
          'SKLUSDT', 'GTCUSDT', 'DOTUSDT', '1INCHUSDT', 'UNFIUSDT', 'FTMUSDT', 'RLCUSDT', 'ATOMUSDT', 'BLZUSDT', 'SNXUSDT',
          'SOLUSDT', 'ETCUSDT', 'BNBUSDT', 'CELRUSDT', 'OGNUSDT', 'ETHUSDT', 'NEOUSDT', 'TOMOUSDT', 'CELOUSDT', 'KLAYUSDT',
          'TRBUSDT', 'TRXUSDT', 'EGLDUSDT', 'CRVUSDT', 'BAKEUSDT', 'NUUSDT', 'SRMUSDT', 'ALICEUSDT', 'CTKUSDT', 'ARPAUSDT',
          'MATICUSDT', 'IOTXUSDT', 'DENTUSDT', 'IOSTUSDT', 'OMGUSDT', 'BANDUSDT', 'BTCUSDT', 'NKNUSDT', 'RSRUSDT', 'IOTAUSDT',
          'CVCUSDT', 'REEFUSDT', 'BTSUSDT', 'BTTUSDT', 'ONEUSDT', 'ANKRUSDT', 'SUSHIUSDT', 'ALGOUSDT', 'SCUSDT', 'ONTUSDT',
          'MANAUSDT', 'ATAUSDT', 'MKRUSDT', 'DODOUSDT', 'LITUSDT', 'ICPUSDT', 'ZECUSDT', 'ICXUSDT', 'ZENUSDT', 'DOGEUSDT',
          'ALPHAUSDT', 'SXPUSDT', 'HBARUSDT', 'RVNUSDT', 'CTSIUSDT', 'KAVAUSDT', 'C98USDT', 'THETAUSDT', 'MASKUSDT', 'AAVEUSDT',
           'AXSUSDT', 'ZILUSDT', 'XEMUSDT', 'COMPUSDT', 'RUNEUSDT', 'AVAXUSDT', 'KNCUSDT', 'LPTUSDT', 'LRCUSDT',
          'MTLUSDT', 'VETUSDT', 'DASHUSDT', 'KEEPUSDT', 'LTCUSDT', 'DYDXUSDT', 'LINAUSDT', 'XLMUSDT', 'LINKUSDT', 'QTUMUSDT',
          'KSMUSDT', 'FILUSDT', 'STMXUSDT', 'BALUSDT', 'GALAUSDT', 'BATUSDT', 'AKROUSDT', 'XMRUSDT', 'COTIUSDT']'''

client = Client(api_key,api_secret)
##################### Run on all USDT pairs or else comment out and specify a list like above ####################################
x = client.futures_ticker()  # [0]
    ##get all symbols
for y in x:
    symbol.append(y['symbol'])
symbol = [x for x in symbol if 'USDT' in x] ##filter for usdt futures
symbol = [x for x in symbol if not '_' in x] ##remove invalid symbols
#symbol = ['GALAUSDT','ENJUSDT','UNIUSDT','SFPUSDT','THETAUSDT']#,'LINKUSDT','HNTUSDT','LUNAUSDT','DOGEUSDT']
###################################################################################################################################
#######################################             SETTINGS            ###########################################################
###################################################################################################################################
OrderSIZE = .01 ## Amount of effective account balance to use per trade
AccountBalance = 1000
leverage = 10  ##leverage being used
fee = .00036
start = '01-08-21' ##start of backtest dd/mm/yy
end = '01-03-22'   ##end of backtest   dd/mm/yy
TIME_INTERVAL = '15m'   ##Candlestick interval in minutes, valid options: 1m,3m,5m,15m,30m,1h,2h,4h,6h,8h,12h,1d,3d,1w,1M I think...
use_trailing_stop = 0 ##(NOT IN USE Causing rounding error I think)  flag to use trailing stop, If on when the takeprofitval margin is reached a trailing stop will be set with the below percentage distance
trailing_stop_distance = .01 ## 1% trailing stop activated by hitting the takeprofitval for a coin
##################################################################################################################################
##################################################################################################################################

######### flags/variables: #######################
Highest_lowest = 0
Type = -99
stoplossval = -99
takeprofitval = -99
CurrentPos = -99
positionSize = -99
positionPrice = -99
PrevPos = -99
Trade_Direction = -99
Trading_index = -99 ##index of coin we are trading
Trade_Stage = 0 ##flag to say in a trade
Close_pos = 0
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
profitgraph.append(AccountBalance)
count = 0
percent = .01 ##percentage to hold out for
originalBalance = copy(AccountBalance)
trailing_stop_value = -99 ##gets set automatically depending on the trailing stop percent, if used above
EffectiveAccountBalance = -99 ##set later
#####################################################################################################################
#####################################################################################################################
trade_data = {}

time_CAGR = Helper.get_CAGR(start, end)
print("Symbols:", symbol, "Start Balance:", AccountBalance, "fee:", fee)
start_equity = AccountBalance
Date_1min, High_1min, Low_1min, Close_1min, Open_1min, Date, Open, Close, High, Low, Volume, symbol =\
    Helper.get_aligned_candles([],[],[],[],[],[],[],[],[],[],[],symbol,TIME_INTERVAL,start,end)

Open_H = []
Close_H = []
High_H = []
Low_H = []
OpenStream_H = []
CloseStream_H = []
HighStream_H = []
LowStream_H = []


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
print(f"{TIME_INTERVAL} OHLC Candle Sticks from a {start} to {end}")
original_time_interval = copy(TIME_INTERVAL)
TIME_INTERVAL = Helper.get_TIME_INTERVAL(TIME_INTERVAL) ##Convert string to an integer for the rest of the script
for i in range(len(High_1min[0])-1):
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
        #print(DateStream)
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

        if Trade_Stage == 0:
            for j in range(len(symbol)):
                if i % TIME_INTERVAL == 0 and (i != 0 or TIME_INTERVAL == 1):
                    break_even_flag = 0

                    ##Public Strats :) :
                    if CurrentPos == -99:
                        #Trade_Direction,stoplossval, takeprofitval = TS.StochRSIMACD(Trade_Direction, CloseStream[j],HighStream[j],LowStream[j])  ###########################################
                        #Trade_Direction,stoplossval, takeprofitval = TS.tripleEMAStochasticRSIATR(CloseStream[j],HighStream[j],LowStream[j],Trade_Direction)
                        #Trade_Direction,stoplossval, takeprofitval=TS.tripleEMA(CloseStream[j],HighStream[j],LowStream[j],Trade_Direction)
                        # Trade_Direction, stoplossval, takeprofitval = TS.breakout(Trade_Direction,CloseStream[j],VolumeStream[j],HighStream[j], LowStream[j])
                        # Trade_Direction,stoplossval,takeprofitval = TS.stochBB(Trade_Direction,CloseStream[j], HighStream[j], LowStream[j])
                        # Trade_Direction, stoplossval, takeprofitval = TS.goldenCross(Trade_Direction,CloseStream[j], HighStream[j], LowStream[j])
                        # Trade_Direction , stoplossval, takeprofitval = TS.candle_wick(Trade_Direction,CloseStream[j],OpenStream[j],HighStream[j],LowStream[j])
                        # Trade_Direction,stoplossval,takeprofitval = TS.fibMACD(Trade_Direction, CloseStream[j], OpenStream[j],HighStream[j],LowStream[j])
                        # Trade_Direction, stoplossval, takeprofitval, Close_pos = TS.heikin_ashi_ema2(CloseStream[j], OpenStream_H[j], HighStream_H[j], LowStream_H[j], CloseStream_H[j], Trade_Direction, stoplossval, takeprofitval, CurrentPos, Close_pos)
                        # Trade_Direction,stoplossval,takeprofitval,Close_pos = TS.heikin_ashi_ema(CloseStream[j], OpenStream_H[j], CloseStream_H[j], Trade_Direction, stoplossval,takeprofitval, CurrentPos, Close_pos)
                        ##must be unhighlighted below in the else clause also as it returns the Close_pos var
                        #Trade_Direction,stoplossval,takeprofitval = TS.single_candle_swing_pump(HighStream[j],LowStream[j],VolumeStream[j],CloseStream[j],OpenStream[j],stoplossval,takeprofitval)
                        Trade_Direction,stoplossval,takeprofitval = TS.yi_long_musk(CloseStream[j])
                        pass
                if CurrentPos == -99 and Trade_Direction == 0:
                    Trading_index = j
                    positionPrice = Open_1min[Trading_index][i]  ##next open candle #CloseStream[j][len(CloseStream[j]) - 1]
                    positionSize = (OrderSIZE * EffectiveAccountBalance) / positionPrice
                    CurrentPos = 0

                    Trade_Stage = 1 ##In a trade
                    trades.append({'x': i, 'y': positionPrice, 'type': "sell", 'current_price': positionPrice})
                    Profit -= Open_1min[Trading_index][i] * fee
                    fees_paid += positionSize * Open_1min[Trading_index][i] * fee
                    AccountBalance -= positionSize * Open_1min[Trading_index][i] * fee
                    month_return -= positionSize * Open_1min[Trading_index][i] * fee
                    Trade_Direction = -99

                    if CurrentPos:
                        Trade_start = [symbol[Trading_index], f"{Date_1min[Trading_index][i]}",
                                       'Long']  ##we enter trade on next candle
                    else:
                        Trade_start = [symbol[Trading_index], f"{Date_1min[Trading_index][i]}", 'Short']

                    print(f"\nCurrent Position {symbol[Trading_index]}:", CurrentPos)
                    print("Time:", Date_1min[Trading_index][i])
                    try:
                        print("Account Balance: ", AccountBalance, "Order Size:", positionSize,
                              "PV:",(Profit * 100) / (tradeNO * CloseStream[Trading_index][-1]), "Stoploss:", stoplossval,
                              "TakeProfit:",
                              takeprofitval)
                    except Exception as e:
                        pass

                    tradeNO += 1

                    break


                elif CurrentPos == -99 and Trade_Direction == 1:
                    Trading_index = j
                    positionPrice = Open_1min[Trading_index][i]  ##next open candle
                    positionSize = (OrderSIZE * EffectiveAccountBalance) / positionPrice
                    CurrentPos = 1

                    Trade_Stage = 1  ##In a trade
                    trades.append({'x': i, 'y': positionPrice, 'type': "buy", 'current_price': positionPrice})
                    Profit -= Open_1min[Trading_index][i] * fee
                    fees_paid += positionSize * Open_1min[Trading_index][i] * fee
                    AccountBalance -= positionSize * Open_1min[Trading_index][i] * fee
                    month_return -= positionSize * Open_1min[Trading_index][i] * fee
                    Trade_Direction = -99
                    if CurrentPos:
                        Trade_start = [symbol[Trading_index], f"{Date_1min[Trading_index][i]}",
                                       'Long']  ##we enter trade on next candle
                    else:
                        Trade_start = [symbol[Trading_index], f"{Date_1min[Trading_index][i]}", 'Short']
                    print(f"\nCurrent Position {symbol[Trading_index]}:", CurrentPos)
                    print("Time:", Date_1min[Trading_index][i])
                    try:
                        print("Account Balance: ", AccountBalance, "Order Size:", positionSize, "PV:",
                              (Profit * 100) / (tradeNO * CloseStream[Trading_index][-1]), "Stoploss:", stoplossval,
                              "TakeProfit:",
                              takeprofitval)
                    except Exception as e:
                        pass

                    tradeNO += 1
                    break

    if Trade_Stage == 1:
        if positionPrice - High_1min[Trading_index][i] < -stoplossval and CurrentPos == 0:  # and not Hold_pos:
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
            print(f"\nCurrent Position {symbol[Trading_index]}:", CurrentPos)
            print("Time:", Date_1min[Trading_index][i])
            try:
                print("Account Balance: ", AccountBalance, "Order Size:", positionSize, "PV:",
                      (Profit * 100) / (tradeNO * CloseStream[Trading_index][-1]), "Stoploss:", stoplossval,
                      "TakeProfit:",
                      takeprofitval)
            except Exception as e:
                pass
            Trading_index = -99

        elif Low_1min[Trading_index][i] - positionPrice < -stoplossval and CurrentPos == 1:  # and not Hold_pos:
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
            print(f"\nCurrent Position {symbol[Trading_index]}:", CurrentPos)
            print("Time:", Date_1min[Trading_index][i])
            try:
                print("Account Balance: ", AccountBalance, "Order Size:", positionSize, "PV:",
                      (Profit * 100) / (tradeNO * CloseStream[Trading_index][-1]), "Stoploss:", stoplossval,
                      "TakeProfit:",
                      takeprofitval)
            except Exception as e:
                pass
            Trading_index = -99

        elif positionPrice - Low_1min[Trading_index][i] > takeprofitval and CurrentPos == 0 and not use_trailing_stop:  # and not Hold_pos:
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
            print(f"\nCurrent Position {symbol[Trading_index]}:", CurrentPos)
            print("Time:", Date_1min[Trading_index][i])
            try:
                print("Account Balance: ", AccountBalance, "Order Size:", positionSize,
                      "PV:",(Profit * 100) / (tradeNO * CloseStream[Trading_index][-1]), "Stoploss:", stoplossval,
                      "TakeProfit:",
                      takeprofitval)
            except Exception as e:
                pass
            winning_trades.append(Trade_start)
            Trading_index = -99

        elif High_1min[Trading_index][i] - positionPrice > takeprofitval and CurrentPos == 1 and not use_trailing_stop:  # and not Hold_pos:
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
            print(f"\nCurrent Position {symbol[Trading_index]}:", CurrentPos)
            print("Time:", Date_1min[Trading_index][i])
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
            print(f"\nCurrent Position {symbol[Trading_index]}:", CurrentPos)
            print("Time:", Date_1min[Trading_index][i])
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
                trailing_stop_value = (positionPrice - takeprofitval) * (1 + trailing_stop_distance)  ##price at which we will sell if moved up to
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
            elif Open_1min[Trading_index][i] * (
                    1 + trailing_stop_distance) < trailing_stop_value and trailing_stop_value != -99:
                trailing_stop_value = Open_1min[Trading_index][i] * (1 + trailing_stop_distance)  ##move trailing stop as a new low was reached
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
                cashout.append({'x': i, 'y': trailing_stop_value, 'type': "win", 'position': 'long',
                                'Profit': positionSize * (trailing_stop_value - positionPrice)})
                CurrentPos = -99
                profitgraph.append(AccountBalance)
                trailing_stop_value = -99
                winning_trades.append(Trade_start)
                Trade_Stage = 0
            elif Open_1min[Trading_index][i] * (
                    1 - trailing_stop_distance) > trailing_stop_value and trailing_stop_value != -99:
                trailing_stop_value = Open_1min[Trading_index][i] * (1 - trailing_stop_distance)  ##move trailing stop as a new high was reached
                print("Trailing Stop: ", trailing_stop_value)

    if i%1440==0 and i!=0:
        Daily_return.append(AccountBalance)
    elif i==len(High_1min[0])-1:
        Daily_return.append(AccountBalance)

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
print(f"{original_time_interval} OHLC Candle Sticks from {start} to {end}")
print("Account Balance:", AccountBalance)
print("% Gain on Account:", ((AccountBalance - originalBalance) * 100) / originalBalance)
print("Total Returns:",AccountBalance-start_equity,"\n")

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
print("Accuracy: ",(correct/tradeNO)*100)
try:
    print("Win/Loss Ratio: ",{correct/(tradeNO-correct)})
except:
    pass
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
print("All Trades: ")
for x in losing_trades:
    print(x)
for x in winning_trades:
    print(x)
plt.plot(profitgraph)
plt.title(f"{symbol}: {original_time_interval} from {start} to {end}")
plt.ylabel('Dollars')
plt.xlabel('# Trades')
plt.show()