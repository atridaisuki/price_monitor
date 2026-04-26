import unittest
from unittest.mock import AsyncMock, patch

import nonebot

nonebot.init()


class PriceAlertPluginTests(unittest.IsolatedAsyncioTestCase):
    async def test_send_price_alert_uses_user_qq_when_present(self):
        from bot.src.plugins import price_alert

        fake_bot = AsyncMock()
        data = {
            "product_name": "Test Game",
            "current_price": 49.99,
            "target_price": 50.0,
            "platform": "steam",
            "url": "https://example.com/game",
            "user_qq": "123456",
        }

        with patch.object(price_alert, "get_bot", return_value=fake_bot), patch.object(
            price_alert, "SUPERUSERS", ["999999"]
        ):
            await price_alert.send_price_alert(data)

        fake_bot.send_private_msg.assert_awaited_once()
        self.assertEqual(fake_bot.send_private_msg.await_args.kwargs["user_id"], 123456)

    async def test_send_price_alert_falls_back_to_superusers(self):
        from bot.src.plugins import price_alert

        fake_bot = AsyncMock()
        data = {
            "product_name": "Test Game",
            "current_price": 49.99,
            "target_price": 50.0,
            "platform": "steam",
            "url": "https://example.com/game",
            "user_qq": None,
        }

        with patch.object(price_alert, "get_bot", return_value=fake_bot), patch.object(
            price_alert, "SUPERUSERS", ["111111", "222222"]
        ):
            await price_alert.send_price_alert(data)

        self.assertEqual(fake_bot.send_private_msg.await_count, 2)
        self.assertEqual(fake_bot.send_private_msg.await_args_list[0].kwargs["user_id"], 111111)
        self.assertEqual(fake_bot.send_private_msg.await_args_list[1].kwargs["user_id"], 222222)


if __name__ == "__main__":
    unittest.main()
