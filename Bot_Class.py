import os
import sys
from datetime import datetime
import time
from ta.momentum import stochrsi_d, stochrsi_k, stoch, stoch_signal, rsi, awesome_oscillator
from ta.trend import ema_indicator, macd_signal, macd, sma_indicator, adx, sma_indicator, cci
from ta.volatility import average_true_range, bollinger_pband, bollinger_hband, bollinger_lband, bollinger_mavg
from ta.volume import ease_of_movement, on_balance_volume, force_index, money_flow_index
from ta.momentum import tsi
from ta.trend import stc
import numpy as np
import pandas as pd
import TradingStrats as TS


class Bot:
    def __init__(self, symbol, Open, Close, High, Low, Volume, Date, OP, CP, index, tick,
                 strategy, TP_choice, SL_choice, SL_mult, TP_mult, backtesting=0):
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
        self.generate_heikin_ashi = True
        self.Open_H = []
        self.Close_H = []
        self.High_H = []
        self.Low_H = []
        self.tick_size = tick
        self.socket_failed = False
        self.backtesting = backtesting
        self.use_close_pos = False
        self.strategy = strategy
        self.TP_choice = TP_choice
        self.SL_choice = SL_choice
        self.SL_mult = SL_mult
        self.TP_mult = TP_mult
        self.fastd = None
        self.fastk = None
        self.RSI = None
        self.MACD = None
        self.macdsignal = None
        self.EMA100 = None
        self.EMA50 = None
        self.EMA20 = None
        self.EMA14 = None
        self.EMA9 = None
        self.EMA8 = None
        self.EMA6 = None
        self.EMA3 = None
        self.max_Close = None
        self.min_Close = None
        self.max_Vol = None
        self.percent_B = None
        self.MACD_signal = None
        self.EMA200 = None
        self.EMA_short = None
        self.EMA_long = None
        self.current_index = -1  ## -1 for live Bot to always reference the most recent candle, will update in Backtester
        if backtesting:
            self.update_indicators()

    def update_indicators(self):
        ## Calculate indicators
        if self.strategy == 'StochRSIMACD':
            CloseS = pd.Series(self.Close)
            HighS = pd.Series(self.High)
            LowS = pd.Series(self.Low)
            self.fastd = np.array(stoch(close=CloseS, high=HighS, low=LowS))
            self.fastk = np.array(stoch_signal(close=CloseS, high=HighS, low=LowS))
            self.RSI = np.array(rsi(CloseS))
            self.MACD = np.array(macd(CloseS))
            self.macdsignal = np.array(macd_signal(CloseS))
        elif self.strategy == 'tripleEMAStochasticRSIATR':
            Close = np.array(self.Close)
            self.EMA50 = np.array(ema_indicator(pd.Series(Close), window=50))
            self.EMA14 = np.array(ema_indicator(pd.Series(Close), window=14))
            self.EMA8 = np.array(ema_indicator(pd.Series(Close), window=8))
            self.fastd = np.array(stochrsi_d(pd.Series(Close)))
            self.fastk = np.array(stochrsi_k(pd.Series(Close)))
        elif self.strategy == 'tripleEMA':
            self.EMA3 = np.array(ema_indicator(pd.Series(self.Close), window=5))
            self.EMA6 = np.array(ema_indicator(pd.Series(self.Close), window=20))
            self.EMA9 = np.array(ema_indicator(pd.Series(self.Close), window=50))
        elif self.strategy == 'breakout':
            CloseS = pd.Series(self.Close).pct_change()
            Volume = pd.Series(self.Volume)
            self.max_Close = CloseS.rolling(10).max()
            self.min_Close = CloseS.rolling(10).min()
            self.max_Vol = Volume.rolling(10).max()
        elif self.strategy == 'stochBB':
            self.fastd = np.array(stochrsi_d(pd.Series(self.Close)))
            self.fastk = np.array(stochrsi_k(pd.Series(self.Close)))
            self.percent_B = np.array(bollinger_pband(pd.Series(self.Close)))
        elif self.strategy == 'goldenCross':
            self.EMA100 = np.array(ema_indicator(pd.Series(self.Close), window=100))
            self.EMA50 = np.array(ema_indicator(pd.Series(self.Close), window=50))
            self.EMA20 = np.array(ema_indicator(pd.Series(self.Close), window=20))
            self.RSI = np.array(rsi(pd.Series(self.Close)))

        elif self.strategy == 'fibMACD':
            self.MACD_signal = np.array(macd_signal(pd.Series(self.Close)))
            self.MACD = np.array(macd(pd.Series(self.Close)))
            self.EMA200 = np.array(sma_indicator(pd.Series(self.Close), window=200))

        elif self.strategy == 'EMA_cross':
            self.EMA_short = np.array(ema_indicator(pd.Series(self.Close), window=5))
            self.EMA_long = np.array(ema_indicator(pd.Series(self.Close), window=20))
        elif self.strategy == 'heikin_ashi_ema2':
            self.use_close_pos = True
            self.fastd = np.array(stochrsi_d(pd.Series(self.Close)))
            self.fastk = np.array(stochrsi_k(pd.Series(self.Close)))
            self.EMA200 = np.array(ema_indicator(pd.Series(self.Close), window=200))
        elif self.strategy == 'heikin_ashi_ema':
            self.use_close_pos = True
            self.fastd = np.array(stochrsi_d(pd.Series(self.Close)))
            self.fastk = np.array(stochrsi_k(pd.Series(self.Close)))
            self.EMA200 = np.array(ema_indicator(pd.Series(self.Close), window=200))
        elif self.strategy == 'ema_crossover':
            self.EMA_short = np.array(ema_indicator(pd.Series(self.Close), window=10))
            self.EMA_long = np.array(ema_indicator(pd.Series(self.Close), window=20))

    def add_hist(self, Date_temp, Open_temp, Close_temp, High_temp, Low_temp, Volume_temp):
        if not self.backtesting:
            while 0 < len(self.Date):
                if self.Date[0] > Date_temp[-1]:
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
        if self.generate_heikin_ashi:
            ##Create Heikin Ashi bars
            for i in range(len(self.Close)):
                self.Close_H.append((self.Open[i] + self.Close[i] + self.Low[i] + self.High[i]) / 4)
                if i == 0:
                    self.Open_H.append((self.Close[i] + self.Open[i]) / 2)
                    self.High_H.append(self.High[i])
                    self.Low_H.append(self.Low[i])
                else:
                    self.Open_H.append((self.Open_H[i - 1] + self.Close_H[i - 2]) / 2)
                    self.High_H.append(max(self.High[i], self.Open_H[i], self.Close_H[i]))
                    self.Low_H.append(min(self.Low[i], self.Open_H[i], self.Close_H[i]))
        self.add_hist_complete = 1
        # for i in range(len(self.Date)):
        #    print(f"Date: {self.Date[i]}, Open_H: {self.Open_H[i]}, Close_H: {self.Close_H[i]}, High_H: {self.High_H[i]}, Low_H: {self.Low_H[i]}")

    def handle_socket_message(self, Data, Date=0, Close=0, Volume=0, Open=0, High=0, Low=0):
        try:
            if Data == -99:
                self.Date.append(Date)
                self.Close.append(Close)
                self.Volume.append(Volume)
                self.High.append(High)
                self.Low.append(Low)
                self.Open.append(Open)
                if self.add_hist_complete:
                    self.Date.pop(0)
                    self.Close.pop(0)
                    self.Volume.pop(0)
                    self.High.pop(0)
                    self.Low.pop(0)
                    self.Open.pop(0)
                    if self.generate_heikin_ashi:
                        self.Close_H.append((self.Open[-1] + self.Close[-1] + self.Low[-1] + self.High[-1]) / 4)
                        self.Open_H.append((self.Open_H[-1] + self.Close_H[-2]) / 2)
                        self.High_H.append(max(self.High[-1], self.Open_H[-1], self.Close_H[-1]))
                        self.Low_H.append(min(self.Low[-1], self.Open_H[-1], self.Close_H[-1]))
                        self.Open_H.pop(0)
                        self.Close_H.pop(0)
                        self.Low_H.pop(0)
                        self.High_H.pop(0)
                    self.new_data = 1
            elif Data['Date'] != -99:
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
                    if self.generate_heikin_ashi:
                        self.Close_H.append((self.Open[-1] + self.Close[-1] + self.Low[-1] + self.High[-1]) / 4)
                        self.Open_H.append((self.Open_H[-1] + self.Close_H[-2]) / 2)
                        self.High_H.append(max(self.High[-1], self.Open_H[-1], self.Close_H[-1]))
                        self.Low_H.append(min(self.Low[-1], self.Open_H[-1], self.Close_H[-1]))
                        self.Open_H.pop(0)
                        self.Close_H.pop(0)
                        self.Low_H.pop(0)
                        self.High_H.pop(0)
                    self.new_data = 1
                self.update_indicators()
        # except Exception as e:
        #     print(e)
        #     exc_type, exc_obj, exc_tb = sys.exc_info()
        #     fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        #     print(exc_type, fname, exc_tb.tb_lineno) ## Can add this except statement in to code to figure out what line the error was thrown on
        except Exception as e:
            print(f"Error in {self.symbol}.handle_socket_message(): ", e)
            self.socket_failed = True

    def Make_decision(self):
        ##Initialize vars:
        Trade_Direction = -99  ## Short (0), Long (1)
        stop_loss_val = -99  ##the margin of increase/decrease that would stop us out/ be our take profit, NOT the price target.
        take_profit_val = -99  # That is worked out later by adding or subtracting:
        ## Strategies found in TradingStrats.py:
        if self.strategy == 'StochRSIMACD':
            Trade_Direction, stop_loss_val, take_profit_val = TS.StochRSIMACD(Trade_Direction, self.Close, self.High,
                                                                              self.Low, self.SL_mult, self.TP_mult,
                                                                              self.TP_choice, self.SL_choice,
                                                                              self.fastd, self.fastk, self.RSI, self.MACD, self.macdsignal, self.current_index)
        elif self.strategy == 'tripleEMAStochasticRSIATR':
            Trade_Direction, stop_loss_val, take_profit_val = TS.tripleEMAStochasticRSIATR(self.Close, self.High,
                                                                                           self.Low, Trade_Direction,
                                                                                           self.SL_mult, self.TP_mult,
                                                                                           self.TP_choice,
                                                                                           self.SL_choice,
                                                                                           self.EMA50, self.EMA14,
                                                                                           self.EMA8,
                                                                                           self.fastd, self.fastk,
                                                                                           self.current_index)
        elif self.strategy == 'tripleEMA':
            Trade_Direction, stop_loss_val, take_profit_val = TS.tripleEMA(self.Close, self.High, self.Low,
                                                                           Trade_Direction, self.SL_mult, self.TP_mult,
                                                                           self.TP_choice, self.SL_choice, self.EMA3,
                                                                           self.EMA6,
                                                                           self.EMA9, self.current_index)
        elif self.strategy == 'breakout':
            Trade_Direction, stop_loss_val, take_profit_val = TS.breakout(Trade_Direction, self.Close, self.Volume,
                                                                          self.High, self.Low, self.SL_mult,
                                                                          self.TP_mult,
                                                                          self.TP_choice, self.SL_choice,
                                                                          self.max_Close,
                                                                          self.min_Close, self.max_Vol,
                                                                          self.current_index)
        elif self.strategy == 'stochBB':
            Trade_Direction, stop_loss_val, take_profit_val = TS.stochBB(Trade_Direction, self.Close, self.High,
                                                                         self.Low, self.SL_mult, self.TP_mult,
                                                                         self.TP_choice, self.SL_choice, self.fastd,
                                                                         self.fastk, self.percent_B, self.current_index)
        elif self.strategy == 'goldenCross':
            Trade_Direction, stop_loss_val, take_profit_val = TS.goldenCross(Trade_Direction, self.Close, self.High,
                                                                             self.Low, self.SL_mult, self.TP_mult,
                                                                             self.TP_choice, self.SL_choice,
                                                                             self.EMA100,
                                                                             self.EMA50, self.EMA20, self.RSI,
                                                                             self.current_index)
        elif self.strategy == 'candle_wick':
            Trade_Direction, stop_loss_val, take_profit_val = TS.candle_wick(Trade_Direction, self.Close, self.Open,
                                                                             self.High, self.Low, self.SL_mult,
                                                                             self.TP_mult,
                                                                             self.TP_choice, self.SL_choice,
                                                                             self.current_index)
        elif self.strategy == 'fibMACD':
            Trade_Direction, stop_loss_val, take_profit_val = TS.fibMACD(Trade_Direction, self.Close, self.Open,
                                                                         self.High, self.Low, self.MACD_signal,
                                                                         self.MACD, self.EMA200,
                                                                         self.current_index)
        elif self.strategy == 'EMA_cross':
            Trade_Direction, stop_loss_val, take_profit_val = TS.EMA_cross(Trade_Direction, self.Close, self.High,
                                                                           self.Low, self.SL_mult, self.TP_mult,
                                                                           self.TP_choice, self.SL_choice,
                                                                           self.EMA_short, self.EMA_long,
                                                                           self.current_index)

        elif self.strategy == 'heikin_ashi_ema2':
            Trade_Direction, stop_loss_val, take_profit_val, _ = TS.heikin_ashi_ema2(self.Close, self.Open_H,
                                                                                     self.High_H, self.Low_H,
                                                                                     self.Close_H, self.High,
                                                                                     self.Low, Trade_Direction,
                                                                                     -99, 0, self.SL_mult, self.TP_mult,
                                                                                     self.TP_choice, self.SL_choice,
                                                                                     self.fastd, self.fastk,
                                                                                     self.EMA200, self.current_index)
        elif self.strategy == 'heikin_ashi_ema':
            Trade_Direction, stop_loss_val, take_profit_val, _ = TS.heikin_ashi_ema(self.Close, self.Open_H,
                                                                                    self.Close_H, Trade_Direction, -99,
                                                                                    0, self.High, self.Low,
                                                                                    self.SL_mult, self.TP_mult,
                                                                                    self.TP_choice, self.SL_choice,
                                                                                    self.fastd, self.fastk, self.EMA200,
                                                                                    self.current_index)
        elif self.strategy == 'ema_crossover':
            Trade_Direction, stop_loss_val, take_profit_val = ema_crossover(self.Trade_Direction, self.Close, self.High, self.Low,
                                                                            self.SL, self.TP, self.TP_choice, self.SL_choice,
                                                                            self.current_index, self.EMA_short, self.EMA_long)

        return Trade_Direction, stop_loss_val, take_profit_val

    def check_close_pos(self, current_pos):
        close_pos = 0
        Trade_Direction = -99  ## Short (0), Long (1)
        stop_loss_val = -99  ##the margin of increase/decrease that would stop us out/ be our take profit, NOT the price target.
        take_profit_val = -99  # That is worked out later by adding or subtracting:
        if self.strategy == 'heikin_ashi_ema2':
            _, _, _, close_pos = TS.heikin_ashi_ema2(self.Close, self.Open_H, self.High_H, self.Low_H,
                                                     self.Close_H, self.High,
                                                     self.Low, Trade_Direction,
                                                     -99, 0, self.SL_mult, self.TP_mult,
                                                     self.TP_choice, self.SL_choice,
                                                     self.fastd, self.fastk,
                                                     self.EMA200, self.current_index)
        elif self.strategy == 'heikin_ashi_ema':
            _, _, _, close_pos = TS.heikin_ashi_ema(self.Close, self.Open_H, self.Close_H, Trade_Direction, -99,
                                                    0, self.High, self.Low,
                                                    self.SL_mult, self.TP_mult,
                                                    self.TP_choice, self.SL_choice,
                                                    self.fastd, self.fastk, self.EMA200,
                                                    self.current_index)
        return close_pos
