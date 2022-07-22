import pandas as pd
import numpy as np
from ta.momentum import stochrsi_d, stochrsi_k, stoch, stoch_signal, rsi, awesome_oscillator
from ta.trend import ema_indicator, macd_signal, macd, sma_indicator, adx, sma_indicator, cci, ichimoku_a, ichimoku_b, \
    ichimoku_base_line, ichimoku_conversion_line
from ta.volatility import average_true_range, bollinger_pband, bollinger_hband, bollinger_lband, bollinger_mavg, \
    bollinger_wband
from ta.volume import ease_of_movement, on_balance_volume, force_index, money_flow_index
from ta.momentum import tsi
import math
# import statsmodels.api as sm
# from sklearn import tree
# from statsmodels.tsa.stattools import adfuller,coint
from math import log10, floor
from copy import copy
import time


def candle_wick(Trade_Direction, Close, Open, High, Low, SL, TP, TP_choice, SL_choice):
    if Close[-5] < Close[-4] < Close[-3] and Close[-2] < Open[-2] and (
            High[-2] - Open[-2] + Close[-2] - Low[-2]) > 10 * (Open[-2] - Close[-2]) and Close[-1] < Close[-2]:
        ##3 green candles followed by a red candle with a huge wick
        Trade_Direction = 0
    elif Close[-5] > Close[-4] > Close[-3] and Close[-2] > Open[-2] and (
            High[-2] - Close[-2] + Open[-2] - Low[-2]) > 10 * (Close[-2] - Open[-2]) and Close[-1] > Close[-2]:
        ##3 red candles followed by a green candle with a huge wick
        Trade_Direction = 1
    stop_loss_val, take_profit_val = SetSLTP(-99, -99, Close, High, Low, Trade_Direction, SL, TP, TP_choice, SL_choice)
    return Trade_Direction, stop_loss_val, take_profit_val


def fibMACD(Trade_Direction, Close, Open, High, Low):
    stop_loss_val = 0
    take_profit_val = 0
    period = 100  ##Record peaks and troughs in last period timesteps
    MACD_signal = np.array(macd_signal(pd.Series(Close)))
    MACD = np.array(macd(pd.Series(Close)))
    Close_peaks = []  ##Store peak values
    location_peaks = []  ##store index of peak value , used for debugging
    Close_troughs = []  ##store trough values
    location_troughs = []  ##store index of peak trough , used for debugging
    #####################Find peaks & troughs in Close ##############################
    for i in range(len(High) - period, len(High) - 2):
        if High[i] > High[i - 1] and High[i] > High[i + 1] and High[i] > High[i - 2] and High[i] > High[i + 2]:
            ##Weve found a peak:
            Close_peaks.append(High[i])
            location_peaks.append(i)
        elif Low[i] < Low[i - 1] and Low[i] < Low[i + 1] and Low[i] < Low[i - 2] and Low[i] < Low[i + 2]:
            ##Weve found a trough:
            Close_troughs.append(Low[i])
            location_troughs.append(i)

    EMA200 = np.array(sma_indicator(pd.Series(Close), window=200))
    trend = -99  ##indicate the direction of trend
    if Close[-1] < EMA200[-1]:
        trend = 0
    elif Close[-1] > EMA200[-1]:
        trend = 1
    max_pos = -99
    min_pos = -99
    if trend == 1:
        ##Find the start and end of the pullback
        max_Close = -9999999
        min_Close = 9999999
        max_flag = 0
        min_flag = 0
        for i in range(len(Close_peaks) - 1, -1, -1):
            if Close_peaks[i] > max_Close and max_flag < 2:
                max_Close = Close_peaks[i]
                max_pos = location_peaks[i]
                max_flag = 0
            elif max_flag == 2:
                break
            else:
                max_flag += 1
        ##Find the start and end of the pullback
        startpoint = -99
        for i in range(len(location_troughs)):
            if location_troughs[i] < max_pos:
                startpoint = i
            else:
                break
        for i in range(startpoint, -1, -1):
            if Close_troughs[i] < min_Close and min_flag < 2:
                min_Close = Close_troughs[i]
                min_pos = location_troughs[i]
                min_flag = 0
            elif min_flag == 2:
                break
            else:
                min_flag += 1
        ##fibonacci levels
        fib_level_0 = max_Close
        fib_level_1 = max_Close - .236 * (max_Close - min_Close)
        fib_level_2 = max_Close - .382 * (max_Close - min_Close)
        fib_level_3 = max_Close - .5 * (max_Close - min_Close)
        fib_level_4 = max_Close - .618 * (max_Close - min_Close)
        fib_level_5 = max_Close - .786 * (max_Close - min_Close)
        fib_level_6 = min_Close

        ##Take profit targets, Don't think this is configured properly so maybe have a look at fibonacci extensions and fix here, Right hand side is ment to be the corresponding extension level
        fib_retracement_level_1 = fib_level_0 + 1.236 * (max_Close - min_Close) - Close[
            -1]  ##target max_Close+1.236*(max_Close - min_Close)
        fib_retracement_level_2 = fib_level_0 + 1.382 * (max_Close - min_Close) - Close[-1]
        fib_retracement_level_3 = fib_level_0 + 1.5 * (max_Close - min_Close) - Close[-1]
        fib_retracement_level_4 = fib_level_0 + 1.618 * (max_Close - min_Close) - Close[-1]
        fib_retracement_level_5 = fib_level_0 + 1.786 * (max_Close - min_Close) - Close[-1]
        fib_retracement_level_6 = fib_level_0 + 2 * (max_Close - min_Close) - Close[-1]

        ## fib_level_0>Low[-3]>fib_level_1: recent low was between two of our levels
        ## Close[-4]>fib_level_1 and Close[-5]>fib_level_1 and Close[-6]>fib_level_1: Ensure the bottom level was respected  ie. no recent close below it
        if fib_level_0 > Low[-3] > fib_level_1 and Close[-4] > fib_level_1 and Close[-5] > fib_level_1 and Close[
            -6] > fib_level_1:
            if Close[-3] < Open[-3] < Close[-2] < Close[-1] and (
                    (MACD_signal[-2] < MACD[-2] or MACD_signal[-3] < MACD[-3]) and MACD_signal[-1] > MACD[
                -1]):  ##Bullish Engulfing Candle and cross up on MACD
                # print("level 1")
                Trade_Direction = 1  ##signal a buy
                take_profit_val = fib_retracement_level_1  ##target the corresponding extensiuon level
                stop_loss_val = Close[-1] - fib_level_1 * 1.0001  ##stoploss below bottom level with a bit extra
        elif fib_level_1 > Low[-3] > fib_level_2 and Close[-4] > fib_level_2 and Close[-5] > fib_level_2 and Close[
            -6] > fib_level_2:
            if Close[-3] < Open[-3] < Close[-2] < Close[-1] and (
                    (MACD_signal[-2] < MACD[-2] or MACD_signal[-3] < MACD[-3]) and MACD_signal[-1] > MACD[
                -1]):  ##Bullish Engulfing Candle and cross up on MACD
                # print("level 1")
                Trade_Direction = 1  ##signal a buy
                take_profit_val = fib_retracement_level_2
                stop_loss_val = Close[-1] - fib_level_2 * 1.0001

        elif fib_level_2 > Low[-2] > fib_level_3 and Close[-3] > fib_level_3 and Close[-4] > fib_level_3 and Close[
            -5] > fib_level_3:
            if Close[-2] < Open[-2] < Close[-1] < Close[-1] and (
                    (MACD_signal[-2] < MACD[-2] or MACD_signal[-3] < MACD[-3]) and MACD_signal[-1] > MACD[
                -1]):  ##Bullish Engulfing Candle and cross up on MACD
                # print("level 2")
                Trade_Direction = 1  ##signal a buy
                take_profit_val = fib_retracement_level_3
                stop_loss_val = Close[-1] - fib_level_3 * 1.0001

        elif fib_level_3 > Low[-2] > fib_level_4 and Close[-3] > fib_level_4 and Close[-4] > fib_level_4 and Close[
            -5] > fib_level_4:
            if Close[-2] < Open[-2] < Close[-1] < Close[-1] and (
                    (MACD_signal[-2] < MACD[-2] or MACD_signal[-3] < MACD[-3]) and MACD_signal[-1] > MACD[
                -1]):  ##Bullish Engulfing Candle and cross up on MACD
                # print("level 3")
                Trade_Direction = 1  ##signal a buy
                take_profit_val = fib_retracement_level_4
                stop_loss_val = Close[-1] - fib_level_4 * 1.0001
        elif fib_level_4 > Low[-2] > fib_level_5 and Close[-3] > fib_level_5 and Close[-4] > fib_level_5 and Close[
            -5] > fib_level_5:
            if Close[-2] < Open[-2] < Close[-1] < Close[-1] and (
                    (MACD_signal[-2] < MACD[-2] or MACD_signal[-3] < MACD[-3]) and MACD_signal[-1] > MACD[
                -1]):  ##Bullish Engulfing Candle and cross up on MACD
                # print("level 4")
                Trade_Direction = 1  ##signal a buy
                take_profit_val = fib_retracement_level_5
                stop_loss_val = Close[-1] - fib_level_5 * 1.0001
        elif fib_level_5 > Low[-2] > fib_level_6 and Close[-3] > fib_level_6 and Close[-4] > fib_level_6 and Close[
            -5] > fib_level_6:
            if Close[-2] < Open[-2] < Close[-1] < Close[-1] and (
                    (MACD_signal[-2] < MACD[-2] or MACD_signal[-3] < MACD[-3]) and MACD_signal[-1] > MACD[
                -1]):  ##Bullish Engulfing Candle and cross up on MACD
                # print("level 5")
                Trade_Direction = 1  ##signal a buy
                take_profit_val = fib_retracement_level_6
                stop_loss_val = Close[-1] - fib_level_6 * 1.0001

    elif trend == 0:
        ##Find the start and end of the pullback
        max_Close = -9999999
        min_Close = 9999999
        max_flag = 0
        min_flag = 0
        for i in range(len(Close_troughs) - 1, -1, -1):
            if Close_troughs[i] < min_Close and min_flag < 2:
                min_Close = Close_troughs[i]
                min_pos = location_troughs[i]
                min_flag = 0
            elif min_flag == 2:
                break
            else:
                min_flag += 1

        ##Find the start and end of the pullback
        startpoint = -99
        for i in range(len(location_peaks)):
            if location_peaks[i] < min_pos:
                startpoint = i
            else:
                break
        for i in range(startpoint, -1, -1):
            if Close_peaks[i] > max_Close and max_flag < 2:
                max_Close = Close_peaks[i]
                max_pos = location_peaks[i]
                max_flag = 0
            elif max_flag == 2:
                break
            else:
                max_flag += 1
        ##fibonacci levels
        fib_level_0 = min_Close
        fib_level_1 = min_Close + .236 * (max_Close - min_Close)
        fib_level_2 = min_Close + .382 * (max_Close - min_Close)
        fib_level_3 = min_Close + .5 * (max_Close - min_Close)
        fib_level_4 = min_Close + .618 * (max_Close - min_Close)
        fib_level_5 = min_Close + .786 * (max_Close - min_Close)
        fib_level_6 = max_Close

        ##Take profit targets, Don't think this is configured properly so maybe have a look at fibonacci extensions and fix here, Right hand side is ment to be the corresponding extension level
        fib_retracement_level_1 = Close[-1] - (fib_level_0 + 1.236 * (max_Close - min_Close))
        fib_retracement_level_2 = Close[-1] - (fib_level_0 + 1.382 * (max_Close - min_Close))
        fib_retracement_level_3 = Close[-1] - (fib_level_0 + 1.5 * (max_Close - min_Close))
        fib_retracement_level_4 = Close[-1] - (fib_level_0 + 1.618 * (max_Close - min_Close))
        fib_retracement_level_5 = Close[-1] - (fib_level_0 + 1.786 * (max_Close - min_Close))
        fib_retracement_level_6 = Close[-1] - (fib_level_0 + 2 * (max_Close - min_Close))

        ## fib_level_0 < High[-3] < fib_level_1: recent low was between two of our levels
        ## Close[-4] < fib_level_1 and Close[-5] < fib_level_1 and Close[-6] < fib_level_1: Ensure the Top level was respected, ie no recent close above it
        if fib_level_0 < High[-3] < fib_level_1 and Close[-4] < fib_level_1 and Close[-5] < fib_level_1 and Close[
            -6] < fib_level_1:
            if Close[-3] > Open[-3] > Close[-2] > Close[-1] and (
                    (MACD_signal[-2] > MACD[-2] or MACD_signal[-3] > MACD[-3]) and MACD_signal[-1] < MACD[
                -1]):  ##Bearish Engulfing Candle and cross down on MACD
                # print("level 1")
                Trade_Direction = 0  ##signal a sell
                take_profit_val = fib_retracement_level_1  ##target corresponding extension level
                stop_loss_val = fib_level_1 * 1.0001 - Close[-1]  ##stoploss above Top level with a bit extra
        elif fib_level_1 < High[-3] < fib_level_2 and Close[-4] < fib_level_2 and Close[-5] < fib_level_2 and Close[
            -6] < fib_level_2:
            if Close[-3] > Open[-3] > Close[-2] > Close[-1] and (
                    (MACD_signal[-2] > MACD[-2] or MACD_signal[-3] > MACD[-3]) and MACD_signal[-1] < MACD[
                -1]):  ##Bearish Engulfing Candle and cross down on MACD
                # print("level 1")
                Trade_Direction = 0  ##signal a sell
                take_profit_val = fib_retracement_level_2
                stop_loss_val = fib_level_2 * 1.0001 - Close[-1]
        elif fib_level_2 < High[-3] < fib_level_3 and Close[-4] < fib_level_3 and Close[-5] < fib_level_3 and Close[
            -6] < fib_level_3:
            if Close[-3] > Open[-3] > Close[-2] > Close[-1] and (
                    (MACD_signal[-2] > MACD[-2] or MACD_signal[-3] > MACD[-3]) and MACD_signal[-1] < MACD[
                -1]):  ##Bearish Engulfing Candle and cross down on MACD
                # print("level 1")
                Trade_Direction = 0  ##signal a sell
                take_profit_val = fib_retracement_level_3
                stop_loss_val = fib_level_3 * 1.0001 - Close[-1]
        elif fib_level_3 < High[-3] < fib_level_4 and Close[-4] < fib_level_4 and Close[-5] < fib_level_4 and Close[
            -6] < fib_level_4:
            if Close[-3] > Open[-3] > Close[-2] > Close[-1] and (
                    (MACD_signal[-2] > MACD[-2] or MACD_signal[-3] > MACD[-3]) and MACD_signal[-1] < MACD[
                -1]):  ##Bearish Engulfing Candle and cross down on MACD
                # print("level 1")
                Trade_Direction = 0  ##signal a sell
                take_profit_val = fib_retracement_level_4
                stop_loss_val = fib_level_4 * 1.0001 - Close[-1]
        elif fib_level_4 < High[-3] < fib_level_5 and Close[-4] < fib_level_5 and Close[-5] < fib_level_5 and Close[
            -6] < fib_level_5:
            if Close[-3] > Open[-3] > Close[-2] > Close[-1] and (
                    (MACD_signal[-2] > MACD[-2] or MACD_signal[-3] > MACD[-3]) and MACD_signal[-1] < MACD[
                -1]):  ##Bearish Engulfing Candle and cross down on MACD
                # print("level 1")
                Trade_Direction = 0  ##signal a sell
                take_profit_val = fib_retracement_level_5
                stop_loss_val = fib_level_5 * 1.0001 - Close[-1]
        elif fib_level_5 < High[-3] < fib_level_6 and Close[-4] < fib_level_6 and Close[-5] < fib_level_6 and Close[
            -6] < fib_level_6:
            if Close[-3] > Open[-3] > Close[-2] > Close[-1] and (
                    (MACD_signal[-2] > MACD[-2] or MACD_signal[-3] > MACD[-3]) and MACD_signal[-1] < MACD[
                -1]):  ##Bearish Engulfing Candle and cross down on MACD
                # print("level 1")
                Trade_Direction = 0  ##signal a sell
                take_profit_val = fib_retracement_level_6
                stop_loss_val = fib_level_6 * 1.0001 - Close[-1]

    return Trade_Direction, stop_loss_val, take_profit_val


def goldenCross(Trade_Direction, Close, High, Low, SL, TP, TP_choice, SL_choice):
    EMA100 = np.array(ema_indicator(pd.Series(Close), window=100))
    EMA50 = np.array(ema_indicator(pd.Series(Close), window=50))
    EMA20 = np.array(ema_indicator(pd.Series(Close), window=20))
    RSI = np.array(rsi(pd.Series(Close)))
    if Close[-1] > EMA100[-1] and RSI[-1] > 50:
        ##looking for long entries
        if (EMA20[-2] < EMA50[-2] and EMA20[-1] > EMA50[-1]) or (EMA20[-3] < EMA50[-3] and EMA20[-1] > EMA50[-1]) or (
                EMA20[-4] < EMA50[-4] and EMA20[-1] > EMA50[-1]):
            ##Cross up occured
            Trade_Direction = 1  ##buy
    elif Close[-1] < EMA100[-1] and RSI[-1] < 50:
        ##looking for short entries
        if (EMA20[-2] > EMA50[-2] and EMA20[-1] < EMA50[-1]) or (EMA20[-3] > EMA50[-3] and EMA20[-1] < EMA50[-1]) or (
                EMA20[-4] > EMA50[-4] and EMA20[-1] < EMA50[-1]):
            ##Cross up occured
            Trade_Direction = 0  ##Sell
    stop_loss_val, take_profit_val = SetSLTP(-99, -99, Close, High, Low, Trade_Direction, SL, TP, TP_choice, SL_choice)
    return Trade_Direction, stop_loss_val, take_profit_val


def StochRSIMACD(Trade_Direction, Close, High, Low, SL, TP, TP_choice, SL_choice):
    CloseS = pd.Series(Close)
    HighS = pd.Series(High)
    LowS = pd.Series(Low)
    fastd = np.array(stoch(close=CloseS, high=HighS, low=LowS))
    fastk = np.array(stoch_signal(close=CloseS, high=HighS, low=LowS))
    RSI = np.array(rsi(CloseS))
    MACD = np.array(macd(CloseS))
    macdsignal = np.array(macd_signal(CloseS))
    if ((fastd[-1] < 20 and fastk[-1] < 20 and RSI[-1] > 50 and MACD[-1] > macdsignal[-1] and MACD[-2] < macdsignal[
        -2]) or
            (fastd[-2] < 20 and fastk[-2] < 20 and RSI[-1] > 50 and MACD[-1] > macdsignal[-1] and MACD[-3] < macdsignal[
                -3] and fastd[-1] < 80 and fastk[-1] < 80) or
            (fastd[-3] < 20 and fastk[-3] < 20 and RSI[-1] > 50 and MACD[-1] > macdsignal[-1] and MACD[-2] < macdsignal[
                -2] and fastd[-1] < 80 and fastk[-1] < 80) or
            (fastd[-4] < 20 and fastk[-4] < 20 and RSI[-1] > 50 and MACD[-1] > macdsignal[-1] and MACD[-3] < macdsignal[
                -3] and fastd[-1] < 80 and fastk[-1] < 80)):
        Trade_Direction = 1
    elif ((fastd[-1] > 80 and fastk[-1] > 80 and RSI[-1] < 50 and MACD[-1] < macdsignal[-1] and MACD[-2] > macdsignal[
        -2]) or
          (fastd[-2] > 80 and fastk[-2] > 80 and RSI[-1] < 50 and MACD[-1] < macdsignal[-1] and MACD[-3] > macdsignal[
              -3] and fastd[-1] > 20 and fastk[-1] > 20) or
          (fastd[-3] > 80 and fastk[-3] > 80 and RSI[-1] < 50 and MACD[-1] < macdsignal[-1] and MACD[-2] > macdsignal[
              -2] and fastd[-1] > 20 and fastk[-1] > 20) or
          (fastd[-4] > 80 and fastk[-4] > 80 and RSI[-1] < 50 and MACD[-1] < macdsignal[-1] and MACD[-3] > macdsignal[
              -3] and fastd[-1] > 20 and fastk[-1] > 20)):
        Trade_Direction = 0
    stop_loss_val, take_profit_val = SetSLTP(-99, -99, Close, High, Low, Trade_Direction, SL, TP, TP_choice, SL_choice)
    return Trade_Direction, stop_loss_val, take_profit_val


##############################################################################################################################
##############################################################################################################################
##############################################################################################################################


def tripleEMA(Close, High, Low, Trade_Direction, SL, TP, TP_choice, SL_choice):
    EMA3 = np.array(ema_indicator(pd.Series(Close), window=5))
    EMA6 = np.array(ema_indicator(pd.Series(Close), window=20))
    EMA9 = np.array(ema_indicator(pd.Series(Close), window=50))

    if EMA3[-5] > EMA6[-5] and EMA3[-5] > EMA9[-5] \
            and EMA3[-4] > EMA6[-4] and EMA3[-4] > EMA9[-4] \
            and EMA3[-3] > EMA6[-3] and EMA3[-3] > EMA9[-3] \
            and EMA3[-2] > EMA6[-2] and EMA3[-2] > EMA9[-2] \
            and EMA3[-1] < EMA6[-1] and EMA3[-1] < EMA9[-1]:
        Trade_Direction = 0
    if EMA3[-5] < EMA6[-5] and EMA3[-5] < EMA9[-5] \
            and EMA3[-4] < EMA6[-4] and EMA3[-4] < EMA9[-4] \
            and EMA3[-3] < EMA6[-3] and EMA3[-3] < EMA9[-3] \
            and EMA3[-2] < EMA6[-2] and EMA3[-2] < EMA9[-2] \
            and EMA3[-1] > EMA6[-1] and EMA3[-1] > EMA9[-1]:
        Trade_Direction = 1
    stop_loss_val, take_profit_val = SetSLTP(-99, -99, Close, High, Low, Trade_Direction, SL, TP, TP_choice, SL_choice)
    return Trade_Direction, stop_loss_val, take_profit_val


def heikin_ashi_ema2(Close, OpenStream_H, High_H, Low_H, Close_H, High, Low, Trade_Direction, CurrentPos, Close_pos, SL,
                     TP, TP_choice, SL_choice):
    if CurrentPos == -99:
        Trade_Direction = -99
        fastd = np.array(stochrsi_d(pd.Series(Close)))
        fastk = np.array(stochrsi_k(pd.Series(Close)))
        EMA200 = np.array(ema_indicator(pd.Series(Close), window=200))

        short_threshold = .7  ##If RSI falls below this don't open any shorts
        long_threshold = .3  ##If RSI goes above this don't open any longs

        ##Check Most recent Candles to see if we got a cross down and we are below 200EMA
        if fastk[-2] > fastd[-2] and fastk[-1] < fastd[-1] and Close_H[-1] < EMA200[-1]:
            for i in range(10, 2, -1):
                ##Find Bearish Meta Candle
                if Close_H[-i] < OpenStream_H[-i] and OpenStream_H[-i] == High_H[-i]:
                    for j in range(i, 2, -1):
                        ##Find cross below EMA200
                        if Close_H[-j] > EMA200[-j] and Close_H[-j + 1] < EMA200[-j + 1] and OpenStream_H[-j] > Close_H[
                            -j]:
                            ##Now look for Overbought signal
                            flag = 1
                            for r in range(j, 0, -1):
                                if fastd[-r] < short_threshold or fastk[-r] < short_threshold:
                                    flag = 0
                            if flag:
                                ##Open a trade
                                Trade_Direction = 0
                                break  ##break out of current loop
                    if Trade_Direction == 0:
                        break
        ##Check Most recent Candles to see if we got a cross up and we are above 200EMA
        elif fastk[-2] < fastd[-2] and fastk[-1] > fastd[-1] and Close_H[-1] > EMA200[-1]:
            for i in range(10, 2, -1):
                ##Find Bullish Meta Candle
                if Close_H[-i] > OpenStream_H[-i] and OpenStream_H[-i] == Low_H[-i]:
                    for j in range(i, 2, -1):
                        ##Find cross above EMA200
                        if Close_H[-j] < EMA200[-j] and Close_H[-j + 1] > EMA200[-j + 1] and OpenStream_H[-j] < Close_H[
                            -j]:
                            ##Now look for OverSold signal
                            flag = 1
                            for r in range(j, 0, -1):
                                if fastd[-r] > long_threshold or fastk[-r] > long_threshold:
                                    flag = 0
                            if flag:
                                ##Open a trade
                                Trade_Direction = 1
                                break  ##break out of current loop
                    if Trade_Direction == 1:
                        break

    elif CurrentPos == 1 and Close_H[-1] < OpenStream_H[-1]:
        Close_pos = 1
    elif CurrentPos == 0 and Close_H[-1] > OpenStream_H[-1]:
        Close_pos = 1
    else:
        Close_pos = 0
    stop_loss_val, take_profit_val = SetSLTP(-99, -99, Close, High, Low, Trade_Direction, SL, TP, TP_choice, SL_choice)
    return Trade_Direction, stop_loss_val, take_profit_val, Close_pos


def heikin_ashi_ema(Close, OpenStream_H, Close_H, Trade_Direction, CurrentPos, Close_pos, High, Low, SL, TP, TP_choice,
                    SL_choice):
    if CurrentPos == -99:
        Trade_Direction = -99
        fastd = np.array(stochrsi_d(pd.Series(Close)))
        fastk = np.array(stochrsi_k(pd.Series(Close)))
        EMA200 = np.array(ema_indicator(pd.Series(Close), window=200))

        short_threshold = .8  ##If RSI falls below this don't open any shorts
        long_threshold = .2  ##If RSI goes above this don't open any longs
        ##look for shorts
        if fastk[-1] > short_threshold and fastd[-1] > short_threshold:
            ##Check last 10 candles, a bit overkill
            for i in range(10, 2, -1):
                if fastd[-i] >= .8 and fastk[-i] >= .8:
                    ##both oscillators in the overbought position
                    for j in range(i, 2, -1):
                        ##now check if we get a cross on the in the next few candles
                        if fastk[-j] > fastd[-j] and fastk[-j + 1] < fastd[-j + 1]:
                            flag = 1
                            for r in range(j, 2, -1):
                                ##we passed the threshold
                                if fastk[r] < short_threshold or fastd[r] < short_threshold:
                                    flag = 0
                                    break
                            ##Cross down on the k and d lines, look for the candle stick pattern
                            if Close_H[-3] > EMA200[-3] and Close_H[-2] < EMA200[-2] and flag:
                                ##closed below 200EMA
                                if Close_H[-1] < OpenStream_H[-1]:
                                    ##bearish candle
                                    ##all conditions met so open a short
                                    Trade_Direction = 0
                                else:
                                    break  ##break out of the current for loop
                            else:
                                break  ##break out of the current for loop
        ##Look for longs
        elif fastk[-1] < long_threshold and fastd[-1] < long_threshold:
            ##Check last 10 candles, a bit overkill
            for i in range(10, 2, -1):
                if fastd[-i] <= .2 and fastk[-i] <= .2:
                    ##both oscillators in the overbought position
                    for j in range(i, 2, -1):
                        ##now check if we get a cross on the in the next few candles
                        if fastk[-j] < fastd[-j] and fastk[-j + 1] > fastd[-j + 1] and fastk[-1] < long_threshold and \
                                fastd[-1] < long_threshold:
                            flag = 1
                            for r in range(j, 2, -1):
                                ##we passed the threshold
                                if fastk[r] > long_threshold or fastd[r] > long_threshold:
                                    flag = 0
                                    break
                            ##Cross up on the k and d lines, look for the candle stick pattern
                            ##candle crosses 200EMA
                            if Close_H[-3] < EMA200[-3] and Close_H[-2] > EMA200[-2] and flag:
                                ##closed above 200EMA
                                if Close_H[-1] > OpenStream_H[-1]:
                                    ##bullish candle
                                    ##all conditions met so open a long
                                    Trade_Direction = 1
                                else:
                                    break  ##break out of the current for loop
                            else:
                                break  ##break out of the current for loop
    elif CurrentPos == 1 and Close_H[-1] < OpenStream_H[-1]:
        Close_pos = 1
    elif CurrentPos == 0 and Close_H[-1] > OpenStream_H[-1]:
        Close_pos = 1
    else:
        Close_pos = 0
    stop_loss_val, take_profit_val = SetSLTP(-99, -99, Close, High, Low, Trade_Direction, SL, TP, TP_choice, SL_choice)
    return Trade_Direction, stop_loss_val, take_profit_val, Close_pos


def tripleEMAStochasticRSIATR(Close, High, Low, Trade_Direction, SL, TP, TP_choice, SL_choice):
    Close = np.array(Close)
    EMA50 = np.array(ema_indicator(pd.Series(Close), window=50))
    EMA14 = np.array(ema_indicator(pd.Series(Close), window=14))
    EMA8 = np.array(ema_indicator(pd.Series(Close), window=8))
    fastd = np.array(stochrsi_d(pd.Series(Close)))
    fastk = np.array(stochrsi_k(pd.Series(Close)))
    ##buy signal
    if (Close[-1] > EMA8[-1] > EMA14[-1] > EMA50[-1]) and (
            (fastk[-1] > fastd[-1]) and (fastk[-2] < fastd[-2])):  # and (fastk[-1]<80 and fastd[-1]<80):
        Trade_Direction = 1
    elif (Close[-1] < EMA8[-1] < EMA14[-1] < EMA50[-1]) and (
            (fastk[-1] < fastd[-1]) and (fastk[-2] > fastd[-2])):  # and (fastk[-1]>20 and fastd[-1]>20):
        Trade_Direction = 0

    stop_loss_val, take_profit_val = SetSLTP(-99, -99, Close, High, Low, Trade_Direction, SL, TP, TP_choice, SL_choice)
    return Trade_Direction, stop_loss_val, take_profit_val


##############################################################################################################################
##############################################################################################################################
##############################################################################################################################


def RSIStochEMA(Trade_Direction, Close, High, Low, signal1, currentPos, SL, TP, TP_choice, SL_choice):
    period = 60
    CloseS = pd.Series(Close)
    Close = np.array(Close)
    # High = np.array(High)
    # Low = np.array(Low)
    fastk = np.array(stoch_signal(pd.Series(High), pd.Series(Low), pd.Series(Close)))
    fastd = np.array(stoch(pd.Series(High), pd.Series(Low), pd.Series(Close)))
    RSI = np.array(rsi(CloseS))
    EMA200 = np.array(ema_indicator(CloseS, window=200))
    peaks_RSI = []
    corresponding_Close_peaks = []
    location_peaks = []
    troughs_RSI = []
    corresponding_Close_troughs = []
    location_troughs = []
    #####################Find peaks & troughs in RSI ##############################
    for i in range(len(RSI) - period, len(RSI) - 2):
        if RSI[i] > RSI[i - 1] and RSI[i] > RSI[i + 1] and RSI[i] > RSI[i - 2] and RSI[i] > RSI[i + 2]:
            ##Weve found a peak:
            peaks_RSI.append(RSI[i])
            corresponding_Close_peaks.append(Close[i])
            location_peaks.append(i)
        elif RSI[i] < RSI[i - 1] and RSI[i] < RSI[i + 1] and RSI[i] < RSI[i - 2] and RSI[i] < RSI[i + 2]:
            ##Weve found a trough:
            troughs_RSI.append(RSI[i])
            corresponding_Close_troughs.append(Close[i])
            location_troughs.append(i)
    ##Lower High Price & Higher High RSI => Bearish Divergence
    ##Higher Low Price & Lower low RSI => Bullish Divergence
    length = 0
    if len(peaks_RSI) > len(troughs_RSI):
        length = len(peaks_RSI)
    else:
        length = len(troughs_RSI)
    loc1 = -99
    loc2 = -99
    if length != 0:
        for i in range(length - 1):
            if i < len(peaks_RSI):
                ##Check for hidden Bearish Divergence
                if peaks_RSI[i] < peaks_RSI[-1] and corresponding_Close_peaks[i] > corresponding_Close_peaks[-1] and \
                        peaks_RSI[-1] - peaks_RSI[i] > 1:
                    for j in range(i + 1, len(peaks_RSI) - 1):
                        if peaks_RSI[j] > peaks_RSI[i]:
                            break
                        elif j == len(peaks_RSI) - 2:
                            loc1 = location_peaks[i]

            if i < len(troughs_RSI):
                ##Check for hidden Bullish Divergence
                if troughs_RSI[i] > troughs_RSI[-1] and corresponding_Close_troughs[i] < corresponding_Close_troughs[
                    -1] and troughs_RSI[i] - troughs_RSI[-1] > 1:
                    for j in range(i + 1, len(troughs_RSI) - 1):
                        if troughs_RSI[j] < troughs_RSI[i]:
                            break
                        elif j == len(troughs_RSI) - 2:
                            loc2 = location_troughs[i]
        if loc1 == loc2:
            signal1 = -99
        elif loc1 > loc2:  # and 300-loc1<15:
            signal1 = 0
            # print(300-loc1)
        else:  # 300-loc2<15:
            # print(300-loc2)
            signal1 = 1
        '''else:
            signal1=-99'''

    ##Bullish Divergence
    if signal1 == 1 and (fastk[-1] > fastd[-1] and (fastk[-2] < fastd[-2] or fastk[-3] < fastd[-3])) and Close[-1] > \
            EMA200[-1]:
        Trade_Direction = 1
        signal1 = -99

    ##Bearish Divergence
    elif signal1 == 0 and (fastk[-1] < fastd[-1] and (fastk[-2] > fastd[-2] or fastk[-3] > fastd[-3])) and Close[-1] < \
            EMA200[-1]:
        Trade_Direction = 0
        signal1 = -99

    if currentPos != -99:
        signal1 = -99
        Trade_Direction = -99
    stop_loss_val, take_profit_val = SetSLTP(-99, -99, Close, High, Low, Trade_Direction, SL, TP, TP_choice, SL_choice)
    return Trade_Direction, signal1, stop_loss_val, take_profit_val


##############################################################################################################

def stochBB(Trade_Direction, Close, High, Low, SL, TP, TP_choice, SL_choice):
    fastd = np.array(stochrsi_d(pd.Series(Close)))
    fastk = np.array(stochrsi_k(pd.Series(Close)))

    # print(fastd[-1],fastk[-1])
    percent_B = np.array(bollinger_pband(pd.Series(Close)))
    percent_B1 = percent_B[-1]
    percent_B2 = percent_B[-2]
    percent_B3 = percent_B[-3]
    # print(percent_B)

    if fastk[-1] < .2 and fastd[-1] < .2 and (fastk[-1] > fastd[-1] and fastk[-2] < fastd[-2]) and (
            percent_B1 < 0 or percent_B2 < 0 or percent_B3 < 0):  # or percent_B3<0):# or percent_B2<.05):
        Trade_Direction = 1
    elif fastk[-1] > .8 and fastd[-1] > .8 and (fastk[-1] < fastd[-1] and fastk[-2] > fastd[-2]) and (
            percent_B1 > 1 or percent_B2 > 1 or percent_B3 > 1):  # or percent_B3>1):# or percent_B2>1):
        Trade_Direction = 0
    stop_loss_val, take_profit_val = SetSLTP(-99, -99, Close, High, Low, Trade_Direction, SL, TP, TP_choice, SL_choice)
    return Trade_Direction, stop_loss_val, take_profit_val


def breakout(Trade_Direction, Close, VolumeStream, High, Low, SL, TP, TP_choice, SL_choice):
    invert = 0  ## switch shorts and longs, basically fakeout instead of breakout
    # if symbol=='BTCUSDT' or symbol=='ETHUSDT':
    #    invert=0
    CloseS = pd.Series(Close).pct_change()
    Volume = pd.Series(VolumeStream[:-1])
    max_Close = CloseS.iloc[:-1].rolling(10).max()
    min_Close = CloseS.iloc[:-1].rolling(10).min()
    max_Vol = Volume.rolling(10).max()
    if invert:
        if CloseS.iloc[-1] > max_Close.iloc[-1] and VolumeStream[-1] > max_Vol.iloc[-1]:
            Trade_Direction = 0
        elif CloseS.iloc[-1] < min_Close.iloc[-1] and VolumeStream[-1] > max_Vol.iloc[-1]:
            Trade_Direction = 1
    else:
        if CloseS.iloc[-1] > max_Close.iloc[-1] and VolumeStream[-1] > max_Vol.iloc[-1]:
            Trade_Direction = 1
        elif CloseS.iloc[-1] < min_Close.iloc[-1] and VolumeStream[-1] > max_Vol.iloc[-1]:
            Trade_Direction = 0

    stop_loss_val, take_profit_val = SetSLTP(-99, -99, Close, High, Low, Trade_Direction, SL, TP, TP_choice, SL_choice)
    return Trade_Direction, stop_loss_val, take_profit_val


def fakeout(Trade_Direction, Close, VolumeStream, High, Low, SL, TP, TP_choice, SL_choice):
    invert = 1
    # if symbol == 'BTCUSDT' or symbol == 'ETHUSDT':
    #    invert = 0
    Close = pd.Series(Close)  # .pct_change() ##get size of bars in a percentage
    Volume = pd.Series(VolumeStream[:-1])
    max_Close = Close.iloc[:-1].rolling(15).max()
    min_Close = Close.iloc[:-1].rolling(15).min()
    max_Vol = Volume.rolling(15).max()
    if invert:
        if Close.iloc[-1] > max_Close.iloc[-1] and VolumeStream[-1] < max_Vol.iloc[-1]:
            Trade_Direction = 0
        elif Close.iloc[-1] < min_Close.iloc[-1] and VolumeStream[-1] < max_Vol.iloc[-1]:
            Trade_Direction = 1
    else:
        if Close.iloc[-1] > max_Close.iloc[-1] and VolumeStream[-1] < max_Vol.iloc[-1]:
            Trade_Direction = 1
        elif Close.iloc[-1] < min_Close.iloc[-1] and VolumeStream[-1] < max_Vol.iloc[-1]:
            Trade_Direction = 0
    stop_loss_val, take_profit_val = SetSLTP(-99, -99, Close, High, Low, Trade_Direction, SL, TP, TP_choice, SL_choice)
    return Trade_Direction, stop_loss_val, take_profit_val


def EMA_cross(Trade_Direction, Close, High, Low, SL, TP, TP_choice, SL_choice):
    EMA_short = np.array(ema_indicator(pd.Series(Close), window=5))
    EMA_long = np.array(ema_indicator(pd.Series(Close), window=20))

    if EMA_short[-5] > EMA_long[-5] \
            and EMA_short[-4] > EMA_long[-4] \
            and EMA_short[-3] > EMA_long[-3] \
            and EMA_short[-2] > EMA_long[-2] \
            and EMA_short[-1] < EMA_long[-1]:
        Trade_Direction = 0

    if EMA_short[-5] < EMA_long[-5] \
            and EMA_short[-4] < EMA_long[-4] \
            and EMA_short[-3] < EMA_long[-3] \
            and EMA_short[-2] < EMA_long[-2] \
            and EMA_short[-1] > EMA_long[-1]:
        Trade_Direction = 1

    stop_loss, take_profit = SetSLTP(-99, -99, Close, High, Low, Trade_Direction, SL, TP, TP_choice, SL_choice)
    return Trade_Direction, stop_loss, take_profit


'''def pairTrading(Trade_Direction,Close1,Close2,log=0,TPSL=0,percent_TP=0,percent_SL=0):
    new_Close = []
    
    #multiplier = Close1[0]/Close2[0]
    if not log:
        multiplier = (sm.OLS(Close1, Close2).fit()).params[0]
        for i in range(len(Close1)-30,len(Close1)):
            new_Close.append(Close1[i]-multiplier*Close2[i])
    else:
        log_close1 = []
        log_close2 = []
        for i in range(len(Close1)-30,len(Close1)):
            log_close1.append(math.log(Close1[i]))
            log_close2.append(math.log(Close2[i]))
        multiplier = (sm.OLS(log_close1, log_close2).fit()).params[0]
        for i in range(len(log_close1)):
            new_Close.append(log_close1[i] - multiplier * log_close2[i])
    BB =np.array(bollinger_pband(pd.Series(new_Close),window_dev=3))
    #BB1 = np.array(bollinger_hband(pd.Series(new_Close),window_dev=3))
    #BB2 = np.array(bollinger_lband(pd.Series(new_Close), window_dev=3))
    #SMA20 = np.array(bollinger_mavg(pd.Series(new_Close)))
    #print(BB[-1])
    if BB[-1]>1:
        Trade_Direction = [0,1]  # [1,0]
        
    elif BB[-1]<0:
        Trade_Direction = [1,0] # [0,1]
        
    return Trade_Direction,[9,9] #,Close1_TP,Close2_TP,Close1_SL,Close2_SL


def pairTrading_Crossover(Trade_Direction, Close1, Close2, CurrentPos, percent_SL=0):
    new_Close = []
    Close_pos=0
    Close1_SL = 0
    Close2_SL = 0
    multiplier = (sm.OLS(Close1, Close2).fit()).params[0]
    for i in range(len(Close1)-30,len(Close1)):
        new_Close.append(Close1[i]-multiplier*Close2[i])
    BB =np.array(bollinger_pband(pd.Series(new_Close),window_dev=3))
    SMA20 = np.array(bollinger_mavg(pd.Series(new_Close)))
    if BB[-1]>1:
        Trade_Direction = [0,1]
        Close1_SL = Close1[-1] * percent_SL
        Close2_SL = Close2[-1] * percent_SL
    elif BB[-1]<0:
        Trade_Direction = [1,0]
        Close1_SL = Close1[-1] * percent_SL
        Close2_SL = Close2[-1] * percent_SL
    if CurrentPos!=-99:
        if (new_Close[-1]>SMA20[-1] and (new_Close[-2]<SMA20[-2] or new_Close[-3]<SMA20[-3])) or (new_Close[-1]<SMA20[-1] and (new_Close[-2]>SMA20[-2] or new_Close[-3]>SMA20[-3])):
            ##Price has crossed up or down over the Moving average so close the position
            Close_pos=1
    return Trade_Direction,Close1_SL,Close2_SL,Close_pos'''


def SetSLTP(stop_loss_val, take_profit_val, Close, High, Low, Trade_Direction, SL, TP, TP_choice, SL_choice):
    if TP_choice == '%':
        take_profit_val = (TP / 100) * Close[-1]
    if SL_choice == '%':
        stop_loss_val = (SL / 100) * Close[-1]

    if TP_choice == 'x (ATR)':
        ATR = np.array(average_true_range(pd.Series(High), pd.Series(Low), pd.Series(Close)))
        take_profit_val = TP * abs(ATR[-1])

    if SL_choice == 'x (ATR)':
        ATR = np.array(average_true_range(pd.Series(High), pd.Series(Low), pd.Series(Close)))
        stop_loss_val = SL * abs(ATR[-1])

    if TP_choice == 'x (Swing High/Low) level 1':
        high_swing = High[-1]
        Low_swing = Low[-1]
        high_flag = 0
        low_flag = 0
        j = -2
        while j > -len(High) + 1:
            if High[j] > high_swing and high_flag == 0:
                high_swing = High[j]
                if High[j - 1] < High[j] > High[j + 1]:
                    ##found a swing high level 1
                    high_flag = 1
            if Low[j] < Low_swing and low_flag == 0:
                Low_swing = Low[j]
                if Low[j - 1] > Low[j] < Low[j + 1]:
                    ##found a swing low level 1
                    low_flag = 1
            if (high_flag == 1 and Trade_Direction == 1) or (low_flag == 1 and Trade_Direction == 0):
                break
            j -= 1

        if Trade_Direction == 0:
            take_profit_val = TP * (Close[-1] - Low_swing)
        elif Trade_Direction == 1:
            take_profit_val = TP * (high_swing - Close[-1])

    if SL_choice == 'x (Swing High/Low) level 1':
        high_swing = High[-1]
        Low_swing = Low[-1]
        high_flag = 0
        low_flag = 0
        j = -2
        while j > -len(High) + 1:
            if High[j] > high_swing and high_flag == 0:
                high_swing = High[j]
                if High[j - 1] < High[j] > High[j + 1]:
                    ##found a swing high level 1
                    high_flag = 1
            if Low[j] < Low_swing and low_flag == 0:
                Low_swing = Low[j]
                if Low[j - 1] > Low[j] < Low[j + 1]:
                    ##found a swing low level 1
                    low_flag = 1
            if (high_flag == 1 and Trade_Direction == 1) or (low_flag == 1 and Trade_Direction == 0):
                break
            j -= 1

        if Trade_Direction == 0:
            stop_loss_val = SL * (high_swing - Close[-1])
        elif Trade_Direction == 1:
            stop_loss_val = SL * (Close[-1] - Low_swing)

    if TP_choice == 'x (Swing High/Low) level 2':
        high_swing = High[-1]
        Low_swing = Low[-1]
        high_flag = 0
        low_flag = 0
        j = -3
        while j > -len(High) + 2:
            if High[j] > high_swing and high_flag == 0:
                high_swing = High[j]
                if High[j - 1] < High[j] > High[j + 1] and High[j - 2] < High[j] > High[j + 2]:
                    ##found a swing high level 2
                    high_flag = 1
            if Low[j] < Low_swing and low_flag == 0:
                Low_swing = Low[j]
                if Low[j - 1] > Low[j] < Low[j + 1] and Low[j - 2] > Low[j] < Low[j + 2]:
                    ##found a swing low level 2
                    low_flag = 1
            if (high_flag == 1 and Trade_Direction == 1) or (low_flag == 1 and Trade_Direction == 0):
                break
            j -= 1

        if Trade_Direction == 0:
            take_profit_val = TP * (Close[-1] - Low_swing)
        elif Trade_Direction == 1:
            take_profit_val = TP * (high_swing - Close[-1])

    if SL_choice == 'x (Swing High/Low) level 2':
        high_swing = High[-1]
        Low_swing = Low[-1]
        high_flag = 0
        low_flag = 0
        j = -3
        while j > -len(High) + 2:
            if High[j] > high_swing and high_flag == 0:
                high_swing = High[j]
                if High[j - 1] < High[j] > High[j + 1] and High[j - 2] < High[j] > \
                        High[j + 2]:
                    ##found a swing high level 2
                    high_flag = 1
            if Low[j] < Low_swing and low_flag == 0:
                Low_swing = Low[j]
                if Low[j - 1] > Low[j] < Low[j + 1] and Low[j - 2] > Low[j] < Low[
                    j + 2]:
                    ##found a swing low level 2
                    low_flag = 1
            if (high_flag == 1 and Trade_Direction == 1) or (low_flag == 1 and Trade_Direction == 0):
                break
            j -= 1

        if Trade_Direction == 0:
            stop_loss_val = SL * (high_swing - Close[-1])
        elif Trade_Direction == 1:
            stop_loss_val = SL * (Close[-1] - Low_swing)

    if TP_choice == 'x (Swing High/Low) level 3':
        high_swing = High[-1]
        Low_swing = Low[-1]
        high_flag = 0
        low_flag = 0
        j = -4
        while j > -len(High) + 3:
            if High[j] > high_swing and high_flag == 0:
                high_swing = High[j]
                if High[j - 1] < High[j] > High[j + 1] and High[j - 2] < High[j] > \
                        High[j + 2] and High[j - 3] < High[j] > \
                        High[j + 3]:
                    ##found a swing high level 2
                    high_flag = 1
            if Low[j] < Low_swing and low_flag == 0:
                Low_swing = Low[j]
                if Low[j - 1] > Low[j] < Low[j + 1] and Low[j - 2] > Low[j] < Low[
                    j + 2] and Low[j - 3] > Low[j] < Low[
                    j + 3]:
                    ##found a swing low level 2
                    low_flag = 1
            if (high_flag == 1 and Trade_Direction == 1) or (low_flag == 1 and Trade_Direction == 0):
                break
            j -= 1

        if Trade_Direction == 0:
            take_profit_val = TP * (Close[-1] - Low_swing)
        elif Trade_Direction == 1:
            take_profit_val = TP * (high_swing - Close[-1])

    if SL_choice == 'x (Swing High/Low) level 3':
        high_swing = High[-1]
        Low_swing = Low[-1]
        high_flag = 0
        low_flag = 0
        j = -4
        while j > -len(High) + 3:
            if High[j] > high_swing and high_flag == 0:
                high_swing = High[j]
                if High[j - 1] < High[j] > High[j + 1] and High[j - 2] < High[j] > \
                        High[j + 2] and High[j - 3] < High[j] > \
                        High[j + 3]:
                    ##found a swing high level 2
                    high_flag = 1
            if Low[j] < Low_swing and low_flag == 0:
                Low_swing = Low[j]
                if Low[j - 1] > Low[j] < Low[j + 1] and Low[j - 2] > Low[j] < Low[
                    j + 2] and Low[j - 3] > Low[j] < Low[
                    j + 3]:
                    ##found a swing low level 2
                    low_flag = 1
            if (high_flag == 1 and Trade_Direction == 1) or (low_flag == 1 and Trade_Direction == 0):
                break
            j -= 1

        if Trade_Direction == 0:
            stop_loss_val = SL * (high_swing - Close[-1])
        elif Trade_Direction == 1:
            stop_loss_val = SL * (Close[-1] - Low_swing)

    if TP_choice == 'x (Swing Close) level 1':
        high_swing = Close[-1]
        Low_swing = Close[-1]
        high_flag = 0
        low_flag = 0
        j = -2
        while j > -len(Close) + 1:
            if Close[j] > high_swing and high_flag == 0:
                high_swing = Close[j]
                if Close[j - 1] < Close[j] > Close[j + 1]:
                    ##found a swing high level 1
                    high_flag = 1
            if Close[j] < Low_swing and low_flag == 0:
                Low_swing = Close[j]
                if Close[j - 1] > Close[j] < Close[j + 1]:
                    ##found a swing low level 1
                    low_flag = 1
            if (high_flag == 1 and Trade_Direction == 1) or (low_flag == 1 and Trade_Direction == 0):
                break
            j -= 1

        if Trade_Direction == 0:
            take_profit_val = TP * (Close[-1] - Low_swing)
        elif Trade_Direction == 1:
            take_profit_val = TP * (high_swing - Close[-1])

    if SL_choice == 'x (Swing Close) level 1':
        high_swing = Close[-1]
        Low_swing = Close[-1]
        high_flag = 0
        low_flag = 0
        j = -2
        while j > -len(Close) + 1:
            if Close[j] > high_swing and high_flag == 0:
                high_swing = Close[j]
                if Close[j - 1] < Close[j] > Close[j + 1]:
                    ##found a swing high level 1
                    high_flag = 1
            if Close[j] < Low_swing and low_flag == 0:
                Low_swing = Close[j]
                if Close[j - 1] > Close[j] < Close[j + 1]:
                    ##found a swing low level 1
                    low_flag = 1
            if (high_flag == 1 and Trade_Direction == 1) or (low_flag == 1 and Trade_Direction == 0):
                break
            j -= 1

        if Trade_Direction == 0:
            stop_loss_val = SL * (high_swing - Close[-1])
        elif Trade_Direction == 1:
            stop_loss_val = SL * (Close[-1] - Low_swing)

    if TP_choice == 'x (Swing Close) level 2':
        high_swing = Close[-1]
        Low_swing = Close[-1]
        high_flag = 0
        low_flag = 0
        j = -3
        while j > -len(Close) + 2:
            if Close[j] > high_swing and high_flag == 0:
                high_swing = Close[j]
                if Close[j - 1] < Close[j] > Close[j + 1] and Close[j - 2] < Close[j] > \
                        Close[j + 2]:
                    ##found a swing high level 2
                    high_flag = 1
            if Close[j] < Low_swing and low_flag == 0:
                Low_swing = Close[j]
                if Close[j - 1] > Close[j] < Close[j + 1] and Close[j - 2] > Close[j] < Close[
                    j + 2]:
                    ##found a swing low level 2
                    low_flag = 1
            if (high_flag == 1 and Trade_Direction == 1) or (low_flag == 1 and Trade_Direction == 0):
                break
            j -= 1

        if Trade_Direction == 0:
            take_profit_val = TP * (Close[-1] - Low_swing)
        elif Trade_Direction == 1:
            take_profit_val = TP * (high_swing - Close[-1])

    if SL_choice == 'x (Swing Close) level 2':
        high_swing = Close[-1]
        Low_swing = Close[-1]
        high_flag = 0
        low_flag = 0
        j = -3
        while j > -len(Close) + 2:
            if Close[j] > high_swing and high_flag == 0:
                high_swing = Close[j]
                if Close[j - 1] < Close[j] > Close[j + 1] and Close[j - 2] < Close[j] > \
                        Close[j + 2]:
                    ##found a swing high level 2
                    high_flag = 1
            if Low[j] < Low_swing and low_flag == 0:
                Low_swing = Low[j]
                if Low[j - 1] > Low[j] < Low[j + 1] and Low[j - 2] > Low[j] < Low[
                    j + 2]:
                    ##found a swing low level 2
                    low_flag = 1
            if (high_flag == 1 and Trade_Direction == 1) or (low_flag == 1 and Trade_Direction == 0):
                break
            j -= 1

        if Trade_Direction == 0:
            stop_loss_val = SL * (high_swing - Close[-1])
        elif Trade_Direction == 1:
            stop_loss_val = SL * (Close[-1] - Low_swing)

    if TP_choice == 'x (Swing Close) level 3':
        high_swing = Close[-1]
        Low_swing = Close[-1]
        high_flag = 0
        low_flag = 0
        j = -4
        while j > -len(Close) + 3:
            if Close[j] > high_swing and high_flag == 0:
                high_swing = Close[j]
                if Close[j - 1] < Close[j] > Close[j + 1] and Close[j - 2] < Close[j] > \
                        Close[j + 2] and Close[j - 3] < Close[j] > \
                        Close[j + 3]:
                    ##found a swing high level 2
                    high_flag = 1
            if Close[j] < Low_swing and low_flag == 0:
                Low_swing = Close[j]
                if Close[j - 1] > Close[j] < Close[j + 1] and Close[j - 2] > Close[j] < Close[
                    j + 2] and Close[j - 3] > Close[j] < Close[
                    j + 3]:
                    ##found a swing low level 2
                    low_flag = 1
            if (high_flag == 1 and Trade_Direction == 1) or (low_flag == 1 and Trade_Direction == 0):
                break
            j -= 1

        if Trade_Direction == 0:
            take_profit_val = TP * (Close[-1] - Low_swing)
        elif Trade_Direction == 1:
            take_profit_val = TP * (high_swing - Close[-1])

    if SL_choice == 'x (Swing Close) level 3':
        high_swing = Close[-1]
        Low_swing = Close[-1]
        high_flag = 0
        low_flag = 0
        j = -4
        while j > -len(Close) + 3:
            if Close[j] > high_swing and high_flag == 0:
                high_swing = Close[j]
                if Close[j - 1] < Close[j] > Close[j + 1] and Close[j - 2] < Close[j] > \
                        Close[j + 2] and Close[j - 3] < Close[j] > \
                        Close[j + 3]:
                    ##found a swing high level 2
                    high_flag = 1
            if Close[j] < Low_swing and low_flag == 0:
                Low_swing = Close[j]
                if Close[j - 1] > Close[j] < Close[j + 1] and Close[j - 2] > Close[j] < Close[
                    j + 2] and Close[j - 3] > Close[j] < Close[
                    j + 3]:
                    ##found a swing low level 2
                    low_flag = 1
            if (high_flag == 1 and Trade_Direction == 1) or (low_flag == 1 and Trade_Direction == 0):
                break
            j -= 1

        if Trade_Direction == 0:
            stop_loss_val = SL * (high_swing - Close[-1])
        elif Trade_Direction == 1:
            stop_loss_val = SL * (Close[-1] - Low_swing)

    return stop_loss_val, take_profit_val
