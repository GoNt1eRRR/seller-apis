import io
import logging.config
import os
import re
import zipfile
from environs import Env

import pandas as pd
import requests

logger = logging.getLogger(__file__)


def get_product_list(last_id, client_id, seller_token):
    """
    Получает список товаров магазина Ozon.

    Args:
        last_id (str): ID товара.
        client_id (str): ID клиента.
        seller_token (str): Токен продавца.

    Returns:
        list: Содержимое ответа API со списком товаров.

    Example:
        >>> get_product_list("last123", "client123", "token123")
        >>> [{'item': 'product123', 'price': 100.0}, {'item': 'product124', 'price': 150.0}]

    Raises:
        AttributeError: Если атрибуты last_id, client_id, seller_token не являются строками.
        HTTPError: Если произошла ошибка при выполнении запроса.
    """
    url = "https://api-seller.ozon.ru/v2/product/list"
    headers = {
        "Client-Id": client_id,
        "Api-Key": seller_token,
    }
    payload = {
        "filter": {
            "visibility": "ALL",
        },
        "last_id": last_id,
        "limit": 1000,
    }
    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()
    response_object = response.json()
    return response_object.get("result")


def get_offer_ids(client_id, seller_token):
    """
    Получить артикулы товаров магазина озон.

    Args:
        client_id (str): ID клиента.
        seller_token (str): Токен продавца.

    Returns:
        list: Список артикулов товаров.

    Example:
        >>> get_offer_ids("12345", "token123")
        ['offer_001', 'offer_002', 'offer_003']

    Raises:
        AttributeError: Если атрибуты client_id, seller_token не являются строками.
    """
    last_id = ""
    product_list = []
    while True:
        some_prod = get_product_list(last_id, client_id, seller_token)
        product_list.extend(some_prod.get("items"))
        total = some_prod.get("total")
        last_id = some_prod.get("last_id")
        if total == len(product_list):
            break
    offer_ids = []
    for product in product_list:
        offer_ids.append(product.get("offer_id"))
    return offer_ids


def update_price(prices: list, client_id, seller_token):
    """
    Обновить цены товаров.

    Args:
        prices (list): Список словарей, содержащих данные об артикуле и его цене.
        client_id (str): Идентификатор клиента, сгенерированный для доступа к API Ozon.
        seller_token (str): Токен, сгенерированный для доступа к API Ozon.

    Returns:
        list: Список содержащий новую цену на товары.

    Example:
        >>> prices = [{"offer_id": "offer_001", "price": 5000}]
        >>> update_price(prices, "12345", "token123")
        {'result': 'Цены успешно обновлены'}

    Raises:
        AttributeError: Если атрибуты client_id, seller_token не являются строками, prices не является списком.
        HTTPError: Если произошла ошибка при выполнении запроса.
    """
    url = "https://api-seller.ozon.ru/v1/product/import/prices"
    headers = {
        "Client-Id": client_id,
        "Api-Key": seller_token,
    }
    payload = {"prices": prices}
    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()
    return response.json()


def update_stocks(stocks: list, client_id, seller_token):
    """
    Обновить остатки.

    Args:
        stocks (list): Список остатков товаров.
        client_id (str): id клиента.
        seller_token (str): Токен продавца.

    Returns:
        list: Ответ сервера в формате JSON с информацией о статусе обновления остатков.

    Example:
        >>> stocks = [{"offer_id": "offer_001", "stock": 10}]
        >>> update_stocks(stocks, "12345", "token123")
        {'result': 'Остатки успешно обновлены'}

    Raises:
        AttributeError: Если атрибуты client_id, seller_token не являются строками, stocks не являутся списком.
        HTTPError: Если произошла ошибка при выполнении запроса.
    """
    url = "https://api-seller.ozon.ru/v1/product/import/stocks"
    headers = {
        "Client-Id": client_id,
        "Api-Key": seller_token,
    }
    payload = {"stocks": stocks}
    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()
    return response.json()


def download_stock():
    """
    Скачать файл ostatki с сайта casio.

    Returns:
        list: Список словарей, содержащих данные об остатках товаров.

    Example:
        >>> download_stock()
        [{'product': 'Часы Casio A158WA', 'quantity': 12, 'price': 4500}, ...]

    Raises:
        HTTPError: Если произошла ошибка при выполнении запроса.
    """
    # Скачать остатки с сайта
    casio_url = "https://timeworld.ru/upload/files/ostatki.zip"
    session = requests.Session()
    response = session.get(casio_url)
    response.raise_for_status()
    with response, zipfile.ZipFile(io.BytesIO(response.content)) as archive:
        archive.extractall(".")
    # Создаем список остатков часов:
    excel_file = "ostatki.xls"
    watch_remnants = pd.read_excel(
        io=excel_file,
        na_values=None,
        keep_default_na=False,
        header=17,
    ).to_dict(orient="records")
    os.remove("./ostatki.xls")  # Удалить файл
    return watch_remnants


def create_stocks(watch_remnants, offer_ids):
    """
    Создать список остатков товаров.

    Args:
        watch_remnants (list): Список содержащий информацию об остатках часов.
        offer_ids (list): Список артикулов товаров выставленных на Озон.

    Returns:
        list: Список содезжащий обновленную информацию об остатках часов.

    Example:
        >>> watch_remnants = [
        ...     {"Код": "123", "Количество": ">10"},
        ...     {"Код": "456", "Количество": "1"},
        ... ]
        >>> offer_ids = ["123", "456"]
        >>> create_stocks(watch_remnants, offer_ids)
        [
            {"offer_id": "123", "stock": 10},
            {"offer_id": "456", "stock": 1}
        ]

    Raises:
        AttributeError: Если атрибуты watch_remnants, offer_ids не являются списками.
    """
    # Уберем то, что не загружено в seller
    stocks = []
    for watch in watch_remnants:
        if str(watch.get("Код")) in offer_ids:
            count = str(watch.get("Количество"))
            if count == ">10":
                stock = 100
            elif count == "1":
                stock = 0
            else:
                stock = int(watch.get("Количество"))
            stocks.append({"offer_id": str(watch.get("Код")), "stock": stock})
            offer_ids.remove(str(watch.get("Код")))
    # Добавим недостающее из загруженного:
    for offer_id in offer_ids:
        stocks.append({"offer_id": offer_id, "stock": 0})
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
        >>>create_prices(
        >>>[{"Код": "123", "Цена": "5'990.00 руб."},
        >>>{"Код": "456", "Цена": "7'500.50 руб."}], ["123", "789"])

    [{'auto_action_enabled': 'UNKNOWN', 'currency_code': 'RUB',
    'offer_id': '123', 'old_price': '0', 'price': '5990'},
    {'auto_action_enabled': 'UNKNOWN', 'currency_code': 'RUB',
     offer_id': '456', 'old_price': '0', 'price': '7500'}]

    Raises:
        AttributeError: Если атрибуты watch_remnants, offer_ids не являются списками.
        """
    prices = []
    for watch in watch_remnants:
        if str(watch.get("Код")) in offer_ids:
            price = {
                "auto_action_enabled": "UNKNOWN",
                "currency_code": "RUB",
                "offer_id": str(watch.get("Код")),
                "old_price": "0",
                "price": price_conversion(watch.get("Цена")),
            }
            prices.append(price)
    return prices


def price_conversion(price: str) -> str:
    """
    Преобразовать цену.

    Args:
        price(str): Строка содержащая цену товара с точкой.

    Returns:
        str: Строка содержащая целое число.

    Examples:
        >>> price_conversion('5990.00 руб.')
        5900

    Raises:
        AttributeError: Если атрибут price не является строкой.
    """
    return re.sub("[^0-9]", "", price.split(".")[0])


def divide(lst: list, n: int):
    """
    Разделить список lst на части по n элементов

    Args:
        lst(list): Список, который надо будет разделить.
        n(int): Количество элементов в разделенных списках.

    Returns:
        iter: Итератор, который поочередно возвращает разделенные списки заданной длины.

    Examples:
        >>> list(divide([1, 2, 3, 4], 2))
        [[1, 2], [3, 4]]

    Raises:
        ValueError: Если n отрицательно число или равна нулю.
    """
    for i in range(0, len(lst), n):
        yield lst[i : i + n]


async def upload_prices(watch_remnants, client_id, seller_token):
    """
    Асинхронно загружает данные о ценах на товары на площадку Ozon.

    Args:
        watch_remnants(list): Список с остатками.
        client_id(str): Идентификатор клиента на Ozon.
        seller_token(str): Токен продавца для API Ozon.

    Returns:
        list: Список обновленных цен, которые будут загружены на площадку.
    """
    offer_ids = get_offer_ids(client_id, seller_token)
    prices = create_prices(watch_remnants, offer_ids)
    for some_price in list(divide(prices, 1000)):
        update_price(some_price, client_id, seller_token)
    return prices


async def upload_stocks(watch_remnants, client_id, seller_token):
    """
    Асинхронно загружает данные об остатках на товары на площадку Ozon.

    Args:
        watch_remnants (list): Список с остатками.
        client_id (str): Идентификатор клиента на Ozon.
        seller_token (str): Токен продавца для API Ozon.

    Returns:
        not_empty (list): Список отфильтрованных оставшихся товаров с количеством, которое не равно нулу.
        stocks (list): Список остатков товаров.
    """
    offer_ids = get_offer_ids(client_id, seller_token)
    stocks = create_stocks(watch_remnants, offer_ids)
    for some_stock in list(divide(stocks, 100)):
        update_stocks(some_stock, client_id, seller_token)
    not_empty = list(filter(lambda stock: (stock.get("stock") != 0), stocks))
    return not_empty, stocks


def main():
    env = Env()
    seller_token = env.str("SELLER_TOKEN")
    client_id = env.str("CLIENT_ID")
    try:
        offer_ids = get_offer_ids(client_id, seller_token)
        watch_remnants = download_stock()
        # Обновить остатки
        stocks = create_stocks(watch_remnants, offer_ids)
        for some_stock in list(divide(stocks, 100)):
            update_stocks(some_stock, client_id, seller_token)
        # Поменять цены
        prices = create_prices(watch_remnants, offer_ids)
        for some_price in list(divide(prices, 900)):
            update_price(some_price, client_id, seller_token)
    except requests.exceptions.ReadTimeout:
        print("Превышено время ожидания...")
    except requests.exceptions.ConnectionError as error:
        print(error, "Ошибка соединения")
    except Exception as error:
        print(error, "ERROR_2")


if __name__ == "__main__":
    main()
