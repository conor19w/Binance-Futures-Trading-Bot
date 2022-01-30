from binance.client import Client
from binance.exceptions import BinanceAPIException
from binance.enums import *
from datetime import timezone,datetime,date,timedelta
import API_keys
from joblib import load,dump
from download_Data import path
client = Client(api_key=API_keys.api_key,api_secret=API_keys.api_secret) ##Binance keys needed to get historical data/ Trade on an account

def get_TIME_INTERVAL(TIME_INTERVAL):
    ##Convert String to minutes
    if TIME_INTERVAL[1]=='m':
        TIME_INTERVAL = int(TIME_INTERVAL[0])
    elif TIME_INTERVAL[2]=='m':
        TIME_INTERVAL = int(TIME_INTERVAL[0])*10+int(TIME_INTERVAL[1])
    elif TIME_INTERVAL[1]=='h':
        TIME_INTERVAL = int(TIME_INTERVAL[0])*60
    elif TIME_INTERVAL[2]=='h':
        TIME_INTERVAL = int(TIME_INTERVAL[0])*10*60 + int(TIME_INTERVAL[1])*60
    elif TIME_INTERVAL[1]=='d':
        TIME_INTERVAL = int(TIME_INTERVAL[0]) * 1440
    elif TIME_INTERVAL[1]=='w':
        TIME_INTERVAL = int(TIME_INTERVAL[0]) * 1440*7
    elif TIME_INTERVAL[1]=='M':
        TIME_INTERVAL = int(TIME_INTERVAL[0]) * 1440*7*4
    return TIME_INTERVAL
def get_Klines(TIME_INTERVAL,symbol,time_period,test_set,time_period_units,save_data):
    print(f"Downloading CandleStick Data for {symbol}...")
    LENGTH = f"{time_period * 2} {time_period_units} ago UTC"  ##default to make the test set the same size as the non-test set
    time_period = f'{time_period} {time_period_units} ago UTC'

    Date = []
    Open = []
    Close = []
    High = []
    Low = []
    Volume = []
    High_1min = []
    Low_1min = []
    Close_1min = []
    Open_1min = []
    Date_1min = []
    ##klines for candlestick patterns and TA
    if not test_set:
        for kline in client.futures_historical_klines(symbol, TIME_INTERVAL, start_str=time_period):
            Date.append(datetime.utcfromtimestamp((round(kline[0] / 1000))))
            Open.append(float(kline[1]))
            Close.append(float(kline[4]))
            High.append(float(kline[2]))
            Low.append(float(kline[3]))
            Volume.append(float(kline[7]))

        if TIME_INTERVAL != '1m':
            for kline in client.futures_historical_klines(symbol, '1m', start_str=time_period):
                # print(kline)
                Date_1min.append(datetime.utcfromtimestamp((round(kline[0] / 1000))))
                Open_1min.append(float(kline[1]))
                High_1min.append(float(kline[2]))
                Low_1min.append(float(kline[3]))
                Close_1min.append(float(kline[4]))
        else:
            Date_1min = Date
            Open_1min = Open
            High_1min = High
            Low_1min = Low
            Close_1min = Close
    else:
        for kline in client.futures_historical_klines(symbol, TIME_INTERVAL, start_str=LENGTH, end_str=time_period):
            Date.append(datetime.utcfromtimestamp((round(kline[0] / 1000))))
            Open.append(float(kline[1]))
            Close.append(float(kline[4]))
            High.append(float(kline[2]))
            Low.append(float(kline[3]))
            Volume.append(float(kline[7]))
        if TIME_INTERVAL != '1m':
            for kline in client.futures_historical_klines(symbol, '1m', start_str=LENGTH, end_str=time_period):
                # print(kline)
                Date_1min.append(datetime.utcfromtimestamp((round(kline[0] / 1000))))
                Open_1min.append(float(kline[1]))
                High_1min.append(float(kline[2]))
                Low_1min.append(float(kline[3]))
                Close_1min.append(float(kline[4]))
        else:
            Date_1min = Date
            Open_1min = Open
            High_1min = High
            Low_1min = Low
            Close_1min = Close

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
                found_flag = 1
                break
        if found_flag:
            break
    for i in range(-1, -len(Date), -1):
        found_flag = 0
        for j in range(-1, -len(Date_1min), -1):
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
                found_flag = 1
                break
        if found_flag:
            break


    if save_data:
        price_data = {'Date': Date, 'Open': Open, 'Close': Close, 'High': High, 'Low': Low,
                      'Volume': Volume, 'High_1min': High_1min, 'Low_1min': Low_1min, 'Close_1min': Close_1min,
                      'Open_1min': Open_1min, 'Date_1min': Date_1min}
        try:
            print("Saving Price data")
            if test_set:
                dump(price_data,f"{path}\\price_data\\{symbol}_{TIME_INTERVAL}_{time_period}_test.joblib")  ## address of where you will keep the data,
            else:
                dump(price_data,f"{path}\\price_data\\{symbol}_{TIME_INTERVAL}_{time_period}.joblib")  ## address of where you will keep the data,
        except:
            print("Failed to save data")

    return Date,Open,Close,High,Low,Volume,High_1min,Low_1min,Close_1min,Open_1min,Date_1min

def get_historical(symbol,start_string,Interval):
    Open = []
    High = []
    Low = []
    Close = []
    Volume = []
    Date = []
    try:
        for kline in client.futures_historical_klines(symbol, Interval,start_str=start_string):
            Date.append(datetime.utcfromtimestamp(round(kline[0]/1000)))
            Open.append(float(kline[1]))
            Close.append(float(kline[4]))
            High.append(float(kline[2]))
            Low.append(float(kline[3]))
            Volume.append(float(kline[7]))
    except BinanceAPIException as e:
        print(e)
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

    return Date_1min,High_1min,Low_1min,Close_1min,Open_1min,Date,Open,Close,High,Low,Volume#,locations_to_pop

def get_CAGR(time_period_units,time_period):
    time_CAGR = -99
    if time_period_units == 'day':
        time_CAGR = time_period / 365
    elif time_period_units == 'week':
        time_CAGR = time_period / 52
    elif time_period_units == 'month':
        time_CAGR = time_period/ 12
    elif time_period_units == 'year':
        time_CAGR = time_period

    return time_CAGR

def align_Datasets_easy(Date,Close,Open):
    start_date = [Date[0][0],0]
    end_date = [Date[0][-1],0]
    for i in range(len(Date)):
        if Date[i][0] < start_date[0]:
            start_date = [Date[i][0],i] ##Date,index of start date
        if Date[i][-1] > end_date[0]:
            end_date = [Date[i][-1],i] ##Date, index of end date
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
            Close[i].insert(0, Close[i][0])
            Open[i].insert(0,Open[i][0])
        for j in range(len_behind):
            Date[i].append("Data Set Ended")
            Close[i].append(Close[i][-1])
            Open[i].append(Open[i][-1])

    return Date,Close,Open

def get_heikin_ashi(Open, Close, High, Low):
    Open_heikin = []
    Close_heikin = []
    High_heikin = []
    Low_heikin = []
    for i in range(len(Close)):
        Open_heikin.append([])
        Close_heikin.append([])
        High_heikin.append([])
        Low_heikin.append([])
        for j in range(len(Close[i])):
            Close_heikin[i].append((Open[i][j] + Close[i][j] + Low[i][j] + High[i][j]) / 4)
            if j==0:
                Open_heikin[i].append((Close_heikin[i][j]+Open[i][j])/2)
                High_heikin[i].append(High[i][j])
                Low_heikin[i].append(Low[i][j])
            else:
                Open_heikin[i].append((Open_heikin[i][j-1]+Close_heikin[i][j-1])/2)
                High_heikin[i].append(max(High[i][j],Open_heikin[i][j],Close_heikin[i][j]))
                Low_heikin[i].append(min(Low[i][j],Open_heikin[i][j],Close_heikin[i][j]))
    return Open_heikin, Close_heikin, High_heikin, Low_heikin


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
        Coin_precision = 4
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
        Coin_precision = 3
        Order_precision = 1

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
        Coin_precision = 4
        Order_precision = 0

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
