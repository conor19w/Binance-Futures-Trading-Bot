import pandas as pd
from binance.client import Client
from binance.enums import *
from datetime import timezone,datetime,date,timedelta
import API_keys
client = Client(api_key=API_keys.api_key,api_secret=API_keys.api_secret) ##Binance keys needed to get historical data/ Trade on an account
from joblib import load, dump

path = f"C:\\Users\\conor\\Desktop\\"
def get_data(TIME_INTERVAL,symbol,time_period,test_set,time_period_units,path=''):
    if path=='':
        path = f"C:\\Users\\conor\\Desktop\\"

    path+='price_data'

    LENGTH = f"{time_period*2} {time_period_units} ago UTC" ##default to make the test set the same size as the non-test set
    time_period = f'{time_period} {time_period_units} ago UTC'

    Date = []
    Open = []
    Close = []
    High =[]
    Low = []
    Volume = []
    High_1min = []
    Low_1min = []
    Close_1min = []
    Open_1min = []
    Date_1min = []
    ##klines for candlestick patterns and TA
    if not test_set:
        for kline in client.futures_historical_klines(symbol, TIME_INTERVAL,start_str = time_period):
            Date.append(datetime.utcfromtimestamp((round(kline[0] / 1000))))
            Open.append(float(kline[1]))
            Close.append(float(kline[4]))
            High.append(float(kline[2]))
            Low.append(float(kline[3]))
            Volume.append(float(kline[7]))


        if TIME_INTERVAL!='1m':
            for kline in client.futures_historical_klines(symbol, '1m',start_str = time_period):
                # print(kline)
                Date_1min.append(datetime.utcfromtimestamp((round(kline[0]/1000))))
                Open_1min.append(float(kline[1]))
                High_1min.append(float(kline[2]))
                Low_1min.append(float(kline[3]))
                Close_1min.append(float(kline[4]))
        else:
            Date_1min=Date
            Open_1min=Open
            High_1min=High
            Low_1min=Low
            Close_1min=Close
    else:
        for kline in client.futures_historical_klines(symbol, TIME_INTERVAL,start_str = LENGTH ,end_str = time_period):
            Date.append(datetime.utcfromtimestamp((round(kline[0] / 1000))))
            Open.append(float(kline[1]))
            Close.append(float(kline[4]))
            High.append(float(kline[2]))
            Low.append(float(kline[3]))
            Volume.append(float(kline[7]))
        if TIME_INTERVAL!='1m':
            for kline in client.futures_historical_klines(symbol, '1m',start_str = LENGTH ,end_str = time_period):
                # print(kline)
                Date_1min.append(datetime.utcfromtimestamp((round(kline[0]/1000))))
                Open_1min.append(float(kline[1]))
                High_1min.append(float(kline[2]))
                Low_1min.append(float(kline[3]))
                Close_1min.append(float(kline[4]))
        else:
            Date_1min=Date
            Open_1min=Open
            High_1min=High
            Low_1min=Low
            Close_1min=Close

    ##Align minute data with higher timeframe
    for i in range(len(Date)):
        found_flag = 0
        for j in range(len(Date_1min)):
            if Date_1min[j] == Date[i]:
                High_1min = High_1min[j:]
                Low_1min = Low_1min[j:]
                Date_1min = Date_1min[j:]
                Close_1min = Close_1min[j:]
                Open_1min = Open_1min[j:]
                High = High[i:]
                Low = Low[i:]
                Date = Date[i:]
                Close = Close[i:]
                Open = Open[i:]
                Volume = Volume[i:]
                found_flag=1
                break
        if found_flag:
            break
    for i in range(-1,-len(Date),-1):
        found_flag = 0
        for j in range(-1,-len(Date_1min),-1):
            if Date_1min[j] == Date[i]:
                High_1min = High_1min[:j]
                Low_1min = Low_1min[:j]
                Date_1min = Date_1min[:j]
                Close_1min = Close_1min[:j]
                Open_1min = Open_1min[:j]
                High = High[:i]
                Low = Low[:i]
                Date = Date[:i]
                Close = Close[:i]
                Open = Open[:i]
                Volume = Volume[:i]
                found_flag=1
                break
        if found_flag:
            break



    price_data = {'Date': Date, 'Open': Open, 'Close': Close, 'High': High, 'Low': Low,
                 'Volume': Volume,'High_1min': High_1min, 'Low_1min': Low_1min, 'Close_1min': Close_1min,
                 'Open_1min': Open_1min, 'Date_1min': Date_1min}

    try:
        print("Saving Price data")
        if test_set:
            dump(price_data, f"{path}\\{symbol}_{TIME_INTERVAL}_{time_period}_test.joblib") ## address of where you will keep the data,
        else:
            dump(price_data, f"{path}\\{symbol}_{TIME_INTERVAL}_{time_period}.joblib") ## address of where you will keep the data,
    except:
        print("Failed to save data")
if __name__ == '__main__':
    ##Run this script with the parameters below to just download data without testing a strategy
    symbol =['SFPUSDT','RAYUSDT', 'NEARUSDT', 'AUDIOUSDT', 'HNTUSDT', 'DGBUSDT', 'ZRXUSDT', 'BCHUSDT', 'HOTUSDT', 'ARUSDT', 'FLMUSDT',
              'SFPUSDT', 'BELUSDT', 'RENUSDT', 'ADAUSDT', 'STORJUSDT', 'BZRXUSDT', 'CHRUSDT', 'WAVESUSDT', 'CHZUSDT', 'XRPUSDT',
              'SANDUSDT', 'OCEANUSDT', 'ENJUSDT', 'YFIIUSDT', 'GRTUSDT', 'UNIUSDT', 'TLMUSDT', 'XTZUSDT', 'LUNAUSDT', 'EOSUSDT',
              'SKLUSDT', 'GTCUSDT', 'DOTUSDT', '1INCHUSDT', 'UNFIUSDT', 'FTMUSDT', 'RLCUSDT', 'ATOMUSDT', 'BLZUSDT', 'SNXUSDT',
              'SOLUSDT', 'ETCUSDT', 'BNBUSDT', 'CELRUSDT', 'OGNUSDT', 'ETHUSDT', 'NEOUSDT', 'TOMOUSDT', 'CELOUSDT', 'KLAYUSDT',
              'TRBUSDT', 'TRXUSDT', 'EGLDUSDT', 'CRVUSDT', 'BAKEUSDT', 'NUUSDT', 'SRMUSDT', 'ALICEUSDT', 'CTKUSDT', 'ARPAUSDT',
              'MATICUSDT', 'IOTXUSDT', 'DENTUSDT', 'IOSTUSDT', 'OMGUSDT', 'BANDUSDT', 'BTCUSDT', 'NKNUSDT', 'RSRUSDT', 'IOTAUSDT',
              'CVCUSDT', 'REEFUSDT', 'BTSUSDT', 'BTTUSDT', 'ONEUSDT', 'ANKRUSDT', 'SUSHIUSDT', 'ALGOUSDT', 'SCUSDT', 'ONTUSDT',
              'MANAUSDT', 'ATAUSDT', 'MKRUSDT', 'DODOUSDT', 'LITUSDT', 'ICPUSDT', 'ZECUSDT', 'ICXUSDT', 'ZENUSDT', 'DOGEUSDT',
              'ALPHAUSDT', 'SXPUSDT', 'HBARUSDT', 'RVNUSDT', 'CTSIUSDT', 'KAVAUSDT', 'C98USDT', 'THETAUSDT', 'MASKUSDT', 'AAVEUSDT',
              'YFIUSDT', 'AXSUSDT', 'ZILUSDT', 'XEMUSDT', 'COMPUSDT', 'RUNEUSDT', 'AVAXUSDT', 'KNCUSDT', 'LPTUSDT', 'LRCUSDT',
              'MTLUSDT', 'VETUSDT', 'DASHUSDT', 'KEEPUSDT', 'LTCUSDT', 'DYDXUSDT', 'LINAUSDT', 'XLMUSDT', 'LINKUSDT', 'QTUMUSDT',
              'KSMUSDT', 'FILUSDT', 'STMXUSDT', 'BALUSDT', 'GALAUSDT', 'BATUSDT', 'AKROUSDT', 'XMRUSDT', 'COTIUSDT']
    TIME_INTERVAL = '1d' ##candles
    time_period = 365 ##length of data set
    time_period_units = 'day'
    for x in symbol:
        print(f"Downloading {TIME_INTERVAL} candles from {time_period} {time_period_units} ago on {x}")
        get_data(TIME_INTERVAL,x,time_period,0,time_period_units)
