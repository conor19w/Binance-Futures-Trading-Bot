import telegram
import asyncio
from LiveTradingConfig import TELEGRAM_API_KEY, TELEGRAM_USER_ID, SEND_TELEGRAM_MESSAGE
import logging

if SEND_TELEGRAM_MESSAGE:
    telegram_bot = telegram.Bot(token=TELEGRAM_API_KEY)

def send_open_short_position_message(order_id, entry_price, account_balance, order_notional):
    percent_of_balance = (order_notional / account_balance) * 100
    message = f"Short position opened with order_id {order_id}. Entry Price: {entry_price}. Using {percent_of_balance:.2f}% of balance."
    send_message(message)

def send_open_long_position_message(order_id, entry_price, account_balance, order_notional):
    percent_of_balance = (order_notional / account_balance) * 100
    message = f"Long position opened with order_id {order_id}. Entry Price: {entry_price}. Using {percent_of_balance:.2f}% of balance."
    send_message(message)

def send_close_position_message(symbol, trade_direction, total_position_size):
    direction = "Long" if trade_direction == 1 else "Short"
    message = f"Closed {direction} position for {symbol}. Size: {total_position_size}."
    send_message(message)

def send_message(message):
    if not SEND_TELEGRAM_MESSAGE:
        return

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(async_send_message(message))
    finally:
        loop.close()

async def async_send_message(message):
    try:
        await telegram_bot.send_message(chat_id=TELEGRAM_USER_ID, text=message)
    except telegram.error.TelegramError:
        logging.error("ERROR in sending message to telegram")