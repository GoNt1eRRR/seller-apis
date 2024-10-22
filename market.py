import datetime
import logging.config
from environs import Env
from seller import download_stock

import requests

from seller import divide, price_conversion

logger = logging.getLogger(__file__)


def get_product_list(page, campaign_id, access_token):
    """
    Получить список товаров с Яндекс Маркета.

    Args:
        page (str): Токен страницы.
        campaign_id (str): Идентификатор кампании.
        access_token (str): Токен доступа.

    Returns:
        list: Список содержащий информацию о продаваемых на Яндекс Маркете товарах.

    Examples:
        >>> get_product_list("page123", "campaign123", "access_token123")
        [{'item': 'product123', 'price': 100.0},
        {'item': 'product124', 'price': 150.0}]

    Raises:
        AttributeError: Если атрибуты page, campaign_id, access_token не являются строками.
        HTTPError: Если произошла ошибка при выполнении запроса.
    """
    endpoint_url = "https://api.partner.market.yandex.ru/"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
        "Host": "api.partner.market.yandex.ru",
    }
    payload = {
        "page_token": page,
        "limit": 200,
    }
    url = endpoint_url + f"campaigns/{campaign_id}/offer-mapping-entries"
    response = requests.get(url, headers=headers, params=payload)
    response.raise_for_status()
    response_object = response.json()
    return response_object.get("result")


def update_stocks(stocks, campaign_id, access_token):
    """
    Обновить остатки товаров.

    Args:
        stocks (list): Список содержащий информацию об остатках товаров.
        campaign_id (str): Идентификатор кампании.
        access_token (str): Токен доступа.

    Returns:
        list: Список содержащий обновленную информацию об остатках товаров.

    Examples:
        >>> update_stocks([{"stock": 5, "item_id": "123"}], "campaign123", "access_token123")
        {'result': 'success'}

    Raises:
        AttributeError: Если атрибуты campaign_id, access_token не являются строками, stocks не является списком.
        HTTPError: Если произошла ошибка при выполнении запроса.
    """
    endpoint_url = "https://api.partner.market.yandex.ru/"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
        "Host": "api.partner.market.yandex.ru",
    }
    payload = {"skus": stocks}
    url = endpoint_url + f"campaigns/{campaign_id}/offers/stocks"
    response = requests.put(url, headers=headers, json=payload)
    response.raise_for_status()
    response_object = response.json()
    return response_object


def update_price(prices, campaign_id, access_token):
    """
    Обновить цену.

    Args:
        prices (list): Список цен.
        campaign_id (str): Идентификатор кампании.
        access_token (str): Токен доступа.

    Returns:
        list: Список содержащий новую цену на товары.

    Examples:
        >>> update_price([{"price": "5990", "item_id": "123"}], "campaign123", "access_token123")
        {'result': 'success'}

    Raises:
        AttributeError: Если атрибуты campaign_id, access_token не являются строками, prices не является списком.
        HTTPError: Если произошла ошибка при выполнении запроса.
    """
    endpoint_url = "https://api.partner.market.yandex.ru/"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
        "Host": "api.partner.market.yandex.ru",
    }
    payload = {"offers": prices}
    url = endpoint_url + f"campaigns/{campaign_id}/offer-prices/updates"
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    response_object = response.json()
    return response_object


def get_offer_ids(campaign_id, market_token):
    """
    Получить артикулы товаров Яндекс маркета.

    Args:
        campaign_id (str): Идентификатор кампании.
        market_token (str): Токен доступа.

    Returns:
          list: Список содержащий артикулы товаров.

    Examples:
        >>> get_offer_ids("campaign123", "market_token123")
        ['offer123', 'offer124']

    Raises:
        AttributeError: Если атрибуты campaign_id, market_token не являются строками.
    """
    page = ""
    product_list = []
    while True:
        some_prod = get_product_list(page, campaign_id, market_token)
        product_list.extend(some_prod.get("offerMappingEntries"))
        page = some_prod.get("paging").get("nextPageToken")
        if not page:
            break
    offer_ids = []
    for product in product_list:
        offer_ids.append(product.get("offer").get("shopSku"))
    return offer_ids


def create_stocks(watch_remnants, offer_ids, warehouse_id):
    """
    Сформировать список остатков.

    Args:
        watch_remnants (list): Список содезжащий информацию об остатках часов.
        offer_ids (str): Список содержащий артикулы товаров.
        warehouse_id (str): id склада.

    Returns:
        list: Список содезжащий обновленную информацию об остатках часов.

    Examples:
        >>> create_stocks([{"Код": "123", "Количество": ">10"}], ["123"], "warehouse123")
        [{'offer_id': '123', 'stock': 100}]

    Raises:
        AttributeError: Если атрибуты offer_ids, warehouse_id не являются строками, watch_remnants не является списком.
    """
    # Уберем то, что не загружено в market
    stocks = list()
    date = str(datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z")
    for watch in watch_remnants:
        if str(watch.get("Код")) in offer_ids:
            count = str(watch.get("Количество"))
            if count == ">10":
                stock = 100
            elif count == "1":
                stock = 0
            else:
                stock = int(watch.get("Количество"))
            stocks.append(
                {
                    "sku": str(watch.get("Код")),
                    "warehouseId": warehouse_id,
                    "items": [
                        {
                            "count": stock,
                            "type": "FIT",
                            "updatedAt": date,
                        }
                    ],
                }
            )
            offer_ids.remove(str(watch.get("Код")))
    # Добавим недостающее из загруженного:
    for offer_id in offer_ids:
        stocks.append(
            {
                "sku": offer_id,
                "warehouseId": warehouse_id,
                "items": [
                    {
                        "count": 0,
                        "type": "FIT",
                        "updatedAt": date,
                    }
                ],
            }
        )
    return stocks


def create_prices(watch_remnants, offer_ids):
    """
    Создать цены на товары.

    Args:
        watch_remnants (list): Список содержащий информацию об остатках часов.
        offer_ids (list): Список артикулов товаров выставленных на Озон.

    Returns:
        list: Список содержащий информацию о новых ценах на товары.

    Examples:
        >>> create_prices([{"Код": "123", "Цена": "5'990.00 руб."}], ["123"])
        [{'auto_action_enabled': 'UNKNOWN', 'currency_code': 'RUB',
        'offer_id': '123', 'old_price': '0', 'price': '5990'}]

    Raises:
        AttributeError: Если атрибуты watch_remnants, offer_ids не являются списками.
    """
    prices = []
    for watch in watch_remnants:
        if str(watch.get("Код")) in offer_ids:
            price = {
                "id": str(watch.get("Код")),
                # "feed": {"id": 0},
                "price": {
                    "value": int(price_conversion(watch.get("Цена"))),
                    # "discountBase": 0,
                    "currencyId": "RUR",
                    # "vat": 0,
                },
                # "marketSku": 0,
                # "shopSku": "string",
            }
            prices.append(price)
    return prices


async def upload_prices(watch_remnants, campaign_id, market_token):
    """
    Асинхронно загружает обновленные цены на товары.

    Args:
        watch_remnants (dict): Словарь с остатками товара из файла excel.
        campaign_id (str): Идентификатор кампании на Яндекс Маркете.
        market_token (str): Токен доступа к API Яндекс Маркета.

    Returns:
        list: Список обновленных цен товаров.
    """
    offer_ids = get_offer_ids(campaign_id, market_token)
    prices = create_prices(watch_remnants, offer_ids)
    for some_prices in list(divide(prices, 500)):
        update_price(some_prices, campaign_id, market_token)
    return prices


async def upload_stocks(watch_remnants, campaign_id, market_token, warehouse_id):
    """
    Асинхронно обновляет остатки товаров.

    Args:
        watch_remnants (dict): Словарь с остатками товара из файла excel.
        campaign_id (str): Идентификатор кампании на Яндекс Маркете.
        market_token (str): Токен доступа к API Яндекс Маркета.
        warehouse_id (str) : Идентификатор склада.

    Returns:
        list: Список обновленных данных о наличии товара и отфильтрованных оставшихся товаров, которые не расны нулю.
    """
    offer_ids = get_offer_ids(campaign_id, market_token)
    stocks = create_stocks(watch_remnants, offer_ids, warehouse_id)
    for some_stock in list(divide(stocks, 2000)):
        update_stocks(some_stock, campaign_id, market_token)
    not_empty = list(
        filter(lambda stock: (stock.get("items")[0].get("count") != 0), stocks)
    )
    return not_empty, stocks


def main():
    env = Env()
    market_token = env.str("MARKET_TOKEN")
    campaign_fbs_id = env.str("FBS_ID")
    campaign_dbs_id = env.str("DBS_ID")
    warehouse_fbs_id = env.str("WAREHOUSE_FBS_ID")
    warehouse_dbs_id = env.str("WAREHOUSE_DBS_ID")

    watch_remnants = download_stock()
    try:
        # FBS
        offer_ids = get_offer_ids(campaign_fbs_id, market_token)
        # Обновить остатки FBS
        stocks = create_stocks(watch_remnants, offer_ids, warehouse_fbs_id)
        for some_stock in list(divide(stocks, 2000)):
            update_stocks(some_stock, campaign_fbs_id, market_token)
        # Поменять цены FBS
        upload_prices(watch_remnants, campaign_fbs_id, market_token)

        # DBS
        offer_ids = get_offer_ids(campaign_dbs_id, market_token)
        # Обновить остатки DBS
        stocks = create_stocks(watch_remnants, offer_ids, warehouse_dbs_id)
        for some_stock in list(divide(stocks, 2000)):
            update_stocks(some_stock, campaign_dbs_id, market_token)
        # Поменять цены DBS
        upload_prices(watch_remnants, campaign_dbs_id, market_token)
    except requests.exceptions.ReadTimeout:
        print("Превышено время ожидания...")
    except requests.exceptions.ConnectionError as error:
        print(error, "Ошибка соединения")
    except Exception as error:
        print(error, "ERROR_2")


if __name__ == "__main__":
    main()
