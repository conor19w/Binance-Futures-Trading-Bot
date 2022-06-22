# Binance-Futures-Trading-Bot [![Tweet](https://img.shields.io/twitter/url/http/shields.io.svg?style=social)](https://twitter.com/intent/tweet?text=Check%20out%20this%20free%20Binance%20Trading%20Bot%20I%20found%20on%20Github%20&url=https://github.com/conor19w/Binance-Futures-Trading-Bot&hashtags=Trading,Bot,Trading_Bot,Cryptocurrency_Trading_Bot,Crypto,Bitcoin,Ethereum,Cryptocurrency,Binance,DOGE,dogecoin)
---
## Technical Analysis driven Crypto Trading bot on Binance Futures 📈 ₿ 🚀 [![Tweet](https://img.shields.io/twitter/url/http/shields.io.svg?style=social)](https://twitter.com/intent/tweet?text=Check%20out%20this%20free%20Binance%20Trading%20Bot%20I%20found%20on%20Github%20&url=https://github.com/conor19w/Binance-Futures-Trading-Bot&hashtags=Trading,Bot,Trading_Bot,Cryptocurrency_Trading_Bot,Crypto,Bitcoin,Ethereum,Cryptocurrency,Binance,DOGE,dogecoin)
[__Join My public Discord Server__](https://discord.gg/jBu6thyP66) __&__ [__Follow The Twitter__](https://twitter.com/futures_bot)
* Create a [Binance Account](https://accounts.binance.com/en/register?ref=BKR8BMMP) (This link uses my referral which gives you 5% kickback on trades & would be greatly appreciated)
* Want me to host a Bot for you on AWS, I have a [monthly tier](https://github.com/sponsors/conor19w) available for this join & I'll get in touch to get you set up 😃
* Utilizes [python-Binance](https://python-binance.readthedocs.io/en/latest/) Client to execute orders and pull data from Binance
* Utilizes [ta](https://technical-analysis-library-in-python.readthedocs.io/en/latest/) library for Technical indicators
* Write your own functions/classes to implement your TA strategies.
* Comes with some pre-coded strategies found in [TradingStrats.py](https://github.com/conor19w/Binance-Futures-Trading-Bot/blob/main/TradingStrats.py)
* If you enjoy the repo please share it around to friends & tweet about it using the tweet button above 😃   
or [Buy me a Coffee](https://www.buymeacoffee.com/conor19w)
* Want Coding Assistance, Custom Strategies & Custom Features? [Sponsor Me](https://github.com/sponsors/conor19w) (private repo coming soon)
* [One time payment](https://github.com/sponsors/conor19w) for custom strategies available also.
* Min version = Python 3.7 
* Max version = Python 3.9.x
* Recommended version = Python 3.8.10 (one I use and have no issues with)
* [Set up windows to sync time once a day](https://www.makeuseof.com/tag/synchronise-computer-time-internet-custom-schedule-windows-7/#:~:text=Go%20to%20%3E%20Start%20and%20type,on%20the%20right%20hand%20side) if you don't do this binance will eventually reject orders with a timestamp error.

---

### Run strategies live on Binance from __Live_Bot.py__
---
__Run strategies at your own risk I am not responsible for your trading decisions, futures are risky and proper risk management should be adhered to at all times, always have a stoploss__
---
__There is no set strategy, You can select one by uncommenting it in make_Decision() inside Bot_Class.py , These Strategies are from Trading_Strats.py and should be backtested thoroughly/ Altered to make more profitable__
* Settings are in __Config_File.py__
* Trade a single position at a time by setting ```Number_Of_Trades = 1```, to trade multiple coins just increment this value.
* Choose the Interval you want to trade and the buffer of candlesticks your strategy will need this will be dependent on indicators you need to ensure you have a sufficient buffer, or you will get errors.
* Leverage and order_size should be changed according to your preference
* symbol[] is a list of the symbols you wish to trade, the default is all the coins on the exchange currently.
* __Trailing stop: set ```use_trailing_stop = 1``` and change ```trailing_stop_percent``` to suit your strategy to use the trailing stop (Min val .001 i.e .1%, Max 5 i.e. 5%). The trailing stop will be placed when the take profit value margin of increase/decrease is reached from your strategy__.
* To close a trade based off a condition check_close_pos() must return a close_pos flag, and you must ensure ```self.use_close_pos = True``` in Bot_Class also.
* Want me to host a Bot for you on AWS, I have a [monthly tier](https://github.com/sponsors/conor19w) available for this join & I'll get in touch to get you set up 😃
---
#### Creating Custom Strategies:
__Strategies are implemented in Bot_Class.py as a function named Make_decision() in the Bot class__
* ```Make_decision()``` must return ```Trade_Direction, stop_loss_val, take_profit_val``` for the strategy to work properly
* You might draw inspiration for a strategy from one in __TradingStrats.py__
* I recommend using the backtester first.
---
### YouTube Channels with Strategy Ideas:
[__Silicon Trader__](https://www.youtube.com/channel/UCVRGsC6JVsB8F6HE_xjLyJg) | [__Trade Pro__](https://www.youtube.com/channel/UCrXjzUN6EtlyhaaAerbPfkQ) | [__Strategy Testing__](https://www.youtube.com/c/TradingStrategyTesting) | [__Trading Journal__](https://www.youtube.com/c/TradingJournal1) |  [__The Moving Average__](https://www.youtube.com/channel/UCYFQzaZyTUzY-Tiytyv3HhA)  
---
### Back test strategies in [Backtester.py](https://github.com/conor19w/Binance-Futures-Trading-Bot/blob/main/Backtester.py)
---
* Create a 'price_data' folder on the desktop and change the path variable in Helper.py to suit your machine. Data pulled from Binance will be stored in this folder and automatically loaded from memory in future.
* Create a list named 'symbol' of coin/coins you wish to run a strategy on ie. ```symbol = ['BTCUSDT' , 'ETHUSDT']``` , this would run your strategy on BTC and ETH.
Whereas ```symbol = ['BTCUSDT']``` would run the strategy on BTC only.
* Settings are found at the top of the script, __line 13__.
* Trailing Stop: turn the ```use_trailing_stop``` flag on, specify the ```trailing_stop_callback``` in decimal, now when a take profit margin target is hit the trailing stop will be placed and automatically & adjusted based off new Lows or Highs in price and the ```trailing_stop_callback``` you've specified.
* Next we want to choose our TA strategy, this is done in Bot_Class.py in Make_decision() , uncomment a strategy or call a new strategy you have written yourself here, the ```Trade_Direction``` variable is used to tell the script to go short (0), go long (1), or go flat (-99). This should be returned by custom strategy functions/classes you write for the strategy to be executed correctly
* Now just run the script and wait a few minutes for it to pull the data and begin backtesting
* Trade_All_Symbols flag will run the strategy on all the coins on binance if True.
* Trade_Each_Coin_With_Separate_Accounts flag will run the strategy with isolated account Balances for each coin you list if True. (Useful to see which coins the strategy works on before combining the trades to a single account)
* ```generate_heikin_ashi``` flag will make Heikin Ashi candles available to be consumed by your strategy ```make_decision()``` in the Bot Class.
* Generate a csv file of all the trades taken over a backtest by setting ```print_to_csv``` to True and setting csv_name to a unique name,
will throw an error if the file already exists.
* Flag variable ```plot_graphs_to_folder```, When active the equity curves will be plotted to a folder instead of displayed.
* To close a trade based off a condition ```check_close_pos()``` must return a close_pos flag, and you must ensure ```self.use_close_pos = True``` in Bot_Class also.
* Want me to host a Bot for you on AWS, I have a [monthly tier](https://github.com/sponsors/conor19w) available for this join & I'll get in touch to get you set up 😃
---
### __Back Test top performers:__
---
__Not indicative of future returns__
* Check out the other backtests although results were poor on some that was due to transaction fees in many cases so maybe altering to take less trades or add confirmation could work.
* All of the strategies can be improved on but this is just a good place to start.
* Try removing some coins from the list traded, the tests below were on all coins available at the time. 
---
__Triple EMA RUNEUSDT 01-04-22 to 28-04-22 (labelling is wrong)__
---
![](https://github.com/conor19w/Crypto-Bot/blob/main/Recent%20Backtests/TripleEMA/3m/RUNEUSDT_TripleEMA_INTERVAL_3m_01-04-22_28-04-22.png)  
---
__Golden Cross 15m candles__  
---
![](https://github.com/conor19w/Binance-Futures-Trading-Bot/blob/main/Backtest%20results%20of%202%20month%20period/goldenCross/15m%20candles%202%20months%20ago.png)  
__Triple EMA 4hr candles__
---
![](https://github.com/conor19w/Binance-Futures-Trading-Bot/blob/main/Backtest%20results%20of%202%20month%20period/tripleEMA/4hr%20candles%202%20months%20ago.png)
---
## To-Do list: (suggest something and I'll add it) 😃
* GUI if people were interested (could take a while I've no experience here)
* Data Cleaning task to run every x amount of minutes, ensuring the Live Bot hasn't lost any candles
* Option to give config in shell flags (Not sure yet but this was requested)
* Refactor happening soon to make the bot easier to use, and update the README
---
## Latest Changes (if any):
* Changed the Data structure (making old data obsolete apologies), new structure will have faster downloads and Now all candles are constructed 
from the 1m candles so if you run a backtest over a period you will now have data for all candles over that same period.(28/04/22)
* New flag ```plot_graphs_to_folder```, When active the equity curves will be plotted to a folder instead of displayed. (28/04/22)
* Added Trailing Stop into the backtester. (25/04/22)
* Added feature which can close a position based on a condition, by returning a flag close_pos from a strategy. (24/04/22)
* Added feature to trade each coin with an isolated account balance in Backtester, activated with new flag variable 'Trade_Each_Coin_With_Separate_Accounts'. (19/04/22)
* Added option to create a csv file from a backtest __Line 33__. (19/04/22)
* Updated Backtester to Open multiple positions, and Improved similarities to live Bot. (15/04/22)
* Added a check that removes trades that the user manually closed by the user. (15/04/22)
---
## Binance Setup
---
* Create a [Binance Account](https://accounts.binance.com/en/register?ref=BKR8BMMP) (This link uses my referral which gives you 5% kickback on trades & would be greatly appreciated)
* __Enable Two-factor Authentication in the security section to keep your crypto safe.__
* Create a new API key under the API Management section.
*  [✓] Read Info [✓] Enable Trading [✓] Enable Futures [X] Enable Withdrawals
* Whitelist your IP address to further secure your account, and so that your API keys don't expire after 1 month.
* Fill in your api keys into api_secret and api_key in __Config_File.py__
* [Set up windows to sync time once a day](https://www.makeuseof.com/tag/synchronise-computer-time-internet-custom-schedule-windows-7/#:~:text=Go%20to%20%3E%20Start%20and%20type,on%20the%20right%20hand%20side) if you don't do this binance will eventually reject orders with a timestamp error.
---
# Contact me [![Tweet](https://img.shields.io/twitter/url/http/shields.io.svg?style=social)](https://twitter.com/intent/tweet?text=Check%20out%20this%20free%20Binance%20Trading%20Bot%20I%20found%20on%20Github%20&url=https://github.com/conor19w/Binance-Futures-Trading-Bot&hashtags=Trading,Bot,Trading_Bot,Cryptocurrency_Trading_Bot,Crypto,Bitcoin,Ethereum,Cryptocurrency,Binance,DOGE,dogecoin)
* If you have any querys about anything, or need me to explain any blocks of code please reach out to me at wconor539@gmail.com.
* If you have any suggestions or requests please reach out to me as well.  
[__Join My public Discord Server__](https://discord.gg/jBu6thyP66) __&__ [__Follow The Twitter__](https://twitter.com/futures_bot)
* Want me to host a Bot for you on AWS, I have a [monthly tier](https://github.com/sponsors/conor19w) available for this join & I'll get in touch to get you set up 😃

