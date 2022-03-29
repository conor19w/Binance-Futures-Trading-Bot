##fill in your API keys here to be accessed by other scripts
api_key = ''
api_secret = ''

################## settings, these are very strategy dependant ensure you have enough data for your chosen strategy ##################################
order_Size = .02
leverage = 10
start_string = '4 hour ago' ## Buffer of candle sticks be careful if you don't provide enough the bot will throw an error
Interval = '1m' ##candle sticks you want to trade
Max_Margin = 0  ## Set to zero to hold only a single position at a time, Margin allowed to be used up by opening positions
use_heikin_ashi = 0 ## Create heikin ashi candles that can be referenced in Bot_Class.Bot.make_decision()
use_trailing_stop = 0 ##If on we will use our TP value as the Activation price for a trailing stop loss
trailing_stop_callback = 0.1 ##trailing stop percent, this is .1% range is [.1% - 5%] .ie [0.1 - 5]

######################################################################################################################################################