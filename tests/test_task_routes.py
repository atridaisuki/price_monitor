import unittest
from unittest.mock import AsyncMock, patch

from app.routers.tasks import test_notification, trigger_price_check


class TaskRouteTests(unittest.IsolatedAsyncioTestCase):
    async def test_trigger_price_check_returns_summary(self):
        summary = {
            "total_products": 1,
            "success_count": 1,
            "failure_count": 0,
            "history_count": 1,
            "notification_count": 1,
            "results": [],
        }

        with patch("app.routers.tasks.check_all_prices", AsyncMock(return_value=summary)):
            response = await trigger_price_check()

        self.assertEqual(response["status"], "completed")
        self.assertEqual(response["summary"], summary)

    async def test_test_notification_uses_manual_trigger_reason(self):
        with patch(
            "app.routers.tasks.NotificationService.publish_price_alert",
            AsyncMock(return_value=True),
        ) as publish_mock:
            response = await test_notification()

        self.assertTrue(response["success"])
        self.assertEqual(response["message"], "测试通知已发送")
        self.assertEqual(publish_mock.await_args.kwargs["trigger_reason"], "manual_test")
        self.assertIsNone(publish_mock.await_args.kwargs["user_qq"])


if __name__ == "__main__":
    unittest.main()
