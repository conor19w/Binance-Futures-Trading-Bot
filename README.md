# Binance-Futures-Trading-Bot [![Tweet](https://img.shields.io/twitter/url/http/shields.io.svg?style=social)](https://twitter.com/intent/tweet?text=Check%20out%20this%20free%20Binance%20Trading%20Bot%20I%20found%20on%20Github%20&url=https://github.com/conor19w/Binance-Futures-Trading-Bot&hashtags=Trading,Bot,Trading_Bot,Cryptocurrency_Trading_Bot,Crypto,Bitcoin,Ethereum,Cryptocurrency,Binance,DOGE,dogecoin)
## Technical Analysis driven Crypto Trading bot on Binance Futures 📈 ₿ 🚀
* Utilizes [python-Binance](https://python-binance.readthedocs.io/en/latest/) Client to execute orders and pull data from Binance
* Utilizes [ta](https://technical-analysis-library-in-python.readthedocs.io/en/latest/) library to calculate Technical indicators
* Write your own functions to implement your TA strategies
* Comes with some pre-coded strategies found in [TradingStrats.py](https://github.com/conor19w/Binance-Futures-Trading-Bot/blob/main/TradingStrats.py)
* If you enjoy the repo please share it around to friends & tweet about it using the tweet button above 😃

## Binance Setup
---
* Create a [Binance Account](https://accounts.binance.com/en/register?ref=UZBGCD6U) (This link uses my refferal & would be greatly appreciated)
* __Enable Two-factor Authentication in the security section to keep your crypto safe.__
* Create a new API key under the API Management section.
*  [✓] Read Info [✓] Enable Trading [X] Enable Withdrawals
* Whitelist your IP address to further secure your account, and so that your API keys don't expire after 1 month.
* Fill in your api keys into api_secret and api_key in [API_keys.py](https://github.com/conor19w/Binance-Futures-Trading-Bot/blob/main/API_keys.py).

### Back test strategies in [Bot.py](https://github.com/conor19w/Binance-Futures-Trading-Bot/blob/main/Bot.py)
---
* To back test ensure Trading is switched off on [line 92](https://github.com/conor19w/Binance-Futures-Trading-Bot/blob/92841dd2b8c0b8778e90b28fe887e0e19b2949e4/Bot.py#L92)
* Back test section starts at [line 707](https://github.com/conor19w/Binance-Futures-Trading-Bot/blob/92841dd2b8c0b8778e90b28fe887e0e19b2949e4/Bot.py#L707)
* Create a list named 'symbol' of coin/coins you wish to run a strategy on ie. symbol = ['BTCUSDT' , 'ETHUSDT'] , this would run your strategy on BTC and ETH.
* Ignore the [pair-trading](https://github.com/conor19w/Binance-Futures-Trading-Bot/blob/92841dd2b8c0b8778e90b28fe887e0e19b2949e4/Bot.py#L731) section if you are executing a TA strategy
* The [time_period](https://github.com/conor19w/Binance-Futures-Trading-Bot/blob/92841dd2b8c0b8778e90b28fe887e0e19b2949e4/Bot.py#L759) variable is the length of time in the past from today to run the strategy on
* The [TIME_INTERVAL](https://github.com/conor19w/Binance-Futures-Trading-Bot/blob/92841dd2b8c0b8778e90b28fe887e0e19b2949e4/Bot.py#L760) variable is the interval for the candlesticks we want to trade on.
* Next we want to choose our TA strategy, this is done after [line 886](https://github.com/conor19w/Binance-Futures-Trading-Bot/blob/92841dd2b8c0b8778e90b28fe887e0e19b2949e4/Bot.py#L886), uncomment a strategy or call a new strategy you have written yourself here, the 'prediction' variable is used to tell the script to go short (0), go long (1), or go flat (-99). This should be returned by custom strategy functions you create for the strategy to be executed correctly
* Some of the pre-coded strategies return a 'Type' variable, if a strategy returns the 'Type' variable you must call the SetSLTP() function from [TradingStrats.py](https://github.com/conor19w/Binance-Futures-Trading-Bot/blob/120baa9bb0b6f17d31daedb5769428b95ee3930e/TradingStrats.py) in order to set the corresponding Stop loss value, and Take profit value, this function is found in TradingStrats.py
* Now just run the script and wait a few minutes for it to pull the data and begin backtesting
### Run strategies live in [Bot.py](https://github.com/conor19w/Binance-Futures-Trading-Bot/blob/main/Bot.py)
---
__Run strategies at your own risk I am not responsible for your trading decisions, futures are risky and proper risk management should be adhered to at all times, always have a stoploss__
* Switch Trading On at [line 92](https://github.com/conor19w/Binance-Futures-Trading-Bot/blob/92841dd2b8c0b8778e90b28fe887e0e19b2949e4/Bot.py#L92)
* Choose the [Interval](https://github.com/conor19w/Binance-Futures-Trading-Bot/blob/92841dd2b8c0b8778e90b28fe887e0e19b2949e4/Bot.py#L105) of candle sticks you wish to trade over.
* Now uncomment a symbol or add a new symbol you want to trade after [line 107](https://github.com/conor19w/Binance-Futures-Trading-Bot/blob/92841dd2b8c0b8778e90b28fe887e0e19b2949e4/Bot.py#L107).
* To trade a coin not listed at the top of the script we must add an elif symbol clause in [get_coin_attrib()](https://github.com/conor19w/Binance-Futures-Trading-Bot/blob/92841dd2b8c0b8778e90b28fe887e0e19b2949e4/Helper.py#L298) in Helper.py specifying Coin_precision (how many decimal point places the price of the coin is measured in)
& Order_precision (how many decimal point places orders are measured in). __Note: some coins have no decimal places in order quantity, in this case we set Order_precision = 0.__
* Adjust 'OrderSIZE' line 95 and 'leverage' line 35 as you see fit, adjusting the leverage only changes the EffectiveAccountBalance variable in the script which will affect the order quantity, you must manually adjust the leverage on the exchange currently. __Note: OrderSIZE just helps scale trades in reality you may be risking more than your desired percentage, this will be decided by your stoploss values implemented__
* The Market_Orders switch on line 91 decides whether to use market orders (1) or to use limit orders (0).
* Now we select our trading strategy, one which we have thoroughly Backtested in the section starting on line 349.
* Custom Strategies must return a 'prediction' parameter either 1, 0, or -99 to go long, short or flat respectively. 
* Again like in Backtesting we call our trading strategy in the form of a function, If the function returns a Type then we must call the SetSLTP() function to set our Stop loss and Take profit before sending our orders.
* Now just run the script and your strategy is up and running.
### Create Custom Strategies
---
* Custom Strategies Can be implemented in [TradingStrats.py](https://github.com/conor19w/Binance-Futures-Trading-Bot/blob/main/TradingStrats.py)
* Custom Strategies should return 'prediction' parameter to indicate the strategy's decision to go short (0), go long (1), go flat (-99).
* For stop loss and take profit you must calculate and assign values to stoplossval and takeprofitval respectively, some pre-coded stoploss functions are already encapsulated in the [SetSLTP()](https://github.com/conor19w/Binance-Futures-Trading-Bot/blob/120baa9bb0b6f17d31daedb5769428b95ee3930e/TradingStrats.py#L750) function you may use these by getting your custom strategy to return a Type parameter corresponding to the Type in SetSLTP() or else set these in a custom function of your own. 
__Note: Stop loss and Take profit should be the margin of increase/decrease not the target price.__

# Contact me
* If you have any querys about anything, or need me to explain any blocks of code please reach out to me at wconor539@gmail.com.
* If you have any suggestions or requests please reach out to me as well.
