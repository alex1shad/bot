import json
import logging
from pybit.unified_trading import HTTP


with open('config_data.json', 'r') as file:
    config_data = json.load(file)

# logging.basicConfig(format='%(asctime)s %(message)s', level=logging.DEBUG)
client = HTTP(api_key=config_data['api_key'],
              api_secret=config_data['api_secret'],
              return_response_headers=True,
              recv_window=60000
              )

def check_func(func):
    def wrapper(*args, **kwargs):
        while True:
            result = func(*args, **kwargs)
            if result[0] == 'OK':
                return result
            else:
                continue
    return wrapper


def change_round(number, length):
    result = str(int(number // 1)) + '.' + str(number % 1)[2:length]

    return result

@check_func
def get_curse(client, coin, delta):
    response_curse = client.get_orderbook(testnet=True,
                                          category='spot',
                                          symbol=f'{coin}USDT'
                                          )[0]

    response_mark = response_curse['retMsg']

    coin_price = float(response_curse['result']['a'][0][0])
    response_curse_dict = {'price': coin_price,
                           'price_delta': coin_price * delta / 100
                           }
    return [response_mark, response_curse_dict]

# print(get_curse(client=client, coin='BTC', delta=0.25))


def get_limit(client):
    response_limit = client.get_executions(category='linear',
                                           limit=10
                                           )
    response_mark = response_limit[0]['retMsg']

    response_limit_dict = {'all_limit': int(response_limit[2]['X-Bapi-Limit']),
                           'limit_status' : int(response_limit[2]['X-Bapi-Limit-Status']),
                           'limit_reset_time': int(response_limit[2]['X-Bapi-Limit-Reset-Timestamp']),
                           'server_time': int(response_limit[2]['Timenow'])
                           }

    return [response_mark, response_limit_dict]


def get_assets(client):
    response_assets = client.get_wallet_balance(accountType="UNIFIED")[0]
    response_mark = response_assets['retMsg']

    response_assets_dict = {}
    for coin in response_assets['result']['list'][0]['coin']:
        response_assets_dict[coin['coin']] = coin['walletBalance']

    return [response_mark, response_assets_dict]

# print(get_assets(client=client))


def get_coin_info(client, coin):
    response_coin_info = client.get_instruments_info(category='spot', symbol=f'{coin}USDT')
    response_mark = response_coin_info[0]['retMsg']

    response_coin_info_dict = response_coin_info[0]['result']['list'][0]['lotSizeFilter']
    return [response_mark, response_coin_info_dict]

# print(get_coin_info(client=client, coin='BTC'))


def create_order(client, coin, order_choice, delta):
    price = get_curse(client=client, coin=coin, delta=delta)[1]['price']
    delta = get_curse(client=client, coin=coin, delta=delta)[1]['price_delta']
    print(price-delta)

    if order_choice == 'Buy':
        price_order = change_round(number=price-delta, length=4)
    else:
        price_order = change_round(number=price+delta, length=4)
    print(price_order)
    if order_choice == 'Buy':
        usdt_precision = len(get_coin_info(client=client, coin=coin)[1]['quotePrecision'])
        quantity_usdt = float(get_assets(client=client)[1]['USDT'])
        quantity = change_round(number=quantity_usdt, length=usdt_precision)
    else:
        coin_precision = len(get_coin_info(client=client, coin=coin)[1]['basePrecision'])
        quantity_coin = float(get_assets(client=client)[1][coin])
        quantity = change_round(number=quantity_coin, length=coin_precision)
    print(quantity)

    responce_order = client.place_order(category='spot',
                                        symbol=f'{coin}USDT',
                                        side=order_choice,
                                        orderType='Limit',
                                        qty=quantity,
                                        price=price_order
                                        )[0]

    return responce_order

print(create_order(client=client,
                   coin='BTC',
                   order_choice='Buy',
                   delta=0.35
                   ))
