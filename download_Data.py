from binance.client import Client
from binance.enums import *
from datetime import timezone,datetime,date,timedelta
import API_keys
client = Client(api_key=API_keys.api_key,api_secret=API_keys.api_secret) ##Binance keys needed to get historical data/ Trade on an account
from joblib import load, dump

path = f"C:\\Users\\conor\\Desktop\\price_data"
def get_data(TIME_INTERVAL,symbol,time_period,test_set,test_set_length,path=''):
    if path=='':
        path = f"C:\\Users\\conor\\Desktop\\price_data"
    LENGTH = ""
    ##Parse test_set_length to work out the time period we are taking data from, being sure to leave the test_set alone
    if test_set_length[2] == 'd':
        LENGTH = f"{time_period + int(test_set_length[0])} day ago UTC"
        time_period = f'{time_period} day ago UTC'
    elif test_set_length[3] == 'd':
        LENGTH = f"{time_period + int(test_set_length[0]) * 10 + int(test_set_length[1])} day ago UTC"
        time_period = f'{time_period} day ago UTC'
    elif test_set_length[4] == 'd':
        LENGTH = f"{time_period + int(test_set_length[0]) * 100 + int(test_set_length[1]) * 10 + int(test_set_length[0])} day ago UTC"
        time_period = f'{time_period} day ago UTC'
    elif test_set_length[2] == 'w':
        LENGTH = f"{time_period + int(test_set_length[0])} week ago UTC"
        time_period = f'{time_period} week ago UTC'
    elif test_set_length[3] == 'w':
        LENGTH = f"{time_period + int(test_set_length[0]) * 10 + int(test_set_length[1])} week ago UTC"
        time_period = f'{time_period} week ago UTC'
    elif test_set_length[2] == 'm':
        LENGTH = f"{time_period + int(test_set_length[0])} month ago UTC"
        time_period = f'{time_period} month ago UTC'
    elif test_set_length[3] == 'm':
        LENGTH = f"{time_period + int(test_set_length[0]) * 10 + int(test_set_length[1])} month ago UTC"
        time_period = f'{time_period} month ago UTC'
    elif test_set_length[2] == 'y':
        LENGTH = f"{time_period + int(test_set_length[0])} year ago UTC"
        time_period = f'{time_period} year ago UTC'

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
        if TIME_INTERVAL==1:
            for kline in client.futures_historical_klines(symbol, Client.KLINE_INTERVAL_1MINUTE,start_str = LENGTH,end_str=test_set_length):
                Date.append(datetime.utcfromtimestamp((round(kline[0] / 1000))))
                Open.append(float(kline[1]))
                Close.append(float(kline[4]))
                High.append(float(kline[2]))
                Low.append(float(kline[3]))
                Volume.append(float(kline[7]))
        elif TIME_INTERVAL==3:
            for kline in client.futures_historical_klines(symbol, Client.KLINE_INTERVAL_3MINUTE,start_str = LENGTH,end_str=test_set_length):
                Date.append(datetime.utcfromtimestamp((round(kline[0] / 1000))))
                Open.append(float(kline[1]))
                Close.append(float(kline[4]))
                High.append(float(kline[2]))
                Low.append(float(kline[3]))
                Volume.append(float(kline[7]))
        elif TIME_INTERVAL==5:
            for kline in client.futures_historical_klines(symbol, Client.KLINE_INTERVAL_5MINUTE,start_str = LENGTH,end_str=test_set_length):
                Date.append(datetime.utcfromtimestamp((round(kline[0] / 1000))))
                Open.append(float(kline[1]))
                Close.append(float(kline[4]))
                High.append(float(kline[2]))
                Low.append(float(kline[3]))
                Volume.append(float(kline[7]))
        elif TIME_INTERVAL==15:
            for kline in client.futures_historical_klines(symbol, Client.KLINE_INTERVAL_15MINUTE,start_str = LENGTH,end_str=test_set_length):
                Date.append(datetime.utcfromtimestamp((round(kline[0] / 1000))))
                Open.append(float(kline[1]))
                Close.append(float(kline[4]))
                High.append(float(kline[2]))
                Low.append(float(kline[3]))
                Volume.append(float(kline[7]))
        elif TIME_INTERVAL==30:
            for kline in client.futures_historical_klines(symbol, Client.KLINE_INTERVAL_30MINUTE,start_str = LENGTH,end_str=test_set_length):
                Date.append(datetime.utcfromtimestamp((round(kline[0] / 1000))))
                Open.append(float(kline[1]))
                Close.append(float(kline[4]))
                High.append(float(kline[2]))
                Low.append(float(kline[3]))
                Volume.append(float(kline[7]))
        elif TIME_INTERVAL==60:
            for kline in client.futures_historical_klines(symbol, Client.KLINE_INTERVAL_1HOUR,start_str = LENGTH,end_str=test_set_length):
                Date.append(datetime.utcfromtimestamp((round(kline[0] / 1000))))
                Open.append(float(kline[1]))
                Close.append(float(kline[4]))
                High.append(float(kline[2]))
                Low.append(float(kline[3]))
                Volume.append(float(kline[7]))
        elif TIME_INTERVAL==120:
            for kline in client.futures_historical_klines(symbol, Client.KLINE_INTERVAL_2HOUR,start_str = LENGTH,end_str=test_set_length):
                Date.append(datetime.utcfromtimestamp((round(kline[0] / 1000))))
                Open.append(float(kline[1]))
                Close.append(float(kline[4]))
                High.append(float(kline[2]))
                Low.append(float(kline[3]))
                Volume.append(float(kline[7]))
        elif TIME_INTERVAL==240:
            for kline in client.futures_historical_klines(symbol, Client.KLINE_INTERVAL_4HOUR,start_str = LENGTH,end_str=test_set_length):
                Date.append(datetime.utcfromtimestamp((round(kline[0] / 1000))))
                Open.append(float(kline[1]))
                Close.append(float(kline[4]))
                High.append(float(kline[2]))
                Low.append(float(kline[3]))
                Volume.append(float(kline[7]))
        elif TIME_INTERVAL==360:
            for kline in client.futures_historical_klines(symbol, Client.KLINE_INTERVAL_6HOUR,start_str = LENGTH,end_str=test_set_length):
                Date.append(datetime.utcfromtimestamp((round(kline[0] / 1000))))
                Open.append(float(kline[1]))
                Close.append(float(kline[4]))
                High.append(float(kline[2]))
                Low.append(float(kline[3]))
                Volume.append(float(kline[7]))
        elif TIME_INTERVAL==480:
            for kline in client.futures_historical_klines(symbol, Client.KLINE_INTERVAL_8HOUR,start_str = LENGTH,end_str=test_set_length):
                Date.append(datetime.utcfromtimestamp((round(kline[0] / 1000))))
                Open.append(float(kline[1]))
                Close.append(float(kline[4]))
                High.append(float(kline[2]))
                Low.append(float(kline[3]))
                Volume.append(float(kline[7]))
        elif TIME_INTERVAL==720:
            for kline in client.futures_historical_klines(symbol, Client.KLINE_INTERVAL_12HOUR,start_str = LENGTH,end_str=test_set_length):
                Date.append(datetime.utcfromtimestamp((round(kline[0] / 1000))))
                Open.append(float(kline[1]))
                Close.append(float(kline[4]))
                High.append(float(kline[2]))
                Low.append(float(kline[3]))
                Volume.append(float(kline[7]))
        elif TIME_INTERVAL==1440:
            for kline in client.futures_historical_klines(symbol, Client.KLINE_INTERVAL_1DAY,start_str = LENGTH,end_str=test_set_length):
                Date.append(datetime.utcfromtimestamp((round(kline[0] / 1000))))
                Open.append(float(kline[1]))
                Close.append(float(kline[4]))
                High.append(float(kline[2]))
                Low.append(float(kline[3]))
                Volume.append(float(kline[7]))
        elif TIME_INTERVAL==4320:
            for kline in client.futures_historical_klines(symbol, Client.KLINE_INTERVAL_3DAY,start_str = LENGTH,end_str=test_set_length):
                Date.append(datetime.utcfromtimestamp((round(kline[0] / 1000))))
                Open.append(float(kline[1]))
                Close.append(float(kline[4]))
                High.append(float(kline[2]))
                Low.append(float(kline[3]))
                Volume.append(float(kline[7]))
        elif TIME_INTERVAL==10080:
            for kline in client.futures_historical_klines(symbol, Client.KLINE_INTERVAL_1WEEK,start_str = LENGTH,end_str=test_set_length):
                Date.append(datetime.utcfromtimestamp((round(kline[0] / 1000))))
                Open.append(float(kline[1]))
                Close.append(float(kline[4]))
                High.append(float(kline[2]))
                Low.append(float(kline[3]))
                Volume.append(float(kline[7]))
        elif TIME_INTERVAL==40320:
            for kline in client.futures_historical_klines(symbol, Client.KLINE_INTERVAL_1MONTH,start_str = LENGTH,end_str=test_set_length):
                Date.append(datetime.utcfromtimestamp((round(kline[0] / 1000))))
                Open.append(float(kline[1]))
                Close.append(float(kline[4]))
                High.append(float(kline[2]))
                Low.append(float(kline[3]))
                Volume.append(float(kline[7]))
        if TIME_INTERVAL!=1:
            for kline in client.futures_historical_klines(symbol, Client.KLINE_INTERVAL_1MINUTE,start_str=LENGTH,end_str=test_set_length):
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
        if TIME_INTERVAL==1:
            for kline in client.futures_historical_klines(symbol, Client.KLINE_INTERVAL_1MINUTE,start_str = test_set_length):
                Date.append(datetime.utcfromtimestamp((round(kline[0] / 1000))))
                Open.append(float(kline[1]))
                Close.append(float(kline[4]))
                High.append(float(kline[2]))
                Low.append(float(kline[3]))
                Volume.append(float(kline[7]))
        elif TIME_INTERVAL==3:
            for kline in client.futures_historical_klines(symbol, Client.KLINE_INTERVAL_3MINUTE,start_str = test_set_length):
                Date.append(datetime.utcfromtimestamp((round(kline[0] / 1000))))
                Open.append(float(kline[1]))
                Close.append(float(kline[4]))
                High.append(float(kline[2]))
                Low.append(float(kline[3]))
                Volume.append(float(kline[7]))
        elif TIME_INTERVAL==5:
            for kline in client.futures_historical_klines(symbol, Client.KLINE_INTERVAL_5MINUTE,start_str = test_set_length):
                Date.append(datetime.utcfromtimestamp((round(kline[0] / 1000))))
                Open.append(float(kline[1]))
                Close.append(float(kline[4]))
                High.append(float(kline[2]))
                Low.append(float(kline[3]))
                Volume.append(float(kline[7]))
        elif TIME_INTERVAL==15:
            for kline in client.futures_historical_klines(symbol, Client.KLINE_INTERVAL_15MINUTE,start_str = test_set_length):
                Date.append(datetime.utcfromtimestamp((round(kline[0] / 1000))))
                Open.append(float(kline[1]))
                Close.append(float(kline[4]))
                High.append(float(kline[2]))
                Low.append(float(kline[3]))
                Volume.append(float(kline[7]))
        elif TIME_INTERVAL==30:
            for kline in client.futures_historical_klines(symbol, Client.KLINE_INTERVAL_30MINUTE,start_str = test_set_length):
                Date.append(datetime.utcfromtimestamp((round(kline[0] / 1000))))
                Open.append(float(kline[1]))
                Close.append(float(kline[4]))
                High.append(float(kline[2]))
                Low.append(float(kline[3]))
                Volume.append(float(kline[7]))
        elif TIME_INTERVAL==60:
            for kline in client.futures_historical_klines(symbol, Client.KLINE_INTERVAL_1HOUR,start_str = test_set_length):
                Date.append(datetime.utcfromtimestamp((round(kline[0] / 1000))))
                Open.append(float(kline[1]))
                Close.append(float(kline[4]))
                High.append(float(kline[2]))
                Low.append(float(kline[3]))
                Volume.append(float(kline[7]))
        elif TIME_INTERVAL==120:
            for kline in client.futures_historical_klines(symbol, Client.KLINE_INTERVAL_2HOUR,start_str = test_set_length):
                Date.append(datetime.utcfromtimestamp((round(kline[0] / 1000))))
                Open.append(float(kline[1]))
                Close.append(float(kline[4]))
                High.append(float(kline[2]))
                Low.append(float(kline[3]))
                Volume.append(float(kline[7]))
        elif TIME_INTERVAL==240:
            for kline in client.futures_historical_klines(symbol, Client.KLINE_INTERVAL_4HOUR,start_str = test_set_length):
                Date.append(datetime.utcfromtimestamp((round(kline[0] / 1000))))
                Open.append(float(kline[1]))
                Close.append(float(kline[4]))
                High.append(float(kline[2]))
                Low.append(float(kline[3]))
                Volume.append(float(kline[7]))
        elif TIME_INTERVAL==360:
            for kline in client.futures_historical_klines(symbol, Client.KLINE_INTERVAL_6HOUR,start_str = test_set_length):
                Date.append(datetime.utcfromtimestamp((round(kline[0] / 1000))))
                Open.append(float(kline[1]))
                Close.append(float(kline[4]))
                High.append(float(kline[2]))
                Low.append(float(kline[3]))
                Volume.append(float(kline[7]))
        elif TIME_INTERVAL==480:
            for kline in client.futures_historical_klines(symbol, Client.KLINE_INTERVAL_8HOUR,start_str = test_set_length):
                Date.append(datetime.utcfromtimestamp((round(kline[0] / 1000))))
                Open.append(float(kline[1]))
                Close.append(float(kline[4]))
                High.append(float(kline[2]))
                Low.append(float(kline[3]))
                Volume.append(float(kline[7]))
        elif TIME_INTERVAL==720:
            for kline in client.futures_historical_klines(symbol, Client.KLINE_INTERVAL_12HOUR,start_str = test_set_length):
                Date.append(datetime.utcfromtimestamp((round(kline[0] / 1000))))
                Open.append(float(kline[1]))
                Close.append(float(kline[4]))
                High.append(float(kline[2]))
                Low.append(float(kline[3]))
                Volume.append(float(kline[7]))
        elif TIME_INTERVAL==1440:
            for kline in client.futures_historical_klines(symbol, Client.KLINE_INTERVAL_1DAY,start_str = test_set_length):
                Date.append(datetime.utcfromtimestamp((round(kline[0] / 1000))))
                Open.append(float(kline[1]))
                Close.append(float(kline[4]))
                High.append(float(kline[2]))
                Low.append(float(kline[3]))
                Volume.append(float(kline[7]))
        elif TIME_INTERVAL==4320:
            for kline in client.futures_historical_klines(symbol, Client.KLINE_INTERVAL_3DAY,start_str = test_set_length):
                Date.append(datetime.utcfromtimestamp((round(kline[0] / 1000))))
                Open.append(float(kline[1]))
                Close.append(float(kline[4]))
                High.append(float(kline[2]))
                Low.append(float(kline[3]))
                Volume.append(float(kline[7]))
        elif TIME_INTERVAL==10080:
            for kline in client.futures_historical_klines(symbol, Client.KLINE_INTERVAL_1WEEK,start_str = test_set_length):
                Date.append(datetime.utcfromtimestamp((round(kline[0] / 1000))))
                Open.append(float(kline[1]))
                Close.append(float(kline[4]))
                High.append(float(kline[2]))
                Low.append(float(kline[3]))
                Volume.append(float(kline[7]))
        elif TIME_INTERVAL==40320:
            for kline in client.futures_historical_klines(symbol, Client.KLINE_INTERVAL_1MONTH,start_str =test_set_length):
                Date.append(datetime.utcfromtimestamp((round(kline[0] / 1000))))
                Open.append(float(kline[1]))
                Close.append(float(kline[4]))
                High.append(float(kline[2]))
                Low.append(float(kline[3]))
                Volume.append(float(kline[7]))
        if TIME_INTERVAL!=1:
            for kline in client.futures_historical_klines(symbol, Client.KLINE_INTERVAL_1MINUTE,start_str=test_set_length):
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

    '''for j in range(len(Date_1min)):
        if Date_1min[j] == Date[-1]:
            High_1min = High_1min[:j]
            Low_1min = Low_1min[:j]
            Date_1min = Date_1min[:j]
            Close_1min = Close_1min[:j]
            Open_1min = Open_1min[:j]
            break'''

    price_data = {'Date': Date, 'Open': Open, 'Close': Close, 'High': High, 'Low': Low,
                 'Volume': Volume,'High_1min': High_1min, 'Low_1min': Low_1min, 'Close_1min': Close_1min,
                 'Open_1min': Open_1min, 'Date_1min': Date_1min}

    try:
        print("Saving Price data")
        if test_set:
            dump(price_data, f"{path}\\{symbol}_{TIME_INTERVAL}_{test_set_length}_test.joblib") ## address of where you will keep the data,
        else:
            dump(price_data, f"{path}\\{symbol}_{TIME_INTERVAL}_{time_period}.joblib") ## address of where you will keep the data,
    except:
        print("Failed to save data")
'''if __name__ == '__main__':
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
    TIME_INTERVAL = 5 ##candles
    time_period = 2 ##non-test set length
    test_set_length = '2 month ago' ##length of test set
    for x in symbol:
        print(f"Downloading {TIME_INTERVAL} candles from {test_set_length} on {x}")
        get_data(TIME_INTERVAL,x,time_period,1,test_set_length)'''
