import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import numpy as np
from matplotlib.pyplot import figure
from download_Data import path
def plot(trade_data,trade_graph_folder):
    matplotlib.use("Agg")
    for i in range(len(trade_data)):
        close = trade_data[f'Trade_{i}']['close']
        open = trade_data[f'Trade_{i}']['open']
        high = trade_data[f'Trade_{i}']['high']
        low = trade_data[f'Trade_{i}']['low']
        volume = trade_data[f'Trade_{i}']['volume']
        direction = trade_data[f'Trade_{i}']['direction']
        label = trade_data[f'Trade_{i}']['label']
        stop_loss = trade_data[f'Trade_{i}']['stop_loss']
        take_profit = trade_data[f'Trade_{i}']['take_profit']
        entry_price = trade_data[f'Trade_{i}']['entry_price']
        entry_index = trade_data[f'Trade_{i}']['entry_index']
        symbol = trade_data[f'Trade_{i}']['symbol']
        date = trade_data[f'Trade_{i}']['date']
        num_indicators = trade_data[f'Trade_{i}']['num_indicators']
        indices = trade_data[f'Trade_{i}']['indices']
        del trade_data[f'Trade_{i}']['close']
        del trade_data[f'Trade_{i}']['open']
        del trade_data[f'Trade_{i}']['high']
        del trade_data[f'Trade_{i}']['low']
        del trade_data[f'Trade_{i}']['volume']
        del trade_data[f'Trade_{i}']['direction']
        del trade_data[f'Trade_{i}']['label']
        del trade_data[f'Trade_{i}']['stop_loss']
        del trade_data[f'Trade_{i}']['take_profit']
        del trade_data[f'Trade_{i}']['entry_price']
        del trade_data[f'Trade_{i}']['symbol']
        del trade_data[f'Trade_{i}']['date']
        del trade_data[f'Trade_{i}']['num_indicators']
        del trade_data[f'Trade_{i}']['indices']
        del trade_data[f'Trade_{i}']['entry_index']
        ###Graph OHLCV, SL, TP, PNL line, Trade signal
        ##################################################

        heights = [3]
        for j in range(num_indicators-1):
            heights.append(1)
        fig,axs = plt.subplots(num_indicators,1,gridspec_kw={'height_ratios': heights},figsize=(30,15))
        #fig.set_dpi(100)
        #subfigs = fig.subfigures(2+len(trade_data[f'Trade_{i}']),1)

        if direction == 1:
            axs[0].plot(entry_index, low[entry_index]*.998, '^', markersize=15, color='g')
            axs[0].axhline(y=take_profit, color='g', linestyle='-',label='Take Profit')
            axs[0].axhline(y=entry_price, color='y', linestyle='-',label='PNL')
            axs[0].axhline(y=stop_loss, color='r', linestyle='-',label='Stop Loss')
        else:
            axs[0].plot(entry_index, high[entry_index]*1.002, 'v', markersize=15, color='r')
            axs[0].axhline(y=take_profit, color='g', linestyle='-', label='Take Profit')
            axs[0].axhline(y=entry_price, color='y', linestyle='-', label='PNL')
            axs[0].axhline(y=stop_loss, color='r', linestyle='-', label='Stop Loss')

        # define width of candlestick elements
        width = .4
        width2 = .05



        # define up and down prices
        col1 = 'green'
        col2 = 'red'
        for o,h,l,c,v,j in zip(open,high,low,close,volume,indices):
            if c>o:
                axs[0].bar(j, c - o, width, bottom=o, color=col1)
                axs[0].bar(j, h - c, width2, bottom=c, color=col1)
                axs[0].bar(j, l - o, width2, bottom=o, color=col1)
                axs[1].bar(j,v,width,color=col1)
            else:
                axs[0].bar(j, c - o, width, bottom=o, color=col2)
                axs[0].bar(j, h - o, width2, bottom=o, color=col2)
                axs[0].bar(j, l - c, width2, bottom=c, color=col2)
                axs[1].bar(j,v,width,color=col2)
        ##################################################
        ######## Graph the remaining Indicators ##########
        labels = []
        for x in trade_data[f'Trade_{i}']:
            labels.append(x)
        while len(labels)>0:
            temp = trade_data[f'Trade_{i}'][labels[0]]
            axs[temp['axis']].plot(indices,temp['y'],label=labels[0])
            del trade_data[f'Trade_{i}'][labels[0]]
            labels.pop(0)
        fig.legend(loc='upper right',prop={'size': 13})
        plt.title(f'Trade {i} on {symbol} at {date}')
        if label==1:
            plt.savefig(f'{path}{trade_graph_folder}\\winning trades\\{symbol}_{i}.png', dpi=300,bbox_inches='tight')
        else:
            plt.savefig(f'{path}{trade_graph_folder}\\losing trades\\{symbol}_{i}.png', dpi=300,bbox_inches='tight')

        plt.close()
