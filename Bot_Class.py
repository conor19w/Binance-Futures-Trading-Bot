import os
import sys
from datetime import datetime
import time
from ta.momentum import stochrsi_d, stochrsi_k, stoch, stoch_signal, rsi, awesome_oscillator
from ta.trend import ema_indicator, macd_signal, macd, sma_indicator, adx, sma_indicator, cci
from ta.volatility import average_true_range, bollinger_pband, bollinger_hband, bollinger_lband, bollinger_mavg
from ta.volume import ease_of_movement, on_balance_volume, force_index, money_flow_index
from ta.momentum import stochrsi
from ta.trend import stc
import numpy as np
import pandas as pd
import TradingStrats as TS
from Utils import calculate_momentum, update_higher_timeframe_candles, get_date_index


class Bot:
    def __init__(self, symbol: str, Open: [float], Close: [float], High: [float], Low: [float], Volume: [float], Date: [str], OP: int, CP: int, index: int, tick: float,
                 strategy: str, TP_SL_choice: str, SL_mult: float, TP_mult: float, backtesting=0):
        self.symbol = symbol
        self.Date = Date

        # Remove extra candle if present
        shortest = len(Open)
        if shortest > len(Close):
            shortest = len(Close)
        if shortest > len(High):
            shortest = len(High)
        if shortest > len(Low):
            shortest = len(Low)
        if shortest > len(Volume):
            shortest = len(Volume)
        self.Open = Open[:shortest]
        self.Close = Close[:shortest]
        self.High = High[:shortest]
        self.Low = Low[:shortest]
        self.Volume = Volume[:shortest]

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
        self.TP_SL_choice = TP_SL_choice
        self.SL_mult = SL_mult
        self.TP_mult = TP_mult
        self.indicators = {}
        self.using_heikin_ashi = False
        # -1 for live Bot to always reference the most recent candle, will update in Backtester
        self.current_index = -1
        self.take_profit_val, self.stop_loss_val = [], []
        self.peaks, self.troughs = [], []

        self.price_data = update_higher_timeframe_candles(
            None, self.Date, self.Close, self.Volume, self.Open, self.High, self.Low)

        if backtesting:
            self.update_indicators()
            self.update_TP_SL()

    def update_indicators(self):
        # Calculate indicators
        if self.strategy == 'StochRSIMACD':
            Close = pd.Series(self.Close)
            High = pd.Series(self.High)
            Low = pd.Series(self.Low)
            self.indicators = {"fastd": {"values": list(stoch(close=Close, high=High, low=Low)),
                                         "plotting_axis": 3},
                               "fastk": {"values": list(stoch_signal(close=Close, high=High, low=Low)),
                                         "plotting_axis": 3},
                               "RSI": {"values": list(rsi(Close)),
                                       "plotting_axis": 4},
                               "MACD": {"values": list(macd(Close)),
                                        "plotting_axis": 5},
                               "macdsignal": {"values": list(macd_signal(Close)),
                                              "plotting_axis": 5}
                               }
        elif self.strategy == 'tripleEMAStochasticRSIATR':
            Close = pd.Series(self.Close)
            self.indicators = {"EMA_L": {"values": list(ema_indicator(Close, window=50)),
                                         "plotting_axis": 1},
                               "EMA_M": {"values": list(ema_indicator(Close, window=14)),
                                         "plotting_axis": 1},
                               "EMA_S": {"values": list(ema_indicator(Close, window=8)),
                                         "plotting_axis": 1},
                               "fastd": {"values": list(stochrsi_d(Close)),
                                         "plotting_axis": 3},
                               "fastk": {"values": list(stochrsi_k(Close)),
                                         "plotting_axis": 3}
                               }
        elif self.strategy == 'tripleEMA':
            Close = pd.Series(self.Close)
            self.indicators = {"EMA_L": {"values": list(ema_indicator(Close, window=50)),
                                         "plotting_axis": 1},
                               "EMA_M": {"values": list(ema_indicator(Close, window=20)),
                                         "plotting_axis": 1},
                               "EMA_S": {"values": list(ema_indicator(Close, window=5)),
                                         "plotting_axis": 1}
                               }
        elif self.strategy == 'breakout':
            Close = pd.Series(self.Close).pct_change()
            Volume = pd.Series(self.Volume)
            self.indicators = {"max Close % change": {"values": Close.rolling(10).max(),
                                                      "plotting_axis": 3},
                               "min Close % change": {"values": Close.rolling(10).min(),
                                                      "plotting_axis": 3},
                               "max Volume": {"values": Volume.rolling(10).max(),
                                              "plotting_axis": 2}
                               }
        elif self.strategy == 'stochBB':
            Close = pd.Series(self.Close)
            self.indicators = {"fastd": {"values": list(stochrsi_d(Close)),
                                         "plotting_axis": 3},
                               "fastk": {"values": list(stochrsi_k(Close)),
                                         "plotting_axis": 3},
                               "percent_B": {"values": list(bollinger_pband(Close)),
                                             "plotting_axis": 4}
                               }
        elif self.strategy == 'goldenCross':
            Close = pd.Series(self.Close)
            self.indicators = {"EMA_L": {"values": list(ema_indicator(Close, window=100)),
                                         "plotting_axis": 1},
                               "EMA_M": {"values": list(ema_indicator(Close, window=50)),
                                         "plotting_axis": 1},
                               "EMA_S": {"values": list(ema_indicator(Close, window=20)),
                                         "plotting_axis": 1},
                               "RSI": {"values": list(rsi(Close)),
                                       "plotting_axis": 3}
                               }
        elif self.strategy == 'fibMACD':
            Close = pd.Series(self.Close)
            self.indicators = {"MACD_signal": {"values": list(macd_signal(Close)),
                                               "plotting_axis": 3},
                               "MACD": {"values": list(macd(Close)),
                                        "plotting_axis": 3},
                               "EMA": {"values": list(sma_indicator(Close, window=200)),
                                       "plotting_axis": 1}
                               }
        elif self.strategy == 'EMA_cross':
            Close = pd.Series(self.Close)
            self.indicators = {"EMA_S": {"values": list(ema_indicator(Close, window=5)),
                                         "plotting_axis": 1},
                               "EMA_L": {"values": list(ema_indicator(Close, window=20)),
                                         "plotting_axis": 1}
                               }
        elif self.strategy == 'heikin_ashi_ema2':
            self.use_close_pos = True
            self.using_heikin_ashi = True  # for graphing heikin ashi candles
            Close = pd.Series(self.Close)
            self.indicators = {"fastd": {"values": list(stochrsi_d(Close)),
                                         "plotting_axis": 3},
                               "fastk": {"values": list(stochrsi_k(Close)),
                                         "plotting_axis": 3},
                               "EMA": {"values": list(ema_indicator(Close, window=200)),
                                       "plotting_axis": 1}
                               }
        elif self.strategy == 'heikin_ashi_ema':
            self.use_close_pos = True
            self.using_heikin_ashi = True  # for graphing heikin ashi candles
            Close = pd.Series(self.Close)
            self.indicators = {"fastd": {"values": list(stochrsi_d(Close)),
                                         "plotting_axis": 3},
                               "fastk": {"values": list(stochrsi_k(Close)),
                                         "plotting_axis": 3},
                               "EMA": {"values": list(ema_indicator(Close, window=200)),
                                       "plotting_axis": 1}
                               }
        elif self.strategy == 'ema_crossover':
            Close = pd.Series(self.Close)
            self.indicators = {"ema_short": {"values": list(ema_indicator(Close, window=20)),
                                             "plotting_axis": 1},
                               "ema_long": {"values": list(ema_indicator(Close, window=50)),
                                            "plotting_axis": 1},
                               }
        elif self.strategy == 'bb_confluence':
            # Update the higher candles
            # _, Close5m, _, _, _, _, = construct_higher_timeframe_candles(
            #     self.Date, self.Close, self.Volume, self.Open, self.High, self.Low, 5)
            # _, Close30m, _, _, _, _, = construct_higher_timeframe_candles(
            #     self.Date, self.Close, self.Volume, self.Open, self.High, self.Low, 30)
            # _, Close1h, _, _, _, _, = construct_higher_timeframe_candles(
            #     self.Date, self.Close, self.Volume, self.Open, self.High, self.Low, 60)
            # _, Close4h, _, _, _, _, = construct_higher_timeframe_candles(
            #     self.Date, self.Close, self.Volume, self.Open, self.High, self.Low, 4*60)
            # _, Close24h, _, _, _, _, = construct_higher_timeframe_candles(
            #     self.Date, self.Close, self.Volume, self.Open, self.High, self.Low, 24*60)

            Close5m = self.price_data["Close_5m"]
            Close30m = self.price_data["Close_30m"]
            Close1h = self.price_data["Close_1h"]
            Close4h = self.price_data["Close_4h"]
            Close24h = self.price_data["Close_12h"]

            High5m = self.price_data["High_5m"]
            High30m = self.price_data["High_30m"]
            High1h = self.price_data["High_1h"]
            High4h = self.price_data["High_4h"]

            Low5m = self.price_data["Low_5m"]
            Low30m = self.price_data["Low_30m"]
            Low1h = self.price_data["Low_1h"]
            Low4h = self.price_data["Low_4h"]
            

            Date5m = self.price_data["Date_5m"]
            Date30m = self.price_data["Date_30m"]
            Date1h = self.price_data["Date_1h"]
            Date4h = self.price_data["Date_4h"]
            Date24h = self.price_data["Date_12h"]

            # print(len(self.price_data["Close_5m"]),len(self.price_data["Close_30m"]), 'Close1h', len(Close1h),'Close4h', len(Close4h), len(self.Close))

            stochrsi_5m = stochrsi(pd.Series(Close5m, dtype=float))
            k_line_5m = stochrsi_5m - stochrsi_5m.rolling(window=3).min()
            k_line_5m /= stochrsi_5m.rolling(window=3).max() - stochrsi_5m.rolling(window=3).min()
            d_line_5m = k_line_5m.rolling(window=3).mean()

            stochrsi_30m = stochrsi(pd.Series(Close30m, dtype=float))
            k_line_30m = stochrsi_30m - stochrsi_30m.rolling(window=3).min()
            k_line_30m /= stochrsi_30m.rolling(window=3).max() - stochrsi_30m.rolling(window=3).min()
            d_line_30m = k_line_30m.rolling(window=3).mean()

            self.indicators = {
                "Close_5m": {"values": Close5m, "plotting_axis": 3},
                "Close_30m": {"values": Close30m, "plotting_axis": 3},
                "Close_1h": {"values": Close1h, "plotting_axis": 3},
                "Close_4h": {"values": Close4h, "plotting_axis": 3},

                "High_5m": {"values": High5m, "plotting_axis": 3},
                "High_30m": {"values": High30m, "plotting_axis": 3},
                "High_1h": {"values": High1h, "plotting_axis": 3},
                "High_4h": {"values": High4h, "plotting_axis": 3},

                "Low_5m": {"values": Low5m, "plotting_axis": 3},
                "Low_30m": {"values": Low30m, "plotting_axis": 3},
                "Low_1h": {"values": Low1h, "plotting_axis": 3},
                "Low_4h": {"values": Low4h, "plotting_axis": 3},

                "Date_5m": {"values": Date5m, "plotting_axis": 3},
                "Date_30m": {"values": Date30m, "plotting_axis": 3},
                "Date_1h": {"values": Date1h, "plotting_axis": 3},
                "Date_4h": {"values": Date4h, "plotting_axis": 3},
                "Date_1d": {"values": Date24h, "plotting_axis": 3},

                "bollinger_hband_5m": {"values": list(bollinger_hband(pd.Series(Close5m, dtype=float), window=21)), "plotting_axis": 3},
                "bollinger_lband_5m": {"values": list(bollinger_lband(pd.Series(Close5m, dtype=float), window=21)), "plotting_axis": 3},
                "bollinger_hband_30m": {"values": list(bollinger_hband(pd.Series(Close30m, dtype=float), window=21)), "plotting_axis": 3},
                "bollinger_lband_30m": {"values": list(bollinger_lband(pd.Series(Close30m, dtype=float), window=21)), "plotting_axis": 3},
                "bollinger_hband_1h": {"values": list(bollinger_hband(pd.Series(Close1h, dtype=float), window=21)), "plotting_axis": 3},
                "bollinger_lband_1h": {"values": list(bollinger_lband(pd.Series(Close1h, dtype=float), window=21)), "plotting_axis": 3},
                "bollinger_hband_4h": {"values": list(bollinger_hband(pd.Series(Close4h, dtype=float), window=21)), "plotting_axis": 3},
                "bollinger_lband_4h": {"values": list(bollinger_lband(pd.Series(Close4h, dtype=float), window=21)), "plotting_axis": 3},
                "bollinger_hband_1d": {"values": list(bollinger_hband(pd.Series(Close24h, dtype=float), window=21)), "plotting_axis": 3},
                "bollinger_lband_1d": {"values": list(bollinger_lband(pd.Series(Close24h, dtype=float), window=21)), "plotting_axis": 3},

                "stochrsi_5m": {"values": list(stochrsi_5m), "plotting_axis": 3},
                "k_line_5m": {"values": list(k_line_5m), "plotting_axis": 3},
                "d_line_5m": {"values": list(d_line_5m), "plotting_axis": 3},

                "stochrsi_30m": {"values": list(stochrsi_30m), "plotting_axis": 3},
                "k_line_30m": {"values": list(k_line_30m), "plotting_axis": 3},
                "d_line_30m": {"values": list(d_line_30m), "plotting_axis": 3},

            
            }

    def update_TP_SL(self):
        # Run Once in Backtester/ Run every candle in Live Bot
        if self.TP_SL_choice == '1h (Swing High/Low) level 1':
            self.take_profit_val = [2+(self.TP_mult / 100) * self.Close[i]
                                    for i in range(len(self.Close))]
            self.stop_loss_val = [5+(self.SL_mult / 100) * self.Close[i]
                                  for i in range(len(self.Close))]
            
        if self.TP_SL_choice == '%':
            self.take_profit_val = [(self.TP_mult / 100) * self.Close[i]
                                    for i in range(len(self.Close))]
            self.stop_loss_val = [(self.SL_mult / 100) * self.Close[i]
                                  for i in range(len(self.Close))]

        if self.TP_SL_choice == 'x (ATR)':
            ATR = list(average_true_range(pd.Series(self.High),
                       pd.Series(self.Low), pd.Series(self.Close)))
            self.take_profit_val = [self.TP_mult *
                                    abs(ATR[i]) for i in range(len(ATR))]
            self.stop_loss_val = [self.SL_mult *
                                  abs(ATR[i]) for i in range(len(ATR))]

        if self.TP_SL_choice == 'x (Swing High/Low) level 1':
            self.peaks = [0 if (i < 1 or i > len(self.High) - 2) else self.High[i] if (
                self.High[i - 1] < self.High[i] > self.High[i + 1]) else 0 for i in range(len(self.High))]

            self.troughs = [0 if (i < 1 or i > len(self.High) - 2) else self.Low[i] if (
                self.Low[i - 1] > self.Low[i] < self.Low[i + 1]) else 0 for i in range(len(self.Low))]

        if self.TP_SL_choice == 'x (Swing High/Low) level 2':
            self.peaks = [0 if (i < 2 or i > len(self.High) - 3) else self.High[i] if (self.High[i - 1] < self.High[i] > self.High[i + 1]) and (self.High[i - 2] < self.High[i] > self.High[i + 2])
                          else 0 for i in range(len(self.High))]

            self.troughs = [0 if (i < 2 or i > len(self.Low) - 3) else self.Low[i] if (self.Low[i - 1] > self.Low[i] < self.Low[i + 1]) and (self.Low[i - 2] > self.Low[i] < self.Low[i + 2])
                            else 0 for i in range(len(self.Low))]

        if self.TP_SL_choice == 'x (Swing High/Low) level 3':
            self.peaks = [0 if (i < 3 or i > len(self.High) - 4) else self.High[i] if (self.High[i - 1] < self.High[i] > self.High[i + 1]) and (self.High[i - 2] < self.High[i] > self.High[i + 2])
                          and (self.High[i - 3] < self.High[i] > self.High[i + 3]) else 0 for i in range(len(self.High))]

            self.troughs = [0 if (i < 3 or i > len(self.Low) - 4) else self.Low[i] if (self.Low[i - 1] > self.Low[i] < self.Low[i + 1]) and (self.Low[i - 2] > self.Low[i] < self.Low[i + 2])
                            and (self.Low[i - 3] > self.Low[i] < self.Low[i + 3]) else 0 for i in range(len(self.Low))]

        if self.TP_SL_choice == 'x (Swing Close) level 1':
            self.peaks = [0 if (i < 1 or i > len(self.Close) - 2) else self.Close[i] if (
                self.Close[i - 1] < self.Close[i] > self.Close[i + 1]) else 0 for i in range(len(self.Close))]

            self.troughs = [0 if (i < 1 or i > len(self.Close) - 2) else self.Close[i] if (
                self.Close[i - 1] > self.Close[i] < self.Close[i + 1]) else 0 for i in range(len(self.Close))]

        if self.TP_SL_choice == 'x (Swing Close) level 2':
            self.peaks = [0 if (i < 2 or i > len(self.Close) - 3) else self.Close[i] if (self.Close[i - 1] < self.Close[i] > self.Close[i + 1]) and
                                                                                        (self.Close[i - 2] < self.Close[i] > self.Close[i + 2]) else 0 for i in range(len(self.Close))]

            self.troughs = [0 if (i < 2 or i > len(self.Close) - 3) else self.Close[i] if (self.Close[i - 1] > self.Close[i] < self.Close[i + 1]) and
                                                                                          (self.Close[i - 2] > self.Close[i] < self.Close[i + 2]) else 0 for i in range(len(self.Close))]

        if self.TP_SL_choice == 'x (Swing Close) level 3':
            self.peaks = [0 if (i < 3 or i > len(self.Close) - 4) else self.Close[i] if (self.Close[i - 1] < self.Close[i] > self.Close[i + 1]) and
                                                                                        (self.Close[i - 2] < self.Close[i] > self.Close[i + 2]) and (
                                                                                            self.Close[i - 3] < self.Close[i] > self.Close[i + 3])
                          else 0 for i in range(len(self.Close))]

            self.troughs = [0 if (i < 3 or i > len(self.Close) - 4) else self.Close[i] if (self.Close[i - 1] > self.Close[i] < self.Close[i + 1]) and
                                                                                          (self.Close[i - 2] > self.Close[i] < self.Close[i + 2]) and (
                                                                                              self.Close[i - 3] > self.Close[i] < self.Close[i + 3])
                            else 0 for i in range(len(self.Close))]
        
        if self.TP_SL_choice == 'x (Swing Close30) level 3':
            Date1m = self.Date[self.current_index]
            Close30mIndex = get_date_index(Date1m, self.indicators["Date_30m"]["values"])
            Close = self.indicators["Close_30m"]["values"][:Close30mIndex]
            self.peaks = [0 if (i < 3 or i > len(Close) - 4) else Close[i] if (Close[i - 1] < Close[i] > Close[i + 1]) and
                                                                                        (Close[i - 2] < Close[i] > Close[i + 2]) and (
                                                                                            Close[i - 3] < Close[i] > Close[i + 3])
                          else 0 for i in range(len(Close))]

            self.troughs = [0 if (i < 3 or i > len(Close) - 4) else Close[i] if (Close[i - 1] > Close[i] < Close[i + 1]) and
                                                                                          (Close[i - 2] > Close[i] < Close[i + 2]) and (
                                                                                              Close[i - 3] > Close[i] < Close[i + 3])
                            else 0 for i in range(len(Close))]

    def add_hist(self, Date_temp: [float], Open_temp: [float], Close_temp: [float], High_temp: [float], Low_temp: [float], Volume_temp: [str]):
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
            # Create Heikin Ashi bars
            for i in range(len(self.Close)):
                self.Close_H.append(
                    (self.Open[i] + self.Close[i] + self.Low[i] + self.High[i]) / 4)
                if i == 0:
                    self.Open_H.append((self.Close[i] + self.Open[i]) / 2)
                    self.High_H.append(self.High[i])
                    self.Low_H.append(self.Low[i])
                else:
                    self.Open_H.append(
                        (self.Open_H[i - 1] + self.Close_H[i - 2]) / 2)
                    self.High_H.append(
                        max(self.High[i], self.Open_H[i], self.Close_H[i]))
                    self.Low_H.append(
                        min(self.Low[i], self.Open_H[i], self.Close_H[i]))
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
                        self.Close_H.append(
                            (self.Open[-1] + self.Close[-1] + self.Low[-1] + self.High[-1]) / 4)
                        self.Open_H.append(
                            (self.Open_H[-1] + self.Close_H[-2]) / 2)
                        self.High_H.append(
                            max(self.High[-1], self.Open_H[-1], self.Close_H[-1]))
                        self.Low_H.append(
                            min(self.Low[-1], self.Open_H[-1], self.Close_H[-1]))
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
                        self.Close_H.append(
                            (self.Open[-1] + self.Close[-1] + self.Low[-1] + self.High[-1]) / 4)
                        self.Open_H.append(
                            (self.Open_H[-1] + self.Close_H[-2]) / 2)
                        self.High_H.append(
                            max(self.High[-1], self.Open_H[-1], self.Close_H[-1]))
                        self.Low_H.append(
                            min(self.Low[-1], self.Open_H[-1], self.Close_H[-1]))
                        self.Open_H.pop(0)
                        self.Close_H.pop(0)
                        self.Low_H.pop(0)
                        self.High_H.pop(0)
                    self.new_data = 1
                self.update_indicators()
                self.update_TP_SL()
            self.price_data = update_higher_timeframe_candles(self.price_data, [self.Date[-1]], [
                                                              self.Close[-1]], [self.Volume[-1]], [self.Open[-1]], [self.High[-1]], [self.Low[-1]])
        except Exception as e:
            print(f"Error in {self.symbol}.handle_socket_message(): ", e)
            self.socket_failed = True
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            # Can add this except statement in to code to figure out what line the error was thrown on
            print(exc_type, fname, exc_tb.tb_lineno)

    def Make_decision(self):
        # Initialize vars:
        Trade_Direction = -99  # Short (0), Long (1)
        # the margin of increase/decrease that would stop us out/ be our take profit, NOT the price target.
        stop_loss_val = -99
        # That is worked out later by adding or subtracting:
        take_profit_val = -99
        # Strategies found in TradingStrats.py:
        if self.strategy == 'StochRSIMACD':
            Trade_Direction = TS.StochRSIMACD(Trade_Direction, self.indicators["fastd"]["values"], self.indicators["fastk"]["values"],
                                              self.indicators["RSI"]["values"], self.indicators["MACD"]["values"],
                                              self.indicators["macdsignal"]["values"], self.current_index)
        elif self.strategy == 'tripleEMAStochasticRSIATR':
            Trade_Direction = TS.tripleEMAStochasticRSIATR(self.Close, Trade_Direction, self.indicators["EMA_L"]["values"],
                                                           self.indicators["EMA_M"]["values"], self.indicators["EMA_S"]["values"],
                                                           self.indicators["fastd"]["values"], self.indicators["fastk"]["values"], self.current_index)
        elif self.strategy == 'tripleEMA':
            Trade_Direction = TS.tripleEMA(Trade_Direction, self.indicators["EMA_S"]["values"],
                                           self.indicators["EMA_M"]["values"], self.indicators["EMA_L"]["values"], self.current_index)
        elif self.strategy == 'breakout':
            Trade_Direction = TS.breakout(Trade_Direction, self.Close, self.Volume, self.indicators["max Close % change"]["values"],
                                          self.indicators["min Close % change"]["values"], self.indicators["max Volume"]["values"],
                                          self.current_index)
        elif self.strategy == 'stochBB':
            Trade_Direction = TS.stochBB(Trade_Direction, self.indicators["fastd"]["values"],
                                         self.indicators["fastk"]["values"], self.indicators["percent_B"]["values"], self.current_index)
        elif self.strategy == 'goldenCross':
            Trade_Direction = TS.goldenCross(Trade_Direction, self.Close, self.indicators["EMA_L"]["values"],
                                             self.indicators["EMA_M"]["values"], self.indicators["EMA_S"]["values"],
                                             self.indicators["RSI"]["values"], self.current_index)
        elif self.strategy == 'candle_wick':
            Trade_Direction = TS.candle_wick(
                Trade_Direction, self.Close, self.Open, self.High, self.Low, self.current_index)
        elif self.strategy == 'fibMACD':
            Trade_Direction = TS.fibMACD(Trade_Direction, self.Close, self.Open,
                                         self.High, self.Low, self.indicators["MACD_signal"]["values"],
                                         self.indicators["MACD"]["values"], self.indicators["EMA"]["values"],
                                         self.current_index)
        elif self.strategy == 'EMA_cross':
            Trade_Direction = TS.EMA_cross(Trade_Direction, self.indicators["EMA_S"]["values"],
                                           self.indicators["EMA_L"]["values"], self.current_index)
        elif self.strategy == 'heikin_ashi_ema2':
            Trade_Direction, _ = TS.heikin_ashi_ema2(self.Open_H, self.High_H, self.Low_H,
                                                     self.Close_H, Trade_Direction,
                                                     -99, 0, self.indicators["fastd"]["values"], self.indicators["fastk"]["values"],
                                                     self.indicators["EMA"]["values"], self.current_index)
        elif self.strategy == 'heikin_ashi_ema':
            Trade_Direction, _ = TS.heikin_ashi_ema(self.Open_H, self.Close_H, Trade_Direction, -99, 0,
                                                    self.indicators["fastd"]["values"],
                                                    self.indicators["fastk"]["values"],
                                                    self.indicators["EMA"]["values"], self.current_index)
        elif self.strategy == "ema_crossover":
            Trade_Direction = TS.ema_crossover(Trade_Direction, self.current_index,
                                               self.indicators["ema_short"]["values"],
                                               self.indicators["ema_long"]["values"])
        elif self.strategy == "bb_confluence":
            Date1m = self.Date[self.current_index]
            Close5mIndex = get_date_index(Date1m, self.indicators["Date_5m"]["values"])
            Close30mIndex = get_date_index(Date1m, self.indicators["Date_30m"]["values"])
            Close1hIndex = get_date_index(Date1m, self.indicators["Date_1h"]["values"])
            Close4hIndex = get_date_index(Date1m, self.indicators["Date_4h"]["values"])
            Close1dIndex = get_date_index(Date1m, self.indicators["Date_1d"]["values"])

            Trade_Direction = TS.bb_confluence(Trade_Direction, self.Close, self.Open, self.High, self.Low,
                                               self.current_index,
                                               self.indicators["Close_5m"]["values"][:Close5mIndex],
                                               self.indicators["Close_30m"]["values"][:Close30mIndex],
                                               self.indicators["Close_1h"]["values"][:Close1hIndex],
                                               self.indicators["Close_4h"]["values"][:Close4hIndex],

                                               self.indicators["bollinger_hband_5m"]["values"][:Close5mIndex],
                                               self.indicators["bollinger_lband_5m"]["values"][:Close5mIndex],
                                               self.indicators["bollinger_hband_30m"]["values"][:Close30mIndex],
                                               self.indicators["bollinger_lband_30m"]["values"][:Close30mIndex],
                                               self.indicators["bollinger_hband_1h"]["values"][:Close1hIndex],
                                               self.indicators["bollinger_lband_1h"]["values"][:Close1hIndex],
                                               self.indicators["bollinger_hband_4h"]["values"][:Close4hIndex],
                                               self.indicators["bollinger_lband_4h"]["values"][:Close4hIndex],
                                               self.indicators["bollinger_hband_1d"]["values"][:Close1dIndex],
                                               self.indicators["bollinger_lband_1d"]["values"][:Close1dIndex],

                                               self.indicators["stochrsi_5m"]["values"][:Close5mIndex],
                                               self.indicators["d_line_5m"]["values"][:Close5mIndex],
                                               self.indicators["k_line_5m"]["values"][:Close5mIndex],

                                               self.indicators["stochrsi_30m"]["values"][:Close30mIndex],
                                               self.indicators["d_line_30m"]["values"][:Close30mIndex],
                                               self.indicators["k_line_30m"]["values"][:Close30mIndex],
                                               )

        # Get TP/SL values if we enter a trade:
        if Trade_Direction != -99:
            stop_loss_val, take_profit_val = TS.SetSLTP(self.stop_loss_val, self.take_profit_val, self.peaks,
                                                        self.troughs,
                                                        self.Close, self.High, self.Low, Trade_Direction, self.SL_mult,
                                                        self.TP_mult, self.TP_SL_choice,
                                                        self.current_index, self.indicators)
        return Trade_Direction, stop_loss_val, take_profit_val

    def check_close_pos(self, Trade_Direction):
        close_pos = 0
        if self.strategy == 'heikin_ashi_ema2':
            _, close_pos = TS.heikin_ashi_ema2(self.Open_H, self.High_H, self.Low_H,
                                               self.Close_H, -99, Trade_Direction,
                                               0, self.indicators["fastd"]["values"], self.indicators["fastk"]["values"],
                                               self.indicators["EMA"]["values"], self.current_index)
        elif self.strategy == 'heikin_ashi_ema':
            _, close_pos = TS.heikin_ashi_ema(self.Open_H, self.Close_H, -99, Trade_Direction, 0,
                                              self.indicators["fastd"]["values"], self.indicators["fastk"]["values"], self.indicators["EMA"]["values"], self.current_index)
        return close_pos
