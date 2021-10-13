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
            Date.append(datetime.utcfromtimestamp((round(kline[0] / 1000))) + timedelta(hours=1))
            Open.append(float(kline[1]))
            Close.append(float(kline[4]))
            High.append(float(kline[2]))
            Low.append(float(kline[3]))
            Volume.append(float(kline[7]))
    elif TIME_INTERVAL==3 and not test_set:
        for kline in client.futures_historical_klines(symbol, Client.KLINE_INTERVAL_3MINUTE,start_str=start_string,end_str=test_set_length):
            Date.append(datetime.utcfromtimestamp((round(kline[0] / 1000))) + timedelta(hours=1))
            Open.append(float(kline[1]))
            Close.append(float(kline[4]))
            High.append(float(kline[2]))
            Low.append(float(kline[3]))
            Volume.append(float(kline[7]))
    elif TIME_INTERVAL==5 and not test_set:
        for kline in client.futures_historical_klines(symbol, Client.KLINE_INTERVAL_5MINUTE,start_str=start_string,end_str=test_set_length):
            Date.append(datetime.utcfromtimestamp((round(kline[0] / 1000))) + timedelta(hours=1))
            Open.append(float(kline[1]))
            Close.append(float(kline[4]))
            High.append(float(kline[2]))
            Low.append(float(kline[3]))
            Volume.append(float(kline[7]))
    elif TIME_INTERVAL==15 and not test_set:
        for kline in client.futures_historical_klines(symbol, Client.KLINE_INTERVAL_15MINUTE,start_str=start_string,end_str=test_set_length):
            Date.append(datetime.utcfromtimestamp((round(kline[0] / 1000))) + timedelta(hours=1))
            Open.append(float(kline[1]))
            Close.append(float(kline[4]))
            High.append(float(kline[2]))
            Low.append(float(kline[3]))
            Volume.append(float(kline[7]))
    elif TIME_INTERVAL==30 and not test_set:
        for kline in client.futures_historical_klines(symbol, Client.KLINE_INTERVAL_30MINUTE,start_str=start_string,end_str=test_set_length):
            Date.append(datetime.utcfromtimestamp((round(kline[0] / 1000))) + timedelta(hours=1))
            Open.append(float(kline[1]))
            Close.append(float(kline[4]))
            High.append(float(kline[2]))
            Low.append(float(kline[3]))
            Volume.append(float(kline[7]))
    elif TIME_INTERVAL==60 and not test_set:
        for kline in client.futures_historical_klines(symbol, Client.KLINE_INTERVAL_1HOUR,start_str=start_string,end_str=test_set_length):
            Date.append(datetime.utcfromtimestamp((round(kline[0] / 1000))) + timedelta(hours=1))
            Open.append(float(kline[1]))
            Close.append(float(kline[4]))
            High.append(float(kline[2]))
            Low.append(float(kline[3]))
            Volume.append(float(kline[7]))
    elif TIME_INTERVAL==120 and not test_set:
        for kline in client.futures_historical_klines(symbol, Client.KLINE_INTERVAL_2HOUR,start_str=start_string,end_str=test_set_length):
            Date.append(datetime.utcfromtimestamp((round(kline[0] / 1000))) + timedelta(hours=1))
            Open.append(float(kline[1]))
            Close.append(float(kline[4]))
            High.append(float(kline[2]))
            Low.append(float(kline[3]))
            Volume.append(float(kline[7]))
    elif TIME_INTERVAL==240 and not test_set:
        for kline in client.futures_historical_klines(symbol, Client.KLINE_INTERVAL_4HOUR,start_str=start_string,end_str=test_set_length):
            Date.append(datetime.utcfromtimestamp((round(kline[0] / 1000))) + timedelta(hours=1))
            Open.append(float(kline[1]))
            Close.append(float(kline[4]))
            High.append(float(kline[2]))
            Low.append(float(kline[3]))
            Volume.append(float(kline[7]))
    elif TIME_INTERVAL==360 and not test_set:
        for kline in client.futures_historical_klines(symbol, Client.KLINE_INTERVAL_6HOUR,start_str=start_string,end_str=test_set_length):
            Date.append(datetime.utcfromtimestamp((round(kline[0] / 1000))) + timedelta(hours=1))
            Open.append(float(kline[1]))
            Close.append(float(kline[4]))
            High.append(float(kline[2]))
            Low.append(float(kline[3]))
            Volume.append(float(kline[7]))
    elif TIME_INTERVAL==480 and not test_set:
        for kline in client.futures_historical_klines(symbol, Client.KLINE_INTERVAL_8HOUR,start_str=start_string,end_str=test_set_length):
            Date.append(datetime.utcfromtimestamp((round(kline[0] / 1000))) + timedelta(hours=1))
            Open.append(float(kline[1]))
            Close.append(float(kline[4]))
            High.append(float(kline[2]))
            Low.append(float(kline[3]))
            Volume.append(float(kline[7]))
    elif TIME_INTERVAL==720 and not test_set:
        for kline in client.futures_historical_klines(symbol, Client.KLINE_INTERVAL_12HOUR,start_str=start_string,end_str=test_set_length):
            Date.append(datetime.utcfromtimestamp((round(kline[0] / 1000))) + timedelta(hours=1))
            Open.append(float(kline[1]))
            Close.append(float(kline[4]))
            High.append(float(kline[2]))
            Low.append(float(kline[3]))
            Volume.append(float(kline[7]))
    elif TIME_INTERVAL==1440 and not test_set:
        for kline in client.futures_historical_klines(symbol, Client.KLINE_INTERVAL_1DAY,start_str=start_string,end_str=test_set_length):
            Date.append(datetime.utcfromtimestamp((round(kline[0] / 1000))) + timedelta(hours=1))
            Open.append(float(kline[1]))
            Close.append(float(kline[4]))
            High.append(float(kline[2]))
            Low.append(float(kline[3]))
            Volume.append(float(kline[7]))
    elif TIME_INTERVAL==4320 and not test_set:
        for kline in client.futures_historical_klines(symbol, Client.KLINE_INTERVAL_3DAY,start_str=start_string,end_str=test_set_length):
            Date.append(datetime.utcfromtimestamp((round(kline[0] / 1000))) + timedelta(hours=1))
            Open.append(float(kline[1]))
            Close.append(float(kline[4]))
            High.append(float(kline[2]))
            Low.append(float(kline[3]))
            Volume.append(float(kline[7]))
    elif TIME_INTERVAL==10080 and not test_set:
        for kline in client.futures_historical_klines(symbol, Client.KLINE_INTERVAL_1WEEK,start_str=start_string,end_str=test_set_length):
            Date.append(datetime.utcfromtimestamp((round(kline[0] / 1000))) + timedelta(hours=1))
            Open.append(float(kline[1]))
            Close.append(float(kline[4]))
            High.append(float(kline[2]))
            Low.append(float(kline[3]))
            Volume.append(float(kline[7]))
    elif TIME_INTERVAL==40320 and not test_set:
        for kline in client.futures_historical_klines(symbol, Client.KLINE_INTERVAL_1MONTH,start_str=start_string,end_str=test_set_length):
            Date.append(datetime.utcfromtimestamp((round(kline[0] / 1000))) + timedelta(hours=1))
            Open.append(float(kline[1]))
            Close.append(float(kline[4]))
            High.append(float(kline[2]))
            Low.append(float(kline[3]))
            Volume.append(float(kline[7]))
    elif TIME_INTERVAL==1 and test_set:
        for kline in client.futures_historical_klines(symbol, Client.KLINE_INTERVAL_1MINUTE,start_str=test_set_length):
            Date.append(datetime.utcfromtimestamp((round(kline[0] / 1000))) + timedelta(hours=1))
            Open.append(float(kline[1]))
            Close.append(float(kline[4]))
            High.append(float(kline[2]))
            Low.append(float(kline[3]))
            Volume.append(float(kline[7]))
    elif TIME_INTERVAL==3 and test_set:
        for kline in client.futures_historical_klines(symbol, Client.KLINE_INTERVAL_3MINUTE,start_str=test_set_length):
            Date.append(datetime.utcfromtimestamp((round(kline[0] / 1000))) + timedelta(hours=1))
            Open.append(float(kline[1]))
            Close.append(float(kline[4]))
            High.append(float(kline[2]))
            Low.append(float(kline[3]))
            Volume.append(float(kline[7]))
    elif TIME_INTERVAL==5 and test_set:
        for kline in client.futures_historical_klines(symbol, Client.KLINE_INTERVAL_5MINUTE,start_str=test_set_length):
            Date.append(datetime.utcfromtimestamp((round(kline[0] / 1000))) + timedelta(hours=1))
            Open.append(float(kline[1]))
            Close.append(float(kline[4]))
            High.append(float(kline[2]))
            Low.append(float(kline[3]))
            Volume.append(float(kline[7]))
    elif TIME_INTERVAL==15 and test_set:
        for kline in client.futures_historical_klines(symbol, Client.KLINE_INTERVAL_15MINUTE,start_str=test_set_length):
            Date.append(datetime.utcfromtimestamp((round(kline[0] / 1000))) + timedelta(hours=1))
            Open.append(float(kline[1]))
            Close.append(float(kline[4]))
            High.append(float(kline[2]))
            Low.append(float(kline[3]))
            Volume.append(float(kline[7]))
    elif TIME_INTERVAL==30 and test_set:
        for kline in client.futures_historical_klines(symbol, Client.KLINE_INTERVAL_30MINUTE,start_str=test_set_length):
            Date.append(datetime.utcfromtimestamp((round(kline[0] / 1000))) + timedelta(hours=1))
            Open.append(float(kline[1]))
            Close.append(float(kline[4]))
            High.append(float(kline[2]))
            Low.append(float(kline[3]))
            Volume.append(float(kline[7]))
    elif TIME_INTERVAL==60 and test_set:
        for kline in client.futures_historical_klines(symbol, Client.KLINE_INTERVAL_1HOUR,start_str=test_set_length):
            Date.append(datetime.utcfromtimestamp((round(kline[0] / 1000))) + timedelta(hours=1))
            Open.append(float(kline[1]))
            Close.append(float(kline[4]))
            High.append(float(kline[2]))
            Low.append(float(kline[3]))
            Volume.append(float(kline[7]))
    elif TIME_INTERVAL==120 and test_set:
        for kline in client.futures_historical_klines(symbol, Client.KLINE_INTERVAL_2HOUR,start_str=test_set_length):
            Date.append(datetime.utcfromtimestamp((round(kline[0] / 1000))) + timedelta(hours=1))
            Open.append(float(kline[1]))
            Close.append(float(kline[4]))
            High.append(float(kline[2]))
            Low.append(float(kline[3]))
            Volume.append(float(kline[7]))
    elif TIME_INTERVAL==240 and test_set:
        for kline in client.futures_historical_klines(symbol, Client.KLINE_INTERVAL_4HOUR,start_str=test_set_length):
            Date.append(datetime.utcfromtimestamp((round(kline[0] / 1000))) + timedelta(hours=1))
            Open.append(float(kline[1]))
            Close.append(float(kline[4]))
            High.append(float(kline[2]))
            Low.append(float(kline[3]))
            Volume.append(float(kline[7]))
    elif TIME_INTERVAL==360 and test_set:
        for kline in client.futures_historical_klines(symbol, Client.KLINE_INTERVAL_6HOUR,start_str=test_set_length):
            Date.append(datetime.utcfromtimestamp((round(kline[0] / 1000))) + timedelta(hours=1))
            Open.append(float(kline[1]))
            Close.append(float(kline[4]))
            High.append(float(kline[2]))
            Low.append(float(kline[3]))
            Volume.append(float(kline[7]))
    elif TIME_INTERVAL==480 and test_set:
        for kline in client.futures_historical_klines(symbol, Client.KLINE_INTERVAL_8HOUR,start_str=test_set_length):
            Date.append(datetime.utcfromtimestamp((round(kline[0] / 1000))) + timedelta(hours=1))
            Open.append(float(kline[1]))
            Close.append(float(kline[4]))
            High.append(float(kline[2]))
            Low.append(float(kline[3]))
            Volume.append(float(kline[7]))
    elif TIME_INTERVAL==720 and test_set:
        for kline in client.futures_historical_klines(symbol, Client.KLINE_INTERVAL_12HOUR,start_str=test_set_length):
            Date.append(datetime.utcfromtimestamp((round(kline[0] / 1000))) + timedelta(hours=1))
            Open.append(float(kline[1]))
            Close.append(float(kline[4]))
            High.append(float(kline[2]))
            Low.append(float(kline[3]))
            Volume.append(float(kline[7]))
    elif TIME_INTERVAL==1440 and test_set:
        for kline in client.futures_historical_klines(symbol, Client.KLINE_INTERVAL_1DAY,start_str=test_set_length):
            Date.append(datetime.utcfromtimestamp((round(kline[0] / 1000))) + timedelta(hours=1))
            Open.append(float(kline[1]))
            Close.append(float(kline[4]))
            High.append(float(kline[2]))
            Low.append(float(kline[3]))
            Volume.append(float(kline[7]))
    elif TIME_INTERVAL==4320 and test_set:
        for kline in client.futures_historical_klines(symbol, Client.KLINE_INTERVAL_3DAY,start_str=test_set_length):
            Date.append(datetime.utcfromtimestamp((round(kline[0] / 1000))) + timedelta(hours=1))
            Open.append(float(kline[1]))
            Close.append(float(kline[4]))
            High.append(float(kline[2]))
            Low.append(float(kline[3]))
            Volume.append(float(kline[7]))
    elif TIME_INTERVAL==10080 and test_set:
        for kline in client.futures_historical_klines(symbol, Client.KLINE_INTERVAL_1WEEK,start_str=test_set_length):
            Date.append(datetime.utcfromtimestamp((round(kline[0] / 1000))) + timedelta(hours=1))
            Open.append(float(kline[1]))
            Close.append(float(kline[4]))
            High.append(float(kline[2]))
            Low.append(float(kline[3]))
            Volume.append(float(kline[7]))
    elif TIME_INTERVAL==40320 and test_set:
        for kline in client.futures_historical_klines(symbol, Client.KLINE_INTERVAL_1MONTH,start_str=test_set_length):
            Date.append(datetime.utcfromtimestamp((round(kline[0] / 1000))) + timedelta(hours=1))
            Open.append(float(kline[1]))
            Close.append(float(kline[4]))
            High.append(float(kline[2]))
            Low.append(float(kline[3]))
            Volume.append(float(kline[7]))
    if not test_set:
        ##klines used for stoploss and takeprofit
        for kline in client.futures_historical_klines(symbol, Client.KLINE_INTERVAL_1MINUTE,start_str=start_string,end_str=test_set_length):
            # print(kline)
            Date_1min.append(datetime.utcfromtimestamp((round(kline[0]/1000)))+timedelta(hours=1))
            Open_1min.append(float(kline[1]))
            High_1min.append(float(kline[2]))
            Low_1min.append(float(kline[3]))
            Close_1min.append(float(kline[4]))
    elif test_set:
        ##klines used for stoploss and takeprofit
        for kline in client.futures_historical_klines(symbol, Client.KLINE_INTERVAL_1MINUTE, start_str=test_set_length):
            # print(kline)
            Date_1min.append(datetime.utcfromtimestamp((round(kline[0] / 1000))) + timedelta(hours=1))
            Open_1min.append(float(kline[1]))
            High_1min.append(float(kline[2]))
            Low_1min.append(float(kline[3]))
            Close_1min.append(float(kline[4]))

    return Date,Open,Close,High,Low,Volume,High_1min,Low_1min,Close_1min,Open_1min,Date_1min

def get_coin_attrib(symbol):
    Coin_precision = -99
    Order_precision = -99

    if symbol == 'BTCUSDT':
        Coin_precision = 2
        Order_precision = 2

    elif symbol == 'ETHUSDT':
        Coin_precision = 2
        Order_precision = 2

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
            Date.append(int(kline[0]))
            Open.append(float(kline[1]))
            Close.append(float(kline[4]))
            High.append(float(kline[2]))
            Low.append(float(kline[3]))
            Volume.append(float(kline[7]))
    elif Interval == '3m':
        for kline in client.futures_historical_klines(symbol, Client.KLINE_INTERVAL_3MINUTE,start_str=start_string):
            Date.append(int(kline[0]))
            Open.append(float(kline[1]))
            Close.append(float(kline[4]))
            High.append(float(kline[2]))
            Low.append(float(kline[3]))
            Volume.append(float(kline[7]))
    elif Interval == '5m':
        for kline in client.futures_historical_klines(symbol, Client.KLINE_INTERVAL_5MINUTE,start_str=start_string):
            Date.append(int(kline[0]))
            Open.append(float(kline[1]))
            Close.append(float(kline[4]))
            High.append(float(kline[2]))
            Low.append(float(kline[3]))
            Volume.append(float(kline[7]))
    elif Interval == '15m':
        for kline in client.futures_historical_klines(symbol, Client.KLINE_INTERVAL_15MINUTE,start_str=start_string):
            Date.append(int(kline[0]))
            Open.append(float(kline[1]))
            Close.append(float(kline[4]))
            High.append(float(kline[2]))
            Low.append(float(kline[3]))
            Volume.append(float(kline[7]))
    elif Interval == '30m':
        for kline in client.futures_historical_klines(symbol, Client.KLINE_INTERVAL_30MINUTE,start_str=start_string):
            Date.append(int(kline[0]))
            Open.append(float(kline[1]))
            Close.append(float(kline[4]))
            High.append(float(kline[2]))
            Low.append(float(kline[3]))
            Volume.append(float(kline[7]))
    elif Interval == '1h':
        for kline in client.futures_historical_klines(symbol, Client.KLINE_INTERVAL_1HOUR,start_str=start_string):
            Date.append(int(kline[0]))
            Open.append(float(kline[1]))
            Close.append(float(kline[4]))
            High.append(float(kline[2]))
            Low.append(float(kline[3]))
            Volume.append(float(kline[7]))
    elif Interval == '2h':
        for kline in client.futures_historical_klines(symbol, Client.KLINE_INTERVAL_2HOUR,start_str=start_string):
            Date.append(int(kline[0]))
            Open.append(float(kline[1]))
            Close.append(float(kline[4]))
            High.append(float(kline[2]))
            Low.append(float(kline[3]))
            Volume.append(float(kline[7]))
    elif Interval == '4h':
        for kline in client.futures_historical_klines(symbol, Client.KLINE_INTERVAL_4HOUR,start_str=start_string):
            Date.append(int(kline[0]))
            Open.append(float(kline[1]))
            Close.append(float(kline[4]))
            High.append(float(kline[2]))
            Low.append(float(kline[3]))
            Volume.append(float(kline[7]))
    elif Interval == '6h':
        for kline in client.futures_historical_klines(symbol, Client.KLINE_INTERVAL_6HOUR,start_str=start_string):
            Date.append(int(kline[0]))
            Open.append(float(kline[1]))
            Close.append(float(kline[4]))
            High.append(float(kline[2]))
            Low.append(float(kline[3]))
            Volume.append(float(kline[7]))
    elif Interval == '8h':
        for kline in client.futures_historical_klines(symbol, Client.KLINE_INTERVAL_8HOUR,start_str=start_string):
            Date.append(int(kline[0]))
            Open.append(float(kline[1]))
            Close.append(float(kline[4]))
            High.append(float(kline[2]))
            Low.append(float(kline[3]))
            Volume.append(float(kline[7]))
    elif Interval == '12h':
        for kline in client.futures_historical_klines(symbol, Client.KLINE_INTERVAL_12HOUR,start_str=start_string):
            Date.append(int(kline[0]))
            Open.append(float(kline[1]))
            Close.append(float(kline[4]))
            High.append(float(kline[2]))
            Low.append(float(kline[3]))
            Volume.append(float(kline[7]))
    elif Interval == '1d':
        for kline in client.futures_historical_klines(symbol, Client.KLINE_INTERVAL_1DAY,start_str=start_string):
            Date.append(int(kline[0]))
            Open.append(float(kline[1]))
            Close.append(float(kline[4]))
            High.append(float(kline[2]))
            Low.append(float(kline[3]))
            Volume.append(float(kline[7]))
    elif Interval == '3d':
        for kline in client.futures_historical_klines(symbol, Client.KLINE_INTERVAL_3DAY,start_str=start_string):
            Date.append(int(kline[0]))
            Open.append(float(kline[1]))
            Close.append(float(kline[4]))
            High.append(float(kline[2]))
            Low.append(float(kline[3]))
            Volume.append(float(kline[7]))
    elif Interval == '1w':
        for kline in client.futures_historical_klines(symbol, Client.KLINE_INTERVAL_1WEEK,start_str=start_string):
            Date.append(int(kline[0]))
            Open.append(float(kline[1]))
            Close.append(float(kline[4]))
            High.append(float(kline[2]))
            Low.append(float(kline[3]))
            Volume.append(float(kline[7]))

    return Date,Open,Close,High,Low,Volume
