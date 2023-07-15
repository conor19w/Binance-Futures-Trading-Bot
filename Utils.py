
from datetime import datetime, timedelta
import numpy as np
from scipy.stats import linregress

def get_trend_direction(close_prices, window=5, outlier_threshold=2.5):
    # Apply moving average smoothing to reduce short-term fluctuations
    smoothed_prices = np.convolve(close_prices, np.ones(window) / window, mode='valid')
    
    # Calculate the linear regression line using robust regression (RANSAC)
    _, _, r_value, _, _ = linregress(range(len(smoothed_prices)), smoothed_prices)
    
    # Adjust the outlier threshold based on the data variability
    outlier_threshold *= np.std(smoothed_prices)
    
    # Check the slope of the regression line to determine the trend direction
    if r_value > outlier_threshold:
        return 'up'
    elif r_value < -outlier_threshold:
        return 'down'
    else:
        return 'sideways'

def round_up_to_nearest_interval(date, interval_minutes):
    hours = date.hour
    minutes = date.minute

    if interval_minutes == 5:
        remainder = minutes % 5
        minutes -= remainder
    elif interval_minutes == 30:
        remainder = minutes % 30
        minutes -= remainder
    elif interval_minutes == 60:
        minutes = 0
    elif interval_minutes == 240:
        hours -= hours % 4
        minutes = 0
    elif interval_minutes == 1440:
        hours = 0
        minutes = 0

    rounded_date = date.replace(
        hour=hours, minute=minutes, second=0, microsecond=0)
    return rounded_date


def construct_higher_timeframe_candles(Date, Close, Volume, Open, High, Low, timeframe_minutes):
    higher_timeframe_Date = []
    higher_timeframe_Close = []
    higher_timeframe_Volume = []
    higher_timeframe_Open = []
    higher_timeframe_High = []
    higher_timeframe_Low = []

    timeframe_delta = timedelta(minutes=timeframe_minutes)
    candle_timeframe_start = round_up_to_nearest_interval(
        Date[0], timeframe_minutes)
    candle_timeframe_end = candle_timeframe_start + timeframe_delta
    current_candle = [
        candle_timeframe_start,
        candle_timeframe_end,
        Open[0],
        High[0],
        Low[0],
        Close[0],
        Volume[0]
    ]

    for i in range(len(Date)):
        candle_timestamp = Date[i]
        temp_time = round_up_to_nearest_interval(
            candle_timestamp, timeframe_minutes)
        if temp_time != candle_timeframe_start:
            higher_timeframe_Date.append(current_candle[0])
            higher_timeframe_Close.append(current_candle[5])
            higher_timeframe_Volume.append(current_candle[6])
            higher_timeframe_Open.append(current_candle[2])
            higher_timeframe_High.append(current_candle[3])
            higher_timeframe_Low.append(current_candle[4])

            candle_timeframe_start = temp_time
            # candle_timestamp.replace(minute=0, second=0, microsecond=0)
            candle_timeframe_end = candle_timeframe_start + timeframe_delta
            current_candle = [
                candle_timeframe_start,
                candle_timeframe_end,
                Open[i],
                High[i],
                Low[i],
                Close[i],
                Volume[i]
            ]
            continue

        current_candle[3] = max(current_candle[3], High[i])
        current_candle[4] = min(current_candle[4], Low[i])
        current_candle[5] = Close[i]
        current_candle[6] += Volume[i]

    if current_candle is not None:
        higher_timeframe_Date.append(current_candle[0])
        higher_timeframe_Close.append(current_candle[5])
        higher_timeframe_Volume.append(current_candle[6])
        higher_timeframe_Open.append(current_candle[2])
        higher_timeframe_High.append(current_candle[3])
        higher_timeframe_Low.append(current_candle[4])

    return (
        higher_timeframe_Date,
        higher_timeframe_Close,
        higher_timeframe_Volume,
        higher_timeframe_Open,
        higher_timeframe_High,
        higher_timeframe_Low
    )

def update_higher_timeframe_candles(cur_price_data, Date, Close, Volume, Open, High, Low):
    price_data = cur_price_data
    if price_data == None:
      price_data = {'High_1m': [], 'Low_1m': [], 'Close_1m': [],
                  'Open_1m': [], 'Date_1m': [], 'Volume_1m': [],
                  'High_3m': [], 'Low_3m': [], 'Close_3m': [],
                  'Open_3m': [], 'Date_3m': [], 'Volume_3m': [],
                  'High_5m': [], 'Low_5m': [], 'Close_5m': [],
                  'Open_5m': [], 'Date_5m': [], 'Volume_5m': [],
                  'High_15m': [], 'Low_15m': [], 'Close_15m': [],
                  'Open_15m': [], 'Date_15m': [], 'Volume_15m': [],
                  'High_30m': [], 'Low_30m': [], 'Close_30m': [],
                  'Open_30m': [], 'Date_30m': [], 'Volume_30m': [],
                  'High_1h': [], 'Low_1h': [], 'Close_1h': [],
                  'Open_1h': [], 'Date_1h': [], 'Volume_1h': [],
                  'High_2h': [], 'Low_2h': [], 'Close_2h': [],
                  'Open_2h': [], 'Date_2h': [], 'Volume_2h': [],
                  'High_4h': [], 'Low_4h': [], 'Close_4h': [],
                  'Open_4h': [], 'Date_4h': [], 'Volume_4h': [],
                  'High_6h': [], 'Low_6h': [], 'Close_6h': [],
                  'Open_6h': [], 'Date_6h': [], 'Volume_6h': [],
                  'High_8h': [], 'Low_8h': [], 'Close_8h': [],
                  'Open_8h': [], 'Date_8h': [], 'Volume_8h': [],
                  'High_12h': [], 'Low_12h': [], 'Close_12h': [],
                  'Open_12h': [], 'Date_12h': [], 'Volume_12h': [],
                  'High_1d': [], 'Low_1d': [], 'Close_1d': [],
                  'Open_1d': [], 'Date_1d': [], 'Volume_1d': []}

    for i in range(len(Date)):
        #:return: list of OHLCV values (Open time, Open, High, Low, Close, Volume, Close time, Quote asset volume, Number of trades, Taker buy base asset volume, Taker buy quote asset volume, Ignore)
        candle_open = Date[i]
        candle_close = candle_open + timedelta(minutes=1) # datetime.utcfromtimestamp((round(Date[i] / 1000))) # Date[i]

        price_data['Open_1m'].append(float(Open[i]))
        price_data['High_1m'].append(float(High[i]))
        price_data['Low_1m'].append(float(Low[i]))
        price_data['Close_1m'].append(float(Close[i]))
        price_data['Volume_1m'].append(round(float(Volume[i])))
        price_data['Date_1m'].append(candle_open)

        for unit in [3, 5, 15, 30]:
            try:
                
                ## Construct the 3m, 5m, 15m, and 30m candles
                if int(str(candle_open)[-5:-3]) % unit == 0:
                    ##Candle open
                    price_data[f'Date_{unit}m'].append(candle_open)
                    price_data[f'Open_{unit}m'].append(price_data['Open_1m'][-1])
                    price_data[f'High_{unit}m'].append(price_data['High_1m'][-1])  ##initialize as highest
                    price_data[f'Low_{unit}m'].append(price_data['Low_1m'][-1])  ##initialize as lowest
                    price_data[f'Volume_{unit}m'].append(price_data['Volume_1m'][-1])  ##initialize
                if int(str(candle_close)[-5:-3]) % unit == 0:
                    ##Candle close time
                    price_data[f'Close_{unit}m'].append(price_data['Close_1m'][-1])
                    ##Check if higher high or lower low present:
                    if price_data['High_1m'][-1] > price_data[f'High_{unit}m'][-1]:
                        price_data[f'High_{unit}m'][-1] = price_data['High_1m'][-1]  ##update as highest
                    if price_data['Low_1m'][-1] < price_data[f'Low_{unit}m'][-1]:
                        price_data[f'Low_{unit}m'][-1] = price_data['Low_1m'][-1]  ##update as lowest
                    price_data[f'Volume_{unit}m'][-1] += price_data['Volume_1m'][-1]  ## add on volume
                    price_data[f'Volume_{unit}m'][-1] = round(price_data[f'Volume_{unit}m'][-1])
                elif not int(str(candle_open)[-5:-3]) % unit == 0 and not int(str(candle_close)[-5:-3]) % unit == 0:
                    ## Check for higher and lower candle inbetween:
                    if price_data['High_1m'][-1] > price_data[f'High_{unit}m'][-1]:
                        price_data[f'High_{unit}m'][-1] = price_data['High_1m'][-1]  ##update as highest
                    if price_data['Low_1m'][-1] < price_data[f'Low_{unit}m'][-1]:
                        price_data[f'Low_{unit}m'][-1] = price_data['Low_1m'][-1]  ##update as lowest
                    price_data[f'Volume_{unit}m'][-1] += price_data['Volume_1m'][-1]  ## add on volume

                if len(price_data[f'Close_{unit}m']) < len(price_data[f'Date_{unit}m']):
                    price_data[f'Close_{unit}m'].append(price_data['Close_1m'][-1])
                else:
                    price_data[f'Close_{unit}m'][-1] = price_data['Close_1m'][-1]

            except Exception as e:
                print(f"Error in {unit}m candles should be fine just for debugging purposes, {e}")
        for unit in [1, 2, 4, 6, 8, 12]:
            try:
                ## Construct the 1h, 2h, 4h, 6h, 8h and 12h candles
                if int(str(candle_open)[-8:-6]) % unit == 0 and int(str(candle_open)[-5:-3]) == 0:
                    ##Candle open
                    price_data[f'Date_{unit}h'].append(candle_open)
                    price_data[f'Open_{unit}h'].append(price_data['Open_1m'][-1])
                    price_data[f'High_{unit}h'].append(price_data['High_1m'][-1])  ##initialize as highest
                    price_data[f'Low_{unit}h'].append(price_data['Low_1m'][-1])  ##initialize as lowest
                    price_data[f'Volume_{unit}h'].append(price_data['Volume_1m'][-1])  ##initialize
                if int(str(candle_close)[-8:-6]) % unit == 0 and int(str(candle_close)[-5:-3]) == 0:
                    ##Candle close time
                    price_data[f'Close_{unit}h'].append(price_data['Close_1m'][-1])
                    ##Check if higher high or lower low present:
                    if price_data['High_1m'][-1] > price_data[f'High_{unit}h'][-1]:
                        price_data[f'High_{unit}h'][-1] = price_data['High_1m'][-1]  ##update as highest
                    if price_data['Low_1m'][-1] < price_data[f'Low_{unit}h'][-1]:
                        price_data[f'Low_{unit}h'][-1] = price_data['Low_1m'][-1]  ##update as lowest
                    price_data[f'Volume_{unit}h'][-1] += price_data['Volume_1m'][-1]  ## add on volume
                    price_data[f'Volume_{unit}h'][-1] = round(price_data[f'Volume_{unit}h'][-1])
                elif not (int(str(candle_open)[-8:-6]) % unit == 0 and int(str(candle_open)[-5:-3]) == 0) and \
                        not (int(str(candle_close)[-8:-6]) % unit == 0 and int(str(candle_close)[-5:-3]) == 0):
                    ## Check for higher and lower candle inbetween:
                    if price_data['High_1m'][-1] > price_data[f'High_{unit}h'][-1]:
                        price_data[f'High_{unit}h'][-1] = price_data['High_1m'][-1]  ##update as highest
                    if price_data['Low_1m'][-1] < price_data[f'Low_{unit}h'][-1]:
                        price_data[f'Low_{unit}h'][-1] = price_data['Low_1m'][-1]  ##update as lowest
                    price_data[f'Volume_{unit}h'][-1] += price_data['Volume_1m'][-1]  ## add on volume

                if len(price_data[f'Close_{unit}h']) < len(price_data[f'Date_{unit}h']):
                    price_data[f'Close_{unit}h'].append(price_data['Close_1m'][-1])
                else:
                    price_data[f'Close_{unit}h'][-1] = price_data['Close_1m'][-1]
            except Exception as e:
                print(f"Error in {unit}h candles should be fine just for debugging purposes, {e}")
    ## Clean up the extra candles
    for unit in [3, 5, 15, 30]:
        price_data[f'Open_{unit}m'].pop(-1)  ## remove the last candle
        price_data[f'High_{unit}m'].pop(-1)  ## remove the last candle
        price_data[f'Low_{unit}m'].pop(-1)  ## remove the last candle
        price_data[f'Date_{unit}m'].pop(-1)  ## remove the last candle
        price_data[f'Volume_{unit}m'].pop(-1)  ## remove the last candle
        if len(price_data[f'Date_{unit}m']) < len(price_data[f'Close_{unit}m']):
            price_data[f'Close_{unit}m'].pop(-1)  ## remove the last candle

    for unit in [1, 2, 4, 6, 8, 12]:
        price_data[f'Open_{unit}h'].pop(-1)  ## remove the last candle
        price_data[f'High_{unit}h'].pop(-1)  ## remove the last candle
        price_data[f'Low_{unit}h'].pop(-1)  ## remove the last candle
        price_data[f'Date_{unit}h'].pop(-1)  ## remove the last candle
        price_data[f'Volume_{unit}h'].pop(-1)  ## remove the last candle
        if len(price_data[f'Date_{unit}h']) < len(price_data[f'Close_{unit}h']):
            price_data[f'Close_{unit}h'].pop(-1)  ## remove the last candle


    # try:
    #     for kline in client.futures_historical_klines(symbol, '1d', start_str=start_date, end_str=end_date):
    #         price_data['Date_1d'].append(datetime.utcfromtimestamp((round(kline[0] / 1000))))
    #         price_data['Open_1d'].append(float(kline[1]))
    #         price_data['High_1d'].append(float(kline[2]))
    #         price_data['Low_1d'].append(float(kline[3]))
    #         price_data['Close_1d'].append(float(kline[4]))
    # except Exception as e:
    #     print("Error downloading daily candles:",e)
    return price_data

def get_date_index(Date, DateList):
    low = 0
    high = len(DateList) - 1

    while low <= high:
        mid = (low + high) // 2
        if DateList[mid] == Date:
            return mid
        elif DateList[mid] > Date:
            if mid > 0 and DateList[mid - 1] <= Date:
                return mid - 1
            high = mid - 1
        else:
            low = mid + 1

    return -1

def get_date_index0(Date, DateList):
    for i in range(len(DateList)):
        if DateList[i] > Date:
            return i-1
        if DateList[i] == Date:
            return i
    return -1

def calculate_momentum(prices, period=5):
    if len(prices) < period:
        return None
    
    momentum = ((prices[-1] - prices[-period]) / prices[-period]) * 100
    return momentum
