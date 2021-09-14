import pandas as pd
import numpy as np
from ta.momentum import stochrsi_d,stochrsi_k,stoch,stoch_signal,rsi
from ta.trend import ema_indicator,macd_signal,macd,sma_indicator,adx
from ta.volatility import average_true_range,bollinger_pband
from ta.momentum import tsi
import math


def MTFMACD(prediction1,Close_1hr,Close_15min,Close):

    EMA50_1hr = np.array(ema_indicator(pd.Series(Close_1hr), window=50))
    EMA50_15min = np.array(ema_indicator(pd.Series(Close_15min), window=50))
    MACD_signal = macd_signal(pd.Series(Close))

    ##Look for divergence in macd



def goldenCross(prediction1,CloseStream):
    EMA100 = np.array(ema_indicator(pd.Series(CloseStream), window=100))
    EMA50 = np.array(ema_indicator(pd.Series(CloseStream), window=50))
    EMA20 = np.array(ema_indicator(pd.Series(CloseStream), window=20))
    RSI = np.array(rsi(pd.Series(CloseStream)))
    if CloseStream[-1]>EMA100[-1] and RSI[-1]>50:
        ##looking for long entries
        if (EMA20[-2]<EMA50[-2] and EMA20[-1]>EMA50[-1]) or (EMA20[-3]<EMA50[-3] and EMA20[-1]>EMA50[-1]) or (EMA20[-4]<EMA50[-4] and EMA20[-1]>EMA50[-1]):
            ##Cross up occured
            prediction1=1 ##buy
    elif CloseStream[-1]<EMA100[-1] and RSI[-1]<50:
        ##looking for short entries
        if (EMA20[-2]>EMA50[-2] and EMA20[-1]<EMA50[-1]) or (EMA20[-3]>EMA50[-3] and EMA20[-1]<EMA50[-1]) or (EMA20[-4]>EMA50[-4] and EMA20[-1]<EMA50[-1]):
            ##Cross up occured
            prediction1=0 ##Sell

    return prediction1,6

def StochRSIMACD(prediction1,CloseStream,signal1,signal2):
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
            prediction1=0
        else:
            signal1=-99
            signal2 = -99

    elif signal1 == signal2 == 1:
        if fastk[-1] <=80 and fastd[-1] <=80:
            prediction1=1
        else:
            signal1=-99
            signal2 = -99

    return prediction1,signal1,signal2,2


##############################################################################################################################
##############################################################################################################################
##############################################################################################################################

def tripleEMAStochasticRSIATR(CloseStream,signal1,signal2,prediction1):
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
        prediction1=0
    elif signal1 == 1:
        prediction1=1
    return  prediction1, signal1, signal2, 1

##############################################################################################################################
##############################################################################################################################
##############################################################################################################################


def Fractal(CloseStream,LowStream,HighStream,prediction1):
    stoplossval = 0
    takeprofitval = 0
    try:
        Close = np.array(CloseStream)
        High = np.array(HighStream)
        Low = np.array(LowStream)
        #RSI = np.array(rsi(pd.Series(CloseStream)))
        #TSI = np.array(tsi(pd.Series(CloseStream)))
        CloseS = pd.Series(CloseStream)
        LowS = pd.Series(LowStream)
        HighS = pd.Series(HighStream)
        ADX = np.array(adx(high=HighS,low=LowS,close=CloseS))
        #EMA200 = np.array(ema_indicator(CloseS,window=200))
        EMA100 = np.array(ema_indicator(CloseS,window=100))
        EMA50 = np.array(ema_indicator(CloseS,window=50))
        EMA20 = np.array(ema_indicator(CloseS,window=20))

        if (High[-3]>High[-5] and High[-3]>High[-4] and High[-3]>High[-2] and High[-3]>High[-1]) and \
                EMA20[-5]<EMA50[-5]<EMA100[-5] and EMA20[-4]<EMA50[-4]<EMA100[-4] and EMA20[-1]<EMA50[-1]<EMA100[-1] \
                and EMA20[-2]<EMA50[-2]<EMA100[-2] and EMA20[-3]<EMA50[-3]<EMA100[-3] and\
                (EMA50[-3]>High[-3]>EMA20[-3]) \
                 and Close[-5]<EMA100[-5] and Close[-4]<EMA100[-4] and Close[-3]<EMA100[-3] and Close[-2]<EMA100[-2] and Close[-1]<EMA100[-1] and ADX[-1]>25:
            prediction1=0
            stoplossval=math.fabs(Close[-1]-EMA50[-1])*1.05
            takeprofitval = math.fabs(Close[-1]-EMA50[-1])*1.55
        elif (High[-3]>High[-5] and High[-3]>High[-4] and High[-3]>High[-2] and High[-3]>High[-1]) and \
                EMA20[-5]<EMA50[-5]<EMA100[-5] and EMA20[-4]<EMA50[-4]<EMA100[-4] and EMA20[-1]<EMA50[-1]<EMA100[-1]\
                and EMA20[-2]<EMA50[-2]<EMA100[-2] and EMA20[-3]<EMA50[-3]<EMA100[-3] and\
                (EMA100[-3]>High[-3]>EMA50[-3]) \
                and Close[-5]<EMA100[-5] and Close[-4]<EMA100[-4] and Close[-3]<EMA100[-3] and Close[-2]<EMA100[-2] and Close[-1]<EMA100[-1] and ADX[-1]>25:
            prediction1=0
            stoplossval = math.fabs(Close[-1]-EMA100[-1])*1.05
            takeprofitval =   math.fabs(Close[-1]-EMA100[-1])*1.55
        elif (Low[-3]<Low[-5] and Low[-3]<Low[-4] and Low[-3]<Low[-2] and Low[-3]<Low[-1]) and \
                EMA20[-5] > EMA50[-5] > EMA100[-5] and EMA20[-4] > EMA50[-4] > EMA100[-4] and EMA20[-1] > EMA50[-1] > EMA100[-1]\
                and EMA20[-2] > EMA50[-2] > EMA100[-2] and EMA20[-3] > EMA50[-3] > \
                EMA100[-3] and \
                (EMA50[-3] < Low[-3] < EMA20[-3]) \
                and Close[-5] > EMA100[-5] and Close[-4] > EMA100[-4] and Close[-3] > EMA100[-3] and Close[-2] > EMA100[-2] and Close[-1] > EMA100[-1] and ADX[-1]>25:
            prediction1 = 1
            stoplossval = math.fabs(Close[-1] - EMA50[-1])*1.05
            takeprofitval =   math.fabs(Close[-1]-EMA50[-1])*1.55
        elif (Low[-3]<Low[-5] and Low[-3]<Low[-4] and Low[-3]<Low[-2] and Low[-3]<Low[-1]) and \
                EMA20[-5] > EMA50[-5] > EMA100[-5] and EMA20[-4] > EMA50[-4] > EMA100[-4] and EMA20[-1]>EMA50[-1]>EMA100[-1]\
                and EMA20[-2]>EMA50[-2]>EMA100[-2] and EMA20[-3]>EMA50[-3]>EMA100[-3] and \
                (EMA100[-3]<Low[-3]<EMA50[-3]) \
                and Close[-5] > EMA100[-5] and Close[-4] > EMA100[-4] and Close[-3]>EMA100[-3] and Close[-2]>EMA100[-2] and Close[-1]>EMA100[-1] and ADX[-1]>25:
            prediction1=1
            stoplossval = math.fabs(Close[-1]-EMA100[-1])*1.05
            takeprofitval = math.fabs(Close[-1]-EMA100[-1])*1.55
        else:
            prediction1=-99
    except RuntimeWarning as e:
        pass

    return prediction1,stoplossval,takeprofitval


def RSIStochEMA(prediction1,CloseStream,HighStream,LowStream,signal1,currentPos):

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
        prediction1=1
        signal1=-99

    ##Bearish Divergence
    elif signal1==0 and (fastk[-1]<fastd[-1] and (fastk[-2]>fastd[-2] or fastk[-3]>fastd[-3])) and Close[-1]<EMA200[-1]:
        prediction1=0
        signal1=-99

    if currentPos!=-99:
        signal1=-99
        prediction1=-99

    return prediction1, signal1, 4,loc1,location_peaks[-1],loc2,location_troughs[-1],location_peaks,RSI


##############################################################################################################

def stochBB(prediction1,CloseStream):
    fastd = np.array(stochrsi_d(pd.Series(CloseStream)))
    fastk = np.array(stochrsi_k(pd.Series(CloseStream)))

    #print(fastd[-1],fastk[-1])
    percent_B = np.array(bollinger_pband(pd.Series(CloseStream)))
    percent_B1= percent_B[-1]
    percent_B2 = percent_B[-2]
    percent_B3 = percent_B[-3]
    #print(percent_B)

    if fastk[-1]<.2 and fastd[-1]<.2 and (fastk[-1]>fastd[-1] and fastk[-2]<fastd[-2])   and (percent_B1<0 or percent_B2<0 or percent_B3<0):# or percent_B3<0):# or percent_B2<.05):
        prediction1=1
    elif fastk[-1]>.8 and fastd[-1]>.8 and (fastk[-1]<fastd[-1] and fastk[-2]>fastd[-2])  and (percent_B1>1 or percent_B2>1 or percent_B3>1):# or percent_B3>1):# or percent_B2>1):
        prediction1=0

    return prediction1,6






def SARMACD200EMA(stoplossval, takeprofitval,CloseStream,HighStream,LowStream,prediction1,CurrentPos,signal1):
    newOrder=0
    Close = np.array(CloseStream)
    High = np.array(HighStream)
    Low = np.array(LowStream)
    SAR=ta.SAR(High,Low,acceleration=.02,maximum=.2)
    EMA200 = ta.EMA(Close,timeperiod=200)
    macd, macdsignal, macdhist = ta.MACD(Close)

    if Close[-1]>EMA200[-1] and macd[-1]>macdsignal[-1] and macd[-2]<macdsignal[-2]:
        signal1=1
    elif Close[-1]<EMA200[-1] and macd[-1]<macdsignal[-1] and macd[-2]>macdsignal[-2]:
        signal1=0




    if signal1==1 and SAR[-1]<Close[-1] and macd[-1]>macdsignal[-1]:
        prediction1=1
        newOrder=1
    elif signal1==0 and SAR[-1]>Close[-1] and macd[-1]<macdsignal[-1]:
        prediction1=0
        newOrder=1


    if newOrder:
        #Close = np.array(CloseStream)
        #High = np.array(HighStream)
        #Low = np.array(LowStream)
        ATR = np.array(average_true_range(pd.Series(HighStream),pd.Series(LowStream),pd.Series(CloseStream)))
        if prediction1 == 0 and CurrentPos == -99:
            stoplossval = 2 * ATR[-1]
            takeprofitval = 5 * ATR[-1]
        elif prediction1 == 1 and CurrentPos == -99:
            stoplossval = 2 * ATR[-1]
            takeprofitval = 5 * ATR[-1]
        '''highswing = HighStream[-2]
        Lowswing = LowStream[-2]
        highflag = 0
        lowflag = 0
        for j in range(-3, -60, -1):
            if HighStream[j] > highswing and HighStream[j] > HighStream[j - 1] and HighStream[j] > HighStream[
                j - 2] and highflag == 0:
                highswing = HighStream[j]
                highflag = 1
            if LowStream[j] < Lowswing and LowStream[j] < LowStream[j - 1] and LowStream[j] < LowStream[
                j - 2] and lowflag == 0:
                Lowswing = LowStream[j]
                lowflag = 1

        if prediction1 == 0 and CurrentPos == -99:
            stoplossval = (highswing - CloseStream[-1])
            if stoplossval < 0:
                stoplossval *= -1
            takeprofitval = stoplossval * 2

        elif prediction1 == 1 and CurrentPos == -99:
            stoplossval = (CloseStream[-1] - Lowswing)
            if stoplossval < 0:
                stoplossval *= -1
            takeprofitval = stoplossval * 2'''
        '''if prediction1 == 0 and CurrentPos == -99:
            stoplossval = SAR[-1] - CloseStream[-1]
            if stoplossval > 0.007 * CloseStream[-1]:
                stoplossval = 0.007 * CloseStream[-1]
            takeprofitval = 1.5*stoplossval
            signal1=-99

        elif prediction1 == 1 and CurrentPos == -99:
            stoplossval = CloseStream[-1] - SAR[-1]
            if stoplossval > 0.007*CloseStream[-1]:
                stoplossval = 0.007*CloseStream[-1]
            takeprofitval = 1.5*stoplossval
            signal1 = -99'''

    return takeprofitval,stoplossval,prediction1,signal1


def SetSLTP(stoplossval, takeprofitval,CloseStream,HighStream,LowStream,prediction1,CurrentPos,Type):
    ##Average True Range with multipliers
    if Type==1:
        ATR = np.array(average_true_range(pd.Series(HighStream), pd.Series(LowStream), pd.Series(CloseStream)))
        if prediction1 == 0 and CurrentPos == -99:
            stoplossval = 1.5 * ATR[-1]
            takeprofitval = 8 * ATR[-1]
        elif prediction1 == 1 and CurrentPos == -99:
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

        if prediction1 == 0 and CurrentPos == -99:
            stoplossval = (highswing - CloseStream[-1])
            if stoplossval < 0:
                stoplossval *= -1
            takeprofitval = stoplossval * 2
        elif prediction1 == 1 and CurrentPos == -99:
            stoplossval = (CloseStream[-1] - Lowswing)
            if stoplossval < 0:
                stoplossval *= -1
            takeprofitval = stoplossval * 2

    ## Closest Swing High/Low in Last 20 periods
    elif Type==3:
        highswing = HighStream[-2]
        Lowswing = LowStream[-2]
        highflag = 0
        lowflag = 0
        for j in range(-3, -15, -1):
            if HighStream[j] > highswing and HighStream[j] > HighStream[j - 1] and HighStream[j] > HighStream[j - 2] and highflag == 0:
                highswing = HighStream[j]
                highflag = 1
            if LowStream[j] < Lowswing and LowStream[j] < LowStream[j - 1] and LowStream[j] < LowStream[j - 2] and lowflag == 0:
                Lowswing = LowStream[j]
                lowflag = 1

        if prediction1 == 0 and CurrentPos == -99:
            stoplossval = (highswing - CloseStream[-1])
            if stoplossval < 0:
                stoplossval *= -1
            takeprofitval = stoplossval * 2

        elif prediction1 == 1 and CurrentPos == -99:
            stoplossval = (CloseStream[-1] - Lowswing)
            if stoplossval < 0:
                stoplossval *= -1
            takeprofitval = stoplossval * 2
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

        if prediction1 == 0 and CurrentPos == -99:
            stoplossval = (highswing - CloseStream[-1])
            if stoplossval < 0:
                stoplossval *= -1
            takeprofitval = stoplossval * 2

        elif prediction1 == 1 and CurrentPos == -99:
            stoplossval = (CloseStream[-1] - Lowswing)
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

        if prediction1 == 0 and CurrentPos == -99:
            temp = (highswing - CloseStream[-1])
            stoplossval = 1.25 * ATR[-1]
            if temp < 0:
                temp *= -1
            takeprofitval = temp * 2

        elif prediction1 == 1 and CurrentPos == -99:
            temp = (CloseStream[-1] - Lowswing)
            stoplossval = 1.25 * ATR[-1]
            if temp < 0:
                temp *= -1
            takeprofitval = temp * 2

    elif Type==6:
        ATR = np.array(average_true_range(pd.Series(HighStream), pd.Series(LowStream), pd.Series(CloseStream)))
        if prediction1 == 0 and CurrentPos == -99:
            stoplossval = 0.5 * ATR[-1]
            takeprofitval = 2 * ATR[-1]
        elif prediction1 == 1 and CurrentPos == -99:
            stoplossval = 0.5 * ATR[-1]
            takeprofitval = 2 * ATR[-1]
    return stoplossval,takeprofitval
