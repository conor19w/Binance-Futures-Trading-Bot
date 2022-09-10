import time
from datetime import datetime

from binance import Client

import Helper
symbol = ['ETHUSDT']
start = '07-09-22'
end = '10-09-22'
client = Client()

## Test the candles I generate are the same as the ones binance feeds us
for TIME_INTERVAL in ['1m', '3m', '5m', '15m', '30m', '1h', '2h', '4h', '6h', '8h', '12h']:
    Date_binance, Open_binance, Close_binance, High_binance, Low_binance, Volume_binance = [], [], [], [], [], []

    _, _, _, _, _, Date_created, Open_created, Close_created, High_created, Low_created, Volume_created, symbol = \
        Helper.get_aligned_candles([], [], [], [], [], [], [], [], [], [], [], symbol, TIME_INTERVAL, start, end)
    print("Done Aligning")
    for kline in client.futures_historical_klines(symbol[0], TIME_INTERVAL, start_str=f'{start[3:5]}-{start[0:2]}-{start[6:]}', end_str=f'{end[3:5]}-{end[0:2]}-{end[6:]}'):
        Open_binance.append(float(kline[1]))
        High_binance.append(float(kline[2]))
        Low_binance.append(float(kline[3]))
        Close_binance.append(float(kline[4]))
        Volume_binance.append(round(float(kline[5])))
        Date_binance.append(datetime.utcfromtimestamp((round(kline[6] / 1000))))

    if not (Date_binance[:len(Date_created[0])] == Date_created[0] and Open_binance[:len(Open_created[0])] == Open_created[0] and Close_binance[:len(Close_created[0])] == Close_created[0] and
            High_binance[:len(High_created[0])] == High_created[0] and Low_binance[:len(Low_created[0])] == Low_created[0]) and TIME_INTERVAL == '1m':
        print(f"Price Data is incorrect for the {TIME_INTERVAL} time frame on some values")
    elif not (Date_binance[:len(Date_created[0])] == Date_created[0] and Open_binance[:len(Open_created[0])] == Open_created[0] and Close_binance[:len(Close_created[0])] == Close_created[0] and
            High_binance[:len(High_created[0])] == High_created[0] and Low_binance[:len(Low_created[0])] == Low_created[0]) and TIME_INTERVAL != '1m':
        print(f"Price Data is incorrect for the {TIME_INTERVAL} time frame on some values")
    else:
        print(f"Price Data is correct for all values on the {TIME_INTERVAL} time frame")
    time.sleep(5)
    if not Volume_binance[:len(Volume_created[0])] == Volume_created[0] and TIME_INTERVAL == '1m':
        print(f"Volume Data is incorrect for the {TIME_INTERVAL} time frame on some values")
    elif not Volume_binance[:len(Volume_created[0])] == Volume_created[0] and TIME_INTERVAL != '1m':
        print(f"Volume Data is incorrect for the {TIME_INTERVAL} time frame on some values due to rounding... see below:")
        time.sleep(5)
        for x, y in zip(Volume_binance[:len(Volume_created[0])], Volume_created[0]):
            print(x, y)
    else:
        print(f"Volume Data is correct for all values on the {TIME_INTERVAL} time frame")
