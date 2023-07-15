from binance.client import Client
from Config_File import API_KEY, API_SECRET, BASE_URL

USDTNGN = "USDTNGN"
BTCUSDT = "BTCUSDT"
BTCNGN = "BTCNGN"


def main():
    client = Client(api_key=API_KEY, api_secret=API_SECRET, testnet=False)
    # depth = client.get_order_book(symbol="USDTNGN")
    # print(depth["bids"])
    # print('ASKS')
    # print(depth["asks"])


    ngnBase1(client)
    print('__________________________________')
    ngnBase0(client)
    print('__________________________________')
    usdtBase(client)

    # print(get_base_amount_out(client, USDTNGN, 500000))

def ngnBase0(client):
    NGN_IN = 60000
    USDT_OUT = get_base_amount_out(
        client=client, symbol=USDTNGN, qoute_amount=remove_fee(NGN_IN))
    BTC_OUT = get_base_amount_out(
        client=client, symbol=BTCUSDT, qoute_amount=remove_fee(USDT_OUT))
    NGN_OUT = get_qoute_amount_out(
        client=client, symbol=BTCNGN, base_amount=remove_fee(BTC_OUT))
    PNL = NGN_OUT - NGN_IN

    print('NGN_IN', NGN_IN)
    print('USDT_OUT', USDT_OUT)
    print('BTC_OUT', BTC_OUT)
    print('NGN_OUT', NGN_OUT)
    print('PNL', PNL)

def ngnBase1(client):
    NGN_IN = 600000
    BTC_OUT = get_base_amount_out(
        client=client, symbol=BTCNGN, qoute_amount=remove_fee(NGN_IN))
    USDT_OUT = get_qoute_amount_out(
        client=client, symbol=BTCUSDT, base_amount=remove_fee(BTC_OUT))
    NGN_OUT = get_qoute_amount_out(
        client=client, symbol=USDTNGN, base_amount=remove_fee(USDT_OUT))
    PNL = NGN_OUT - NGN_IN

    print('NGN_IN', NGN_IN)
    print('BTC_OUT', BTC_OUT)
    print('USDT_OUT', USDT_OUT)
    print('NGN_OUT', NGN_OUT)
    print('PNL', PNL)

def usdtBase(client):
    USDT_IN = 200
    BTC_OUT = get_base_amount_out(
        client=client, symbol=BTCUSDT, qoute_amount=remove_fee(USDT_IN))
    NGN_OUT = get_qoute_amount_out(
        client=client, symbol=BTCNGN, base_amount=remove_fee(BTC_OUT))
    USDT_OUT = get_base_amount_out(
        client=client, symbol=BTCNGN, qoute_amount=remove_fee(NGN_OUT))
    
    PNL = USDT_OUT - USDT_IN
    print('USDT_IN', USDT_IN)
    print('BTC_OUT', BTC_OUT)
    print('NGN_OUT', NGN_OUT)
    print('USDT_OUT', USDT_OUT)
    print('PNL', PNL)

def remove_fee(amount):
    return amount*(1-0.001)


def get_qoute_amount_out(client: Client, symbol, base_amount):
    # what is the amount of naira that $1 can give me
    depth = client.get_order_book(symbol=symbol)
    qoute_amount = 0
    for ask_index in range(len(depth["bids"])):
        ask = depth["bids"][ask_index]
        unit_price = float(ask[0])
        volume = float(ask[1])
        amount_to_buy = base_amount if volume > base_amount else volume
        qoute_amount += amount_to_buy * unit_price

        base_amount -= volume
        if base_amount <= 0:
            break

    if base_amount > 0:
        return -1

    return qoute_amount


def get_base_amount_out(client: Client, symbol, qoute_amount):
    depth = client.get_order_book(symbol=symbol)
    base_amount = 0
    for bid_index in range(len(depth["asks"])):
        bid = depth["asks"][bid_index]
        bid_price = float(bid[0])
        volume = float(bid[1])
        amount_to_sell = qoute_amount if volume * \
            bid_price > qoute_amount else volume * bid_price
        base_amount += amount_to_sell/bid_price

        qoute_amount -= amount_to_sell
        if qoute_amount <= 0:
            break

    if qoute_amount > 0:
        return -1

    return base_amount


if __name__ == "__main__":
    main()
