from binance.client import Client
from binance.exceptions import BinanceAPIException
from binance.enums import *
from datetime import datetime
from Config_File import API_KEY, API_SECRET
from joblib import load, dump
import sys, os
from tabulate import tabulate

client = Client(api_key=API_KEY,
                api_secret=API_SECRET)  ##Binance keys needed to get historical data/ Trade on an account

desktop_path = f"C:\\Users\\conor\\Desktop"


class Data_Handler:
    def __init__(self, symbol, index):
        self.symbol = symbol
        self.index = index
        self.new_data = False
        self.socket_failed = False
        self.next_candle = {'Date': '', 'Close': 0.0, 'Open': 0.0, 'High': 0.0, 'Low': 0.0, 'Volume': 0.0}

    def handle_socket_message(self, msg):
        # print(msg['k']['x'])
        try:
            if msg != '':
                payload = msg['k']
                if payload['x']:
                    self.next_candle['Date'] = datetime.utcfromtimestamp(round(payload['T'] / 1000))
                    self.next_candle['Close'] = float(payload['c'])
                    self.next_candle['Volume'] = float(payload['q'])
                    self.next_candle['High'] = float(payload['h'])
                    self.next_candle['Low'] = float(payload['l'])
                    self.next_candle['Open'] = float(payload['o'])
                    # print(self.symbol_data)
                    self.new_data = True
        except Exception as e:
            print(f"Error in handling of websocket, Error: {e}")
            self.socket_failed = True


class Trade_Stats:
    def __init__(self):
        self.total_number_of_trades = 0
        self.wins = 0
        self.losses = 0


class Trade:
    def __init__(self, index, position_size, tp_val, stop_loss_val, trade_direction, order_id_temp, symbol):
        self.index = index
        self.symbol = symbol
        self.entry_price = -99
        self.position_size = position_size
        self.TP_val = tp_val
        self.SL_val = stop_loss_val
        self.trade_direction = trade_direction
        self.order_id = order_id_temp
        self.TP_id = ''
        self.SL_id = ''
        self.trade_status = 0  ## hasn't started
        self.trade_start = ''
        self.Highest_val = -999999
        self.Lowest_val = 999999
        self.trail_activated = False
    def print_vals(self):
        return self.symbol, self.entry_price, self.position_size, self.TP_val, self.SL_val, self.trade_direction, self.trade_status, self.Highest_val, self.Lowest_val


class Trade_Manager:
    def __init__(self, client: Client, use_trailing_stop, trailing_stop_callback):
        self.client = client
        self.use_trailing_stop = use_trailing_stop
        self.trailing_stop_callback = trailing_stop_callback

    def open_trade(self, symbol, side, order_qty, OP):
        orderID = ''
        try:
            try:

                if OP == 0:
                    order_qty = round(order_qty)
                else:
                    order_qty = round(order_qty, OP)

                ##Could Make limit orders but for now the entry is a market
                if side == 0:
                    order = self.client.futures_create_order(
                        symbol=symbol,
                        side=SIDE_SELL,
                        type=FUTURE_ORDER_TYPE_MARKET,
                        quantity=order_qty)
                    orderID = order['orderId']
                if side == 1:
                    order = self.client.futures_create_order(
                        symbol=symbol,
                        side=SIDE_BUY,
                        type=FUTURE_ORDER_TYPE_MARKET,
                        quantity=order_qty)
                    orderID = order['orderId']
            except BinanceAPIException as e:
                print("Error in open_trade(), Error: ", e)

        except Exception as e:
            print(e)
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)

        return orderID, order_qty

    def place_TP(self, symbol, TP, side, CP, tick_size):
        TP_ID = ''
        try:
            try:

                TP_val = 0
                order = ''
                order_side = ''
                if CP == 0:
                    TP_val = round(TP[0])
                else:
                    TP_val = round(round(TP[0] / tick_size) * tick_size, CP)
                if side == 1:
                    order_side = SIDE_SELL
                elif side == 0:
                    order_side = SIDE_BUY
                if not self.use_trailing_stop:
                    order = self.client.futures_create_order(
                        symbol=symbol,
                        side=order_side,
                        type=FUTURE_ORDER_TYPE_LIMIT,
                        price=TP_val,
                        timeInForce=TIME_IN_FORCE_GTC,
                        reduceOnly='true',
                        quantity=TP[1])
                else:
                    order = self.client.futures_create_order(
                        symbol=symbol,
                        side=order_side,
                        type='TRAILING_STOP_MARKET',
                        ActivationPrice=TP_val,
                        callbackRate=self.trailing_stop_callback,
                        quantity=TP[1])
                TP_ID = order['orderId']

            except BinanceAPIException as e:
                print("\nError in place_TP(), Error: ", e)
                print(f"symbol: {symbol} TP: {TP}\n")
        except Exception as e:
            print(e)
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)

        return TP_ID

    def place_SL(self, symbol, SL, side, CP, tick_size):
        order_ID = ''
        try:
            try:
                if CP == 0:
                    SL = round(SL)
                else:
                    SL = round(round(SL / tick_size) * tick_size, CP)

                if side == 1:
                    order = self.client.futures_create_order(
                        symbol=symbol,
                        side=SIDE_SELL,
                        type=FUTURE_ORDER_TYPE_STOP_MARKET,
                        stopPrice=SL,
                        closePosition='true')
                    order_ID = order['orderId']
                else:
                    order = self.client.futures_create_order(
                        symbol=symbol,
                        side=SIDE_BUY,
                        type=FUTURE_ORDER_TYPE_STOP_MARKET,
                        stopPrice=SL,
                        closePosition='true')
                    order_ID = order['orderId']



            except BinanceAPIException as e:
                print("Error in place_SL(), Error: ", e)
                print(f"symbol: {symbol} SL: {SL}\n")
                return -1

        except Exception as e:
            print(e)
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)

        return order_ID

    def close_position(self, symbol, trade_direction, total_position_size):
        try:
            try:
                self.client.futures_cancel_all_open_orders(symbol=symbol)  ##cancel orders for this symbol
                if trade_direction == 0:
                    order = self.client.futures_create_order(
                        symbol=symbol,
                        side=SIDE_BUY,
                        type=FUTURE_ORDER_TYPE_MARKET,
                        quantity=total_position_size)
                if trade_direction == 1:
                    order = self.client.futures_create_order(
                        symbol=symbol,
                        side=SIDE_SELL,
                        type=FUTURE_ORDER_TYPE_MARKET,
                        quantity=total_position_size)

            except BinanceAPIException as e:
                print(f"{symbol}: Error in close_position(), Error: ", e)
        except Exception as e:
            print(e)
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)


def get_TIME_INTERVAL(TIME_INTERVAL):
    ##Convert String to minutes
    if TIME_INTERVAL[1] == 'm':
        TIME_INTERVAL = int(TIME_INTERVAL[0])
    elif TIME_INTERVAL[1] == 'h':
        TIME_INTERVAL = int(TIME_INTERVAL[0]) * 60
    elif TIME_INTERVAL[1] == 'd':
        TIME_INTERVAL = int(TIME_INTERVAL[0]) * 1440
    elif TIME_INTERVAL[1] == 'w':
        TIME_INTERVAL = int(TIME_INTERVAL[0]) * 1440 * 7
    elif TIME_INTERVAL[1] == 'M':
        TIME_INTERVAL = int(TIME_INTERVAL[0]) * 1440 * 7 * 4
    elif TIME_INTERVAL[2] == 'm':
        TIME_INTERVAL = int(TIME_INTERVAL[0]) * 10 + int(TIME_INTERVAL[1])
    elif TIME_INTERVAL[2] == 'h':
        TIME_INTERVAL = int(TIME_INTERVAL[0]) * 10 * 60 + int(TIME_INTERVAL[1]) * 60
    return TIME_INTERVAL


def get_Klines(TIME_INTERVAL, symbol, start_str, end_str, path):
    ##Manipulate dates to american format:
    start_date = f'{start_str[3:5]}-{start_str[0:2]}-{start_str[6:]}'
    end_date = f'{end_str[3:5]}-{end_str[0:2]}-{end_str[6:]}'
    # start_date = start_str
    # end_date = end_str

    print(f"Downloading CandleStick Data for {symbol}...")

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
    for kline in client.futures_historical_klines(symbol, TIME_INTERVAL, start_str=start_date, end_str=end_date):
        Date.append(datetime.utcfromtimestamp((round(kline[0] / 1000))))
        Open.append(float(kline[1]))
        Close.append(float(kline[4]))
        High.append(float(kline[2]))
        Low.append(float(kline[3]))
        Volume.append(float(kline[7]))

    if TIME_INTERVAL != '1m':
        for kline in client.futures_historical_klines(symbol, '1m', start_str=start_date, end_str=end_date):
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

    price_data = {'Date': Date, 'Open': Open, 'Close': Close, 'High': High, 'Low': Low,
                  'Volume': Volume, 'High_1min': High_1min, 'Low_1min': Low_1min, 'Close_1min': Close_1min,
                  'Open_1min': Open_1min, 'Date_1min': Date_1min}
    try:
        print("Saving Price data")
        dump(price_data, path)  ## address of where you will keep the data,
    except:
        print("Failed to save data")

    return Date, Open, Close, High, Low, Volume, High_1min, Low_1min, Close_1min, Open_1min, Date_1min


def get_historical(symbol, start_string, Interval):
    Open = []
    High = []
    Low = []
    Close = []
    Volume = []
    Date = []
    try:
        for kline in client.futures_historical_klines(symbol, Interval, start_str=start_string):
            Date.append(datetime.utcfromtimestamp(round(kline[6] / 1000)))
            Open.append(float(kline[1]))
            Close.append(float(kline[4]))
            High.append(float(kline[2]))
            Low.append(float(kline[3]))
            Volume.append(float(kline[7]))
    except BinanceAPIException as e:
        print(e)
    return Date, Open, Close, High, Low, Volume


def align_Datasets(Date_1min, High_1min, Low_1min, Close_1min, Open_1min, Date, Open, Close, High, Low, Volume):
    start_date = [Date[0][0], 0]  ##get 1st date of first coin
    end_date = [Date[0][-1], 0]  ##get last date of first coin
    for i in range(len(Date)):
        if Date[i][0] < start_date[0]:  ##Check if any other coin has an earlier date to find the earliest date
            start_date = [Date[i][0], i]  ##Date,index of start date
        if Date[i][-1] > end_date[0]:  ##Check if any other coin has a later date to find the latest date
            end_date = [Date[i][-1], i]  ##Date, index of end date
    for i in range(len(Date_1min)):
        len_infront = 0  ##count how many dates we move along until we find the date at the current index's start, used to repeat the data until size is the same
        len_behind = 0  ##count how many dates we move along until we find the date at the current index's end, used to repeat the data until size is the same
        for j in range(len(Date_1min[start_date[1]])):
            if Date_1min[start_date[1]][j] != Date_1min[i][0]:
                len_infront += 1
            else:
                break
        for j in range(len(Date_1min[end_date[1]]) - 1, -1, -1):
            if Date_1min[end_date[1]][j] != Date_1min[i][-1]:
                len_behind += 1
            else:
                break
        for j in range(len_infront):
            Date_1min[i].insert(0, "Data Set hasn't started yet")
            High_1min[i].insert(0, High_1min[i][0])
            Low_1min[i].insert(0, Low_1min[i][0])
            Close_1min[i].insert(0, Close_1min[i][0])
            Open_1min[i].insert(0, Open_1min[i][0])
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
            Volume[i].insert(0, Volume[i][0])
        for j in range(len_behind):
            Date[i].append("Data Set Ended")
            High[i].append(High[i][-1])
            Low[i].append(Low[i][-1])
            Close[i].append(Close[i][-1])
            Open[i].append(Open[i][-1])
            Volume[i].insert(0, Volume[i][-1])

    return Date_1min, High_1min, Low_1min, Close_1min, Open_1min, Date, Open, Close, High, Low, Volume


def get_CAGR(start, end):
    return (int(end[0:2]) - int(start[0:2]) + 30 * (int(end[3:5]) - int(start[3:5])) + 365 * (
            int(end[6:]) - int(start[6:]))) / 365


def align_Datasets_easy(Date, Close, Open):
    start_date = [Date[0][0], 0]
    end_date = [Date[0][-1], 0]
    for i in range(len(Date)):
        if Date[i][0] < start_date[0]:
            start_date = [Date[i][0], i]  ##Date,index of start date
        if Date[i][-1] > end_date[0]:
            end_date = [Date[i][-1], i]  ##Date, index of end date
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
            Open[i].insert(0, Open[i][0])
        for j in range(len_behind):
            Date[i].append("Data Set Ended")
            Close[i].append(Close[i][-1])
            Open[i].append(Open[i][-1])

    return Date, Close, Open


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
            if j == 0:
                Open_heikin[i].append((Close_heikin[i][j] + Open[i][j]) / 2)
                High_heikin[i].append(High[i][j])
                Low_heikin[i].append(Low[i][j])
            else:
                Open_heikin[i].append((Open_heikin[i][j - 1] + Close_heikin[i][j - 1]) / 2)
                High_heikin[i].append(max(High[i][j], Open_heikin[i][j], Close_heikin[i][j]))
                Low_heikin[i].append(min(Low[i][j], Open_heikin[i][j], Close_heikin[i][j]))
    return Open_heikin, Close_heikin, High_heikin, Low_heikin


def get_aligned_candles(Date_1min, High_1min, Low_1min, Close_1min, Open_1min, Date, Open, Close, High, Low, Volume,
                        symbol, TIME_INTERVAL, start, end):
    print("Loading Price Data")
    i = 0
    while i < len(symbol):
        path = f"{desktop_path}\\price_data\\{symbol[i]}_{TIME_INTERVAL}_{start}_{end}.joblib"
        try:
            price_data = load(path)
            Date.append(price_data['Date'])
            Open.append(price_data['Open'])
            Close.append(price_data['Close'])
            High.append(price_data['High'])
            Low.append(price_data['Low'])
            Volume.append(price_data['Volume'])
            High_1min.append(price_data['High_1min'])
            Low_1min.append(price_data['Low_1min'])
            Close_1min.append(price_data['Close_1min'])
            Open_1min.append(price_data['Open_1min'])
            Date_1min.append(price_data['Date_1min'])
            i += 1
        except:
            try:
                print(f"Data doesnt exist in path: {path}, Downloading Data to specified path now...")
                get_Klines(TIME_INTERVAL, symbol[i], start, end, path)
                price_data = load(path)
                Date.append(price_data['Date'])
                Open.append(price_data['Open'])
                Close.append(price_data['Close'])
                High.append(price_data['High'])
                Low.append(price_data['Low'])
                Volume.append(price_data['Volume'])
                High_1min.append(price_data['High_1min'])
                Low_1min.append(price_data['Low_1min'])
                Close_1min.append(price_data['Close_1min'])
                Open_1min.append(price_data['Open_1min'])
                Date_1min.append(price_data['Date_1min'])
                print("Download Successful, Loading Data now")
                i += 1
            except BinanceAPIException as e:
                if str(e) == 'APIError(code=-1121): Invalid symbol.':
                    print(f"Invalid Symbol: {symbol[i]}, removing from data set")
                    symbol.pop(i)
                else:
                    print(f"Wrong path specified in Helper.py,error: {e}")
                    symbol.pop(i)
                    print("Fix path issue or else turn off load_data")
                    print("Contact me if still stuck @ wconor539@gmail.com")

    i = 0
    while i < len(Close):
        if len(Close[i]) == 0:
            Date.pop(i)
            Open.pop(i)
            Close.pop(i)
            High.pop(i)
            Low.pop(i)
            Volume.pop(i)
            High_1min.pop(i)
            Low_1min.pop(i)
            Close_1min.pop(i)
            Open_1min.pop(i)
            Date_1min.pop(i)
            print(f"Not enough candleStick data for {symbol[i]} removing from dataset...")
            symbol.pop(i)
            i -= 1
        i += 1
    print("Aligning Data Sets... This may take a few minutes")

    Date_1min, High_1min, Low_1min, Close_1min, Open_1min, Date, Open, Close, High, Low, Volume = \
        align_Datasets(Date_1min, High_1min, Low_1min, Close_1min, Open_1min, Date, Open, Close, High, Low, Volume)
    return Date_1min, High_1min, Low_1min, Close_1min, Open_1min, Date, Open, Close, High, Low, Volume, symbol


def check_TP(t: Trade, account_balance, High, Low, fee, use_trailing_stop, trailing_stop_callback, CP, printing_on=1):
    if not use_trailing_stop:
        if t.TP_val < High and t.trade_direction == 1:
            if printing_on:
                print(f"Take Profit hit on {t.symbol}")
            account_balance += ((t.TP_val - t.entry_price) * t.position_size - t.TP_val * fee * t.position_size)  ## fee + profit
            t.trade_status = 2

        elif t.TP_val > Low and t.trade_direction == 0:
            if printing_on:
                print(f"Take Profit hit on {t.symbol}")
            account_balance += ((t.entry_price - t.TP_val) * t.position_size - t.TP_val * fee * t.position_size)  ## fee + profit
            t.trade_status = 2
    else:
        if t.trail_activated and t.trade_direction == 0 and High > t.TP_val:
            if printing_on:
                print(f"Trailing Stop hit on {t.symbol}")
            account_balance += ((t.entry_price - t.TP_val) * t.position_size - t.TP_val * fee * t.position_size)  ## fee + profit
            t.trade_status = 2
        elif t.trail_activated and t.trade_direction == 1 and Low < t.TP_val:
            if printing_on:
                print(f"Trailing Stop hit on {t.symbol}")
            account_balance += ((t.TP_val - t.entry_price) * t.position_size - t.TP_val * fee * t.position_size)  ## fee + profit
            t.trade_status = 2
        elif not t.trail_activated and t.trade_direction == 0 and Low < t.TP_val:
            t.trail_activated = True
            if CP == 0:
                t.TP_val = round(Low * (1+trailing_stop_callback))
            else:
                t.TP_val = round(Low * (1 + trailing_stop_callback),CP)
            if printing_on:
                print(f"Trailing Stop updated on {t.symbol} to {t.TP_val}")
        elif not t.trail_activated and t.trade_direction == 1 and High > t.TP_val:
            t.trail_activated = True
            if CP == 0:
                t.TP_val = round(High * (1 - trailing_stop_callback))
            else:
                t.TP_val = round(High * (1 - trailing_stop_callback), CP)
            if printing_on:
                print(f"Trailing Stop updated on {t.symbol} to {t.TP_val}")
        elif t.trail_activated and t.trade_direction == 0 and Low * (1 + trailing_stop_callback) < t.TP_val:
            if CP == 0:
                t.TP_val = round(Low * (1 + trailing_stop_callback))
            else:
                t.TP_val = round(Low * (1 + trailing_stop_callback), CP)
            if printing_on:
                print(f"Trailing Stop updated on {t.symbol} to {t.TP_val}")
        elif t.trail_activated and t.trade_direction == 1 and High * (1 - trailing_stop_callback) > t.TP_val:
            if CP == 0:
                t.TP_val = round(High * (1 - trailing_stop_callback))
            else:
                t.TP_val = round(High * (1 - trailing_stop_callback), CP)
            if printing_on:
                print(f"Trailing Stop updated on {t.symbol} to {t.TP_val}")

    return t, account_balance


def check_SL(t: Trade, account_balance, High, Low, fee, printing_on=1):
    if t.SL_val < High and t.trade_direction == 0:
        if printing_on:
            print(f"Stop Loss hit on {t.symbol}")
        account_balance -= (
                    (t.SL_val - t.entry_price) * t.position_size + t.SL_val * fee * t.position_size)  ## fee + stop loss
        t.trade_status = 3

    elif t.SL_val > Low and t.trade_direction == 1:
        if printing_on:
            print(f"Stop Loss hit on {t.symbol}")
        account_balance -= (
                    (t.entry_price - t.SL_val) * t.position_size + t.SL_val * fee * t.position_size)  ## fee + stop loss
        t.trade_status = 3

    return t, account_balance


def open_trade(symbol, Order_Notional, account_balance, Open, fee, OP, printing_on=1):
    if OP == 0:
        order_qty = round(Order_Notional / Open)
    else:
        order_qty = round(Order_Notional / Open, OP)

    entry_price = Open

    if order_qty > 0:
        account_balance -= Order_Notional * fee
        if printing_on:
            print(f"Trade Opened Successfully on {symbol}")
    return order_qty, entry_price, account_balance


def close_pos(t, account_balance, fee, Close):
    if t.trade_direction == 0:
        account_balance += ((t.entry_price - Close) * t.position_size + Close * fee * t.position_size)  ## fee + stop loss

    elif t.trade_direction == 1:
        account_balance += ((Close - t.entry_price) * t.position_size + Close * fee * t.position_size)  ## fee + stop loss

    return t, account_balance


def print_trades(active_trades: [Trade], trade_price, Date, account_balance, change_occurred, print_to_csv, csv_name):
    ###########################################################################################################
    #####################               PRINT TRADE DETAILS                          ##########################
    ###########################################################################################################

    info = {}
    symbol_info = []
    entry_price_info = []
    position_size_info = []
    TP_vals_info = []
    SL_val_info = []
    trade_direction_info = []
    trade_status_info = []
    trade_highest_info = []
    trade_lowest_info = []
    for k in range(len(active_trades)):
        symbol_info_temp, entry_price_info_temp, position_size_info_temp, TP_vals_info_temp, SL_val_info_temp, \
        trade_direction_info_temp, trade_status_info_temp, trade_highest_temp, trade_lowest_temp = \
            active_trades[k].print_vals()
        symbol_info.append(symbol_info_temp)
        entry_price_info.append(entry_price_info_temp)
        position_size_info.append(position_size_info_temp)
        TP_vals_info.append(TP_vals_info_temp)
        SL_val_info.append(SL_val_info_temp)

        if trade_direction_info_temp == 0:
            trade_direction_info.append('Short')
        elif trade_direction_info_temp == 1:
            trade_direction_info.append('Long')
        elif trade_direction_info_temp == -99:
            trade_direction_info.append('Closed')

        if trade_status_info_temp == 0:
            trade_status_info.append('New position Opened')
        elif trade_status_info_temp == 1:
            trade_status_info.append('In Progress')
        elif trade_status_info_temp == 2:
            trade_status_info.append('Take Profit Hit')
        elif trade_status_info_temp == 3:
            trade_status_info.append('Stop Loss Hit')
        elif trade_status_info_temp == 4:
            trade_status_info.append('Closed on Condition')

        if trade_highest_temp != -999999:
            trade_highest_info.append(trade_highest_temp)
        else:
            trade_highest_info.append('N/A')

        if trade_lowest_temp != 999999:
            trade_lowest_info.append(trade_lowest_temp)
        else:
            trade_lowest_info.append('N/A')

    trade_pnl = []
    for i in range(len(active_trades)):
        if active_trades[i].trade_direction == 0:
            trade_pnl.append((entry_price_info[i] - trade_price[i]) * (position_size_info[i]))
        elif active_trades[i].trade_direction == 1:
            trade_pnl.append((trade_price[i] - entry_price_info[i]) * (position_size_info[i]))
    info['Symbol'] = symbol_info
    info['trade direction'] = trade_direction_info
    info['entry price'] = entry_price_info
    info['current price'] = trade_price
    info['Size'] = position_size_info
    info['Next TP'] = TP_vals_info
    info['SL'] = SL_val_info
    info['PNL'] = trade_pnl
    info['trade status'] = trade_status_info
    info['Highest Candle'] = trade_highest_info
    info['Lowest Candle'] = trade_lowest_info

    if change_occurred and len(account_balance) == 1:
        print(f"\nTime: {Date} , Account Balance: {account_balance[0]}")
        print(tabulate(info, headers='keys', tablefmt='fancy_grid'))
        print(f"Time: {Date} , Account Balance: {account_balance[0]}")
        print("------------------------------------------------------------\n")
        if print_to_csv:
            with open(csv_name, 'a') as O:
                for i in range(len(active_trades)):
                    O.write(
                        f'{Date},{account_balance[0]},{symbol_info[i]},{entry_price_info[i]},{position_size_info[i]},'
                        f'{trade_price[i]},{TP_vals_info[i]},{SL_val_info[i]},{trade_direction_info[i]},{trade_highest_info[i]},{trade_lowest_info[i]},{trade_status_info[i]}\n')
        total_pnl = 0
        for x in trade_pnl:
            total_pnl += x

        if total_pnl + account_balance[0] < 0:
            return total_pnl, 1, False
        else:
            return total_pnl, 0, False
    elif change_occurred and len(account_balance) > 1:
        account_balance_info = []
        for t in active_trades:
            account_balance_info.append(account_balance[t.index])
        info['Account Balance'] = account_balance_info
        print(f"\nTime: {Date}")
        print(tabulate(info, headers='keys', tablefmt='fancy_grid'))
        print(f"Time: {Date}")
        print("------------------------------------------------------------\n")
        if print_to_csv:
            with open(csv_name, 'a') as O:
                for i in range(len(active_trades)):
                    O.write(
                        f'{Date},{account_balance_info[i]},{symbol_info[i]},{entry_price_info[i]},{position_size_info[i]},'
                        f'{trade_price[i]},{TP_vals_info[i]},{SL_val_info[i]},{trade_direction_info[i]},{trade_highest_info[i]},{trade_lowest_info[i]},{trade_status_info[i]}\n')

    return 0, 0, False
