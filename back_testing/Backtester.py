import os
import pprint
import time
from datetime import timedelta, datetime

from binance.client import Client
import matplotlib.pyplot as plt
from copy import copy
import pandas as pd
import numpy as np

import SharedHelper
from BotClass import Bot
from BacktesterConfig import *
from BacktesterHelper import Trade
import matplotlib

from back_testing import BacktesterHelper

time_delta = timedelta(hours=time_change)  ## Adjust time for printing based off GMT (This is GMT+1)

def run_backtester(starting_account_balance, leverage, order_size, start, end, interval, max_number_of_positions,
                   trade_all_symbols, trade_each_symbol_with_separate_balance, only_show_profitable_coins,
                   percent_gain_threshold, use_minimum_drawdown, minimum_drawdown, symbols_to_trade, use_trailing_stop,
                   trailing_stop_callback, slippage, strategy, TP_SL_choice, SL_mult, TP_mult, use_multiprocessing_for_downloading_data,
                   graph_folder_location, auto_open_graph_images, fee, buffer, trading_on, graph_buys_and_sells,
                   graph_buys_and_sells_window_before, graph_buys_and_sells_window_after, trade_log_name, coin_exclusion_list):
    BacktesterHelper.print_config_to_screen()
    matplotlib.use("Agg")
    trades_for_graphing: [BacktesterHelper.trade_info] = []  ## trades: [symbol, entry_price, TP_price, SL_price, indicators, candles]
    change_occurred = False
    if buffer is None:
        buffer = SharedHelper.get_required_buffer(trading_strategy)
    order_size, slippage, minimum_drawdown, percent_gain_threshold, trailing_stop_callback = BacktesterHelper.convert_settings_to_decimal(order_size, slippage, minimum_drawdown, percent_gain_threshold, trailing_stop_callback, use_trailing_stop)
    path_to_graphs_folder, backtest_path = BacktesterHelper.setup_folders(graph_folder_location, strategy, start, end, interval)

    with open(backtest_path+trade_log_name, 'x') as O:
        O.write('Date,Account Balance,symbol,Entry Price,Position Size,Current Price,TP val,SL val,Trade Direction,Highest Candle,Lowest Candle,Trade Status\n')

    client = Client()
    if trade_all_symbols:
        symbols_to_trade = SharedHelper.get_all_symbols(client, coin_exclusion_list)

    y = client.futures_exchange_info()['symbols']
    symbol_info = [[x['pair'], x['pricePrecision'], x['quantityPrecision'], x['filters'][0]['tickSize']] for x in y]

    print(f"Coins Tradeable : {symbols_to_trade}")
    time_CAGR = BacktesterHelper.get_CAGR(start, end)
    if trade_each_symbol_with_separate_balance:
        max_number_of_positions = len(symbols_to_trade)
    Date_1min, High_1min, Low_1min, Close_1min, Open_1min, Date, Open, Close, High, Low, Volume = BacktesterHelper.get_candles(use_multiprocessing_for_downloading_data, symbols_to_trade, interval, start, end)

    original_time_interval = copy(interval)
    interval = BacktesterHelper.get_TIME_INTERVAL(interval)  ##Convert string to an integer for the rest of the script
    Bots: [Bot]
    Bots, wins_and_losses = BacktesterHelper.setup_bots(symbols_to_trade, symbol_info, Open, Close, High, Low, Volume, Date, strategy, TP_SL_choice, SL_mult, TP_mult)

    # Initialize vars for profit calculation
    tradeNO = 0  ##number of trades
    active_trades, new_trades, account_balance, Daily_return, winning_trades, losing_trades, closed_on_condition, profitgraph = [], [], [], [], [], [], [], []
    for i in range(len(symbols_to_trade)):
        account_balance.append(starting_account_balance)
        profitgraph.append([starting_account_balance])
        Daily_return.append([])
    originalBalance = copy(account_balance)

    print(f"{interval} OHLC Candle Sticks from {start} to {end}")
    print("Account Balance: ", account_balance[0])
    for i in range((buffer - 1) * interval, len(Close_1min[0]) - 1 - interval * 2):
        if account_balance[0] < 0 and not trade_each_symbol_with_separate_balance:
            print("Negative Balance")
            break
        ##give each coin next piece of data
        if (i + 1) % interval == 0 or interval == 1:
            for k in range(len(symbols_to_trade)):
                Bots[k].current_index = int(i / interval)
            if not trading_on and str(Date[0][int(i / interval)]) == start_trading_date:
                trading_on = True
                print("Trading Started")

            for k in range(len(Bots)):
                trade_flag = 0
                for t in active_trades:
                    if t.index == k:
                        trade_flag = 1
                        break
                if trade_flag == 0 and len(Bots[k].Date) > i / interval:
                    temp_dec = Bots[k].Make_decision()
                    if temp_dec[0] != -99:
                        new_trades.append([k, temp_dec])

        if len(active_trades) == max_number_of_positions:
            new_trades = []
            ##Sort out new trades to be opened
        while len(new_trades) > 0 and len(active_trades) < max_number_of_positions and trading_on:
            [index, [trade_direction, stop_loss, take_profit]] = new_trades.pop(0)
            order_qty = 0
            entry_price = 0
            if trade_each_symbol_with_separate_balance:
                Order_Notional = account_balance[index] * leverage * order_size
                order_qty, entry_price, account_balance[index] = BacktesterHelper.open_trade(Bots[index].symbol, Order_Notional,
                                                                        account_balance[index], Open_1min[index][i+1],
                                                                        fee, Bots[index].OP, Bots[index].CP, trade_direction, slippage)
            else:
                Order_Notional = account_balance[0] * leverage * order_size
                order_qty, entry_price, account_balance[0] = BacktesterHelper.open_trade(Bots[index].symbol, Order_Notional,
                                                                               account_balance[0],
                                                                               Open_1min[index][i+1],
                                                                               fee, Bots[index].OP, Bots[index].CP, trade_direction, slippage)

            ## Calculate the prices for TP and SL
            stop_loss_val, take_profit_val = BacktesterHelper.get_tp_and_sl(trade_direction, take_profit, stop_loss, entry_price, Bots[index].CP)
            if order_qty > 0:
                tradeNO += 1
                ## Append new trade, to our trade list
                ## (index, position_size, tp_val, stop_loss_val, trade_direction, order_id_temp, symbol)
                active_trades.append(Trade(index, order_qty, take_profit_val, stop_loss_val, trade_direction, 0, Bots[index].symbol))
                active_trades[-1].entry_price = entry_price
                active_trades[-1].trade_start = Date_1min[index][i]
                active_trades[-1].trade_info.entry_price = entry_price
                active_trades[-1].trade_info.trade_start_index = Bots[index].current_index
                active_trades[-1].trade_info.start_time = Date_1min[index][i+1]
                change_occurred = True
                ##Empty the list of trades
                if len(active_trades) == max_number_of_positions:
                    new_trades = []

        for t in active_trades:
            ## stuff for csv
            if t.trade_status == 1:
                if t.Highest_val < High_1min[t.index][i]:
                    t.Highest_val = High_1min[t.index][i]
                if t.Lowest_val > Low_1min[t.index][i]:
                    t.Lowest_val = Low_1min[t.index][i]
            ## Check SL Hit
            if t.trade_status == 1:
                if trade_each_symbol_with_separate_balance:
                    t, account_balance[t.index] = BacktesterHelper.check_SL(t, account_balance[t.index], High_1min[t.index][i], Low_1min[t.index][i], fee)
                else:
                    t, account_balance[0] = BacktesterHelper.check_SL(t, account_balance[0], High_1min[t.index][i], Low_1min[t.index][i], fee)
                if t.trade_status != 1:
                    change_occurred = True
            ##Check if TP Hit
            if t.trade_status == 1:
                if trade_each_symbol_with_separate_balance:
                    t, account_balance[t.index] = BacktesterHelper.check_TP(t, account_balance[t.index], High_1min[t.index][i], Low_1min[t.index][i], fee, use_trailing_stop, trailing_stop_callback, Bots[t.index].CP)
                else:
                    t, account_balance[0] = BacktesterHelper.check_TP(t, account_balance[0], High_1min[t.index][i], Low_1min[t.index][i], fee, use_trailing_stop, trailing_stop_callback, Bots[t.index].CP)
                if t.trade_status != 1:
                    change_occurred = True
            if Bots[t.index].use_close_pos and t.trade_status == 1 and (i % interval == 0 or interval == 1):
                ## Check each interval if the close position was met
                close_pos = Bots[t.index].check_close_pos(t.trade_direction)
                if close_pos:
                    if trade_each_symbol_with_separate_balance:
                        t, account_balance[t.index] = BacktesterHelper.close_pos(t, account_balance[t.index], fee, Close_1min[t.index][i])
                    else:
                        t, account_balance[0] = BacktesterHelper.close_pos(t, account_balance[0], fee, Close_1min[t.index][i])
                    close_pos = 0
                    print(f"Closing Trade on {t.symbols_to_trade} as Close Position condition was met")
                    t.trade_status = 4  ## Closed on condition
                    change_occurred = True

        ## Check PNL here as well as print the current trades:
        trade_price = []
        for t in active_trades:
            trade_price.append(Bots[t.index].Close[Bots[t.index].current_index])
        if trade_each_symbol_with_separate_balance:
            pnl, negative_balance_flag, change_occurred = BacktesterHelper.print_trades(active_trades, trade_price, Date_1min[0][i],
                                                                              account_balance, change_occurred, trade_log_name, path_to_graphs_folder, backtest_path, time_delta)
        else:
            pnl, negative_balance_flag, change_occurred = BacktesterHelper.print_trades(active_trades, trade_price, Date_1min[0][i],
                                                                              [account_balance[0]], change_occurred, trade_log_name, path_to_graphs_folder, backtest_path, time_delta)
        if negative_balance_flag and not trade_each_symbol_with_separate_balance:
            print("**************** You have been liquidated *******************")
            profitgraph[0].append(0)
            account_balance[0] = 0
            break  ## break out of loop as we've been liquidated

        k = 0
        while k < len(active_trades):
            if active_trades[k].trade_status == 2:
                ## Win
                winning_trades.append([active_trades[k].symbol, f'{active_trades[k].trade_start}'])
                if trade_each_symbol_with_separate_balance:
                    profitgraph[active_trades[k].index].append(account_balance[active_trades[k].index])
                    wins_and_losses[active_trades[k].symbol]['wins'] += 1
                    wins_and_losses[active_trades[k].symbol]['trades'] += 1
                else:
                    profitgraph[0].append(account_balance[0])
                active_trades[k].trade_info.trade_success = True
                active_trades[k] = BacktesterHelper.get_candles_for_graphing(Bots[active_trades[k].index], active_trades[k], graph_buys_and_sells_window_before, graph_buys_and_sells_window_after)
                active_trades[k] = BacktesterHelper.get_indicators_for_graphing(Bots[active_trades[k].index].indicators, active_trades[k], graph_buys_and_sells_window_before,
                                                                      graph_buys_and_sells_window_after, Bots[active_trades[k].index].current_index)
                trades_for_graphing.append(active_trades[k].trade_info)
                active_trades.pop(k)
            elif active_trades[k].trade_status == 3:
                ## Loss
                losing_trades.append([active_trades[k].symbol, f'{active_trades[k].trade_start}'])
                if trade_each_symbol_with_separate_balance:
                    profitgraph[active_trades[k].index].append(account_balance[active_trades[k].index])
                    wins_and_losses[active_trades[k].symbol]['losses'] += 1
                    wins_and_losses[active_trades[k].symbol]['trades'] += 1
                else:
                    profitgraph[0].append(account_balance[0])
                active_trades[k] = BacktesterHelper.get_candles_for_graphing(Bots[active_trades[k].index], active_trades[k],
                                                                   graph_buys_and_sells_window_before, graph_buys_and_sells_window_after)
                active_trades[k] = BacktesterHelper.get_indicators_for_graphing(Bots[active_trades[k].index].indicators,
                                                                      active_trades[k], graph_buys_and_sells_window_before, graph_buys_and_sells_window_after,
                                                                      Bots[active_trades[k].index].current_index)
                trades_for_graphing.append(active_trades[k].trade_info)
                active_trades.pop(k)
            elif active_trades[k].trade_status == 4:
                if (active_trades[k].entry_price < Close[active_trades[k].index][Bots[active_trades[k].index].current_index] and active_trades[k].trade_direction == 1) \
                or (active_trades[k].entry_price > Close[active_trades[k].index][Bots[active_trades[k].index].current_index] and active_trades[k].trade_direction == 0):
                    winning_trades.append([active_trades[k].symbol, f'{active_trades[k].trade_start}'])
                    active_trades[k].trade_info.trade_success = True
                    active_trades[k] = BacktesterHelper.get_candles_for_graphing(Bots[active_trades[k].index], active_trades[k],
                                                                       graph_buys_and_sells_window_before, graph_buys_and_sells_window_after)
                    active_trades[k] = BacktesterHelper.get_indicators_for_graphing(Bots[active_trades[k].index].indicators,
                                                                          active_trades[k], graph_buys_and_sells_window_before, graph_buys_and_sells_window_after,
                                                                          Bots[active_trades[k].index].current_index)
                    trades_for_graphing.append(active_trades[k].trade_info)
                else:
                    losing_trades.append([active_trades[k].symbol, f'{active_trades[k].trade_start}'])
                    active_trades[k] = BacktesterHelper.get_candles_for_graphing(Bots[active_trades[k].index], active_trades[k],
                                                                       graph_buys_and_sells_window_before, graph_buys_and_sells_window_after)
                    active_trades[k] = BacktesterHelper.get_indicators_for_graphing(Bots[active_trades[k].index].indicators,
                                                                          active_trades[k], graph_buys_and_sells_window_before, graph_buys_and_sells_window_after,
                                                                          Bots[active_trades[k].index].current_index)
                    trades_for_graphing.append(active_trades[k].trade_info)
                if trade_each_symbol_with_separate_balance:
                    profitgraph[active_trades[k].index].append(account_balance[active_trades[k].index])
                else:
                    profitgraph[0].append(account_balance[0])
                active_trades.pop(k)
            else:
                if active_trades[k].trade_status == 0:
                    active_trades[k].trade_status = 1
                k += 1

        if i == len(Close_1min[0]) - 2:
            for x in Date_1min:
                print(f"Data Set Finished: {x[i]}")
        if i % 1440 == 0 and i != 0:
            for j in range(len(symbols_to_trade)):
                Daily_return[j].append(account_balance[j])  # (day_return/day_start_equity)
            # day_return=0
            # day_start_equity=AccountBalance
        elif i == len(Close_1min[0]) - 1:
            for j in range(len(symbols_to_trade)):
                Daily_return[j].append(account_balance[j])  # (day_return/day_start_equity)
    print("\n")
    if not trade_each_symbol_with_separate_balance:
        average = 0
        num_wins = 0
        for i in range(1, len(profitgraph[0])):
            if profitgraph[0][i] > profitgraph[0][i - 1]:
                num_wins += 1
                average += (profitgraph[0][i] - profitgraph[0][i - 1]) / profitgraph[0][i]

        if num_wins != 0:
            average /= num_wins
        CAGR = 0
        vol = 0
        Sharpe_ratio = 0
        sortino_ratio = 0
        calmar_ratio = 0
        risk_free_rate = 1.41  ##10 year treasury rate
        df = pd.DataFrame({'Account_Balance': Daily_return[0]})
        df['daily_return'] = df['Account_Balance'].pct_change()
        df['cum_return'] = (1 + df['daily_return']).cumprod()
        df['cum_roll_max'] = df['cum_return'].cummax()
        df['drawdown'] = df['cum_roll_max'] - df['cum_return']
        df['drawdown %'] = df['drawdown'] / df['cum_roll_max']
        max_dd = df['drawdown %'].max() * 100
        try:
            # cum_ret = np.array(df['cum_return'])
            CAGR = ((df['cum_return'].iloc[-1]) ** (1 / time_CAGR) - 1) * 100  # ((df['cum_return'].iloc[-1])**(1/time_CAGR)-1)*100
            vol = (df['daily_return'].std() * np.sqrt(365)) * 100
            neg_vol = (df[df['daily_return'] < 0]['daily_return'].std() * np.sqrt(365)) * 100
            Sharpe_ratio = (CAGR - risk_free_rate) / vol
            sortino_ratio = (CAGR - risk_free_rate) / neg_vol
            calmar_ratio = CAGR / max_dd
        except:
            pass

        print("\nSettings:")
        print('leverage:', leverage)
        print('order_size:', order_size)
        print('fee:', fee)
        print("\nSymbol(s):", symbols_to_trade, "fee:", fee)
        print(f"{original_time_interval} OHLC Candle Sticks from {start} to {end}")
        print("Account Balance:", account_balance[0])
        print("% Gain on Account:", ((account_balance[0] - originalBalance[0]) * 100) / originalBalance[0])
        print("Total Returns:", account_balance[0] - originalBalance[0], "\n")

        print(f"Annualized Volatility: {round(vol, 4)}%")
        print(f"CAGR: {round(CAGR, 4)}%")
        print("Sharpe Ratio:", round(Sharpe_ratio, 4))
        print("Sortino Ratio:", round(sortino_ratio, 4))
        print("Calmar Ratio:", round(calmar_ratio, 4))
        print(f"Max Drawdown: {round(max_dd, 4)}%")

        print(f"Average Win: {round(average * 100, 4)}%")
        print("Trades Made: ", tradeNO)
        print("Accuracy: ", f"{(len(winning_trades) / tradeNO) * 100}%", "\n")
        print(f"Winning Trades:\n {len(winning_trades)}")
        print(f"Losing Trades:\n {len(losing_trades)}")
        plt.plot(profitgraph[0])
        if trade_all_symbols:
            plt.title(f"All Coins: {original_time_interval} from {start} to {end}")
        else:
            plt.title(f"{symbols_to_trade}: {original_time_interval} from {start} to {end}")
        plt.ylabel('Account Balance')
        plt.xlabel('Number of Trades')
        if not os.path.exists(path_to_graphs_folder + f'{original_time_interval}'):
            os.makedirs(path_to_graphs_folder + f'{original_time_interval}')
        plt.savefig(f'{backtest_path}equity_curve.png', dpi=300)
        plt.close()

    else:
        useful_coins = []
        num_wins_total = 0
        for j in range(len(symbols_to_trade)):
            if (only_show_profitable_coins and account_balance[j] > originalBalance[j]*(1 + percent_gain_threshold)) or (not only_show_profitable_coins):
                average = 0
                num_wins = 0
                for i in range(1, len(profitgraph[j])):
                    if profitgraph[j][i] > profitgraph[j][i - 1]:
                        num_wins += 1
                        average += (profitgraph[j][i] - profitgraph[j][i - 1]) / profitgraph[j][i]
                if num_wins != 0:
                    average /= num_wins
                num_wins_total += num_wins
                risk_free_rate = 1.41  ##10 year treasury rate
                try:
                    df = pd.DataFrame({'Account_Balance': Daily_return[j]})
                    df['daily_return'] = df['Account_Balance'].pct_change()
                    df['cum_return'] = (1 + df['daily_return']).cumprod()
                    df['cum_roll_max'] = df['cum_return'].cummax()
                    df['drawdown'] = df['cum_roll_max'] - df['cum_return']
                    df['drawdown %'] = df['drawdown'] / df['cum_roll_max']
                    max_dd = df['drawdown %'].max() * 100

                    # cum_ret = np.array(df['cum_return'])
                    CAGR = ((df['cum_return'].iloc[-1]) ** (
                                1 / time_CAGR) - 1) * 100  # ((df['cum_return'].iloc[-1])**(1/time_CAGR)-1)*100
                    vol = (df['daily_return'].std() * np.sqrt(365)) * 100
                    neg_vol = (df[df['daily_return'] < 0]['daily_return'].std() * np.sqrt(365)) * 100
                    Sharpe_ratio = (CAGR - risk_free_rate) / vol
                    sortino_ratio = (CAGR - risk_free_rate) / neg_vol
                    calmar_ratio = CAGR / max_dd
                    if (use_minimum_drawdown and max_dd < minimum_drawdown) or not use_minimum_drawdown:
                        accuracy = (wins_and_losses[symbols_to_trade[j]]['wins'] * 100) / wins_and_losses[symbols_to_trade[j]]['trades']
                        check_accuracy_percent = False
                        accuracy_percent = 90
                        if accuracy_percent < accuracy and check_accuracy_percent or not check_accuracy_percent:
                            useful_coins.append(symbols_to_trade[j])
                            print("Symbol:", symbols_to_trade[j], "fee:", fee)
                            print(f"{original_time_interval} OHLC Candle Sticks from {start} to {end}")
                            print("Account Balance:", account_balance[j])
                            print("% Gain on Account:", ((account_balance[j] - originalBalance[j]) * 100) / originalBalance[j])
                            print("Total Returns:", account_balance[j] - originalBalance[j])
                            print(f"Annualized Volatility: {round(vol, 4)}%")
                            print(f"CAGR: {round(CAGR, 4)}%")
                            print(f"Accuracy: {accuracy}%")
                            print(f"Trades Taken: {wins_and_losses[symbols_to_trade[j]]['trades']}")
                            print("Sharpe Ratio:", round(Sharpe_ratio, 4))
                            print("Sortino Ratio:", round(sortino_ratio, 4))
                            print("Calmar Ratio:", round(calmar_ratio, 4))
                            print(f"Max Drawdown: {round(max_dd, 4)}%")
                            print(f"Average Win: {round(average * 100, 4)}%\n")
                        if not os.path.exists(path_to_graphs_folder + f'{original_time_interval}'):
                            os.makedirs(path_to_graphs_folder + f'{original_time_interval}')
                        plt.plot(profitgraph[j])
                        plt.title(f"{symbols_to_trade[j]}: {original_time_interval} from {start} to {end}")
                        plt.ylabel('Account Balance')
                        plt.xlabel('Number of Trades')
                        plt.savefig(f'{backtest_path}{symbols_to_trade[j]}_equity_curve.png', dpi=300, bbox_inches='tight')
                        plt.close()
                except Exception as e:
                    print(e)
        print("\nSettings:")
        print('leverage:', leverage)
        print('order_size:', order_size)
        print('fee:', fee)
        print(f"symbol = {useful_coins}")
        print("\nOverall Stats based on all coins")
        print("Trades Made: ", tradeNO)
        print("Accuracy: ", f"{(len(winning_trades) / tradeNO) * 100}%", "\n")
        print(f"Winning Trades:\n {len(winning_trades)}")
        print(f"Losing Trades:\n {len(losing_trades)}")
        print(f"Trades Closed on Condition:\n {closed_on_condition}")

    if graph_buys_and_sells:
        BacktesterHelper.generate_trade_graphs(trades_for_graphing, backtest_path, auto_open_graph_images) ## trades: [symbol, entry_price, TP_price, SL_price, indicators, candles]


if __name__ == "__main__":
    run_backtester(starting_account_balance=starting_account_balance, leverage=leverage, order_size=order_size, start=start, end=end,
                   interval=interval, max_number_of_positions=max_number_of_positions, trade_all_symbols=trade_all_symbols,
                   trade_each_symbol_with_separate_balance=trade_each_symbol_with_separate_balance,
                   only_show_profitable_coins=only_show_profitable_coins, percent_gain_threshold=percent_gain_threshold,
                   use_minimum_drawdown=use_minimum_drawdown, minimum_drawdown=minimum_drawdown, symbols_to_trade=symbols_to_trade, use_trailing_stop=use_trailing_stop,
                   trailing_stop_callback=trailing_stop_callback, slippage=slippage, strategy=trading_strategy, TP_SL_choice=TP_SL_choice,
                   SL_mult=SL_mult, TP_mult=TP_mult, use_multiprocessing_for_downloading_data=use_multiprocessing_for_downloading_data,
                   graph_folder_location=graph_folder_location, fee=fee, buffer=buffer, trading_on=trading_on, graph_buys_and_sells=graph_buys_and_sells,
                   auto_open_graph_images=auto_open_graph_images, graph_buys_and_sells_window_before=graph_buys_and_sells_window_before,
                   graph_buys_and_sells_window_after=graph_buys_and_sells_window_after, trade_log_name=trade_log_name, coin_exclusion_list=coin_exclusion_list)
