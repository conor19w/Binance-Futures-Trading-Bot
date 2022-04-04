from datetime import datetime

from ta.momentum import stochrsi_d,stochrsi_k,stoch,stoch_signal,rsi,awesome_oscillator
from ta.trend import ema_indicator,macd_signal,macd,sma_indicator,adx,sma_indicator,cci
from ta.volatility import average_true_range,bollinger_pband,bollinger_hband,bollinger_lband,bollinger_mavg
from ta.volume import ease_of_movement,on_balance_volume,force_index,money_flow_index
from ta.momentum import tsi
import numpy as np
import pandas as pd

import TradingStrats as TS

class Bot:
    def __init__(self,symbol,Open,Close,High,Low,Volume,Date,OP,CP,index,use_heikin_ashi,tick):
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
        self.use_heikin_ashi = use_heikin_ashi
        self.Open_H = []
        self.Close_H = []
        self.High_H = []
        self.Low_H = []
        self.tick_size = tick
        self.socket_failed = False

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
        if self.use_heikin_ashi:
            ##Create Heikin Ashi bars
            for i in range(len(self.Close)):
                self.Close_H.append((self.Open[i] + self.Close[i] + self.Low[i] + self.High[i]) / 4)
                if i == 0:
                    self.Open_H.append((self.Close_H[i] + self.Open[i]) / 2)
                    self.High_H.append(self.High[i])
                    self.Low_H.append(self.Low[i])
                else:
                    self.Open_H.append((self.Open_H[i-1] + self.Close_H[i-1]) / 2)
                    self.High_H.append(max(self.High[i], self.Open_H[i], self.Close_H[i]))
                    self.Low_H.append(min(self.Low[i], self.Open_H[i], self.Close_H[i]))
        self.add_hist_complete = 1

    def handle_socket_message(self,Data):
        try:
            if Data['Date'] != -99:
                self.Date.append(Data['Date'])
                self.Close.append(Data['Close'])
                self.Volume.append(Data['Volume'])
                self.High.append(Data['High'])
                self.Low.append(Data['Low'])
                self.Open.append(Data['Open'])
                if self.add_hist_complete:
                    self.Date.pop(0)
                    self.Close.pop(0)
                    self.Volume.pop(0)
                    self.High.pop(0)
                    self.Low.pop(0)
                    self.Open.pop(0)
                    self.new_data = 1
                    if self.use_heikin_ashi:
                        self.Close_H.append((self.Open[-1] + self.Close[-1] + self.Low[-1] + self.High[-1]) / 4)
                        self.Open_H.append((self.Open_H[-2] + self.Close_H[-2]) / 2)
                        self.High_H.append(max(self.High[-1], self.Open_H[-1], self.Close_H[-1]))
                        self.Low_H.append(min(self.Low[-1], self.Open_H[-1], self.Close_H[-1]))
                        self.Open_H.pop(0)
                        self.Close_H.pop(0)
                        self.Low_H.pop(0)
                        self.High_H.pop(0)
                    self.new_data = 1
        except Exception as e:
            print(f"Error in {self.symbol}.handle_socket_message(): ", e)
            self.socket_failed = True

    def Make_decision(self):
        ##Must return these:
        Trade_Direction = -99 ## Short (0), Long (1)
        stop_loss_val = -99   ##the margin of increase/decrease that would stop us out/ be our take profit, NOT the price target.
        take_profit_val = -99 #That is worked out later by adding or subtracting:

        ######################### Strategy ###############################
        ###Can use indicators from ta python & check out TradingStrats.py for some strategy ideas
        ##implement your strategy here:

        ##OR use one of these Strategies Available from the backtester:
        #Trade_Direction,stop_loss_val, take_profit_val = TS.StochRSIMACD(Trade_Direction, self.Close,self.High,self.Low)
        #Trade_Direction,stop_loss_val, take_profit_val = TS.tripleEMAStochasticRSIATR(self.Close,self.High,self.Low,Trade_Direction)
        Trade_Direction, stop_loss_val, take_profit_val = TS.tripleEMA(self.Close, self.High, self.Low, Trade_Direction)
        #Trade_Direction, stop_loss_val, take_profit_val = TS.breakout(Trade_Direction,self.Close,self.Volume,self.High, self.Low)
        #Trade_Direction,stop_loss_val,take_profit_val = TS.stochBB(Trade_Direction,self.Close, self.High, self.Low)
        #Trade_Direction, stop_loss_val, take_profit_val = TS.goldenCross(Trade_Direction,self.Close, self.High, self.Low)
        #Trade_Direction , stop_loss_val, take_profit_val = TS.candle_wick(Trade_Direction,self.Close,self.Open,self.High,self.Low)
        #Trade_Direction,stop_loss_val,take_profit_val = TS.fibMACD(Trade_Direction, self.Close, self.Open,self.High,self.Low)
        #Trade_Direction, stop_loss_val, take_profit_val, _ = TS.heikin_ashi_ema2(self.Close, self.Open_H, self.High_H, self.Low_H, self.Close_H, Trade_Direction, stoplossval, takeprofitval, CurrentPos, 0)
        #Trade_Direction,stop_loss_val,take_profit_val,_ = TS.heikin_ashi_ema(self.Close, self.Open_H, self.Close_H, Trade_Direction, stoplossval,takeprofitval, CurrentPos, 0)
        return Trade_Direction,stop_loss_val,take_profit_val
