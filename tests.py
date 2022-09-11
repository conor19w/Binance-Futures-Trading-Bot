import time
from copy import copy
from datetime import datetime

from binance import Client

import Helper
symbol = ['ETHUSDT']
start = '05-09-22'
end = '10-09-22'
client = Client()

'''

Test the candles I generate are the same as the ones binance feeds us

'''
# for TIME_INTERVAL in ['1m', '3m', '5m', '15m', '30m', '1h', '2h', '4h', '6h', '8h', '12h']:
#     Date_binance, Open_binance, Close_binance, High_binance, Low_binance, Volume_binance = [], [], [], [], [], []
#
#     _, _, _, _, _, Date_created, Open_created, Close_created, High_created, Low_created, Volume_created, symbol = \
#         Helper.get_aligned_candles([], [], [], [], [], [], [], [], [], [], [], symbol, TIME_INTERVAL, start, end)
#     print("Done Aligning")
#     for kline in client.futures_historical_klines(symbol[0], TIME_INTERVAL, start_str=f'{start[3:5]}-{start[0:2]}-{start[6:]}', end_str=f'{end[3:5]}-{end[0:2]}-{end[6:]}'):
#         Open_binance.append(float(kline[1]))
#         High_binance.append(float(kline[2]))
#         Low_binance.append(float(kline[3]))
#         Close_binance.append(float(kline[4]))
#         Volume_binance.append(round(float(kline[5])))
#         Date_binance.append(datetime.utcfromtimestamp((round(kline[6] / 1000))))
#
#     if not (Date_binance[:len(Date_created[0])] == Date_created[0] and Open_binance[:len(Open_created[0])] == Open_created[0] and Close_binance[:len(Close_created[0])] == Close_created[0] and
#             High_binance[:len(High_created[0])] == High_created[0] and Low_binance[:len(Low_created[0])] == Low_created[0]) and TIME_INTERVAL == '1m':
#         print(f"Price Data is incorrect for the {TIME_INTERVAL} time frame on some values")
#     elif not (Date_binance[:len(Date_created[0])] == Date_created[0] and Open_binance[:len(Open_created[0])] == Open_created[0] and Close_binance[:len(Close_created[0])] == Close_created[0] and
#             High_binance[:len(High_created[0])] == High_created[0] and Low_binance[:len(Low_created[0])] == Low_created[0]) and TIME_INTERVAL != '1m':
#         print(f"Price Data is incorrect for the {TIME_INTERVAL} time frame on some values")
#     else:
#         print(f"Price Data is correct for all values on the {TIME_INTERVAL} time frame")
#     time.sleep(5)
#     if not Volume_binance[:len(Volume_created[0])] == Volume_created[0] and TIME_INTERVAL == '1m':
#         print(f"Volume Data is incorrect for the {TIME_INTERVAL} time frame on some values")
#     elif not Volume_binance[:len(Volume_created[0])] == Volume_created[0] and TIME_INTERVAL != '1m':
#         print(f"Volume Data is incorrect for the {TIME_INTERVAL} time frame on some values due to rounding... see below:")
#         time.sleep(5)
#         for x, y in zip(Volume_binance[:len(Volume_created[0])], Volume_created[0]):
#             print(x, y)
#     else:
#         print(f"Volume Data is correct for all values on the {TIME_INTERVAL} time frame")


'''

Test alignment of data in backtester is correct

'''
# buffer = 20
# for TIME_INTERVAL in ['1m', '3m', '5m', '15m', '30m', '1h', '2h', '4h', '6h', '8h', '12h']:
#     Date_1min, High_1min, Low_1min, Close_1min, Open_1min, Date, Open, Close, High, Low, Volume, symbol = \
#         Helper.get_aligned_candles([], [], [], [], [], [], [], [], [], [], [], symbol, TIME_INTERVAL, start, end)
#     flag = 0
#     TIME_INTERVAL_prev = copy(TIME_INTERVAL)
#     TIME_INTERVAL = Helper.get_TIME_INTERVAL(TIME_INTERVAL)
#     for i in range((buffer-1)*TIME_INTERVAL, len(Date_1min[0]) - 2):
#         if ((i + 1) % TIME_INTERVAL == 0 or TIME_INTERVAL == 1) and Date_1min[0][i] != Date[0][int(i/TIME_INTERVAL)]:
#             flag = 1
#     if flag == 0:
#         print(f"Aligned candles are correct for the {TIME_INTERVAL_prev} timeframe")
#     else:
#         print(f"Aligned candles are incorrect for the {TIME_INTERVAL_prev} timeframe")
