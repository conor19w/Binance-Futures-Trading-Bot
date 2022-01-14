from ta.momentum import stochrsi_d,stochrsi_k,stoch,stoch_signal,rsi,awesome_oscillator
from ta.trend import ema_indicator,macd_signal,macd,adx,sma_indicator,cci
from ta.volatility import average_true_range,bollinger_pband,bollinger_hband,bollinger_lband,bollinger_mavg,bollinger_wband
from ta.volume import ease_of_movement,on_balance_volume,force_index,money_flow_index,acc_dist_index,volume_weighted_average_price
from ta.momentum import tsi
import numpy as np

def create_dict(Current_dict,Trading_index,Volume,High,Low,Close,period_leading_to_signal,period_after_signal,use_emas,use_smas,
                sma_lengths,ema_lengths,use_stochastic,use_stochastic_rsi,use_ease_of_movement,
                use_rsi,use_macd,use_atr,use_bollinger_bands,use_awesome,use_adx,use_cci,use_obv,use_fi,use_mfi,use_tsi,use_acc_dist,use_vwap):
    if use_emas:
        for x in ema_lengths:
            Current_dict[f'{x}EMA'] = {}
            Current_dict[f'{x}EMA']['axis'] = 0  ##0 for on the same graph as the candles
            Current_dict[f'{x}EMA']['y'] = np.array(ema_indicator(Close))[-period_leading_to_signal - period_after_signal:]
    if use_smas:
        for x in sma_lengths:
            Current_dict[f'{x}SMA'] = {}
            Current_dict[f'{x}SMA']['axis'] = 0  ##0 for on the same graph as the candles
            Current_dict[f'{x}SMA']['y'] = np.array(sma_indicator(Close))[-period_leading_to_signal - period_after_signal:]
    num_indicators = 2
    if use_stochastic:
        Current_dict[f'STOCH'] = {}
        Current_dict[f'STOCH_signal'] = {}
        Current_dict[f'STOCH']['axis'] = num_indicators
        Current_dict[f'STOCH']['y'] = np.array(stoch(High,Low,Close))[-period_leading_to_signal - period_after_signal:]
        Current_dict[f'STOCH_signal']['axis'] = num_indicators
        Current_dict[f'STOCH_signal']['y'] = np.array(stoch_signal(High,Low,Close))[-period_leading_to_signal - period_after_signal:]
        num_indicators += 1
    if use_stochastic_rsi:
        Current_dict[f'STOCH_RSI_d'] = {}
        Current_dict[f'STOCH_RSI_k'] = {}
        Current_dict[f'STOCH_RSI_d']['axis'] = num_indicators
        Current_dict[f'STOCH_RSI_d']['y'] = np.array(stochrsi_d(Close))[-period_leading_to_signal - period_after_signal:]
        Current_dict[f'STOCH_RSI_k']['axis'] = num_indicators
        Current_dict[f'STOCH_RSI_k']['y'] = np.array(stochrsi_k(Close))[-period_leading_to_signal - period_after_signal:]
        num_indicators += 1
    if use_ease_of_movement:
        Current_dict[f'EOM'] = {}
        Current_dict[f'EOM']['axis'] = num_indicators
        Current_dict[f'EOM']['y'] = np.array(ease_of_movement(High,Low,Volume))[-period_leading_to_signal - period_after_signal:]
        num_indicators += 1
    if use_rsi:
        Current_dict[f'RSI'] = {}
        Current_dict[f'RSI']['axis'] = num_indicators
        Current_dict[f'RSI']['y'] = np.array(rsi(Close))[-period_leading_to_signal - period_after_signal:]
        num_indicators += 1
    if use_macd:
        Current_dict[f'MACD'] = {}
        Current_dict[f'MACD']['axis'] = num_indicators
        Current_dict[f'MACD']['y'] = np.array(macd(Close))[-period_leading_to_signal - period_after_signal:]
        Current_dict[f'MACD_signal'] = {}
        Current_dict[f'MACD_signal']['axis'] = num_indicators
        Current_dict[f'MACD_signal']['y'] = np.array(macd_signal(Close))[-period_leading_to_signal - period_after_signal:]
        num_indicators += 1
    if use_atr:
        Current_dict[f'ATR'] = {}
        Current_dict[f'ATR']['axis'] = num_indicators
        Current_dict[f'ATR']['y'] = np.array(average_true_range(High,Low,Close))[-period_leading_to_signal - period_after_signal:]
        num_indicators += 1
    if use_bollinger_bands:
        Current_dict[f'Upper_BB'] = {}
        Current_dict[f'Upper_BB']['axis'] = 0
        Current_dict[f'Upper_BB']['y'] = np.array(bollinger_hband(Close))[-period_leading_to_signal - period_after_signal:]
        Current_dict[f'Lower_BB'] = {}
        Current_dict[f'Lower_BB']['axis'] = 0
        Current_dict[f'Lower_BB']['y'] = np.array(bollinger_lband(Close))[-period_leading_to_signal - period_after_signal:]
    if use_awesome:
        Current_dict[f'AWESOME'] = {}
        Current_dict[f'AWESOME']['axis'] = num_indicators
        Current_dict[f'AWESOME']['y'] = np.array(awesome_oscillator(High,Low))[-period_leading_to_signal - period_after_signal:]
        num_indicators+=1
    if use_adx:
        Current_dict[f'ADX'] = {}
        Current_dict[f'ADX']['axis'] = num_indicators
        Current_dict[f'ADX']['y'] = np.array(adx(High, Low, Close))[-period_leading_to_signal - period_after_signal:]
        num_indicators += 1
    if use_cci:
        Current_dict[f'CCI'] = {}
        Current_dict[f'CCI']['axis'] = num_indicators
        Current_dict[f'CCI']['y'] = np.array(cci(High, Low, Close))[-period_leading_to_signal - period_after_signal:]
        num_indicators += 1
    if use_obv:
        Current_dict[f'OBV'] = {}
        Current_dict[f'OBV']['axis'] = num_indicators
        Current_dict[f'OBV']['y'] = np.array(on_balance_volume(Close))[-period_leading_to_signal - period_after_signal:]
        num_indicators += 1
    if use_fi:
        Current_dict[f'Force_index'] = {}
        Current_dict[f'Force_index']['axis'] = num_indicators
        Current_dict[f'Force_index']['y'] = np.array(force_index(Close, Volume))[-period_leading_to_signal - period_after_signal:]
        num_indicators += 1
    if use_mfi:
        Current_dict[f'MFI'] = {}
        Current_dict[f'MFI']['axis'] = num_indicators
        Current_dict[f'MFI']['y'] = np.array(money_flow_index(High, Low, Close,Volume))[-period_leading_to_signal - period_after_signal:]
        num_indicators += 1
    if use_tsi:
        Current_dict[f'TSI'] = {}
        Current_dict[f'TSI']['axis'] = num_indicators
        Current_dict[f'TSI']['y'] = np.array(tsi(Close))[-period_leading_to_signal - period_after_signal:]
        num_indicators += 1
    if use_acc_dist:
        Current_dict[f'ACC_dist'] = {}
        Current_dict[f'ACC_dist']['axis'] = num_indicators
        Current_dict[f'ACC_dist']['y'] = np.array(acc_dist_index(High,Low,Close,Volume))[-period_leading_to_signal - period_after_signal:]
        num_indicators += 1
    if use_vwap:
        Current_dict[f'VWAP'] = {}
        Current_dict[f'VWAP']['axis'] = 0
        Current_dict[f'VWAP']['y'] = np.array(volume_weighted_average_price(High, Low, Close, Volume))[-period_leading_to_signal - period_after_signal:]

    Current_dict['num_indicators'] = num_indicators


    return Current_dict