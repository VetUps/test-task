import unittest
import asyncio
from decimal import Decimal

from starter import recommend_price, sample_fetch_offers

class TestRecommendPrice(unittest.IsolatedAsyncioTestCase):
    async def test_normal_calculation(self):
        """Обычный расчёт"""
        result = await recommend_price(
            sample_fetch_offers,
            current_price=Decimal("4900.00"),
            min_price=Decimal("4500.00"),
        )
        self.assertEqual(result["price"], Decimal("4728.00"))
        self.assertEqual(result["decision"], "APPLY")

    async def test_timeout_returns_hold(self):
        """Таймаут источника"""
        async def slow_fetch_offers():
            await asyncio.sleep(0.2)
            return {"status": "success", "offers": []}
        result = await recommend_price(
            slow_fetch_offers,
            current_price=Decimal("4900.00"),
            min_price=Decimal("4500.00"),
            timeout_s=0.05,
        )
        self.assertEqual(result["price"], Decimal("4900.00"))
        self.assertEqual(result["decision"], "HOLD")