from binance.client import Client
from binance.enums import *
from datetime import timezone,datetime,date,timedelta
import API_keys
client = Client(api_key=API_keys.api_key,api_secret=API_keys.api_secret) ##Binance keys needed to get historical data/ Trade on an account
def get_Klines(symbol,TIME_INTERVAL,time_period,test_set,test_set_length):
    start_string = ""
    ##Parse test_set_length to work out the time period we are taking data from, being sure to leave the test_set alone
    if test_set_length[2]=='d':
        start_string = f"{time_period+int(test_set_length[0])} days ago UTC"
    elif test_set_length[3]=='d':
        start_string = f"{time_period + int(test_set_length[0])*10+int(test_set_length[1])} days ago UTC"
    elif test_set_length[4]=='d':
        start_string = f"{time_period + int(test_set_length[0])*100+int(test_set_length[1])*10 + int(test_set_length[0])} days ago UTC"
    elif test_set_length[2]=='w':
        start_string = f"{time_period+int(test_set_length[0])} weeks ago UTC"
    elif test_set_length[3]=='w':
        start_string = f"{time_period + int(test_set_length[0])*10+int(test_set_length[1])} weeks ago UTC"
    elif test_set_length[2]=='m':
        start_string = f"{time_period+int(test_set_length[0])} months ago UTC"
    elif test_set_length[3]=='m':
        start_string = f"{time_period + int(test_set_length[0])*10+int(test_set_length[1])} months ago UTC"
    elif test_set_length[2]=='y':
        start_string = f"{time_period + int(test_set_length[0])} years ago UTC"
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
    if TIME_INTERVAL==1 and not test_set:
        for kline in client.futures_historical_klines(symbol, Client.KLINE_INTERVAL_1MINUTE,start_str=start_string,end_str=test_set_length):
            Date.append(datetime.utcfromtimestamp((round(kline[0] / 1000))))
            Open.append(float(kline[1]))
            Close.append(float(kline[4]))
            High.append(float(kline[2]))
            Low.append(float(kline[3]))
            Volume.append(float(kline[7]))
    elif TIME_INTERVAL==3 and not test_set:
        for kline in client.futures_historical_klines(symbol, Client.KLINE_INTERVAL_3MINUTE,start_str=start_string,end_str=test_set_length):
            Date.append(datetime.utcfromtimestamp((round(kline[0] / 1000))) )
            Open.append(float(kline[1]))
            Close.append(float(kline[4]))
            High.append(float(kline[2]))
            Low.append(float(kline[3]))
            Volume.append(float(kline[7]))
    elif TIME_INTERVAL==5 and not test_set:
        for kline in client.futures_historical_klines(symbol, Client.KLINE_INTERVAL_5MINUTE,start_str=start_string,end_str=test_set_length):
            Date.append(datetime.utcfromtimestamp((round(kline[0] / 1000))) )
            Open.append(float(kline[1]))
            Close.append(float(kline[4]))
            High.append(float(kline[2]))
            Low.append(float(kline[3]))
            Volume.append(float(kline[7]))
    elif TIME_INTERVAL==15 and not test_set:
        for kline in client.futures_historical_klines(symbol, Client.KLINE_INTERVAL_15MINUTE,start_str=start_string,end_str=test_set_length):
            Date.append(datetime.utcfromtimestamp((round(kline[0] / 1000))) )
            Open.append(float(kline[1]))
            Close.append(float(kline[4]))
            High.append(float(kline[2]))
            Low.append(float(kline[3]))
            Volume.append(float(kline[7]))
    elif TIME_INTERVAL==30 and not test_set:
        for kline in client.futures_historical_klines(symbol, Client.KLINE_INTERVAL_30MINUTE,start_str=start_string,end_str=test_set_length):
            Date.append(datetime.utcfromtimestamp((round(kline[0] / 1000))) )
            Open.append(float(kline[1]))
            Close.append(float(kline[4]))
            High.append(float(kline[2]))
            Low.append(float(kline[3]))
            Volume.append(float(kline[7]))
    elif TIME_INTERVAL==60 and not test_set:
        for kline in client.futures_historical_klines(symbol, Client.KLINE_INTERVAL_1HOUR,start_str=start_string,end_str=test_set_length):
            Date.append(datetime.utcfromtimestamp((round(kline[0] / 1000))) )
            Open.append(float(kline[1]))
            Close.append(float(kline[4]))
            High.append(float(kline[2]))
            Low.append(float(kline[3]))
            Volume.append(float(kline[7]))
    elif TIME_INTERVAL==120 and not test_set:
        for kline in client.futures_historical_klines(symbol, Client.KLINE_INTERVAL_2HOUR,start_str=start_string,end_str=test_set_length):
            Date.append(datetime.utcfromtimestamp((round(kline[0] / 1000))) )
            Open.append(float(kline[1]))
            Close.append(float(kline[4]))
            High.append(float(kline[2]))
            Low.append(float(kline[3]))
            Volume.append(float(kline[7]))
    elif TIME_INTERVAL==240 and not test_set:
        for kline in client.futures_historical_klines(symbol, Client.KLINE_INTERVAL_4HOUR,start_str=start_string,end_str=test_set_length):
            Date.append(datetime.utcfromtimestamp((round(kline[0] / 1000))) )
            Open.append(float(kline[1]))
            Close.append(float(kline[4]))
            High.append(float(kline[2]))
            Low.append(float(kline[3]))
            Volume.append(float(kline[7]))
    elif TIME_INTERVAL==360 and not test_set:
        for kline in client.futures_historical_klines(symbol, Client.KLINE_INTERVAL_6HOUR,start_str=start_string,end_str=test_set_length):
            Date.append(datetime.utcfromtimestamp((round(kline[0] / 1000))) )
            Open.append(float(kline[1]))
            Close.append(float(kline[4]))
            High.append(float(kline[2]))
            Low.append(float(kline[3]))
            Volume.append(float(kline[7]))
    elif TIME_INTERVAL==480 and not test_set:
        for kline in client.futures_historical_klines(symbol, Client.KLINE_INTERVAL_8HOUR,start_str=start_string,end_str=test_set_length):
            Date.append(datetime.utcfromtimestamp((round(kline[0] / 1000))) )
            Open.append(float(kline[1]))
            Close.append(float(kline[4]))
            High.append(float(kline[2]))
            Low.append(float(kline[3]))
            Volume.append(float(kline[7]))
    elif TIME_INTERVAL==720 and not test_set:
        for kline in client.futures_historical_klines(symbol, Client.KLINE_INTERVAL_12HOUR,start_str=start_string,end_str=test_set_length):
            Date.append(datetime.utcfromtimestamp((round(kline[0] / 1000))) )
            Open.append(float(kline[1]))
            Close.append(float(kline[4]))
            High.append(float(kline[2]))
            Low.append(float(kline[3]))
            Volume.append(float(kline[7]))
    elif TIME_INTERVAL==1440 and not test_set:
        for kline in client.futures_historical_klines(symbol, Client.KLINE_INTERVAL_1DAY,start_str=start_string,end_str=test_set_length):
            Date.append(datetime.utcfromtimestamp((round(kline[0] / 1000))) )
            Open.append(float(kline[1]))
            Close.append(float(kline[4]))
            High.append(float(kline[2]))
            Low.append(float(kline[3]))
            Volume.append(float(kline[7]))
    elif TIME_INTERVAL==4320 and not test_set:
        for kline in client.futures_historical_klines(symbol, Client.KLINE_INTERVAL_3DAY,start_str=start_string,end_str=test_set_length):
            Date.append(datetime.utcfromtimestamp((round(kline[0] / 1000))) )
            Open.append(float(kline[1]))
            Close.append(float(kline[4]))
            High.append(float(kline[2]))
            Low.append(float(kline[3]))
            Volume.append(float(kline[7]))
    elif TIME_INTERVAL==10080 and not test_set:
        for kline in client.futures_historical_klines(symbol, Client.KLINE_INTERVAL_1WEEK,start_str=start_string,end_str=test_set_length):
            Date.append(datetime.utcfromtimestamp((round(kline[0] / 1000))))
            Open.append(float(kline[1]))
            Close.append(float(kline[4]))
            High.append(float(kline[2]))
            Low.append(float(kline[3]))
            Volume.append(float(kline[7]))
    elif TIME_INTERVAL==40320 and not test_set:
        for kline in client.futures_historical_klines(symbol, Client.KLINE_INTERVAL_1MONTH,start_str=start_string,end_str=test_set_length):
            Date.append(datetime.utcfromtimestamp((round(kline[0] / 1000))) )
            Open.append(float(kline[1]))
            Close.append(float(kline[4]))
            High.append(float(kline[2]))
            Low.append(float(kline[3]))
            Volume.append(float(kline[7]))
    elif TIME_INTERVAL==1 and test_set:
        for kline in client.futures_historical_klines(symbol, Client.KLINE_INTERVAL_1MINUTE,start_str=test_set_length):
            Date.append(datetime.utcfromtimestamp((round(kline[0] / 1000))) )
            Open.append(float(kline[1]))
            Close.append(float(kline[4]))
            High.append(float(kline[2]))
            Low.append(float(kline[3]))
            Volume.append(float(kline[7]))
    elif TIME_INTERVAL==3 and test_set:
        for kline in client.futures_historical_klines(symbol, Client.KLINE_INTERVAL_3MINUTE,start_str=test_set_length):
            Date.append(datetime.utcfromtimestamp((round(kline[0] / 1000))) )
            Open.append(float(kline[1]))
            Close.append(float(kline[4]))
            High.append(float(kline[2]))
            Low.append(float(kline[3]))
            Volume.append(float(kline[7]))
    elif TIME_INTERVAL==5 and test_set:
        for kline in client.futures_historical_klines(symbol, Client.KLINE_INTERVAL_5MINUTE,start_str=test_set_length):
            Date.append(datetime.utcfromtimestamp((round(kline[0] / 1000))) )
            Open.append(float(kline[1]))
            Close.append(float(kline[4]))
            High.append(float(kline[2]))
            Low.append(float(kline[3]))
            Volume.append(float(kline[7]))
    elif TIME_INTERVAL==15 and test_set:
        for kline in client.futures_historical_klines(symbol, Client.KLINE_INTERVAL_15MINUTE,start_str=test_set_length):
            Date.append(datetime.utcfromtimestamp((round(kline[0] / 1000))) )
            Open.append(float(kline[1]))
            Close.append(float(kline[4]))
            High.append(float(kline[2]))
            Low.append(float(kline[3]))
            Volume.append(float(kline[7]))
    elif TIME_INTERVAL==30 and test_set:
        for kline in client.futures_historical_klines(symbol, Client.KLINE_INTERVAL_30MINUTE,start_str=test_set_length):
            Date.append(datetime.utcfromtimestamp((round(kline[0] / 1000))) )
            Open.append(float(kline[1]))
            Close.append(float(kline[4]))
            High.append(float(kline[2]))
            Low.append(float(kline[3]))
            Volume.append(float(kline[7]))
    elif TIME_INTERVAL==60 and test_set:
        for kline in client.futures_historical_klines(symbol, Client.KLINE_INTERVAL_1HOUR,start_str=test_set_length):
            Date.append(datetime.utcfromtimestamp((round(kline[0] / 1000))) )
            Open.append(float(kline[1]))
            Close.append(float(kline[4]))
            High.append(float(kline[2]))
            Low.append(float(kline[3]))
            Volume.append(float(kline[7]))
    elif TIME_INTERVAL==120 and test_set:
        for kline in client.futures_historical_klines(symbol, Client.KLINE_INTERVAL_2HOUR,start_str=test_set_length):
            Date.append(datetime.utcfromtimestamp((round(kline[0] / 1000))))
            Open.append(float(kline[1]))
            Close.append(float(kline[4]))
            High.append(float(kline[2]))
            Low.append(float(kline[3]))
            Volume.append(float(kline[7]))
    elif TIME_INTERVAL==240 and test_set:
        for kline in client.futures_historical_klines(symbol, Client.KLINE_INTERVAL_4HOUR,start_str=test_set_length):
            Date.append(datetime.utcfromtimestamp((round(kline[0] / 1000))) )
            Open.append(float(kline[1]))
            Close.append(float(kline[4]))
            High.append(float(kline[2]))
            Low.append(float(kline[3]))
            Volume.append(float(kline[7]))
    elif TIME_INTERVAL==360 and test_set:
        for kline in client.futures_historical_klines(symbol, Client.KLINE_INTERVAL_6HOUR,start_str=test_set_length):
            Date.append(datetime.utcfromtimestamp((round(kline[0] / 1000))) )
            Open.append(float(kline[1]))
            Close.append(float(kline[4]))
            High.append(float(kline[2]))
            Low.append(float(kline[3]))
            Volume.append(float(kline[7]))
    elif TIME_INTERVAL==480 and test_set:
        for kline in client.futures_historical_klines(symbol, Client.KLINE_INTERVAL_8HOUR,start_str=test_set_length):
            Date.append(datetime.utcfromtimestamp((round(kline[0] / 1000))))
            Open.append(float(kline[1]))
            Close.append(float(kline[4]))
            High.append(float(kline[2]))
            Low.append(float(kline[3]))
            Volume.append(float(kline[7]))
    elif TIME_INTERVAL==720 and test_set:
        for kline in client.futures_historical_klines(symbol, Client.KLINE_INTERVAL_12HOUR,start_str=test_set_length):
            Date.append(datetime.utcfromtimestamp((round(kline[0] / 1000))) )
            Open.append(float(kline[1]))
            Close.append(float(kline[4]))
            High.append(float(kline[2]))
            Low.append(float(kline[3]))
            Volume.append(float(kline[7]))
    elif TIME_INTERVAL==1440 and test_set:
        for kline in client.futures_historical_klines(symbol, Client.KLINE_INTERVAL_1DAY,start_str=test_set_length):
            Date.append(datetime.utcfromtimestamp((round(kline[0] / 1000))) )
            Open.append(float(kline[1]))
            Close.append(float(kline[4]))
            High.append(float(kline[2]))
            Low.append(float(kline[3]))
            Volume.append(float(kline[7]))
    elif TIME_INTERVAL==4320 and test_set:
        for kline in client.futures_historical_klines(symbol, Client.KLINE_INTERVAL_3DAY,start_str=test_set_length):
            Date.append(datetime.utcfromtimestamp((round(kline[0] / 1000))))
            Open.append(float(kline[1]))
            Close.append(float(kline[4]))
            High.append(float(kline[2]))
            Low.append(float(kline[3]))
            Volume.append(float(kline[7]))
    elif TIME_INTERVAL==10080 and test_set:
        for kline in client.futures_historical_klines(symbol, Client.KLINE_INTERVAL_1WEEK,start_str=test_set_length):
            Date.append(datetime.utcfromtimestamp((round(kline[0] / 1000))))
            Open.append(float(kline[1]))
            Close.append(float(kline[4]))
            High.append(float(kline[2]))
            Low.append(float(kline[3]))
            Volume.append(float(kline[7]))
    elif TIME_INTERVAL==40320 and test_set:
        for kline in client.futures_historical_klines(symbol, Client.KLINE_INTERVAL_1MONTH,start_str=test_set_length):
            Date.append(datetime.utcfromtimestamp((round(kline[0] / 1000))))
            Open.append(float(kline[1]))
            Close.append(float(kline[4]))
            High.append(float(kline[2]))
            Low.append(float(kline[3]))
            Volume.append(float(kline[7]))
    if not test_set:
        ##klines used for stoploss and takeprofit
        for kline in client.futures_historical_klines(symbol, Client.KLINE_INTERVAL_1MINUTE,start_str=start_string,end_str=test_set_length):
            # print(kline)
            Date_1min.append(datetime.utcfromtimestamp((round(kline[0]/1000))))
            Open_1min.append(float(kline[1]))
            High_1min.append(float(kline[2]))
            Low_1min.append(float(kline[3]))
            Close_1min.append(float(kline[4]))
    elif test_set:
        ##klines used for stoploss and takeprofit
        for kline in client.futures_historical_klines(symbol, Client.KLINE_INTERVAL_1MINUTE, start_str=test_set_length):
            # print(kline)
            Date_1min.append(datetime.utcfromtimestamp((round(kline[0] / 1000))))
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
    return Date,Open,Close,High,Low,Volume,High_1min,Low_1min,Close_1min,Open_1min,Date_1min

def get_coin_attrib(symbol):
    Coin_precision = -99
    Order_precision = -99

    if symbol == 'BTCUSDT':
        Coin_precision = 2
        Order_precision = 3

    elif symbol == 'ETHUSDT':
        Coin_precision = 2
        Order_precision = 3

    elif symbol == 'LTCUSDT':
        Coin_precision = 2
        Order_precision = 3

    elif symbol == 'SOLUSDT':
        Coin_precision = 3
        Order_precision = 0

    elif symbol == 'BNBUSDT':
        Coin_precision = 2
        Order_precision = 2

    elif symbol == 'ADAUSDT':
        Coin_precision = 4
        Order_precision = 0

    elif symbol == 'DOGEUSDT':
        Coin_precision = 5
        Order_precision = 0

    elif symbol == 'MATICUSDT':
        Coin_precision = 4
        Order_precision = 0

    elif symbol == "BAKEUSDT":
        Coin_precision = 4
        Order_precision = 0

    elif symbol == "SHIBUSDT":
        Coin_precision = 5
        Order_precision = 0

    elif symbol == "XRPUSDT":
        Coin_precision = 4
        Order_precision = 1

    elif symbol == "SUSHIUSDT":
        Coin_precision = 3
        Order_precision = 0

    elif symbol == "DOTUSDT":
        Coin_precision = 3
        Order_precision = 1

    elif symbol == "ALPHAUSDT":
        Coin_precision = 4
        Order_precision = 0

    elif symbol == "DGBUSDT":
        Coin_precision = 5
        Order_precision = 0

    elif symbol == "RLCUSDT":
        Coin_precision = 4
        Order_precision = 1

    elif symbol == "HNTUSDT":
        Coin_precision = 3
        Order_precision = 0

    elif symbol == "OCEANUSDT":
        Coin_precision = 5
        Order_precision = 0

    elif symbol == "ZRXUSDT":
        Coin_precision = 4
        Order_precision = 1

    elif symbol == "ONTUSDT":
        Coin_precision = 4
        Order_precision = 1

    elif symbol == "FLMUSDT":
        Coin_precision = 4
        Order_precision = 0

    elif symbol == "BCHUSDT":
        Coin_precision = 2
        Order_precision = 3

    elif symbol == "BTSUSDT":
        Coin_precision = 5
        Order_precision = 0

    elif symbol == "RSRUSDT":
        Coin_precision = 6
        Order_precision = 0

    elif symbol == "BZRXUSDT":
        Coin_precision = 4
        Order_precision = 0

    elif symbol == "SFPUSDT":
        Coin_precision = 4
        Order_precision = 0

    elif symbol == "ZILUSDT":
        Coin_precision = 4
        Order_precision = 0

    elif symbol == "EOSUSDT":
        Coin_precision = 3
        Order_precision = 1

    elif symbol == "ENJUSDT":
        Coin_precision = 4
        Order_precision = 0

    elif symbol == "TRXUSDT":
        Coin_precision = 5
        Order_precision = 0

    elif symbol == "LITUSDT":
        Coin_precision = 3
        Order_precision = 1

    elif symbol == "RENUSDT":
        Coin_precision = 5
        Order_precision = 0

    elif symbol == "COTIUSDT":
        Coin_precision = 5
        Order_precision = 0

    elif symbol == "STORJUSDT":
        Coin_precision = 4
        Order_precision = 0

    elif symbol == "LRCUSDT":
        Coin_precision = 5
        Order_precision = 0

    elif symbol == "UNFIUSDT":
        Coin_precision = 3
        Order_precision = 1

    elif symbol =='BALUSDT':
        Coin_precision = 3
        Order_precision = 1

    elif symbol =='YFIIUSDT':
        Coin_precision = 1
        Order_precision = 3

    elif symbol =='UNIUSDT':
        Coin_precision = 3
        Order_precision = 0

    elif symbol =='TLMUSDT':
        Coin_precision = 4
        Order_precision = 0

    elif symbol =='GTCUSDT':
        Coin_precision = 3
        Order_precision = 1

    elif symbol =='TRBUSDT':
        Coin_precision = 2
        Order_precision = 1

    elif symbol == 'ALICEUSDT':
        Coin_precision = 3
        Order_precision = 1

    elif symbol =='ONEUSDT':
        Coin_precision = 5
        Order_precision = 0

    elif symbol =='RVNUSDT':
        Coin_precision = 5
        Order_precision = 0

    elif symbol =='AXSUSDT':
        Coin_precision = 2
        Order_precision = 0

    elif symbol =='XEMUSDT':
        Coin_precision = 4
        Order_precision = 1

    elif symbol =='VETUSDT':
        Coin_precision = 5
        Order_precision = 0

    elif symbol =='LINAUSDT':
        Coin_precision = 5
        Order_precision = 0

    elif symbol =='XLMUSDT':
        Coin_precision = 5
        Order_precision = 0

    elif symbol =='QTUMUSDT':
        Coin_precision = 3
        Order_precision = 1

    elif symbol =='SOLUSDT':
        Coin_precision = 3
        Order_precision = 0

    elif symbol =='RAYUSDT':
        Coin_precision = 1
        Order_precision = 3

    elif symbol =='NEARUSDT':
        Coin_precision = 4
        Order_precision = 0

    elif symbol =='AUDIOUSDT':
        Coin_precision = 4
        Order_precision = 0

    elif symbol =='HOTUSDT':
        Coin_precision = 6
        Order_precision = 0

    elif symbol =='ARUSDT':
        Coin_precision = 3
        Order_precision = 1

    elif symbol =='BELUSDT':
        Coin_precision = 0
        Order_precision = 4

    elif symbol =='CHRUSDT':
        Coin_precision = 4
        Order_precision = 0

    elif symbol =='WAVESUSDT':
        Coin_precision = 3
        Order_precision = 1

    elif symbol =='CHZUSDT':
        Coin_precision = 5
        Order_precision = 0

    elif symbol =='SANDUSDT':
        Coin_precision = 5
        Order_precision = 0

    elif symbol =='GRTUSDT':
        Coin_precision = 5
        Order_precision = 0

    elif symbol =='FTMUSDT':
        Coin_precision = 5
        Order_precision = 0

    elif symbol =='XTZUSDT':
        Coin_precision = 3
        Order_precision = 0

    elif symbol =='LUNAUSDT':
        Coin_precision = 3
        Order_precision = 0

    elif symbol =='SKLUSDT':
        Coin_precision = 5
        Order_precision = 0

    elif symbol =='1INCHUSDT':
        Coin_precision = 4
        Order_precision = 0

    elif symbol =='ATOMUSDT':
        Coin_precision = 3
        Order_precision = 3

    elif symbol =='BLZUSDT':
        Coin_precision = 5
        Order_precision = 0

    elif symbol =='SNXUSDT':
        Coin_precision = 3
        Order_precision = 1

    elif symbol =='ETCUSDT':
        Coin_precision = 3
        Order_precision = 1

    elif symbol =='CELRUSDT':
        Coin_precision = 5
        Order_precision = 0

    elif symbol =='OGNUSDT':
        Coin_precision = 4
        Order_precision = 0

    elif symbol =='NEOUSDT':
        Coin_precision = 3
        Order_precision = 2

    elif symbol =='TOMOUSDT':
        Coin_precision = 4
        Order_precision = 0

    elif symbol =='CELOUSDT':
        Coin_precision = 3
        Order_precision = 0

    elif symbol =='KLAYUSDT':
        Coin_precision = 4
        Order_precision = 1

    elif symbol =='EGLDUSDT':
        Coin_precision = 2
        Order_precision = 1

    elif symbol =='CRVUSDT':
        Coin_precision = 3
        Order_precision = 1

    elif symbol =='NUUSDT':
        Coin_precision = 4
        Order_precision = 1

    elif symbol =='SRMUSDT':
        Coin_precision = 3
        Order_precision = 0

    elif symbol =='CTKUSDT':
        Coin_precision = 3
        Order_precision = 0

    elif symbol =='ARPAUSDT':
        Coin_precision = 5
        Order_precision = 0

    elif symbol =='IOTXUSDT':
        Coin_precision = 5
        Order_precision = 0

    elif symbol =='DENTUSDT':
        Coin_precision = 6
        Order_precision = 0

    elif symbol =='IOSTUSDT':
        Coin_precision = 6
        Order_precision = 0

    elif symbol =='OMGUSDT':
        Coin_precision = 3
        Order_precision = 1

    elif symbol =='BANDUSDT':
        Coin_precision = 4
        Order_precision = 1

    elif symbol =='NKNUSDT':
        Coin_precision = 5
        Order_precision = 0

    elif symbol =='IOTAUSDT':
        Coin_precision = 4
        Order_precision = 1

    elif symbol =='CVCUSDT':
        Coin_precision = 5
        Order_precision = 0

    elif symbol =='REEFUSDT':
        Coin_precision = 6
        Order_precision = 0

    elif symbol =='BTTUSDT':
        Coin_precision = 6
        Order_precision = 0

    elif symbol =='ANKRUSDT':
        Coin_precision = 5
        Order_precision = 0

    elif symbol =='ALGOUSDT':
        Coin_precision = 4
        Order_precision = 0

    elif symbol =='SCUSDT':
        Coin_precision = 6
        Order_precision = 0

    elif symbol =='MANAUSDT':
        Coin_precision = 4
        Order_precision = 0

    elif symbol =='ATAUSDT':
        Coin_precision = 4
        Order_precision = 0

    elif symbol =='MKRUSDT':
        Coin_precision = 1
        Order_precision = 3

    elif symbol =='DODOUSDT':
        Coin_precision = 3
        Order_precision = 1

    elif symbol =='ICPUSDT':
        Coin_precision = 2
        Order_precision = 2

    elif symbol =='ZECUSDT':
        Coin_precision = 2
        Order_precision = 2

    elif symbol =='ICXUSDT':
        Coin_precision = 4
        Order_precision = 0

    elif symbol == 'ZENUSDT':
        Coin_precision = 3
        Order_precision = 1

    elif symbol == 'SXPUSDT':
        Coin_precision = 4
        Order_precision = 1

    elif symbol == 'HBARUSDT':
        Coin_precision = 5
        Order_precision = 0

    elif symbol == 'CTSIUSDT':
        Coin_precision = 4
        Order_precision = 0

    elif symbol == 'KAVAUSDT':
        Coin_precision = 4
        Order_precision = 0

    elif symbol == 'C98USDT':
        Coin_precision = 4
        Order_precision = 0

    elif symbol == 'THETAUSDT':
        Coin_precision = 3
        Order_precision = 1

    elif symbol == 'MASKUSDT':
        Coin_precision = 4
        Order_precision = 0

    elif symbol == 'AAVEUSDT':
        Coin_precision = 2
        Order_precision = 1

    elif symbol == 'YFIUSDT':
        Coin_precision = 0
        Order_precision = 3

    elif symbol == 'COMPUSDT':
        Coin_precision = 2
        Order_precision = 3

    elif symbol == 'RUNEUSDT':
        Coin_precision = 3
        Order_precision = 0

    elif symbol == 'AVAXUSDT':
        Coin_precision = 3
        Order_precision = 0

    elif symbol == 'KNCUSDT':
        Coin_precision = 3
        Order_precision = 0

    elif symbol == 'LPTUSDT':
        Coin_precision = 3
        Order_precision = 1

    elif symbol == 'MTLUSDT':
        Coin_precision = 4
        Order_precision = 0

    elif symbol == 'DASHUSDT':
        Coin_precision = 2
        Order_precision = 3

    elif symbol == 'KEEPUSDT':
        Coin_precision = 4
        Order_precision = 0

    elif symbol == 'DYDXUSDT':
        Coin_precision = 3
        Order_precision = 1

    elif symbol == 'LINKUSDT':
        Coin_precision = 3
        Order_precision = 2

    elif symbol == 'KSMUSDT':
        Coin_precision = 2
        Order_precision = 1

    elif symbol == 'FILUSDT':
        Coin_precision = 3
        Order_precision = 1

    elif symbol == 'STMXUSDT':
        Coin_precision = 5
        Order_precision = 0

    elif symbol == 'GALAUSDT':
        Coin_precision = 5
        Order_precision = 0

    elif symbol == 'BATUSDT':
        Coin_precision = 4
        Order_precision = 1

    elif symbol == 'AKROUSDT':
        Coin_precision = 5
        Order_precision = 0

    elif symbol == 'XMRUSDT':
        Coin_precision = 2
        Order_precision = 3

    return Coin_precision,Order_precision

def get_historical(symbol,start_string,Interval):
    Open = []
    High = []
    Low = []
    Close = []
    Volume = []
    Date = []
    if Interval == '1m':
        for kline in client.futures_historical_klines(symbol, Client.KLINE_INTERVAL_1MINUTE,start_str=start_string):
            Date.append(int(kline[0])/1000)
            Open.append(float(kline[1]))
            Close.append(float(kline[4]))
            High.append(float(kline[2]))
            Low.append(float(kline[3]))
            Volume.append(float(kline[7]))
    elif Interval == '3m':
        for kline in client.futures_historical_klines(symbol, Client.KLINE_INTERVAL_3MINUTE,start_str=start_string):
            Date.append(int(kline[0])/1000)
            Open.append(float(kline[1]))
            Close.append(float(kline[4]))
            High.append(float(kline[2]))
            Low.append(float(kline[3]))
            Volume.append(float(kline[7]))
    elif Interval == '5m':
        for kline in client.futures_historical_klines(symbol, Client.KLINE_INTERVAL_5MINUTE,start_str=start_string):
            Date.append(int(kline[0])/1000)
            Open.append(float(kline[1]))
            Close.append(float(kline[4]))
            High.append(float(kline[2]))
            Low.append(float(kline[3]))
            Volume.append(float(kline[7]))
    elif Interval == '15m':
        for kline in client.futures_historical_klines(symbol, Client.KLINE_INTERVAL_15MINUTE,start_str=start_string):
            Date.append(int(kline[0])/1000)
            Open.append(float(kline[1]))
            Close.append(float(kline[4]))
            High.append(float(kline[2]))
            Low.append(float(kline[3]))
            Volume.append(float(kline[7]))
    elif Interval == '30m':
        for kline in client.futures_historical_klines(symbol, Client.KLINE_INTERVAL_30MINUTE,start_str=start_string):
            Date.append(int(kline[0])/1000)
            Open.append(float(kline[1]))
            Close.append(float(kline[4]))
            High.append(float(kline[2]))
            Low.append(float(kline[3]))
            Volume.append(float(kline[7]))
    elif Interval == '1h':
        for kline in client.futures_historical_klines(symbol, Client.KLINE_INTERVAL_1HOUR,start_str=start_string):
            Date.append(int(kline[0])/1000)
            Open.append(float(kline[1]))
            Close.append(float(kline[4]))
            High.append(float(kline[2]))
            Low.append(float(kline[3]))
            Volume.append(float(kline[7]))
    elif Interval == '2h':
        for kline in client.futures_historical_klines(symbol, Client.KLINE_INTERVAL_2HOUR,start_str=start_string):
            Date.append(int(kline[0])/1000)
            Open.append(float(kline[1]))
            Close.append(float(kline[4]))
            High.append(float(kline[2]))
            Low.append(float(kline[3]))
            Volume.append(float(kline[7]))
    elif Interval == '4h':
        for kline in client.futures_historical_klines(symbol, Client.KLINE_INTERVAL_4HOUR,start_str=start_string):
            Date.append(int(kline[0])/1000)
            Open.append(float(kline[1]))
            Close.append(float(kline[4]))
            High.append(float(kline[2]))
            Low.append(float(kline[3]))
            Volume.append(float(kline[7]))
    elif Interval == '6h':
        for kline in client.futures_historical_klines(symbol, Client.KLINE_INTERVAL_6HOUR,start_str=start_string):
            Date.append(int(kline[0])/1000)
            Open.append(float(kline[1]))
            Close.append(float(kline[4]))
            High.append(float(kline[2]))
            Low.append(float(kline[3]))
            Volume.append(float(kline[7]))
    elif Interval == '8h':
        for kline in client.futures_historical_klines(symbol, Client.KLINE_INTERVAL_8HOUR,start_str=start_string):
            Date.append(int(kline[0])/1000)
            Open.append(float(kline[1]))
            Close.append(float(kline[4]))
            High.append(float(kline[2]))
            Low.append(float(kline[3]))
            Volume.append(float(kline[7]))
    elif Interval == '12h':
        for kline in client.futures_historical_klines(symbol, Client.KLINE_INTERVAL_12HOUR,start_str=start_string):
            Date.append(int(kline[0])/1000)
            Open.append(float(kline[1]))
            Close.append(float(kline[4]))
            High.append(float(kline[2]))
            Low.append(float(kline[3]))
            Volume.append(float(kline[7]))
    elif Interval == '1d':
        for kline in client.futures_historical_klines(symbol, Client.KLINE_INTERVAL_1DAY,start_str=start_string):
            Date.append(int(kline[0])/1000)
            Open.append(float(kline[1]))
            Close.append(float(kline[4]))
            High.append(float(kline[2]))
            Low.append(float(kline[3]))
            Volume.append(float(kline[7]))
    elif Interval == '3d':
        for kline in client.futures_historical_klines(symbol, Client.KLINE_INTERVAL_3DAY,start_str=start_string):
            Date.append(int(kline[0])/1000)
            Open.append(float(kline[1]))
            Close.append(float(kline[4]))
            High.append(float(kline[2]))
            Low.append(float(kline[3]))
            Volume.append(float(kline[7]))
    elif Interval == '1w':
        for kline in client.futures_historical_klines(symbol, Client.KLINE_INTERVAL_1WEEK,start_str=start_string):
            Date.append(int(kline[0])/1000)
            Open.append(float(kline[1]))
            Close.append(float(kline[4]))
            High.append(float(kline[2]))
            Low.append(float(kline[3]))
            Volume.append(float(kline[7]))

    return Date,Open,Close,High,Low,Volume

def align_Datasets(Date_1min,High_1min,Low_1min,Close_1min,Open_1min,Date,Open,Close,High,Low,Volume,symbol):

    start_date = [Date[0][0],0]
    end_date = [Date[0][-1],0]
    for i in range(len(Date)):
        if Date[i][0] < start_date[0]:
            start_date = [Date[i][0],i] ##Date,index of start date
        if Date[i][-1] > end_date[0]:
            end_date = [Date[i][-1],i] ##Date, index of end date
    for i in range(len(Date_1min)):
        len_infront = 0
        len_behind = 0
        for j in range(len(Date_1min[start_date[1]])):
            if Date_1min[start_date[1]][j]!=Date_1min[i][0]:
                len_infront+=1
            else:
                break
        for j in range(len(Date_1min[end_date[1]])-1,-1,-1):
            if Date_1min[end_date[1]][j]!=Date_1min[i][-1]:
                len_behind+=1
            else:
                break
        for j in range(len_infront):
            Date_1min[i].insert(0,"Data Set hasn't started yet")
            High_1min[i].insert(0,High_1min[i][0])
            Low_1min[i].insert(0,Low_1min[i][0])
            Close_1min[i].insert(0,Close_1min[i][0])
            Open_1min[i].insert(0,Open_1min[i][0])
        for j in range(len_behind):
            Date_1min[i].append("Data Set Ended")
            High_1min[i].append(High_1min[i][-1])
            Low_1min[i].append(Low_1min[i][-1])
            Close_1min[i].append(Close_1min[i][-1])
            Open_1min[i].append(Open_1min[i][-1])
    for i in range(len(Date)):
        len_infront = 0
        len_behind = 0
        for j in range(len(Date[start_date[1]])):
            if Date[start_date[1]][j] != Date[i][0]:
                len_infront += 1
            else:
                break
        for j in range(len(Date[end_date[1]]) - 1, -1, -1):
            if Date[end_date[1]][j] != Date[i][-1]:
                len_behind += 1
            else:
                break
        for j in range(len_infront):
            Date[i].insert(0, "Data Set hasn't started yet")
            High[i].insert(0, High[i][0])
            Low[i].insert(0, Low[i][0])
            Close[i].insert(0, Close[i][0])
            Open[i].insert(0, Open[i][0])
            Volume[i].insert(0,Volume[i][0])
        for j in range(len_behind):
            Date[i].append("Data Set Ended")
            High[i].append(High[i][-1])
            Low[i].append(Low[i][-1])
            Close[i].append(Close[i][-1])
            Open[i].append(Open[i][-1])
            Volume[i].insert(0,Volume[i][-1])

    '''locations_to_pop = [] ##list of datasets that won't line up we will remove later
    shortest_dataSet = [-99, 99999999999]  ## [which index , length of dataset]
    for i in range(len(Date_1min)):
        if len(Date_1min[i]) < shortest_dataSet[1]:
            shortest_dataSet[0] = i  ##index of shortest data set
            shortest_dataSet[1] = len(Date_1min[i])  ##length of that data set
    for i in range(len(symbol)):
        found_flag=0
        for j in range(len(Date_1min[i])):
            if Date_1min[i][j] == Date[shortest_dataSet[0]][0]:
                High_1min[i] = High_1min[i][j:]
                Low_1min[i] = Low_1min[i][j:]
                Date_1min[i] = Date_1min[i][j:]
                Close_1min[i] = Close_1min[i][j:]
                Open_1min[i] = Open_1min[i][j:]
                found_flag=1
                # start_1min.append(j)
                break
        if found_flag == 0 :
            locations_to_pop.append(i)
        found_flag=0
        for j in range(len(Date[i])):
            if Date[i][j] == Date[shortest_dataSet[0]][0]:
                Date[i] = Date[i][j:]
                Open[i] = Open[i][j:]
                Close[i] = Close[i][j:]
                High[i] = High[i][j:]
                Low[i] = Low[i][j:]
                Volume[i] = Volume[i][j:]
                found_flag=1
                # start.append(j)
                break

        if found_flag == 0:
            already_in_list = 0
            for x in locations_to_pop:
                if x==i:
                    already_in_list = 1
            if not already_in_list:
                locations_to_pop.append(i)
    ##account for the fact that if we pop an element then the indices in locations_to_pop need to be adjusted by 1 unit for each element we pop
    adjust = 0
    for i in range(len(locations_to_pop)):
        locations_to_pop[i]-=adjust
        adjust+=1

    for i in range(len(symbol)):
        found_flag=[0,0]
        for j in range(len(Date_1min[i])):
            if Date_1min[i][j] == Date[shortest_dataSet[0]][-1]:
                High_1min[i] = High_1min[i][:j]
                Low_1min[i] = Low_1min[i][:j]
                Date_1min[i] = Date_1min[i][:j]
                Close_1min[i] = Close_1min[i][:j]
                Open_1min[i] = Open_1min[i][:j]
                found_flag[0]=1
                # start_1min.append(j)
                break
        for j in range(len(Date[i])):
            if Date[i][j] == Date[shortest_dataSet[0]][-1]:
                Date[i] = Date[i][:j]
                Open[i] = Open[i][:j]
                Close[i] = Close[i][:j]
                High[i] = High[i][:j]
                Low[i] = Low[i][:j]
                Volume[i] = Volume[i][:j]
                found_flag[1] = 1
                # start.append(j)
                break
    longest_dataSet = [-99, -99999999999]  ## [which index , length of dataset]
    for i in range(len(Date_1min)):
        if len(Date_1min[i]) > longest_dataSet[1]:
            longest_dataSet[0] = i  ##index of shortest data set
            longest_dataSet[1] = len(Date_1min[i])  ##length of that data set
    for i in range(len(Date_1min)):
        while len(Date_1min[i])<len(Date_1min[longest_dataSet[0]]):
            High_1min[i].append(High_1min[i][-1])
            Low_1min[i].append(Low_1min[i][-1])
            Date_1min[i].append(Date_1min[i][-1])
            Close_1min[i].append(Close_1min[i][-1])
            Open_1min[i].append(Open_1min[i][-1])
    for i in range(len(Date)):
        while len(Date[i])<len(Date[longest_dataSet[0]]):
            Date[i].append(Date[i][-1])
            Open[i].append(Open[i][-1])
            Close[i].append(Close[i][-1])
            High[i].append(High[i][-1])
            Low[i].append(Low[i][-1])
            Volume[i].append(Volume[i][-1])
    '''

    return Date_1min,High_1min,Low_1min,Close_1min,Open_1min,Date,Open,Close,High,Low,Volume#,locations_to_pop

def get_period_String(test_set_length,time_period):
    period_string = ''
    time_CAGR = -99
    if test_set_length[2] == 'd' or test_set_length[3] == 'd' or test_set_length[4] == 'd':
        time_CAGR = time_period / 365
        period_string = 'day'
    elif test_set_length[2] == 'w' or test_set_length[3] == 'w':
        time_CAGR = time_period / 52
        period_string = 'week'
    elif test_set_length[2] == 'm' or test_set_length[3] == 'm':
        time_CAGR = time_period/ 12
        period_string = 'month'
    elif test_set_length[2] == 'y':
        time_CAGR = time_period
        period_string = 'year'

    return period_string,time_CAGR
