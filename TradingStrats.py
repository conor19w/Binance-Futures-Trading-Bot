import pandas as pd
import numpy as np
from ta.momentum import stochrsi_d,stochrsi_k,stoch,stoch_signal,rsi,awesome_oscillator
from ta.trend import ema_indicator,macd_signal,macd,sma_indicator,adx,sma_indicator,cci
from ta.volatility import average_true_range,bollinger_pband,bollinger_hband,bollinger_lband,bollinger_mavg
from ta.volume import ease_of_movement,on_balance_volume,force_index,money_flow_index
from ta.momentum import tsi
import math
import statsmodels.api as sm
from sklearn import tree
from statsmodels.tsa.stattools import adfuller,coint
from math import log10, floor
from copy import copy
import time



def single_candle_swing_pump(prediction,Close,High,Low,CurrentPos,ClosePos,count,stoploss):
    prediction = -99
    number_bars = 1 ##how many bars to wait until we sell
    if High[-5]<High[-4]<High[-3] and High[-3]>High[-2]>High[-1] and CurrentPos == -99:
        prediction = 0
        #stoploss = 1.5*np.array(average_true_range(pd.Series(High), pd.Series(Low), pd.Series(Close)))[-1]
    elif Low[-5]<Low[-4]<Low[-3] and Low[-3]<Low[-2]<Low[-1] and CurrentPos == -99:
        prediction = 1
        #stoploss = 1.5*np.array(average_true_range(pd.Series(High), pd.Series(Low), pd.Series(Close)))[-1]
    if CurrentPos!=-99 and count==number_bars:
        ClosePos = 1
        count=0
    elif CurrentPos!=-99 and count!=number_bars:
        count+=1
    else:
        ClosePos = -99

    return prediction,ClosePos,count,stoploss
def RSI_trade(prediction,Close,CurrentPos,ClosePos):
    RSI = np.array(rsi(pd.Series(Close)))
    if RSI[-1]<30 and CurrentPos == -99: ## RSI[-2]>50 and RSI[-1]<50 and RSI[-1]>30 and CurrentPos == -99:
        prediction = 1
    elif RSI[-1]>70 and CurrentPos == -99: ##RSI[-2]<50 and RSI[-1]>50 and RSI[-1]<70  and CurrentPos == -99:
        prediction = 0
    elif CurrentPos == 0 and (RSI[-1]<30 or RSI[-1]>50):
        ClosePos = 1
    elif CurrentPos == 1 and (RSI[-1]>70 or RSI[-1]<50):
        ClosePos = 1
    else:
        ClosePos = 0
    return prediction,ClosePos



def candle_wick(prediction,Close,Open,High,Low):
    if Close[-5]<Close[-4]<Close[-3] and Close[-2]<Open[-2] and (High[-2]-Open[-2] + Close[-2]-Low[-2])> 15*(Open[-2]-Close[-2]) and Close[-1]<Close[-2]:
        ##3 green candles followed by a red candle with a huge wick
        prediction = 0
    elif Close[-5]>Close[-4]>Close[-3] and Close[-2]>Open[-2] and (High[-2]-Close[-2] + Open[-2]-Low[-2])> 15*(Close[-2]-Open[-2]) and Close[-1]>Close[-2]:
        ##3 red candles followed by a green candle with a huge wick
        prediction = 1
    return prediction,9

def fibMACD(prediction,Close,Open,High,Low):
    stoplossval = 0
    takeprofitval = 0
    period = 299 ##trend over this period: 15 min ETH:150 , BTC:200 , 5min ETH:180 , 1min ETH:
    MACD_signal = np.array(macd_signal(pd.Series(Close)))
    MACD = np.array(macd(pd.Series(Close)))
    Close_peaks = []
    location_peaks = []
    Close_troughs = []
    location_troughs = []
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
    max_pos=-99
    min_pos=-99
    if trend ==1:
        ##in an uptrend look for the recent max and min to calculate fib levels
        max_Close = -9999999
        min_Close = 9999999
        max_flag=0
        min_flag=0
        for i in range(len(Close_peaks)-1,-1,-1):
            if Close_peaks[i]>max_Close and max_flag<2:
                max_Close = Close_peaks[i]
                max_pos = location_peaks[i]
                max_flag=0
            elif max_flag==2:
                break
            else:
                max_flag+=1
        startpoint=-99
        for i in range(len(location_troughs)):
            if location_troughs[i]<max_pos:
                startpoint=i
            else:
                break
        for i in range(startpoint,-1,-1):
            if Close_troughs[i]<min_Close and min_flag<2:
                min_Close = Close_troughs[i]
                min_pos = location_troughs[i]
                min_flag=0
            elif min_flag==2:
                break
            else:
                min_flag+=1
        ##fibonacci levels
        fib_level_0 = max_Close
        fib_level_1 = max_Close - .236*(max_Close - min_Close)
        fib_level_2 = max_Close - .382 * (max_Close - min_Close)
        fib_level_3 = max_Close - .5 * (max_Close - min_Close)
        fib_level_4 = max_Close - .618 * (max_Close - min_Close)
        fib_level_5 = max_Close - .786 * (max_Close - min_Close)
        fib_level_6 = min_Close


        fib_retracement_level_1 = fib_level_0+1.236*(max_Close - min_Close) - Close[-1]##target max_Close+1.236*(max_Close - min_Close)
        fib_retracement_level_2 = fib_level_0+1.382*(max_Close - min_Close) - Close[-1]
        fib_retracement_level_3 = fib_level_0+1.5*(max_Close - min_Close) - Close[-1]
        fib_retracement_level_4 = fib_level_0+1.618*(max_Close - min_Close) - Close[-1]
        fib_retracement_level_5 = fib_level_0+1.786*(max_Close - min_Close) - Close[-1]
        fib_retracement_level_6 = fib_level_0+2*(max_Close - min_Close) - Close[-1]

        if fib_level_0>Low[-3]>fib_level_1 and Close[-4]>fib_level_1 and Close[-5]>fib_level_1 and Close[-6]>fib_level_1:
            if Close[-3] < Open[-3] < Close[-2] < Close[-1] and ((MACD_signal[-2]<MACD[-2] or MACD_signal[-3]<MACD[-3]) and MACD_signal[-1]>MACD[-1]): ##Bullish Engulfing Candle and cross up on MACD
                #print("level 1")
                prediction=1 ##signal a buy
                takeprofitval = fib_retracement_level_1
                stoplossval = Close[-1] - fib_level_1*1.0001
        elif fib_level_1>Low[-3]>fib_level_2 and Close[-4]>fib_level_2 and Close[-5]>fib_level_2 and Close[-6]>fib_level_2:
            if Close[-3] < Open[-3] < Close[-2] < Close[-1] and ((MACD_signal[-2]<MACD[-2] or MACD_signal[-3]<MACD[-3]) and MACD_signal[-1]>MACD[-1]): ##Bullish Engulfing Candle and cross up on MACD
                #print("level 1")
                prediction=1 ##signal a buy
                takeprofitval = fib_retracement_level_2
                stoplossval = Close[-1] - fib_level_2*1.0001

        elif fib_level_2>Low[-2]>fib_level_3 and Close[-3]>fib_level_3 and Close[-4]>fib_level_3 and Close[-5]>fib_level_3:
            if Close[-2] < Open[-2] < Close[-1] < Close[-1] and ((MACD_signal[-2]<MACD[-2] or MACD_signal[-3]<MACD[-3]) and MACD_signal[-1]>MACD[-1]): ##Bullish Engulfing Candle and cross up on MACD
                #print("level 2")
                prediction=1 ##signal a buy
                takeprofitval = fib_retracement_level_3
                stoplossval = Close[-1] - fib_level_3*1.0001

        elif fib_level_3>Low[-2]>fib_level_4 and Close[-3]>fib_level_4 and Close[-4]>fib_level_4 and Close[-5]>fib_level_4:
            if Close[-2] < Open[-2] < Close[-1] < Close[-1] and ((MACD_signal[-2]<MACD[-2] or MACD_signal[-3]<MACD[-3]) and MACD_signal[-1]>MACD[-1]): ##Bullish Engulfing Candle and cross up on MACD
                #print("level 3")
                prediction=1 ##signal a buy
                takeprofitval = fib_retracement_level_4
                stoplossval = Close[-1] - fib_level_4*1.0001
        elif fib_level_4>Low[-2]>fib_level_5 and Close[-3]>fib_level_5 and Close[-4]>fib_level_5 and Close[-5]>fib_level_5:
            if Close[-2] < Open[-2] < Close[-1] < Close[-1] and ((MACD_signal[-2]<MACD[-2] or MACD_signal[-3]<MACD[-3]) and MACD_signal[-1]>MACD[-1]): ##Bullish Engulfing Candle and cross up on MACD
                #print("level 4")
                prediction=1 ##signal a buy
                takeprofitval = fib_retracement_level_5
                stoplossval = Close[-1] - fib_level_5*1.0001
        elif fib_level_5>Low[-2]>fib_level_6 and Close[-3]>fib_level_6 and Close[-4]>fib_level_6 and Close[-5]>fib_level_6:
            if Close[-2] < Open[-2] < Close[-1] < Close[-1] and ((MACD_signal[-2]<MACD[-2] or MACD_signal[-3]<MACD[-3]) and MACD_signal[-1]>MACD[-1]): ##Bullish Engulfing Candle and cross up on MACD
                #print("level 5")
                prediction=1 ##signal a buy
                takeprofitval = fib_retracement_level_6
                stoplossval = Close[-1] - fib_level_6*1.0001

    elif trend ==0:
        ##in an downtrend look for the recent min and max to calculate fib levels
        max_Close = -9999999
        min_Close = 9999999
        max_flag = 0
        min_flag = 0
        for i in range(len(Close_troughs)-1, -1, -1):
            if Close_troughs[i] < min_Close and min_flag < 2:
                min_Close = Close_troughs[i]
                min_pos = location_troughs[i]
                min_flag = 0
            elif min_flag == 2:
                break
            else:
                min_flag += 1
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

        fib_retracement_level_1 = Close[-1] - (fib_level_0 + 1.236 * (max_Close - min_Close))
        fib_retracement_level_2 = Close[-1] - (fib_level_0 + 1.382 * (max_Close - min_Close))
        fib_retracement_level_3 = Close[-1] - (fib_level_0 + 1.5 * (max_Close - min_Close))
        fib_retracement_level_4 = Close[-1] - (fib_level_0 + 1.618 * (max_Close - min_Close))
        fib_retracement_level_5 = Close[-1] - (fib_level_0 + 1.786 * (max_Close - min_Close))
        fib_retracement_level_6 = Close[-1] - (fib_level_0 + 2 * (max_Close - min_Close))

        if fib_level_0 < High[-3] < fib_level_1 and Close[-4] < fib_level_1 and Close[-5] < fib_level_1 and Close[-6] < fib_level_1:
            if Close[-3] > Open[-3] > Close[-2] > Close[-1] and ((MACD_signal[-2] > MACD[-2] or MACD_signal[-3] > MACD[-3]) and MACD_signal[-1] < MACD[-1]):  ##Bearish Engulfing Candle and cross down on MACD
                #print("level 1")
                prediction = 0  ##signal a sell
                takeprofitval = fib_retracement_level_1
                stoplossval = fib_level_1*1.0001 - Close[-1]
        elif fib_level_1 < High[-3] < fib_level_2 and Close[-4] < fib_level_2 and Close[-5] < fib_level_2 and Close[-6] < fib_level_2:
            if Close[-3] > Open[-3] > Close[-2] > Close[-1] and ((MACD_signal[-2] > MACD[-2] or MACD_signal[-3] > MACD[-3]) and MACD_signal[-1] < MACD[-1]):  ##Bearish Engulfing Candle and cross down on MACD
                #print("level 1")
                prediction = 0  ##signal a sell
                takeprofitval = fib_retracement_level_2
                stoplossval = fib_level_2*1.0001 - Close[-1]
        elif fib_level_2 < High[-3] < fib_level_3 and Close[-4] < fib_level_3 and Close[-5] < fib_level_3 and Close[-6] < fib_level_3:
            if Close[-3] > Open[-3] > Close[-2] > Close[-1] and ((MACD_signal[-2] > MACD[-2] or MACD_signal[-3] > MACD[-3]) and MACD_signal[-1] < MACD[-1]):  ##Bearish Engulfing Candle and cross down on MACD
                #print("level 1")
                prediction = 0  ##signal a sell
                takeprofitval = fib_retracement_level_3
                stoplossval = fib_level_3*1.0001 - Close[-1]
        elif fib_level_3 < High[-3] < fib_level_4 and Close[-4] < fib_level_4 and Close[-5] < fib_level_4 and Close[-6] < fib_level_4:
            if Close[-3] > Open[-3] > Close[-2] > Close[-1] and ((MACD_signal[-2] > MACD[-2] or MACD_signal[-3] > MACD[-3]) and MACD_signal[-1] < MACD[-1]):  ##Bearish Engulfing Candle and cross down on MACD
                #print("level 1")
                prediction = 0  ##signal a sell
                takeprofitval = fib_retracement_level_4
                stoplossval = fib_level_4*1.0001 - Close[-1]
        elif fib_level_4 < High[-3] < fib_level_5 and Close[-4] < fib_level_5 and Close[-5] < fib_level_5 and Close[-6] < fib_level_5:
            if Close[-3] > Open[-3] > Close[-2] > Close[-1] and ((MACD_signal[-2] > MACD[-2] or MACD_signal[-3] > MACD[-3]) and MACD_signal[-1] < MACD[-1]):  ##Bearish Engulfing Candle and cross down on MACD
                #print("level 1")
                prediction = 0  ##signal a sell
                takeprofitval = fib_retracement_level_5
                stoplossval = fib_level_5*1.0001 - Close[-1]
        elif fib_level_5 < High[-3] < fib_level_6 and Close[-4] < fib_level_6 and Close[-5] < fib_level_6 and Close[-6] < fib_level_6:
            if Close[-3] > Open[-3] > Close[-2] > Close[-1] and ((MACD_signal[-2] > MACD[-2] or MACD_signal[-3] > MACD[-3]) and MACD_signal[-1] < MACD[-1]):  ##Bearish Engulfing Candle and cross down on MACD
                #print("level 1")
                prediction = 0  ##signal a sell
                takeprofitval = fib_retracement_level_6
                stoplossval = fib_level_6*1.0001 - Close[-1]

    return prediction,stoplossval,takeprofitval






def MTFMACD(prediction,Close_1hr,Close_15min,Close):

    EMA50_1hr = np.array(ema_indicator(pd.Series(Close_1hr), window=50))
    EMA50_15min = np.array(ema_indicator(pd.Series(Close_15min), window=50))
    MACD_signal = macd_signal(pd.Series(Close))

    ##Look for divergence in macd



def goldenCross(prediction,CloseStream):
    EMA100 = np.array(ema_indicator(pd.Series(CloseStream), window=100))
    EMA50 = np.array(ema_indicator(pd.Series(CloseStream), window=50))
    EMA20 = np.array(ema_indicator(pd.Series(CloseStream), window=20))
    RSI = np.array(rsi(pd.Series(CloseStream)))
    if CloseStream[-1]>EMA100[-1] and RSI[-1]>50:
        ##looking for long entries
        if (EMA20[-2]<EMA50[-2] and EMA20[-1]>EMA50[-1]) or (EMA20[-3]<EMA50[-3] and EMA20[-1]>EMA50[-1]) or (EMA20[-4]<EMA50[-4] and EMA20[-1]>EMA50[-1]):
            ##Cross up occured
            prediction=1 ##buy
    elif CloseStream[-1]<EMA100[-1] and RSI[-1]<50:
        ##looking for short entries
        if (EMA20[-2]>EMA50[-2] and EMA20[-1]<EMA50[-1]) or (EMA20[-3]>EMA50[-3] and EMA20[-1]<EMA50[-1]) or (EMA20[-4]>EMA50[-4] and EMA20[-1]<EMA50[-1]):
            ##Cross up occured
            prediction=0 ##Sell

    return prediction,6

def StochRSI_RSIMACD(prediction,CloseStream,signal1,signal2):
    #prediction=-99
    EMA200 = np.array(ema_indicator(pd.Series(CloseStream),window=200))
    fastd = np.array(stochrsi_d(pd.Series(CloseStream)))
    fastk = np.array(stochrsi_k(pd.Series(CloseStream)))
    RSI = np.array(rsi(pd.Series(CloseStream)))
    MACD = np.array(macd(pd.Series(CloseStream)))
    macdsignal= np.array(macd_signal(pd.Series(CloseStream)))
    ##buy signal
    if fastk[-1] <=20 and fastd[-1] <=20:
        signal1 = 1
    elif fastk[-1] >=80 and fastd[-1] >=80:
        signal1 = 0

    if signal1 ==1:
        if RSI[-1]>50:
            if macdsignal[-1]<MACD[-1]:
                signal2=1
    elif signal1 == 0:
        if RSI[-1]<50:
            if macdsignal[-1] > MACD[-1]:
                signal2=0

    if signal1 == signal2 == 0:
        if fastk[-1] >= 20 and fastd[-1] >= 20:
            prediction=0
        else:
            signal1=-99
            signal2 = -99

    elif signal1 == signal2 == 1 and CloseStream[-1]>EMA200[-1] and CloseStream[-2]>EMA200[-2] and CloseStream[-3]>EMA200[-3] and CloseStream[-4]>EMA200[-4] and CloseStream[-5]>EMA200[-5]:
        if fastk[-1] <=80 and fastd[-1] <=80:
            prediction=1
        else:
            signal1=-99
            signal2 = -99

    return prediction,signal1,signal2,3

def StochRSIMACD(prediction,CloseStream,HighStream,LowStream):
    Close = pd.Series(CloseStream)
    High = pd.Series(HighStream)
    Low = pd.Series(LowStream)
    fastd = np.array(stoch(close=Close,high=High,low=Low))
    fastk = np.array(stoch_signal(close=Close,high=High,low=Low))
    RSI = np.array(rsi(Close))
    MACD = np.array(macd(Close))
    macdsignal= np.array(macd_signal(Close))
    if ((fastd[-1]<20 and fastk[-1]<20 and RSI[-1]>50 and MACD[-1]>macdsignal[-1] and MACD[-2]<macdsignal[-2]) or
        (fastd[-2] < 20 and fastk[-2] < 20 and RSI[-1] > 50 and MACD[-1] > macdsignal[-1] and MACD[-3] < macdsignal[-3] and fastd[-1] < 80 and fastk[-1] < 80) or
        (fastd[-3] < 20 and fastk[-3] < 20 and RSI[-1] > 50 and MACD[-1] > macdsignal[-1] and MACD[-2] < macdsignal[-2] and fastd[-1] < 80 and fastk[-1] < 80) or
        (fastd[-4] < 20 and fastk[-4] < 20 and RSI[-1] > 50 and MACD[-1] > macdsignal[-1] and MACD[-3] < macdsignal[-3] and fastd[-1] < 80 and fastk[-1] < 80)):
        prediction = 1
    elif ((fastd[-1]>80 and fastk[-1]>80 and RSI[-1]<50 and MACD[-1]<macdsignal[-1] and MACD[-2]>macdsignal[-2]) or
        (fastd[-2]>80 and fastk[-2]>80 and RSI[-1]<50 and MACD[-1]<macdsignal[-1] and MACD[-3]>macdsignal[-3] and fastd[-1]>20 and fastk[-1]>20) or
        (fastd[-3]>80 and fastk[-3]>80 and RSI[-1]<50 and MACD[-1]<macdsignal[-1] and MACD[-2]>macdsignal[-2] and fastd[-1]>20 and fastk[-1]>20) or
        (fastd[-4]>80 and fastk[-4]>80 and RSI[-1]<50 and MACD[-1]<macdsignal[-1] and MACD[-3]>macdsignal[-3] and fastd[-1]>20 and fastk[-1]>20)):
        prediction = 0

    return prediction,2

##############################################################################################################################
##############################################################################################################################
##############################################################################################################################
def tripleEMA(CloseStream,OpenStream,prediction):
    EMA3 = np.array(ema_indicator(pd.Series(CloseStream), window=5))
    EMA6 = np.array(ema_indicator(pd.Series(CloseStream), window=20))
    EMA9 = np.array(ema_indicator(pd.Series(CloseStream), window=50))

    if  EMA3[-5]>EMA6[-5] and EMA3[-5]>EMA9[-5] \
            and EMA3[-4]>EMA6[-4] and EMA3[-4]>EMA9[-4] \
            and EMA3[-3]>EMA6[-3] and EMA3[-3]>EMA9[-3] \
            and EMA3[-2]>EMA6[-2] and EMA3[-2]>EMA9[-2] \
            and EMA3[-1]<EMA6[-1] and EMA3[-1]<EMA9[-1] :
        prediction=0
    if EMA3[-5]<EMA6[-5] and EMA3[-5]<EMA9[-5] \
            and EMA3[-4]<EMA6[-4] and EMA3[-4]<EMA9[-4] \
            and EMA3[-3]<EMA6[-3] and EMA3[-3]<EMA9[-3] \
            and EMA3[-2]<EMA6[-2] and EMA3[-2]<EMA9[-2] \
            and EMA3[-1]>EMA6[-1] and EMA3[-1]>EMA9[-1] :
        prediction=1
    return prediction,3

def tripleEMAStochasticRSIATR(CloseStream,signal1,signal2,prediction):
    #newOrder = 0
    Close = np.array(CloseStream)
    EMA50 = np.array(ema_indicator(pd.Series(CloseStream),window=50))
    EMA14 = np.array(ema_indicator(pd.Series(CloseStream),window=14))
    EMA8 = np.array(ema_indicator(pd.Series(CloseStream),window=8))
    fastd = np.array(stochrsi_d(pd.Series(CloseStream)))
    fastk = np.array(stochrsi_k(pd.Series(CloseStream)))
    ##buy signal
    if (Close[-1]>EMA8[-1]>EMA14[-1]>EMA50[-1]) and ((fastk[-1]>fastd[-1]) and (fastk[-2]<fastd[-2])): #and (fastk[-1]<80 and fastd[-1]<80):
        signal1=1
    elif (Close[-1]<EMA8[-1]<EMA14[-1]<EMA50[-1]) and ((fastk[-1]<fastd[-1]) and (fastk[-2]>fastd[-2])) : #and (fastk[-1]>20 and fastd[-1]>20):
        signal1=0
    else:
        signal1=-99

    if signal1 == 0:
        prediction=0
    elif signal1 == 1:
        prediction=1
    return  prediction, signal1, signal2, 1

##############################################################################################################################
##############################################################################################################################
##############################################################################################################################



def RSIStochEMA(prediction,CloseStream,HighStream,LowStream,signal1,currentPos):

    period = 60
    CloseS = pd.Series(CloseStream)
    Close = np.array(CloseStream)
    # High = np.array(HighStream)
    # Low = np.array(LowStream)
    fastk = np.array(stoch_signal(pd.Series(HighStream), pd.Series(LowStream), pd.Series(CloseStream)))
    fastd = np.array(stoch(pd.Series(HighStream), pd.Series(LowStream), pd.Series(CloseStream)))
    RSI = np.array(rsi(CloseS))
    EMA200 = np.array(ema_indicator(CloseS, window=200))
    peaks_RSI = []
    corresponding_Close_peaks = []
    location_peaks = []
    troughs_RSI = []
    corresponding_Close_troughs = []
    location_troughs =[]
    #####################Find peaks & troughs in RSI ##############################
    for i in range(len(RSI)-period,len(RSI)-2):
        if RSI[i]>RSI[i-1] and RSI[i]>RSI[i+1] and RSI[i]>RSI[i-2] and RSI[i]>RSI[i+2]:
            ##Weve found a peak:
            peaks_RSI.append(RSI[i])
            corresponding_Close_peaks.append(Close[i])
            location_peaks.append(i)
        elif RSI[i]<RSI[i-1] and RSI[i]<RSI[i+1] and RSI[i]<RSI[i-2] and RSI[i]<RSI[i+2]:
            ##Weve found a trough:
            troughs_RSI.append(RSI[i])
            corresponding_Close_troughs.append(Close[i])
            location_troughs.append(i)
    ##Lower High Price & Higher High RSI => Bearish Divergence
    ##Higher Low Price & Lower low RSI => Bullish Divergence
    length = 0
    if len(peaks_RSI)>len(troughs_RSI):
        length=len(peaks_RSI)
    else:
        length=len(troughs_RSI)
    loc1 = -99
    loc2 = -99
    if length!=0:
        for i in range(length-1):
            if i<len(peaks_RSI):
                ##Check for hidden Bearish Divergence
                if peaks_RSI[i]<peaks_RSI[-1] and corresponding_Close_peaks[i]>corresponding_Close_peaks[-1] and peaks_RSI[-1]-peaks_RSI[i]>1:
                    for j in range(i+1,len(peaks_RSI)-1):
                        if peaks_RSI[j]>peaks_RSI[i]:
                            break
                        elif j==len(peaks_RSI)-2:
                            loc1=location_peaks[i]

            if i<len(troughs_RSI):
            ##Check for hidden Bullish Divergence
                if troughs_RSI[i] > troughs_RSI[-1] and corresponding_Close_troughs[i] < corresponding_Close_troughs[-1] and troughs_RSI[i] - troughs_RSI[-1]>1:
                    for j in range(i+1,len(troughs_RSI)-1):
                        if troughs_RSI[j]<troughs_RSI[i]:
                            break
                        elif j == len(troughs_RSI)-2:
                           loc2 = location_troughs[i]
        if loc1==loc2:
            signal1=-99
        elif loc1>loc2:# and 300-loc1<15:
            signal1=0
            #print(300-loc1)
        else:# 300-loc2<15:
            #print(300-loc2)
            signal1=1
        '''else:
            signal1=-99'''



    ##Bullish Divergence
    if signal1==1 and (fastk[-1]>fastd[-1] and (fastk[-2]<fastd[-2] or fastk[-3]<fastd[-3])) and Close[-1]>EMA200[-1]:
        prediction=1
        signal1=-99

    ##Bearish Divergence
    elif signal1==0 and (fastk[-1]<fastd[-1] and (fastk[-2]>fastd[-2] or fastk[-3]>fastd[-3])) and Close[-1]<EMA200[-1]:
        prediction=0
        signal1=-99

    if currentPos!=-99:
        signal1=-99
        prediction=-99

    return prediction, signal1, 4


##############################################################################################################

def stochBB(prediction,CloseStream):
    fastd = np.array(stochrsi_d(pd.Series(CloseStream)))
    fastk = np.array(stochrsi_k(pd.Series(CloseStream)))

    #print(fastd[-1],fastk[-1])
    percent_B = np.array(bollinger_pband(pd.Series(CloseStream)))
    percent_B1= percent_B[-1]
    percent_B2 = percent_B[-2]
    percent_B3 = percent_B[-3]
    #print(percent_B)

    if fastk[-1]<.2 and fastd[-1]<.2 and (fastk[-1]>fastd[-1] and fastk[-2]<fastd[-2])   and (percent_B1<0 or percent_B2<0 or percent_B3<0):# or percent_B3<0):# or percent_B2<.05):
        prediction=1
    elif fastk[-1]>.8 and fastd[-1]>.8 and (fastk[-1]<fastd[-1] and fastk[-2]>fastd[-2])  and (percent_B1>1 or percent_B2>1 or percent_B3>1):# or percent_B3>1):# or percent_B2>1):
        prediction=0

    return prediction,6


def breakout(prediction,CloseStream,VolumeStream,symbol):
    invert=1
    #if symbol=='BTCUSDT' or symbol=='ETHUSDT':
    #    invert=0
    Close = pd.Series(CloseStream).pct_change()
    Volume = pd.Series(VolumeStream[:-1])
    max_Close = Close.iloc[:-1].rolling(10).max()
    min_Close = Close.iloc[:-1].rolling(10).min()
    max_Vol = Volume.rolling(10).max()
    if invert:
        if Close.iloc[-1]>max_Close.iloc[-1] and VolumeStream[-1]>max_Vol.iloc[-1]:
            prediction = 0
        elif Close.iloc[-1]<min_Close.iloc[-1] and VolumeStream[-1]>max_Vol.iloc[-1]:
            prediction = 1
    else:
        if Close.iloc[-1]>max_Close.iloc[-1] and VolumeStream[-1]>max_Vol.iloc[-1]:
            prediction = 1
        elif Close.iloc[-1]<min_Close.iloc[-1] and VolumeStream[-1]>max_Vol.iloc[-1]:
            prediction = 0
    return_type=9
    '''if symbol=='DOGEUSDT':
        return_type=9
    elif symbol=='SOLUSDT':
        return_type = 8'''
    return prediction,return_type

def fakeout(prediction,CloseStream,VolumeStream,symbol):
    invert = 1
    #if symbol == 'BTCUSDT' or symbol == 'ETHUSDT':
    #    invert = 0
    Close = pd.Series(CloseStream) #.pct_change() ##get size of bars in a percentage
    Volume = pd.Series(VolumeStream[:-1])
    max_Close = Close.iloc[:-1].rolling(15).max()
    min_Close = Close.iloc[:-1].rolling(15).min()
    max_Vol = Volume.rolling(15).max()
    if invert:
        if Close.iloc[-1] > max_Close.iloc[-1] and VolumeStream[-1] < max_Vol.iloc[-1]:
            prediction = 0
        elif Close.iloc[-1] < min_Close.iloc[-1] and VolumeStream[-1] < max_Vol.iloc[-1]:
            prediction = 1
    else:
        if Close.iloc[-1] > max_Close.iloc[-1] and VolumeStream[-1] < max_Vol.iloc[-1]:
            prediction = 1
        elif Close.iloc[-1] < min_Close.iloc[-1] and VolumeStream[-1] < max_Vol.iloc[-1]:
            prediction = 0

    return prediction, 9

'''def sma_crossover(prediction,CloseStream,HighStream,LowStream):
    fastk = np.array(stoch_signal(pd.Series(HighStream), pd.Series(LowStream), pd.Series(CloseStream)))
    fastd = np.array(stoch(pd.Series(HighStream), pd.Series(LowStream), pd.Series(CloseStream)))
    SMA100 = sma_indicator(pd.Series(CloseStream),window=100)
    SMA200 = sma_indicator(pd.Series(CloseStream),window=200)

    if SMA100[-1]<SMA200[-1] and SMA100[-2]>SMA200[-2]:'''
def trend_Ride(prediction,Close,High,Low,percent,current_Pos,Highest_lowest):
    close_pos = 0
    if (Close[-1]-Close[-2])/Close[-2] > percent and current_Pos==-99:
        prediction = 1 ##uptrend so open long
        Highest_lowest = Close[-1]
    elif (Close[-1]-Close[-2])/Close[-2] < -percent and current_Pos==-99:
        prediction = 0 ##downtrend so open short position
        Highest_lowest = Close[-1]
    if current_Pos == 1 and (Close[-1] - Highest_lowest)/Highest_lowest < - percent/3:
        close_pos = 1
    elif current_Pos == 0 and  (Highest_lowest - Close[-1])/Highest_lowest< - percent/3:
        close_pos = 1
    elif current_Pos == 1 and Highest_lowest < High:
        Highest_lowest = High
    elif current_Pos == 0 and  Highest_lowest > Low:
        Highest_lowest = Low
    return prediction,Highest_lowest,close_pos

def pairTrading(prediction,Close1,Close2,log=0,TPSL=0,percent_TP=0,percent_SL=0):
    new_Close = []
    '''Close1_TP = 0
    Close2_TP = 0
    Close1_SL = 0
    Close2_SL = 0'''
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
        prediction = [0,1]  # [1,0]
        '''if TPSL:
            ##work out distance to the mean and allocate the change to get there to each series:
            #print(new_Close[-1],SMA20[-1])
            #change_in_decimal = math.fabs((new_Close[-1] - SMA20[-1])/new_Close[-1])
            #Close1_TP = Close1[-1] * change_in_decimal/3
            #Close2_TP = Close2[-1] * change_in_decimal/3
            Close1_TP = Close1[-1]*percent_TP
            Close2_TP = Close2[-1]*percent_TP
            Close1_SL = Close1[-1] * percent_SL
            Close2_SL = Close2[-1] * percent_SL'''
    elif BB[-1]<0:
        prediction = [1,0] # [0,1]
        '''if TPSL:
            ##work out distance to the mean and allocate the change to get there to each series:
            #print(new_Close[-1],SMA20[-1])
            #change_in_decimal = math.fabs((new_Close[-1] - SMA20[-1])/new_Close[-1])
            #Close1_TP = Close1[-1] * change_in_decimal/3
            #Close2_TP = Close2[-1] * change_in_decimal/3
            #print(change_in_decimal)
            Close1_TP = Close1[-1] * percent_TP
            Close2_TP = Close2[-1] * percent_TP
            Close1_SL = Close1[-1] * percent_SL
            Close2_SL = Close2[-1] * percent_SL'''
    return prediction,[9,9] #,Close1_TP,Close2_TP,Close1_SL,Close2_SL


def pairTrading_Crossover(prediction, Close1, Close2, CurrentPos, percent_SL=0):
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
        prediction = [0,1]
        Close1_SL = Close1[-1] * percent_SL
        Close2_SL = Close2[-1] * percent_SL
    elif BB[-1]<0:
        prediction = [1,0]
        Close1_SL = Close1[-1] * percent_SL
        Close2_SL = Close2[-1] * percent_SL
    if CurrentPos!=-99:
        if (new_Close[-1]>SMA20[-1] and (new_Close[-2]<SMA20[-2] or new_Close[-3]<SMA20[-3])) or (new_Close[-1]<SMA20[-1] and (new_Close[-2]>SMA20[-2] or new_Close[-3]>SMA20[-3])):
            ##Price has crossed up or down over the Moving average so close the position
            Close_pos=1
    return prediction,Close1_SL,Close2_SL,Close_pos


##Function used to decide stoploss values and takeprofit values based off a type variable returned by specific strategies above
def SetSLTP(stoplossval, takeprofitval,CloseStream,HighStream,LowStream,prediction,CurrentPos,Type,SL=1,TP=1):
    ##Average True Range with multipliers
    if Type==1:
        ATR = np.array(average_true_range(pd.Series(HighStream), pd.Series(LowStream), pd.Series(CloseStream)))
        if prediction == 0 and CurrentPos == -99:
            stoplossval = 1.5 * ATR[-1]
            takeprofitval = 8 * ATR[-1]
        elif prediction == 1 and CurrentPos == -99:
            stoplossval = 1.5 * ATR[-1]
            takeprofitval = 8 * ATR[-1]

    ## Highest/Lowest Close in last 30 periods
    elif Type==2:
        highswing = CloseStream[-2]
        Lowswing = CloseStream[-2]
        highflag = 0
        lowflag = 0
        for j in range(-3, -20, -1):
            if CloseStream[j] > highswing and highflag == 0:
                highswing = CloseStream[j]
            if CloseStream[j] < Lowswing and lowflag == 0:
                Lowswing = CloseStream[j]

        if prediction == 0 and CurrentPos == -99:
            stoplossval = (highswing - CloseStream[-1])
            #if stoplossval>.15*CloseStream[-1]:
            #    stoplossval=.15*CloseStream[-1]
            if stoplossval < 0:
                stoplossval *= -1
            takeprofitval = stoplossval * 2
        elif prediction == 1 and CurrentPos == -99:
            stoplossval = (CloseStream[-1] - Lowswing)
            #if stoplossval>.15*CloseStream[-1]:
            #    stoplossval=.15*CloseStream[-1]
            if stoplossval < 0:
                stoplossval *= -1
            takeprofitval = stoplossval * 2

    ## Closest Swing High/Low
    elif Type==3:
        highswing = CloseStream[-2]
        Lowswing = CloseStream[-2]
        highflag = 0
        lowflag = 0
        for j in range(-3, -50, -1):
            if CloseStream[j] > highswing and CloseStream[j] > CloseStream[j - 1] and CloseStream[j] > CloseStream[j - 2] and highflag == 0:
                highswing = CloseStream[j]
                highflag = 1
            if CloseStream[j] < Lowswing and CloseStream[j] < CloseStream[j - 1] and CloseStream[j] < CloseStream[j - 2] and lowflag == 0:
                Lowswing = CloseStream[j]
                lowflag = 1

        if prediction == 0 and CurrentPos == -99:
            stoplossval = (highswing - CloseStream[-1])*1.003
            if stoplossval < 0:
                stoplossval *= -1
            takeprofitval = (highswing - CloseStream[-1]) * 1.25

        elif prediction == 1 and CurrentPos == -99:
            stoplossval = (CloseStream[-1] - Lowswing)*1.003
            if stoplossval < 0:
                stoplossval *= -1
            takeprofitval = (CloseStream[-1] - Lowswing) * 1.25
    ## Closest Swing Close in Last 60 periods
    elif Type == 4:
        highswing = CloseStream[-1]
        Lowswing = CloseStream[-1]
        highflag = 0
        lowflag = 0
        for j in range(-3, -60, -1):
            if CloseStream[j] > highswing and CloseStream[j] > CloseStream[j - 1] and CloseStream[j] > CloseStream[j - 2] and \
                    CloseStream[j] > CloseStream[j + 2] and CloseStream[j] > CloseStream[j + 1] and highflag == 0:
                highswing = CloseStream[j]
                highflag = 1
            if CloseStream[j] < Lowswing and CloseStream[j] < CloseStream[j - 1] and CloseStream[j] < CloseStream[j - 2] and \
                    CloseStream[j] < CloseStream[j + 2] and CloseStream[j] < CloseStream[j + 1] and lowflag == 0:
                Lowswing = CloseStream[j]
                lowflag = 1

        if prediction == 0 and CurrentPos == -99:
            stoplossval = (highswing - CloseStream[-1])*.5
            if stoplossval < 0:
                stoplossval *= -1
            takeprofitval = stoplossval * 2

        elif prediction == 1 and CurrentPos == -99:
            stoplossval = (CloseStream[-1] - Lowswing)*.5
            if stoplossval < 0:
                stoplossval *= -1
            takeprofitval = stoplossval * 2

    elif Type==5:
        ATR = np.array(average_true_range(pd.Series(HighStream), pd.Series(LowStream), pd.Series(CloseStream)))

        highswing = HighStream[-1]
        Lowswing = LowStream[-1]
        highflag = 0
        lowflag = 0
        for j in range(-3, -60, -1):
            if HighStream[j] > highswing and HighStream[j] > HighStream[j - 1] and HighStream[j] > HighStream[j - 2] and HighStream[j] > HighStream[j + 2] and HighStream[j] > HighStream[j + 1] and highflag == 0:
                highswing = HighStream[j]
                highflag = 1
            if LowStream[j] < Lowswing and LowStream[j] < LowStream[j - 1] and LowStream[j] < LowStream[j - 2] and LowStream[j] < LowStream[j + 2] and LowStream[j] < LowStream[j + 1] and lowflag == 0:
                Lowswing = LowStream[j]
                lowflag = 1

        if prediction == 0 and CurrentPos == -99:
            temp = (highswing - CloseStream[-1])
            stoplossval = 1.25 * ATR[-1]
            if temp < 0:
                temp *= -1
            takeprofitval = temp * 2

        elif prediction == 1 and CurrentPos == -99:
            temp = (CloseStream[-1] - Lowswing)
            stoplossval = 1.25 * ATR[-1]
            if temp < 0:
                temp *= -1
            takeprofitval = temp * 2

    elif Type==6:
        ATR = np.array(average_true_range(pd.Series(HighStream), pd.Series(LowStream), pd.Series(CloseStream)))
        if prediction == 0 and CurrentPos == -99:
            stoplossval = 0.5 * ATR[-1]
            takeprofitval = 2 * ATR[-1]
        elif prediction == 1 and CurrentPos == -99:
            stoplossval = 0.5 * ATR[-1]
            takeprofitval = 2 * ATR[-1]

    elif Type==7:
        stoplossval = .007*CloseStream[-1]
        takeprofitval = .01*CloseStream[-1]

    elif Type==8:
        ATR = np.array(average_true_range(pd.Series(HighStream[:-1]), pd.Series(LowStream[:-1]), pd.Series(CloseStream[:-1]),window=25))
        if prediction == 0 and CurrentPos == -99:
            stoplossval = 2 * ATR[-1]
            takeprofitval = 2.5 * ATR[-1]
        elif prediction == 1 and CurrentPos == -99:
            stoplossval = 2 * ATR[-1]
            takeprofitval = 2.5 * ATR[-1]
    elif Type==9:
        ATR = np.array(average_true_range(pd.Series(HighStream[:-1]), pd.Series(LowStream[:-1]), pd.Series(CloseStream[:-1]),window=20))
        if prediction == 0 and CurrentPos == -99:
            stoplossval = SL * ATR[-1]
            takeprofitval = TP * ATR[-1]
        elif prediction == 1 and CurrentPos == -99:
            stoplossval = SL * ATR[-1]
            takeprofitval = TP * ATR[-1]
    return stoplossval,takeprofitval
