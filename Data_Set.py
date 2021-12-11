from datetime import datetime

from ta.momentum import stochrsi_d,stochrsi_k,stoch,stoch_signal,rsi,awesome_oscillator
from ta.trend import ema_indicator,macd_signal,macd,sma_indicator,adx,sma_indicator,cci
from ta.volatility import average_true_range,bollinger_pband,bollinger_hband,bollinger_lband,bollinger_mavg
from ta.volume import ease_of_movement,on_balance_volume,force_index,money_flow_index
from ta.momentum import tsi

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


        return Trade_Direction,stoplossval,takeprofitval




