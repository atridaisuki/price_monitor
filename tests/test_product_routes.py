import unittest
from unittest.mock import AsyncMock, Mock

from app import models, schemas
from app.routers.products import create_product, update_product


class FakeExecuteResult:
    def __init__(self, product):
        self._product = product

    def scalar_one_or_none(self):
        return self._product


class ProductRouteTests(unittest.IsolatedAsyncioTestCase):
    async def test_create_product_persists_user_qq(self):
        session = Mock()
        session.add = Mock()
        session.commit = AsyncMock()
        session.refresh = AsyncMock()

        payload = schemas.ProductCreate(
            name="Test Game",
            url="https://store.steampowered.com/app/1",
            platform="steam",
            target_price=50.0,
            user_qq="123456",
        )

        product = await create_product(payload, session)

        self.assertIsInstance(product, models.Product)
        self.assertEqual(product.user_qq, "123456")
        session.add.assert_called_once_with(product)
        session.commit.assert_awaited_once()
        session.refresh.assert_awaited_once_with(product)

    async def test_update_product_updates_user_qq(self):
        existing_product = models.Product(
            id=1,
            name="Test Game",
            url="https://store.steampowered.com/app/1",
            platform="steam",
            target_price=50.0,
            user_qq=None,
        )
        session = Mock()
        session.execute = AsyncMock(return_value=FakeExecuteResult(existing_product))
        session.commit = AsyncMock()
        session.refresh = AsyncMock()

        payload = schemas.ProductUpdate(user_qq="654321")

        product = await update_product(1, payload, session)

        self.assertEqual(product.user_qq, "654321")
        session.commit.assert_awaited_once()
        session.refresh.assert_awaited_once_with(existing_product)


if __name__ == "__main__":
    unittest.main()
