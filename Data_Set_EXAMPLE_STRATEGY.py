from datetime import datetime

from ta.momentum import stochrsi_d,stochrsi_k,stoch,stoch_signal,rsi,awesome_oscillator
from ta.trend import ema_indicator,macd_signal,macd,sma_indicator,adx,sma_indicator,cci
from ta.volatility import average_true_range,bollinger_pband,bollinger_hband,bollinger_lband,bollinger_mavg
from ta.volume import ease_of_movement,on_balance_volume,force_index,money_flow_index
from ta.momentum import tsi
import numpy as np
import pandas as pd

class Data_set:
    def __init__(self,symbol,Open,Close,High,Low,Volume,Date,OP,CP,index):
        self.symbol = symbol
        self.Open = Open
        self.Close = Close
        self.High = High
        self.Low = Low
        self.Volume = Volume
        self.Date = Date
        self.OP = OP
        self.CP = CP
        self.index = index
        self.add_hist_complete = 0
        self.new_data = 0

    def add_hist(self,Date_temp, Open_temp, Close_temp, High_temp, Low_temp, Volume_temp):
        while 0<len(self.Date):
            if self.Date[0]>Date_temp[-1]:
                Date_temp.append(self.Date.pop(0))
                Open_temp.append(self.Open.pop(0))
                Close_temp.append(self.Close.pop(0))
                High_temp.append(self.High.pop(0))
                Low_temp.append(self.Low.pop(0))
                Volume_temp.append(self.Volume.pop(0))
            else:
                self.Date.pop(0)
                self.Open.pop(0)
                self.Close.pop(0)
                self.High.pop(0)
                self.Low.pop(0)
                self.Volume.pop(0)
        self.Date = Date_temp
        self.Open = Open_temp
        self.Close = Close_temp
        self.High = High_temp
        self.Low = Low_temp
        self.Volume = Volume_temp
        self.add_hist_complete = 1

    def handle_socket_message(self,msg):
        payload = msg['k']
        if payload['x']:
            ## append incoming data
            self.Open.append(float(payload['o']))
            self.Close.append(float(payload['c']))
            self.High.append(float(payload['h']))
            self.Low.append(float(payload['l']))
            self.Volume.append(float(payload['q']))
            self.Date.append(datetime.utcfromtimestamp(round(payload['t']/1000)))
            ## remove oldest data point
            if self.add_hist_complete:
                self.Open.pop(0)
                self.Close.pop(0)
                self.High.pop(0)
                self.Low.pop(0)
                self.Date.pop(0)
                self.new_data = 1

    def Make_decision(self):
        ##implement your strategy here:

        ##Must return these:
        Trade_Direction = -99 ## Short (0), Long (1)
        stoplossval = -99   ##the margin of increase/decrease that would stop us out/ be our take profit, NOT the price target.
        takeprofitval = -99 #That is worked out later by adding or subtracting:

        ######################### Strategy ###############################
        ###Can use indicators from ta python & check out TradingStrats.py for some strategy ideas
        ######################################################################################
        ~~~~~~~~~~~~~~~~~~~~~~~ tripleEMA Strategy from TradingStrats.py ~~~~~~~~~~~~~~~~~~~~~
        ######################################################################################
        
        
        ##Convert Close to self.Close to reference each coins close
        EMA3 = np.array(ema_indicator(pd.Series(self.Close), window=5))
        EMA6 = np.array(ema_indicator(pd.Series(self.Close), window=20))
        EMA9 = np.array(ema_indicator(pd.Series(self.Close), window=50))

        if EMA3[-5] > EMA6[-5] and EMA3[-5] > EMA9[-5] \
                and EMA3[-4] > EMA6[-4] and EMA3[-4] > EMA9[-4] \
                and EMA3[-3] > EMA6[-3] and EMA3[-3] > EMA9[-3] \
                and EMA3[-2] > EMA6[-2] and EMA3[-2] > EMA9[-2] \
                and EMA3[-1] < EMA6[-1] and EMA3[-1] < EMA9[-1]:
            Trade_Direction = 0 ##change prediction to Trade_Direction
        if EMA3[-5] < EMA6[-5] and EMA3[-5] < EMA9[-5] \
                and EMA3[-4] < EMA6[-4] and EMA3[-4] < EMA9[-4] \
                and EMA3[-3] < EMA6[-3] and EMA3[-3] < EMA9[-3] \
                and EMA3[-2] < EMA6[-2] and EMA3[-2] < EMA9[-2] \
                and EMA3[-1] > EMA6[-1] and EMA3[-1] > EMA9[-1]:
            Trade_Direction = 1 ##change prediction to Trade_Direction

        ##Stoploss and take profit, since TripleEma returns a 3 as its type parameter we look at SetSLTP() in
        ##TradingStrats.py and get the type 3 SL and TP functions and again convert from close to self.Close etc.
        highswing = self.Close[-2]
        Lowswing = self.Close[-2]
        highflag = 0
        lowflag = 0
        for j in range(-3, -50, -1):
            if self.Close[j] > highswing and self.Close[j] > self.Close[j - 1] and self.Close[j] > self.Close[
                j - 2] and highflag == 0:
                highswing = self.Close[j]
                highflag = 1
            if self.Close[j] < Lowswing and self.Close[j] < self.Close[j - 1] and self.Close[j] < self.Close[
                j - 2] and lowflag == 0:
                Lowswing = self.Close[j]
                lowflag = 1

        if Trade_Direction == 0: # and CurrentPos == -99:
            stoplossval = (highswing - self.Close[-1]) * 1.003
            if stoplossval < 0:
                stoplossval *= -1
            takeprofitval = (highswing - self.Close[-1]) * 1.25

        elif Trade_Direction == 1: # and CurrentPos == -99: can get ride of this
                            # as it was just to stop multiple trades in backtester but this is handled by the Bot.py script
            stoplossval = (self.Close[-1] - Lowswing) * 1.003
            if stoplossval < 0:
                stoplossval *= -1
            takeprofitval = (self.Close[-1] - Lowswing) * 1.25

        return Trade_Direction,stoplossval,takeprofitval




