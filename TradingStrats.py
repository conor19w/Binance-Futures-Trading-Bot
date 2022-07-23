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


def candle_wick(Trade_Direction, Close, Open, High, Low, SL, TP, TP_choice, SL_choice, index):
    if Close[index - 4] < Close[index - 3] < Close[index - 2] and Close[index - 1] < Open[index - 1] and (
            High[index - 1] - Open[index - 1] + Close[index - 1] - Low[index - 1]) > 10 * (Open[index - 1] - Close[index - 1]) and Close[index] < Close[index - 1]:
        ##3 green candles followed by a red candle with a huge wick
        Trade_Direction = 0
    elif Close[index - 4] > Close[index - 3] > Close[index - 2] and Close[index - 1] > Open[index - 1] and (
            High[index - 1] - Close[index - 1] + Open[index - 1] - Low[index - 1]) > 10 * (Close[index - 1] - Open[index - 1]) and Close[index] > Close[index - 1]:
        ##3 red candles followed by a green candle with a huge wick
        Trade_Direction = 1
    stop_loss_val, take_profit_val = SetSLTP(-99, -99, Close, High, Low, Trade_Direction, SL, TP, TP_choice, SL_choice, index)
    return Trade_Direction, stop_loss_val, take_profit_val


def fibMACD(Trade_Direction, Close, Open, High, Low, MACD_signal, MACD, EMA200, index):
    stop_loss_val = 0
    take_profit_val = 0
    period = 100  ##Record peaks and troughs in last period timesteps

    Close_peaks = []  ##Store peak values
    location_peaks = []  ##store index of peak value , used for debugging
    Close_troughs = []  ##store trough values
    location_troughs = []  ##store index of peak trough , used for debugging
    #####################Find peaks & troughs in Close ##############################
    for i in range(index - period, index - 2):
        if High[i] > High[i - 1] and High[i] > High[i + 1] and High[i] > High[i - 2] and High[i] > High[i + 2]:
            ##Weve found a peak:
            Close_peaks.append(High[i])
            location_peaks.append(i)
        elif Low[i] < Low[i - 1] and Low[i] < Low[i + 1] and Low[i] < Low[i - 2] and Low[i] < Low[i + 2]:
            ##Weve found a trough:
            Close_troughs.append(Low[i])
            location_troughs.append(i)


    trend = -99  ##indicate the direction of trend
    if Close[index] < EMA200[index]:
        trend = 0
    elif Close[index] > EMA200[index]:
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
            index]  ##target max_Close+1.236*(max_Close - min_Close)
        fib_retracement_level_2 = fib_level_0 + 1.382 * (max_Close - min_Close) - Close[index]
        fib_retracement_level_3 = fib_level_0 + 1.5 * (max_Close - min_Close) - Close[index]
        fib_retracement_level_4 = fib_level_0 + 1.618 * (max_Close - min_Close) - Close[index]
        fib_retracement_level_5 = fib_level_0 + 1.786 * (max_Close - min_Close) - Close[index]
        fib_retracement_level_6 = fib_level_0 + 2 * (max_Close - min_Close) - Close[index]

        ## fib_level_0>Low[index - 2]>fib_level_1: recent low was between two of our levels
        ## Close[index - 3]>fib_level_1 and Close[index - 4]>fib_level_1 and Close[-6]>fib_level_1: Ensure the bottom level was respected  ie. no recent close below it
        if fib_level_0 > Low[index - 2] > fib_level_1 and Close[index - 3] > fib_level_1 and Close[index - 4] > fib_level_1 and Close[
            -6] > fib_level_1:
            if Close[index - 2] < Open[index - 2] < Close[index - 1] < Close[index] and (
                    (MACD_signal[index - 1] < MACD[index - 1] or MACD_signal[index - 2] < MACD[index - 2]) and MACD_signal[index] > MACD[
                index]):  ##Bullish Engulfing Candle and cross up on MACD
                # print("level 1")
                Trade_Direction = 1  ##signal a buy
                take_profit_val = fib_retracement_level_1  ##target the corresponding extensiuon level
                stop_loss_val = Close[index] - fib_level_1 * 1.0001  ##stoploss below bottom level with a bit extra
        elif fib_level_1 > Low[index - 2] > fib_level_2 and Close[index - 3] > fib_level_2 and Close[index - 4] > fib_level_2 and Close[
            -6] > fib_level_2:
            if Close[index - 2] < Open[index - 2] < Close[index - 1] < Close[index] and (
                    (MACD_signal[index - 1] < MACD[index - 1] or MACD_signal[index - 2] < MACD[index - 2]) and MACD_signal[index] > MACD[
                index]):  ##Bullish Engulfing Candle and cross up on MACD
                # print("level 1")
                Trade_Direction = 1  ##signal a buy
                take_profit_val = fib_retracement_level_2
                stop_loss_val = Close[index] - fib_level_2 * 1.0001

        elif fib_level_2 > Low[index - 1] > fib_level_3 and Close[index - 2] > fib_level_3 and Close[index - 3] > fib_level_3 and Close[
            index - 4] > fib_level_3:
            if Close[index - 1] < Open[index - 1] < Close[index] < Close[index] and (
                    (MACD_signal[index - 1] < MACD[index - 1] or MACD_signal[index - 2] < MACD[index - 2]) and MACD_signal[index] > MACD[
                index]):  ##Bullish Engulfing Candle and cross up on MACD
                # print("level 2")
                Trade_Direction = 1  ##signal a buy
                take_profit_val = fib_retracement_level_3
                stop_loss_val = Close[index] - fib_level_3 * 1.0001

        elif fib_level_3 > Low[index - 1] > fib_level_4 and Close[index - 2] > fib_level_4 and Close[index - 3] > fib_level_4 and Close[
            index - 4] > fib_level_4:
            if Close[index - 1] < Open[index - 1] < Close[index] < Close[index] and (
                    (MACD_signal[index - 1] < MACD[index - 1] or MACD_signal[index - 2] < MACD[index - 2]) and MACD_signal[index] > MACD[
                index]):  ##Bullish Engulfing Candle and cross up on MACD
                # print("level 3")
                Trade_Direction = 1  ##signal a buy
                take_profit_val = fib_retracement_level_4
                stop_loss_val = Close[index] - fib_level_4 * 1.0001
        elif fib_level_4 > Low[index - 1] > fib_level_5 and Close[index - 2] > fib_level_5 and Close[index - 3] > fib_level_5 and Close[
            index - 4] > fib_level_5:
            if Close[index - 1] < Open[index - 1] < Close[index] < Close[index] and (
                    (MACD_signal[index - 1] < MACD[index - 1] or MACD_signal[index - 2] < MACD[index - 2]) and MACD_signal[index] > MACD[
                index]):  ##Bullish Engulfing Candle and cross up on MACD
                # print("level 4")
                Trade_Direction = 1  ##signal a buy
                take_profit_val = fib_retracement_level_5
                stop_loss_val = Close[index] - fib_level_5 * 1.0001
        elif fib_level_5 > Low[index - 1] > fib_level_6 and Close[index - 2] > fib_level_6 and Close[index - 3] > fib_level_6 and Close[
            index - 4] > fib_level_6:
            if Close[index - 1] < Open[index - 1] < Close[index] < Close[index] and (
                    (MACD_signal[index - 1] < MACD[index - 1] or MACD_signal[index - 2] < MACD[index - 2]) and MACD_signal[index] > MACD[
                index]):  ##Bullish Engulfing Candle and cross up on MACD
                # print("level 5")
                Trade_Direction = 1  ##signal a buy
                take_profit_val = fib_retracement_level_6
                stop_loss_val = Close[index] - fib_level_6 * 1.0001

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
        fib_retracement_level_1 = Close[index] - (fib_level_0 + 1.236 * (max_Close - min_Close))
        fib_retracement_level_2 = Close[index] - (fib_level_0 + 1.382 * (max_Close - min_Close))
        fib_retracement_level_3 = Close[index] - (fib_level_0 + 1.5 * (max_Close - min_Close))
        fib_retracement_level_4 = Close[index] - (fib_level_0 + 1.618 * (max_Close - min_Close))
        fib_retracement_level_5 = Close[index] - (fib_level_0 + 1.786 * (max_Close - min_Close))
        fib_retracement_level_6 = Close[index] - (fib_level_0 + 2 * (max_Close - min_Close))

        ## fib_level_0 < High[index - 2] < fib_level_1: recent low was between two of our levels
        ## Close[index - 3] < fib_level_1 and Close[index - 4] < fib_level_1 and Close[-6] < fib_level_1: Ensure the Top level was respected, ie no recent close above it
        if fib_level_0 < High[index - 2] < fib_level_1 and Close[index - 3] < fib_level_1 and Close[index - 4] < fib_level_1 and Close[
            -6] < fib_level_1:
            if Close[index - 2] > Open[index - 2] > Close[index - 1] > Close[index] and (
                    (MACD_signal[index - 1] > MACD[index - 1] or MACD_signal[index - 2] > MACD[index - 2]) and MACD_signal[index] < MACD[
                index]):  ##Bearish Engulfing Candle and cross down on MACD
                # print("level 1")
                Trade_Direction = 0  ##signal a sell
                take_profit_val = fib_retracement_level_1  ##target corresponding extension level
                stop_loss_val = fib_level_1 * 1.0001 - Close[index]  ##stoploss above Top level with a bit extra
        elif fib_level_1 < High[index - 2] < fib_level_2 and Close[index - 3] < fib_level_2 and Close[index - 4] < fib_level_2 and Close[
            -6] < fib_level_2:
            if Close[index - 2] > Open[index - 2] > Close[index - 1] > Close[index] and (
                    (MACD_signal[index - 1] > MACD[index - 1] or MACD_signal[index - 2] > MACD[index - 2]) and MACD_signal[index] < MACD[
                index]):  ##Bearish Engulfing Candle and cross down on MACD
                # print("level 1")
                Trade_Direction = 0  ##signal a sell
                take_profit_val = fib_retracement_level_2
                stop_loss_val = fib_level_2 * 1.0001 - Close[index]
        elif fib_level_2 < High[index - 2] < fib_level_3 and Close[index - 3] < fib_level_3 and Close[index - 4] < fib_level_3 and Close[
            -6] < fib_level_3:
            if Close[index - 2] > Open[index - 2] > Close[index - 1] > Close[index] and (
                    (MACD_signal[index - 1] > MACD[index - 1] or MACD_signal[index - 2] > MACD[index - 2]) and MACD_signal[index] < MACD[
                index]):  ##Bearish Engulfing Candle and cross down on MACD
                # print("level 1")
                Trade_Direction = 0  ##signal a sell
                take_profit_val = fib_retracement_level_3
                stop_loss_val = fib_level_3 * 1.0001 - Close[index]
        elif fib_level_3 < High[index - 2] < fib_level_4 and Close[index - 3] < fib_level_4 and Close[index - 4] < fib_level_4 and Close[
            -6] < fib_level_4:
            if Close[index - 2] > Open[index - 2] > Close[index - 1] > Close[index] and (
                    (MACD_signal[index - 1] > MACD[index - 1] or MACD_signal[index - 2] > MACD[index - 2]) and MACD_signal[index] < MACD[
                index]):  ##Bearish Engulfing Candle and cross down on MACD
                # print("level 1")
                Trade_Direction = 0  ##signal a sell
                take_profit_val = fib_retracement_level_4
                stop_loss_val = fib_level_4 * 1.0001 - Close[index]
        elif fib_level_4 < High[index - 2] < fib_level_5 and Close[index - 3] < fib_level_5 and Close[index - 4] < fib_level_5 and Close[
            -6] < fib_level_5:
            if Close[index - 2] > Open[index - 2] > Close[index - 1] > Close[index] and (
                    (MACD_signal[index - 1] > MACD[index - 1] or MACD_signal[index - 2] > MACD[index - 2]) and MACD_signal[index] < MACD[
                index]):  ##Bearish Engulfing Candle and cross down on MACD
                # print("level 1")
                Trade_Direction = 0  ##signal a sell
                take_profit_val = fib_retracement_level_5
                stop_loss_val = fib_level_5 * 1.0001 - Close[index]
        elif fib_level_5 < High[index - 2] < fib_level_6 and Close[index - 3] < fib_level_6 and Close[index - 4] < fib_level_6 and Close[
            -6] < fib_level_6:
            if Close[index - 2] > Open[index - 2] > Close[index - 1] > Close[index] and (
                    (MACD_signal[index - 1] > MACD[index - 1] or MACD_signal[index - 2] > MACD[index - 2]) and MACD_signal[index] < MACD[
                index]):  ##Bearish Engulfing Candle and cross down on MACD
                # print("level 1")
                Trade_Direction = 0  ##signal a sell
                take_profit_val = fib_retracement_level_6
                stop_loss_val = fib_level_6 * 1.0001 - Close[index]

    return Trade_Direction, stop_loss_val, take_profit_val


def goldenCross(Trade_Direction, Close, High, Low, SL, TP, TP_choice, SL_choice, EMA100, EMA50, EMA20, RSI, index):
    if Close[index] > EMA100[index] and RSI[index] > 50:
        ##looking for long entries
        if (EMA20[index - 1] < EMA50[index - 1] and EMA20[index] > EMA50[index]) or (EMA20[index - 2] < EMA50[index - 2] and EMA20[index] > EMA50[index]) or (
                EMA20[index - 3] < EMA50[index - 3] and EMA20[index] > EMA50[index]):
            ##Cross up occured
            Trade_Direction = 1  ##buy
    elif Close[index] < EMA100[index] and RSI[index] < 50:
        ##looking for short entries
        if (EMA20[index - 1] > EMA50[index - 1] and EMA20[index] < EMA50[index]) or (EMA20[index - 2] > EMA50[index - 2] and EMA20[index] < EMA50[index]) or (
                EMA20[index - 3] > EMA50[index - 3] and EMA20[index] < EMA50[index]):
            ##Cross up occured
            Trade_Direction = 0  ##Sell
    stop_loss_val, take_profit_val = SetSLTP(-99, -99, Close, High, Low, Trade_Direction, SL, TP, TP_choice, SL_choice, index)
    return Trade_Direction, stop_loss_val, take_profit_val


def StochRSIMACD(Trade_Direction, Close, High, Low, SL, TP, TP_choice, SL_choice, fastd, fastk, RSI, MACD, macdsignal, index):

    if ((fastd[index] < 20 and fastk[index] < 20 and RSI[index] > 50 and MACD[index] > macdsignal[index] and MACD[index - 1] < macdsignal[
        index - 1]) or
            (fastd[index - 1] < 20 and fastk[index - 1] < 20 and RSI[index] > 50 and MACD[index] > macdsignal[index] and MACD[index - 2] < macdsignal[
                index - 2] and fastd[index] < 80 and fastk[index] < 80) or
            (fastd[index - 2] < 20 and fastk[index - 2] < 20 and RSI[index] > 50 and MACD[index] > macdsignal[index] and MACD[index - 1] < macdsignal[
                index - 1] and fastd[index] < 80 and fastk[index] < 80) or
            (fastd[index - 3] < 20 and fastk[index - 3] < 20 and RSI[index] > 50 and MACD[index] > macdsignal[index] and MACD[index - 2] < macdsignal[
                index - 2] and fastd[index] < 80 and fastk[index] < 80)):
        Trade_Direction = 1
    elif ((fastd[index] > 80 and fastk[index] > 80 and RSI[index] < 50 and MACD[index] < macdsignal[index] and MACD[index - 1] > macdsignal[
        index - 1]) or
          (fastd[index - 1] > 80 and fastk[index - 1] > 80 and RSI[index] < 50 and MACD[index] < macdsignal[index] and MACD[index - 2] > macdsignal[
              index - 2] and fastd[index] > 20 and fastk[index] > 20) or
          (fastd[index - 2] > 80 and fastk[index - 2] > 80 and RSI[index] < 50 and MACD[index] < macdsignal[index] and MACD[index - 1] > macdsignal[
              index - 1] and fastd[index] > 20 and fastk[index] > 20) or
          (fastd[index - 3] > 80 and fastk[index - 3] > 80 and RSI[index] < 50 and MACD[index] < macdsignal[index] and MACD[index - 2] > macdsignal[
              index - 2] and fastd[index] > 20 and fastk[index] > 20)):
        Trade_Direction = 0
    stop_loss_val, take_profit_val = SetSLTP(-99, -99, Close, High, Low, Trade_Direction, SL, TP, TP_choice, SL_choice, index)
    return Trade_Direction, stop_loss_val, take_profit_val


##############################################################################################################################
##############################################################################################################################
##############################################################################################################################


def tripleEMA(Close, High, Low, Trade_Direction, SL, TP, TP_choice, SL_choice, EMA3, EMA6, EMA9, index):

    if EMA3[index - 4] > EMA6[index - 4] and EMA3[index - 4] > EMA9[index - 4] \
            and EMA3[index - 3] > EMA6[index - 3] and EMA3[index - 3] > EMA9[index - 3] \
            and EMA3[index - 2] > EMA6[index - 2] and EMA3[index - 2] > EMA9[index - 2] \
            and EMA3[index - 1] > EMA6[index - 1] and EMA3[index - 1] > EMA9[index - 1] \
            and EMA3[index] < EMA6[index] and EMA3[index] < EMA9[index]:
        Trade_Direction = 0
    if EMA3[index - 4] < EMA6[index - 4] and EMA3[index - 4] < EMA9[index - 4] \
            and EMA3[index - 3] < EMA6[index - 3] and EMA3[index - 3] < EMA9[index - 3] \
            and EMA3[index - 2] < EMA6[index - 2] and EMA3[index - 2] < EMA9[index - 2] \
            and EMA3[index - 1] < EMA6[index - 1] and EMA3[index - 1] < EMA9[index - 1] \
            and EMA3[index] > EMA6[index] and EMA3[index] > EMA9[index]:
        Trade_Direction = 1
    stop_loss_val, take_profit_val = SetSLTP(-99, -99, Close, High, Low, Trade_Direction, SL, TP, TP_choice, SL_choice, index)
    return Trade_Direction, stop_loss_val, take_profit_val


def heikin_ashi_ema2(Close, OpenStream_H, High_H, Low_H, Close_H, High, Low, Trade_Direction, CurrentPos, Close_pos, SL,
                     TP, TP_choice, SL_choice, fastd, fastk, EMA200, index):
    if CurrentPos == -99:
        Trade_Direction = -99
        short_threshold = .7  ##If RSI falls below this don't open any shorts
        long_threshold = .3  ##If RSI goes above this don't open any longs

        ##Check Most recent Candles to see if we got a cross down and we are below 200EMA
        if fastk[index - 1] > fastd[index - 1] and fastk[index] < fastd[index] and Close_H[index] < EMA200[index]:
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
        elif fastk[index - 1] < fastd[index - 1] and fastk[index] > fastd[index] and Close_H[index] > EMA200[index]:
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

    elif CurrentPos == 1 and Close_H[index] < OpenStream_H[index]:
        Close_pos = 1
    elif CurrentPos == 0 and Close_H[index] > OpenStream_H[index]:
        Close_pos = 1
    else:
        Close_pos = 0
    stop_loss_val, take_profit_val = SetSLTP(-99, -99, Close, High, Low, Trade_Direction, SL, TP, TP_choice, SL_choice, index)
    return Trade_Direction, stop_loss_val, take_profit_val, Close_pos


def heikin_ashi_ema(Close, OpenStream_H, Close_H, Trade_Direction, CurrentPos, Close_pos, High, Low, SL, TP, TP_choice,
                    SL_choice, fastd, fastk, EMA200, index):
    if CurrentPos == -99:
        Trade_Direction = -99

        short_threshold = .8  ##If RSI falls below this don't open any shorts
        long_threshold = .2  ##If RSI goes above this don't open any longs
        ##look for shorts
        if fastk[index] > short_threshold and fastd[index] > short_threshold:
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
                            if Close_H[index - 2] > EMA200[index - 2] and Close_H[index - 1] < EMA200[index - 1] and flag:
                                ##closed below 200EMA
                                if Close_H[index] < OpenStream_H[index]:
                                    ##bearish candle
                                    ##all conditions met so open a short
                                    Trade_Direction = 0
                                else:
                                    break  ##break out of the current for loop
                            else:
                                break  ##break out of the current for loop
        ##Look for longs
        elif fastk[index] < long_threshold and fastd[index] < long_threshold:
            ##Check last 10 candles, a bit overkill
            for i in range(10, 2, -1):
                if fastd[-i] <= .2 and fastk[-i] <= .2:
                    ##both oscillators in the overbought position
                    for j in range(i, 2, -1):
                        ##now check if we get a cross on the in the next few candles
                        if fastk[-j] < fastd[-j] and fastk[-j + 1] > fastd[-j + 1] and fastk[index] < long_threshold and \
                                fastd[index] < long_threshold:
                            flag = 1
                            for r in range(j, 2, -1):
                                ##we passed the threshold
                                if fastk[r] > long_threshold or fastd[r] > long_threshold:
                                    flag = 0
                                    break
                            ##Cross up on the k and d lines, look for the candle stick pattern
                            ##candle crosses 200EMA
                            if Close_H[index - 2] < EMA200[index - 2] and Close_H[index - 1] > EMA200[index - 1] and flag:
                                ##closed above 200EMA
                                if Close_H[index] > OpenStream_H[index]:
                                    ##bullish candle
                                    ##all conditions met so open a long
                                    Trade_Direction = 1
                                else:
                                    break  ##break out of the current for loop
                            else:
                                break  ##break out of the current for loop
    elif CurrentPos == 1 and Close_H[index] < OpenStream_H[index]:
        Close_pos = 1
    elif CurrentPos == 0 and Close_H[index] > OpenStream_H[index]:
        Close_pos = 1
    else:
        Close_pos = 0
    stop_loss_val, take_profit_val = SetSLTP(-99, -99, Close, High, Low, Trade_Direction, SL, TP, TP_choice, SL_choice, index)
    return Trade_Direction, stop_loss_val, take_profit_val, Close_pos


def tripleEMAStochasticRSIATR(Close, High, Low, Trade_Direction, SL, TP, TP_choice, SL_choice, EMA50, EMA14, EMA8, fastd, fastk, index):
    ##buy signal
    if (Close[index] > EMA8[index] > EMA14[index] > EMA50[index]) and \
            ((fastk[index] > fastd[index]) and (fastk[index - 1] < fastd[index - 1])):  # and (fastk[index]<80 and fastd[index]<80):
        Trade_Direction = 1
    elif (Close[index] < EMA8[index] < EMA14[index] < EMA50[index]) and\
            ((fastk[index] < fastd[index]) and (fastk[index - 1] > fastd[index - 1])):  # and (fastk[index]>20 and fastd[index]>20):
        Trade_Direction = 0

    stop_loss_val, take_profit_val = SetSLTP(-99, -99, Close, High, Low, Trade_Direction, SL, TP, TP_choice, SL_choice, index)
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
                if peaks_RSI[i] < peaks_RSI[index] and corresponding_Close_peaks[i] > corresponding_Close_peaks[index] and \
                        peaks_RSI[index] - peaks_RSI[i] > 1:
                    for j in range(i + 1, len(peaks_RSI) - 1):
                        if peaks_RSI[j] > peaks_RSI[i]:
                            break
                        elif j == len(peaks_RSI) - 2:
                            loc1 = location_peaks[i]

            if i < len(troughs_RSI):
                ##Check for hidden Bullish Divergence
                if troughs_RSI[i] > troughs_RSI[index] and corresponding_Close_troughs[i] < corresponding_Close_troughs[
                    index] and troughs_RSI[i] - troughs_RSI[index] > 1:
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
    if signal1 == 1 and (fastk[index] > fastd[index] and (fastk[index - 1] < fastd[index - 1] or fastk[index - 2] < fastd[index - 2])) and Close[index] > \
            EMA200[index]:
        Trade_Direction = 1
        signal1 = -99

    ##Bearish Divergence
    elif signal1 == 0 and (fastk[index] < fastd[index] and (fastk[index - 1] > fastd[index - 1] or fastk[index - 2] > fastd[index - 2])) and Close[index] < \
            EMA200[index]:
        Trade_Direction = 0
        signal1 = -99

    if currentPos != -99:
        signal1 = -99
        Trade_Direction = -99
    stop_loss_val, take_profit_val = SetSLTP(-99, -99, Close, High, Low, Trade_Direction, SL, TP, TP_choice, SL_choice, index)
    return Trade_Direction, signal1, stop_loss_val, take_profit_val


##############################################################################################################

def stochBB(Trade_Direction, Close, High, Low, SL, TP, TP_choice, SL_choice, fastd, fastk, percent_B, index):
    percent_B1 = percent_B[index]
    percent_B2 = percent_B[index - 1]
    percent_B3 = percent_B[index - 2]
    # print(percent_B)

    if fastk[index] < .2 and fastd[index] < .2 and (fastk[index] > fastd[index] and fastk[index - 1] < fastd[index - 1]) and (
            percent_B1 < 0 or percent_B2 < 0 or percent_B3 < 0):  # or percent_B3<0):# or percent_B2<.05):
        Trade_Direction = 1
    elif fastk[index] > .8 and fastd[index] > .8 and (fastk[index] < fastd[index] and fastk[index - 1] > fastd[index - 1]) and (
            percent_B1 > 1 or percent_B2 > 1 or percent_B3 > 1):  # or percent_B3>1):# or percent_B2>1):
        Trade_Direction = 0
    stop_loss_val, take_profit_val = SetSLTP(-99, -99, Close, High, Low, Trade_Direction, SL, TP, TP_choice, SL_choice, index)
    return Trade_Direction, stop_loss_val, take_profit_val


def breakout(Trade_Direction, Close, VolumeStream, High, Low, SL, TP, TP_choice, SL_choice, max_Close, min_Close, max_Vol, index):
    invert = 0  ## switch shorts and longs, basically fakeout instead of breakout
    if invert:
        if Close[index] >= max_Close.iloc[index] and VolumeStream[index] >= max_Vol.iloc[index]:
            Trade_Direction = 0
        elif Close[index] <= min_Close.iloc[index] and VolumeStream[index] >= max_Vol.iloc[index]:
            Trade_Direction = 1
    else:
        if Close[index] >= max_Close.iloc[index] and VolumeStream[index] >= max_Vol.iloc[index]:
            Trade_Direction = 1
        elif Close[index] <= min_Close.iloc[index] and VolumeStream[index] >= max_Vol.iloc[index]:
            Trade_Direction = 0

    stop_loss_val, take_profit_val = SetSLTP(-99, -99, Close, High, Low, Trade_Direction, SL, TP, TP_choice, SL_choice, index)
    return Trade_Direction, stop_loss_val, take_profit_val


def fakeout(Trade_Direction, Close, VolumeStream, High, Low, SL, TP, TP_choice, SL_choice):
    invert = 1
    # if symbol == 'BTCUSDT' or symbol == 'ETHUSDT':
    #    invert = 0
    Close = pd.Series(Close)  # .pct_change() ##get size of bars in a percentage
    Volume = pd.Series(VolumeStream[:index])
    max_Close = Close.iloc[:index].rolling(15).max()
    min_Close = Close.iloc[:index].rolling(15).min()
    max_Vol = Volume.rolling(15).max()
    if invert:
        if Close.iloc[index] > max_Close.iloc[index] and VolumeStream[index] < max_Vol.iloc[index]:
            Trade_Direction = 0
        elif Close.iloc[index] < min_Close.iloc[index] and VolumeStream[index] < max_Vol.iloc[index]:
            Trade_Direction = 1
    else:
        if Close.iloc[index] > max_Close.iloc[index] and VolumeStream[index] < max_Vol.iloc[index]:
            Trade_Direction = 1
        elif Close.iloc[index] < min_Close.iloc[index] and VolumeStream[index] < max_Vol.iloc[index]:
            Trade_Direction = 0
    stop_loss_val, take_profit_val = SetSLTP(-99, -99, Close, High, Low, Trade_Direction, SL, TP, TP_choice, SL_choice, index)
    return Trade_Direction, stop_loss_val, take_profit_val


def EMA_cross(Trade_Direction, Close, High, Low, SL, TP, TP_choice, SL_choice, EMA_short, EMA_long, index):
    if EMA_short[index - 4] > EMA_long[index - 4] \
            and EMA_short[index - 3] > EMA_long[index - 3] \
            and EMA_short[index - 2] > EMA_long[index - 2] \
            and EMA_short[index - 1] > EMA_long[index - 1] \
            and EMA_short[index] < EMA_long[index]:
        Trade_Direction = 0

    if EMA_short[index - 4] < EMA_long[index - 4] \
            and EMA_short[index - 3] < EMA_long[index - 3] \
            and EMA_short[index - 2] < EMA_long[index - 2] \
            and EMA_short[index - 1] < EMA_long[index - 1] \
            and EMA_short[index] > EMA_long[index]:
        Trade_Direction = 1

    stop_loss, take_profit = SetSLTP(-99, -99, Close, High, Low, Trade_Direction, SL, TP, TP_choice, SL_choice, index)
    return Trade_Direction, stop_loss, take_profit


'''def pairTrading(Trade_Direction,Close1,Close2,log=0,TPSL=0,percent_TP=0,percent_SL=0):
    new_Close = []
    
    #multiplier = Close1[0]/Close2[0]
    if not log:
        multiplier = (sm.OLS(Close1, Close2).fit()).params[0]
        for i in range(len(Close1)index - 20,len(Close1)):
            new_Close.append(Close1[i]-multiplier*Close2[i])
    else:
        log_close1 = []
        log_close2 = []
        for i in range(len(Close1)index - 20,len(Close1)):
            log_close1.append(math.log(Close1[i]))
            log_close2.append(math.log(Close2[i]))
        multiplier = (sm.OLS(log_close1, log_close2).fit()).params[0]
        for i in range(len(log_close1)):
            new_Close.append(log_close1[i] - multiplier * log_close2[i])
    BB =np.array(bollinger_pband(pd.Series(new_Close),window_dev=3))
    #BB1 = np.array(bollinger_hband(pd.Series(new_Close),window_dev=3))
    #BB2 = np.array(bollinger_lband(pd.Series(new_Close), window_dev=3))
    #SMA20 = np.array(bollinger_mavg(pd.Series(new_Close)))
    #print(BB[index])
    if BB[index]>1:
        Trade_Direction = [0,1]  # [1,0]
        
    elif BB[index]<0:
        Trade_Direction = [1,0] # [0,1]
        
    return Trade_Direction,[9,9] #,Close1_TP,Close2_TP,Close1_SL,Close2_SL


def pairTrading_Crossover(Trade_Direction, Close1, Close2, CurrentPos, percent_SL=0):
    new_Close = []
    Close_pos=0
    Close1_SL = 0
    Close2_SL = 0
    multiplier = (sm.OLS(Close1, Close2).fit()).params[0]
    for i in range(len(Close1)index - 20,len(Close1)):
        new_Close.append(Close1[i]-multiplier*Close2[i])
    BB =np.array(bollinger_pband(pd.Series(new_Close),window_dev=3))
    SMA20 = np.array(bollinger_mavg(pd.Series(new_Close)))
    if BB[index]>1:
        Trade_Direction = [0,1]
        Close1_SL = Close1[index] * percent_SL
        Close2_SL = Close2[index] * percent_SL
    elif BB[index]<0:
        Trade_Direction = [1,0]
        Close1_SL = Close1[index] * percent_SL
        Close2_SL = Close2[index] * percent_SL
    if CurrentPos!=-99:
        if (new_Close[index]>SMA20[index] and (new_Close[index - 1]<SMA20[index - 1] or new_Close[index - 2]<SMA20[index - 2])) or (new_Close[index]<SMA20[index] and (new_Close[index - 1]>SMA20[index - 1] or new_Close[index - 2]>SMA20[index - 2])):
            ##Price has crossed up or down over the Moving average so close the position
            Close_pos=1
    return Trade_Direction,Close1_SL,Close2_SL,Close_pos'''


def SetSLTP(stop_loss_val, take_profit_val, Close, High, Low, Trade_Direction, SL, TP, TP_choice, SL_choice, index):
    if TP_choice == '%':
        take_profit_val = (TP / 100) * Close[index]
    if SL_choice == '%':
        stop_loss_val = (SL / 100) * Close[index]

    if TP_choice == 'x (ATR)':
        ATR = np.array(average_true_range(pd.Series(High), pd.Series(Low), pd.Series(Close)))
        take_profit_val = TP * abs(ATR[index])

    if SL_choice == 'x (ATR)':
        ATR = np.array(average_true_range(pd.Series(High), pd.Series(Low), pd.Series(Close)))
        stop_loss_val = SL * abs(ATR[index])

    if TP_choice == 'x (Swing High/Low) level 1':
        high_swing = High[index]
        Low_swing = Low[index]
        high_flag = 0
        low_flag = 0
        j = index - 1
        while j > -1:
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
            take_profit_val = TP * (Close[index] - Low_swing)
        elif Trade_Direction == 1:
            take_profit_val = TP * (high_swing - Close[index])

    if SL_choice == 'x (Swing High/Low) level 1':
        high_swing = High[index]
        Low_swing = Low[index]
        high_flag = 0
        low_flag = 0
        j = index - 1
        while j > -1:
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
            stop_loss_val = SL * (high_swing - Close[index])
        elif Trade_Direction == 1:
            stop_loss_val = SL * (Close[index] - Low_swing)

    if TP_choice == 'x (Swing High/Low) level 2':
        high_swing = High[index]
        Low_swing = Low[index]
        high_flag = 0
        low_flag = 0
        j = index - 2
        while j > -1:
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
            take_profit_val = TP * (Close[index] - Low_swing)
        elif Trade_Direction == 1:
            take_profit_val = TP * (high_swing - Close[index])

    if SL_choice == 'x (Swing High/Low) level 2':
        high_swing = High[index]
        Low_swing = Low[index]
        high_flag = 0
        low_flag = 0
        j = index - 2
        while j > -1:
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
            stop_loss_val = SL * (high_swing - Close[index])
        elif Trade_Direction == 1:
            stop_loss_val = SL * (Close[index] - Low_swing)

    if TP_choice == 'x (Swing High/Low) level 3':
        high_swing = High[index]
        Low_swing = Low[index]
        high_flag = 0
        low_flag = 0
        j = index - 3
        while j > -1:
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
            take_profit_val = TP * (Close[index] - Low_swing)
        elif Trade_Direction == 1:
            take_profit_val = TP * (high_swing - Close[index])

    if SL_choice == 'x (Swing High/Low) level 3':
        high_swing = High[index]
        Low_swing = Low[index]
        high_flag = 0
        low_flag = 0
        j = index - 3
        while j > -1:
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
            stop_loss_val = SL * (high_swing - Close[index])
        elif Trade_Direction == 1:
            stop_loss_val = SL * (Close[index] - Low_swing)

    if TP_choice == 'x (Swing Close) level 1':
        high_swing = Close[index]
        Low_swing = Close[index]
        high_flag = 0
        low_flag = 0
        j = index - 1
        while j > -1:
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
            take_profit_val = TP * (Close[index] - Low_swing)
        elif Trade_Direction == 1:
            take_profit_val = TP * (high_swing - Close[index])

    if SL_choice == 'x (Swing Close) level 1':
        high_swing = Close[index]
        Low_swing = Close[index]
        high_flag = 0
        low_flag = 0
        j = index - 1
        while j > -1:
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
            stop_loss_val = SL * (high_swing - Close[index])
        elif Trade_Direction == 1:
            stop_loss_val = SL * (Close[index] - Low_swing)

    if TP_choice == 'x (Swing Close) level 2':
        high_swing = Close[index]
        Low_swing = Close[index]
        high_flag = 0
        low_flag = 0
        j = index - 2
        while j > -1:
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
            take_profit_val = TP * (Close[index] - Low_swing)
        elif Trade_Direction == 1:
            take_profit_val = TP * (high_swing - Close[index])

    if SL_choice == 'x (Swing Close) level 2':
        high_swing = Close[index]
        Low_swing = Close[index]
        high_flag = 0
        low_flag = 0
        j = index - 2
        while j > -1:
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
            stop_loss_val = SL * (high_swing - Close[index])
        elif Trade_Direction == 1:
            stop_loss_val = SL * (Close[index] - Low_swing)

    if TP_choice == 'x (Swing Close) level 3':
        high_swing = Close[index]
        Low_swing = Close[index]
        high_flag = 0
        low_flag = 0
        j = index - 3
        while j > -1:
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
            take_profit_val = TP * (Close[index] - Low_swing)
        elif Trade_Direction == 1:
            take_profit_val = TP * (high_swing - Close[index])

    if SL_choice == 'x (Swing Close) level 3':
        high_swing = Close[index]
        Low_swing = Close[index]
        high_flag = 0
        low_flag = 0
        j = index - 3
        while j > -1:
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
            stop_loss_val = SL * (high_swing - Close[index])
        elif Trade_Direction == 1:
            stop_loss_val = SL * (Close[index] - Low_swing)

    return stop_loss_val, take_profit_val
