from binance.client import Client
from binance.enums import *
from datetime import timezone,datetime,date,timedelta
import API_keys
client = Client(api_key=API_keys.api_key,api_secret=API_keys.api_secret) ##Binance keys needed to get historical data/ Trade on an account
from joblib import load, dump

path = f"C:\\Users\\conor\\Desktop\\price_data"
def get_data(TIME_INTERVAL,symbol,LENGTH):
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
    if TIME_INTERVAL==1:
        for kline in client.futures_historical_klines(symbol, Client.KLINE_INTERVAL_1MINUTE,start_str = LENGTH):
            Date.append(datetime.utcfromtimestamp((round(kline[0] / 1000))) + timedelta(hours=1))
            Open.append(float(kline[1]))
            Close.append(float(kline[4]))
            High.append(float(kline[2]))
            Low.append(float(kline[3]))
            Volume.append(float(kline[7]))
    elif TIME_INTERVAL==3:
        for kline in client.futures_historical_klines(symbol, Client.KLINE_INTERVAL_3MINUTE,start_str = LENGTH):
            Date.append(datetime.utcfromtimestamp((round(kline[0] / 1000))) + timedelta(hours=1))
            Open.append(float(kline[1]))
            Close.append(float(kline[4]))
            High.append(float(kline[2]))
            Low.append(float(kline[3]))
            Volume.append(float(kline[7]))
    elif TIME_INTERVAL==5:
        for kline in client.futures_historical_klines(symbol, Client.KLINE_INTERVAL_5MINUTE,start_str = LENGTH):
            Date.append(datetime.utcfromtimestamp((round(kline[0] / 1000))) + timedelta(hours=1))
            Open.append(float(kline[1]))
            Close.append(float(kline[4]))
            High.append(float(kline[2]))
            Low.append(float(kline[3]))
            Volume.append(float(kline[7]))
    elif TIME_INTERVAL==15:
        for kline in client.futures_historical_klines(symbol, Client.KLINE_INTERVAL_15MINUTE,start_str = LENGTH):
            Date.append(datetime.utcfromtimestamp((round(kline[0] / 1000))) + timedelta(hours=1))
            Open.append(float(kline[1]))
            Close.append(float(kline[4]))
            High.append(float(kline[2]))
            Low.append(float(kline[3]))
            Volume.append(float(kline[7]))
    elif TIME_INTERVAL==30:
        for kline in client.futures_historical_klines(symbol, Client.KLINE_INTERVAL_30MINUTE,start_str = LENGTH):
            Date.append(datetime.utcfromtimestamp((round(kline[0] / 1000))) + timedelta(hours=1))
            Open.append(float(kline[1]))
            Close.append(float(kline[4]))
            High.append(float(kline[2]))
            Low.append(float(kline[3]))
            Volume.append(float(kline[7]))
    elif TIME_INTERVAL==60:
        for kline in client.futures_historical_klines(symbol, Client.KLINE_INTERVAL_1HOUR,start_str = LENGTH):
            Date.append(datetime.utcfromtimestamp((round(kline[0] / 1000))) + timedelta(hours=1))
            Open.append(float(kline[1]))
            Close.append(float(kline[4]))
            High.append(float(kline[2]))
            Low.append(float(kline[3]))
            Volume.append(float(kline[7]))
    elif TIME_INTERVAL==120:
        for kline in client.futures_historical_klines(symbol, Client.KLINE_INTERVAL_2HOUR,start_str = LENGTH):
            Date.append(datetime.utcfromtimestamp((round(kline[0] / 1000))) + timedelta(hours=1))
            Open.append(float(kline[1]))
            Close.append(float(kline[4]))
            High.append(float(kline[2]))
            Low.append(float(kline[3]))
            Volume.append(float(kline[7]))
    elif TIME_INTERVAL==240:
        for kline in client.futures_historical_klines(symbol, Client.KLINE_INTERVAL_4HOUR,start_str = LENGTH):
            Date.append(datetime.utcfromtimestamp((round(kline[0] / 1000))) + timedelta(hours=1))
            Open.append(float(kline[1]))
            Close.append(float(kline[4]))
            High.append(float(kline[2]))
            Low.append(float(kline[3]))
            Volume.append(float(kline[7]))
    elif TIME_INTERVAL==360:
        for kline in client.futures_historical_klines(symbol, Client.KLINE_INTERVAL_6HOUR,start_str = LENGTH):
            Date.append(datetime.utcfromtimestamp((round(kline[0] / 1000))) + timedelta(hours=1))
            Open.append(float(kline[1]))
            Close.append(float(kline[4]))
            High.append(float(kline[2]))
            Low.append(float(kline[3]))
            Volume.append(float(kline[7]))
    elif TIME_INTERVAL==480:
        for kline in client.futures_historical_klines(symbol, Client.KLINE_INTERVAL_8HOUR,start_str = LENGTH):
            Date.append(datetime.utcfromtimestamp((round(kline[0] / 1000))) + timedelta(hours=1))
            Open.append(float(kline[1]))
            Close.append(float(kline[4]))
            High.append(float(kline[2]))
            Low.append(float(kline[3]))
            Volume.append(float(kline[7]))
    elif TIME_INTERVAL==720:
        for kline in client.futures_historical_klines(symbol, Client.KLINE_INTERVAL_12HOUR,start_str = LENGTH):
            Date.append(datetime.utcfromtimestamp((round(kline[0] / 1000))) + timedelta(hours=1))
            Open.append(float(kline[1]))
            Close.append(float(kline[4]))
            High.append(float(kline[2]))
            Low.append(float(kline[3]))
            Volume.append(float(kline[7]))
    elif TIME_INTERVAL==1440:
        for kline in client.futures_historical_klines(symbol, Client.KLINE_INTERVAL_1DAY,start_str = LENGTH):
            Date.append(datetime.utcfromtimestamp((round(kline[0] / 1000))) + timedelta(hours=1))
            Open.append(float(kline[1]))
            Close.append(float(kline[4]))
            High.append(float(kline[2]))
            Low.append(float(kline[3]))
            Volume.append(float(kline[7]))
    elif TIME_INTERVAL==4320:
        for kline in client.futures_historical_klines(symbol, Client.KLINE_INTERVAL_3DAY,start_str = LENGTH):
            Date.append(datetime.utcfromtimestamp((round(kline[0] / 1000))) + timedelta(hours=1))
            Open.append(float(kline[1]))
            Close.append(float(kline[4]))
            High.append(float(kline[2]))
            Low.append(float(kline[3]))
            Volume.append(float(kline[7]))
    elif TIME_INTERVAL==10080:
        for kline in client.futures_historical_klines(symbol, Client.KLINE_INTERVAL_1WEEK,start_str = LENGTH):
            Date.append(datetime.utcfromtimestamp((round(kline[0] / 1000))) + timedelta(hours=1))
            Open.append(float(kline[1]))
            Close.append(float(kline[4]))
            High.append(float(kline[2]))
            Low.append(float(kline[3]))
            Volume.append(float(kline[7]))
    elif TIME_INTERVAL==40320:
        for kline in client.futures_historical_klines(symbol, Client.KLINE_INTERVAL_1MONTH,start_str = LENGTH):
            Date.append(datetime.utcfromtimestamp((round(kline[0] / 1000))) + timedelta(hours=1))
            Open.append(float(kline[1]))
            Close.append(float(kline[4]))
            High.append(float(kline[2]))
            Low.append(float(kline[3]))
            Volume.append(float(kline[7]))

    for kline in client.futures_historical_klines(symbol, Client.KLINE_INTERVAL_1MINUTE,start_str=LENGTH):
        # print(kline)
        Date_1min.append(datetime.utcfromtimestamp((round(kline[0]/1000)))+timedelta(hours=1))
        Open_1min.append(float(kline[1]))
        High_1min.append(float(kline[2]))
        Low_1min.append(float(kline[3]))
        Close_1min.append(float(kline[4]))


    for j in range(len(Date_1min)):
        if Date_1min[j] == Date[0]:
            High_1min = High_1min[j:]
            Low_1min = Low_1min[j:]
            Date_1min = Date_1min[j:]
            Close_1min = Close_1min[j:]
            Open_1min = Open_1min[j:]
            break
    for j in range(len(Date_1min)):
        if Date_1min[j] == Date[-1]:
            High_1min = High_1min[:j]
            Low_1min = Low_1min[:j]
            Date_1min = Date_1min[:j]
            Close_1min = Close_1min[:j]
            Open_1min = Open_1min[:j]
            break
    price_data = {'Date': Date, 'Open': Open, 'Close': Close, 'High': High, 'Low': Low,
                 'Volume': Volume,'High_1min': High_1min, 'Low_1min': Low_1min, 'Close_1min': Close_1min,
                 'Open_1min': Open_1min, 'Date_1min': Date_1min}

    try:
        print("Saving Price data")
        dump(price_data, f"{path}\\{symbol}_{TIME_INTERVAL}_{LENGTH}.joblib") ## address of where you will keep the data,
                                                                                                                # this is the address you will use in Bot.py
    except:
        print("Failed to save data")
