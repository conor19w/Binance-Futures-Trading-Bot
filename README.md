# Binance-Futures-Trading-Bot
## Technical Analysis driven Crypto Trading bot on Binance Futures 📈 ₿ 🚀
* Utilizes [python-Binance](https://python-binance.readthedocs.io/en/latest/) Client to execute orders and pull data from Binance
* Write your own functions to implement your TA strategies ie. decide trade entries and execute Orders
* Comes with some pre-coded strategies found in [TradingStrats.py](https://github.com/conor19w/Binance-Futures-Trading-Bot/blob/main/TradingStrats.py)
* Back test strategies in [Bot.py](https://github.com/conor19w/Binance-Futures-Trading-Bot/blob/main/Bot.py)
  * to back test ensure Trading is switched off on [line 210](https://github.com/conor19w/Binance-Futures-Trading-Bot/blob/120baa9bb0b6f17d31daedb5769428b95ee3930e/Bot.py#L210)
  * Back test section starts at [line 898](https://github.com/conor19w/Binance-Futures-Trading-Bot/blob/120baa9bb0b6f17d31daedb5769428b95ee3930e/Bot.py#L898)
  * create a list named 'symbol' of coin/coins you wish to run a strategy on ie. symbol = ['BTCUSDT' , 'ETHUSDT'] , this would run your strategy on BTC and ETH.
  * Ignore the [pair-trading](https://github.com/conor19w/Binance-Futures-Trading-Bot/blob/120baa9bb0b6f17d31daedb5769428b95ee3930e/Bot.py#L922) section if you are executing a TA strategy
  * the [time_period](https://github.com/conor19w/Binance-Futures-Trading-Bot/blob/120baa9bb0b6f17d31daedb5769428b95ee3930e/Bot.py#L948) variable is the length of time in the past from today to run the strategy on
  * the [TIME_INTERVAL](https://github.com/conor19w/Binance-Futures-Trading-Bot/blob/120baa9bb0b6f17d31daedb5769428b95ee3930e/Bot.py#L949) variable is the interval for the candlesticks we want to trade on.
  * next we want to choose our TA strategy, this is done after [line 1077](https://github.com/conor19w/Binance-Futures-Trading-Bot/blob/120baa9bb0b6f17d31daedb5769428b95ee3930e/Bot.py#L1077), uncomment a strategy or call a new strategy you have written yourself here, the 'prediction' variable is used to tell the program to go short (0), go long (1), or go flat (-99). this should be returned by custom functions for the strategy to be executed correctly
  * some of the pre-coded strategies return a 'Type' variable, if a strategy returns the 'Type' variable you must call the [SetSLTP()](https://github.com/conor19w/Binance-Futures-Trading-Bot/blob/120baa9bb0b6f17d31daedb5769428b95ee3930e/TradingStrats.py#L750) function in order to set the corresponding stoploss value, and take profit value, this function is found in TradingStrats.py
