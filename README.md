# Binance-Futures-Trading-Bot [![Tweet](https://img.shields.io/twitter/url/http/shields.io.svg?style=social)](https://twitter.com/intent/tweet?text=Check%20out%20this%20free%20Binance%20Trading%20Bot%20I%20found%20on%20Github%20&url=https://github.com/conor19w/Binance-Futures-Trading-Bot&hashtags=Trading,Bot,Trading_Bot,Cryptocurrency_Trading_Bot,Crypto,Bitcoin,Ethereum,Cryptocurrency,Binance,DOGE,dogecoin)
---
## To-Do list: (suggest something and I'll add it) 😃
* Fix an issue with graphing trades, for now don't use.
* Fix trailing Stop in Back Tester, think its causing some rounding errors.
* GUI if people were interested (could take a while I've no experience here)
* Speed up Data Set aligner in Backtester with multiprocessing
### Strategy suggestions:
* [Heikin Ashi](https://www.youtube.com/watch?v=g3XV1hjCv_8) something like this
---
## Latest Changes (if any):
* Added support in the live Bot environment for some of the strategies in Trading_strats.py , To make use of a strategy in Bot.py just uncomment it inside Make_Decision() inside Data_set.py (11/02/2022).
* Added support for Heikin Ashi candles in Bot.py, there is now a switch in settings use_heikin_ashi. If switched on you may reference self.Open_H, self.Close_H etc. from make_Decision() in Data_set.py (17/01/22).
* Added a feature in the backtester that graphs all the trades made and Indicators at the time of the trade and saves them to folders labelled winning and losing trades, to help with analysis of strategies (14/01/22) See below in the graph trades section.
* Updated Backtester to make it more user friendly & changed naming convention for saved data (14/01/22).
* At the end of a backtest you can see the date & time that every trade was taken. So you can debug strategies by checking on tradingview/binance (07/01/22).
---
## Technical Analysis driven Crypto Trading bot on Binance Futures 📈 ₿ 🚀 [![Tweet](https://img.shields.io/twitter/url/http/shields.io.svg?style=social)](https://twitter.com/intent/tweet?text=Check%20out%20this%20free%20Binance%20Trading%20Bot%20I%20found%20on%20Github%20&url=https://github.com/conor19w/Binance-Futures-Trading-Bot&hashtags=Trading,Bot,Trading_Bot,Cryptocurrency_Trading_Bot,Crypto,Bitcoin,Ethereum,Cryptocurrency,Binance,DOGE,dogecoin)
[__Join My Discord Server__](https://discord.gg/jBu6thyP66) __&__ [__Follow The Twitter__](https://twitter.com/futures_bot)
* Utilizes [python-Binance](https://python-binance.readthedocs.io/en/latest/) Client to execute orders and pull data from Binance
* Utilizes [ta](https://technical-analysis-library-in-python.readthedocs.io/en/latest/) library for Technical indicators
* Write your own functions/classes to implement your TA strategies.
* There is no default Strategy implemented you must do this in Data_Set.py as specified below.
* Comes with some pre-coded strategies found in [TradingStrats.py](https://github.com/conor19w/Binance-Futures-Trading-Bot/blob/main/TradingStrats.py)
* If you enjoy the repo please share it around to friends & tweet about it using the tweet button above 😃   
or [Buy me a Coffee](https://www.buymeacoffee.com/conor19w)
* Min version = python 3.7 
## Binance Setup
---
* Create a [Binance Account](https://accounts.binance.com/en/register?ref=BKR8BMMP) (This link uses my referral which gives you 5% kickback on trades & would be greatly appreciated)
* __Enable Two-factor Authentication in the security section to keep your crypto safe.__
* Create a new API key under the API Management section.
*  [✓] Read Info [✓] Enable Trading [✓] Enable Futures [X] Enable Withdrawals
* Whitelist your IP address to further secure your account, and so that your API keys don't expire after 1 month.
* Fill in your api keys into api_secret and api_key in [API_keys.py](https://github.com/conor19w/Binance-Futures-Trading-Bot/blob/main/API_keys.py).
---
### Run strategies live in [Bot.py](https://github.com/conor19w/Binance-Futures-Trading-Bot/blob/main/Bot.py)
---
__Run strategies at your own risk I am not responsible for your trading decisions, futures are risky and proper risk management should be adhered to at all times, always have a stoploss__
---
__There is no set strategy, You can selet one by uncommenting one in make_Decision() inside data_set.py , These Strategies are from Trading_Strats.py and should be backtested thoroughly/ Altered to make more profitable__
* In __Bot.py__ on __line 341__ are the settings.
* Choose the Interval you want to trade and the buffer of candlesticks your strategy will need.
* leverage and order_size should be changed acording to your preference
* symbol[] is a list of the symbols you wish to trade, the default is all the coins on the exchange currently.
* __Trailing stop (NOT WORKING PROPERLY CURRENTLY): set __use_trailing_stop__ to __1__ and change __trailing_stop_percent__ to suit your strategy to use the trailing stop (Min val .001 i.e .1%, Max 5 i.e 5%). The trailing stop will be placed when the takeprofitval margin of increase/decrease is reached from your strategy__.  
---
#### Creating Custom Strategies:
__Strategies are implemented in Data_Set.py as a function named Make_decision() in the Data_set class__
* Make_decision() must return Trade_Direction,stoplossval,takeprofitval for the strategy to work properly
* You might draw inspiration for a strategy from one In __TradingStrats.py__
* I reccommend using the backtester first.
---
### YouTube Channels with Strategy Ideas:
[__Trade Pro__](https://www.youtube.com/channel/UCrXjzUN6EtlyhaaAerbPfkQ) | [__Strategy Testing__](https://www.youtube.com/c/TradingStrategyTesting) | [__Trading Journal__](https://www.youtube.com/c/TradingJournal1) | [__Critical Trading__](https://www.youtube.com/c/CriticalTrading) | [__The Moving Average__](https://www.youtube.com/channel/UCYFQzaZyTUzY-Tiytyv3HhA)  
---
### Back test strategies in [Backtester.py](https://github.com/conor19w/Binance-Futures-Trading-Bot/blob/main/Backtester.py)
---
* Create a list named 'symbol' of coin/coins you wish to run a strategy on ie. symbol = ['BTCUSDT' , 'ETHUSDT'] , this would run your strategy on BTC and ETH.
Whereas symbol = ['BTCUSDT'] would run the strategy on BTC only.
* The data is split into an in-sample set and a test set, the flag __test_set__ decides which set we are running the strategy on.
* The reason for splitting the data like this is to optimize parameters on the in-sample set and then once optimized run the strategy on the test-set to see if you have overfit your model by cherry picking values for parameters that suit the in-sample data.
* Settings are found at the top of the script, __line 52__.
* Trailing Stop: turn the __use_trailing_stop__ flag on, specify the __trailing_stop_distance__ in decimal, now when a takeprofit margin target is hit the trailing stop will be placed and automatically & adjusted based off new Lows or Highs in price and the __trailing_stop_distance__ you've specified.
* Next we want to choose our TA strategy, this is done after __line 640__ , uncomment a strategy or call a new strategy you have written yourself here, the 'Trade_Direction' variable is used to tell the script to go short (0), go long (1), or go flat (-99). This should be returned by custom strategy functions/classes you write for the strategy to be executed correctly
* Now just run the script and wait a few minutes for it to pull the data and begin backtesting
* Heikin Ashi Candles are available under: CloseStream_H, OpenStream_H, LowStream_H, HighStream_H which can be referenced or passed to Strategies.
## __New:__ Graph your trades by Altering the Trade Graph settings at the top of the script:  
* Ensure your __path__ in __download_data.py__ is correct as specified.
* A folder will be made on your desktop named after the trade_graph_folder paramameter you provide.
* Settings should be easy to follow just change the flags and the indicators will be added to the graphs.
![](https://github.com/conor19w/Binance-Futures-Trading-Bot/blob/main/losing%20trades/ALICEUSDT_16.png) 
---
#### Using Downloaded data for backtesting
---
* Reason to do this is to speed up backtesting 
* Create a folder on the desktop called __price_data__.
*  In __download_Data.py__ change the __path__ to f"C:\\Users\\your_name\\Desktop\\  
__replacing your_name with the user that you are logged into.__
* Switch __load_data__ on in __Backtester.py__ on __line 71__, now when you run the script it will load from the folder & if the specified candlestick data isn't present in the folder then it will be downloaded and saved for future use.  
* To overwrite existing data you can set the save_data flag = 1 & your data will be overwritten with new data.
* Otherwise you can just turn load_data off and pull data from the server everytime you want to run a backtest.
---

### __Back Test top performers:__
---
__Not indicative of future returns, Check out the other backtests although results were poor on some that was due to transaction fees in many cases so maybe altering to take less trades or add confirmation could work. All of the strategies can be improved on but this is just a good place to start.__  
---
__Golden Cross 15m candles__  
---
![](https://github.com/conor19w/Binance-Futures-Trading-Bot/blob/main/Backtest%20results%20of%202%20month%20period/goldenCross/15m%20candles%202%20months%20ago.png)  
__Triple EMA Stochastic RSI 15m candles__
---
![](https://github.com/conor19w/Binance-Futures-Trading-Bot/blob/main/Backtest%20results%20of%202%20month%20period/tripleEMAStochasticRSIATR/15m%20candles%202%20months%20ago.png)  
__Triple EMA 4hr candles__
---
![](https://github.com/conor19w/Binance-Futures-Trading-Bot/blob/main/Backtest%20results%20of%202%20month%20period/tripleEMA/4hr%20candles%202%20months%20ago.png)
---

###### (Depreciated) __Bot__(depreciated).py
###### (Depreciated) __Strategy_Tester(Depreciated).py__
# Contact me [![Tweet](https://img.shields.io/twitter/url/http/shields.io.svg?style=social)](https://twitter.com/intent/tweet?text=Check%20out%20this%20free%20Binance%20Trading%20Bot%20I%20found%20on%20Github%20&url=https://github.com/conor19w/Binance-Futures-Trading-Bot&hashtags=Trading,Bot,Trading_Bot,Cryptocurrency_Trading_Bot,Crypto,Bitcoin,Ethereum,Cryptocurrency,Binance,DOGE,dogecoin)
* If you have any querys about anything, or need me to explain any blocks of code please reach out to me at wconor539@gmail.com.
* If you have any suggestions or requests please reach out to me as well.  
[__Join My Discord Server__](https://discord.gg/jBu6thyP66) __&__ [__Follow The Twitter__](https://twitter.com/futures_bot)
* Find me on tradalize for copy trading under the username conor19w.📈 ₿ 🚀
