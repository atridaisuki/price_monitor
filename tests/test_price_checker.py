import unittest
from unittest.mock import AsyncMock, Mock, patch

from app import models
from app.tasks.price_checker import check_product_price


class CheckProductPriceTests(unittest.IsolatedAsyncioTestCase):
    async def test_check_product_price_updates_product_history_and_sends_notification(self):
        product = models.Product(
            id=1,
            name="Test Game",
            url="https://store.steampowered.com/app/1",
            platform="steam",
            target_price=50.0,
            current_price=80.0,
            user_qq="123456",
        )
        session = Mock()
        session.add = Mock()
        scraper = AsyncMock()
        scraper.scrape.return_value = 49.99

        with patch("app.tasks.price_checker.get_scraper", return_value=scraper), patch(
            "app.tasks.price_checker.NotificationService.publish_price_alert",
            AsyncMock(return_value=True),
        ) as publish_mock:
            result = await check_product_price(product, session)

        self.assertEqual(result.status, "success")
        self.assertEqual(result.current_price, 49.99)
        self.assertEqual(result.previous_price, 80.0)
        self.assertTrue(result.history_written)
        self.assertTrue(result.notification_sent)
        self.assertEqual(product.current_price, 49.99)
        self.assertIsNotNone(product.last_checked_time)

        session.add.assert_called_once()
        history = session.add.call_args.args[0]
        self.assertIsInstance(history, models.PriceHistory)
        self.assertEqual(history.product_id, 1)
        self.assertEqual(history.price, 49.99)

        publish_mock.assert_awaited_once()
        self.assertEqual(publish_mock.await_args.kwargs["trigger_reason"], "target_price_reached")
        self.assertEqual(publish_mock.await_args.kwargs["user_qq"], "123456")

    async def test_check_product_price_skips_notification_when_target_not_reached(self):
        product = models.Product(
            id=2,
            name="Expensive Game",
            url="https://store.steampowered.com/app/2",
            platform="steam",
            target_price=50.0,
            current_price=80.0,
        )
        session = Mock()
        session.add = Mock()
        scraper = AsyncMock()
        scraper.scrape.return_value = 79.99

        with patch("app.tasks.price_checker.get_scraper", return_value=scraper), patch(
            "app.tasks.price_checker.NotificationService.publish_price_alert",
            AsyncMock(return_value=True),
        ) as publish_mock:
            result = await check_product_price(product, session)

        self.assertEqual(result.status, "success")
        self.assertFalse(result.notification_sent)
        publish_mock.assert_not_awaited()


if __name__ == "__main__":
    unittest.main()
