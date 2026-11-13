"""Учебный фрагмент для тестового задания ТОЛЬКООПТ.

Python 3.10+, только стандартная библиотека. Запуск примера: python starter.py
В функции recommend_price намеренно есть ошибки. Исправьте её по правилам ниже.
sample_fetch_offers имитирует внешний источник: реальные запросы не нужны.

Контракт fetch_offers(): async-функция без аргументов, возвращает словарь
со status (success / partial / error) и offers (список предложений).
Все суммы на входе — положительные Decimal с точностью до копейки.
seller — строка; delivery_days — неотрицательное целое число или None.
Формат входных данных корректен; дополнительных проверок типов не требуется.
fetch_offers может завершиться исключением или долго ожидать ответа.
current_price — текущая цена; min_price — минимально допустимая цена.
timeout_s — положительное число секунд, по умолчанию 2.

ПРАВИЛА В ПОРЯДКЕ ПРИМЕНЕНИЯ
1. Ограничьте ожидание fetch_offers значением timeout_s. При ошибке источника,
   тайм-ауте или status != success верните текущую цену и HOLD.
2. Учитывайте предложения с известной доставкой не более 6 дней.
   Исключайте собственный магазин MYSHOP независимо от регистра букв.
3. Если подходящих предложений нет, верните текущую цену и HOLD,
   даже если текущая цена ниже min_price.
4. Минимальную цену подходящего конкурента уменьшите на 1,5% и округлите
   вниз до копейки. Рекомендация — максимум из этой суммы и min_price.
5. Если рекомендация отличается от текущей цены более чем на 30% в любую
   сторону, верните рекомендацию и REVIEW. Иначе — рекомендацию и APPLY.
   Ровно 30% допускается. REVIEW означает, что автоматическое применение
   запрещено до ручной проверки.

РЕЗУЛЬТАТ
Словарь с полями price (Decimal), decision (APPLY / REVIEW / HOLD),
reason (короткая понятная причина). Сохраните интерфейс recommend_price;
вспомогательные функции допустимы. Пример ниже после исправления должен
вернуть price = Decimal("4728.00"), decision = "APPLY".

ПРОВЕРКА
Добавьте минимум два автоматических теста: обычный расчёт и один сбой
или граничный случай на ваш выбор. Укажите команду запуска тестов.
Достаточно стандартной библиотеки; pytest также допустим.
"""

# КОМАНДА ДЛЯ ЗАПУСКА ТЕСТОВ - python -m unittest test.py

import asyncio
from collections.abc import Awaitable, Callable
from decimal import Decimal, ROUND_FLOOR
from typing import Any


SUCCESS_STATUS: str = 'success'
SHOP_EXCLUDE: str = 'myshop'
RECOMMENDATION_BORDER: Decimal = Decimal("0.30")

def filter_prices(fetch_result: dict[str, Any]) -> list[Decimal]:
    """
    Фильтрует цены в соответствии с правилами

    Args:
        fetch_result - словарь офферов

    Returns:
        list[Decimal]: список отфильтрованных цен
    """
    return [
        offer["price"]
        for offer in fetch_result["offers"]
        if offer["delivery_days"] is not None 
        and offer["delivery_days"] <= 6 
        and offer['seller'].lower() != SHOP_EXCLUDE
    ]

def is_recommendation_too_big(price: Decimal, current_price: Decimal) -> bool:
    """
    Проверяет, отличается ли рекомендованная цена от текущей более чем на 30%

    Args:
        price - рекомендованная цена
        current_price - текущая цена

    Returns:
        bool: True, если разница превышает допустимый порог, иначе False
    """
    return abs(price - current_price) > current_price * RECOMMENDATION_BORDER

async def recommend_price(
    fetch_offers: Callable[[], Awaitable[dict[str, Any]]],
    current_price: Decimal,
    min_price: Decimal,
    timeout_s: float = 2.0,
) -> dict[str, Any]:
    try:
        # Ограничиваем время ожидания таймаутом
        result = await asyncio.wait_for(fetch_offers(), timeout=timeout_s)

        if result['status'] != SUCCESS_STATUS:
            # Если данные пришли с ошибкой или неполные
            return {"price": current_price, "decision": "HOLD", "reason": "Цены конкурентов получены с ошибкой или частично"}
        
    except asyncio.TimeoutError:
        # На случай таймаута
        return {"price": current_price, "decision": "HOLD", "reason": "Источник не вернул цены"}
    except Exception:
        # На случай ошибки источника
        return {"price": current_price, "decision": "HOLD", "reason": "Ошибка источника"}

    prices = filter_prices(result)
    if not prices:
        return {"price": current_price, "decision": "HOLD", "reason": "Подходящих предложений нет"}

    min_competitor_price = min(prices) * Decimal("0.985")
    # Округляем вниз до копеек
    price = min_competitor_price.quantize(Decimal('0.01'), rounding=ROUND_FLOOR)
    recommendation = max(price, min_price)

    # Проверяем, разницу между рекомендацией и текущей ценой
    if is_recommendation_too_big(recommendation, current_price):
        return {"price": recommendation, "decision": "REVIEW", "reason": "Необходима ручная проверка"}
    return {"price": recommendation, "decision": "APPLY", "reason": "Найдена минимальная цена"}


async def sample_fetch_offers() -> dict[str, Any]:
    return {
        "status": "success",
        "offers": [
            {"seller": "myshop", "price": Decimal("4300.00"), "delivery_days": 2},
            {"seller": "PARTS", "price": Decimal("4800.00"), "delivery_days": 3},
            {"seller": "SLOW", "price": Decimal("4700.00"), "delivery_days": 8},
        ],
    }

if __name__ == "__main__":
    print(asyncio.run(recommend_price(
        sample_fetch_offers,
        current_price=Decimal("4900.00"),
        min_price=Decimal("4500.00"),
    )))
