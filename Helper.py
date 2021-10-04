from binance.client import Client
from datetime import timezone,datetime,date,timedelta
client = Client(api_key='',api_secret='') ##Binance keys needed to get historical data/ Trade on an account
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
