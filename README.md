# Автоматизация продаж часов Casio на Ozon и Яндекс Маркет

## Скрипт `seller.py` для управления товарами на Ozon

### Описание
Скрипт предназначен для автоматизации работы с маркетплейсом **Ozon**. Он помогает синхронизировать ассортимент и обновлять цены на товары, используя данные с официального сайта **Casio**.  

### Основные этапы работы:
1. **Получение данных с Ozon:**  
   Скрипт загружает список товаров, которые уже продаются на Ozon. На основе этих данных формируется перечень артикулов (ID) текущих товаров.

2. **Сбор информации с сайта Casio:**  
   Скрипт получает актуальные остатки и цены на часы с сайта Casio.

3. **Анализ данных и обновление ассортимента:**  
   - На основе артикулов с Ozon и остатков с Casio формируется список новых товаров.  
   - Для новых товаров цена округляется до целого числа (без копеек).  
   - Эти товары добавляются в список доступных для продажи на Ozon.  

### Требования для запуска
Для запуска данного скрипта необходимо:
- Токен продавца Ozon
- ID клиента Ozon

## Команда для запуска
Скрипт запускается командой:
```
python seller.py
```

## Скрипт `market.py` для управления товарами на Yandex.Market

### Описание
Скрипт предназначен для управления товарами на **Яндекс Маркет**. Он помогает синхронизировать данные о наличии товаров, обновлять цены и управлять ассортиментом в автоматическом режиме.

### Основные этапы работы:
1. **Загрузка товаров с маркетплейса:**  
   Скрипт получает список товаров с актуальными данными (SKU, наличие и цены) с маркетплейса Яндекс Маркет.

2. **Анализ и обновление ассортимента:**  
   - Сравниваются остатки и цены товаров с **Яндекс Маркета** и сайта **Casio**.  
   - Если на маркетплейсе отсутствуют товары, представленные на сайте Casio, они добавляются в список для продажи.  
   - Цены округляются до целого числа (без копеек)

3. **Управление типами доставки:**  
   Поддерживается работа с моделями **FBS** и **DBS**, что позволяет продавцу выбирать, как будет доставляться товар (со своего склада или напрямую покупателю).

### Требования для запуска
- Токен продавца Яндекс Маркет
- ID клиента
- ID кампании и ID склада для FBS и DBS 

## Команда для запуска
Скрипт запускается командой:
```
python market.py
```