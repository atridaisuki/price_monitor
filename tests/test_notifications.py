import json
import unittest
from unittest.mock import AsyncMock, patch

from app.notifications import NotificationService, PRICE_ALERT_CHANNEL


class FakePubSub:
    def __init__(self, messages):
        self._messages = messages
        self.subscribed_channel = None
        self.closed = False

    async def subscribe(self, channel):
        self.subscribed_channel = channel

    async def listen(self):
        for message in self._messages:
            yield message

    async def close(self):
        self.closed = True


class FakeRedis:
    def __init__(self, subscribers=1, pubsub=None):
        self.subscribers = subscribers
        self.pubsub_instance = pubsub
        self.published = []

    async def publish(self, channel, payload):
        self.published.append((channel, payload))
        return self.subscribers

    def pubsub(self):
        return self.pubsub_instance


class NotificationServiceTests(unittest.IsolatedAsyncioTestCase):
    async def test_publish_price_alert_uses_stable_payload(self):
        fake_redis = FakeRedis()

        with patch("app.notifications.get_redis", AsyncMock(return_value=fake_redis)):
            success = await NotificationService.publish_price_alert(
                product_id=1,
                product_name="Test Game",
                current_price=49.99,
                target_price=50.0,
                url="https://example.com/game",
                platform="steam",
                trigger_reason="manual_test",
                user_qq="123456",
            )

        self.assertTrue(success)
        self.assertEqual(len(fake_redis.published), 1)
        channel, payload = fake_redis.published[0]
        self.assertEqual(channel, PRICE_ALERT_CHANNEL)

        data = json.loads(payload)
        self.assertEqual(data["product_id"], 1)
        self.assertEqual(data["product_name"], "Test Game")
        self.assertEqual(data["platform"], "steam")
        self.assertEqual(data["trigger_reason"], "manual_test")
        self.assertEqual(data["user_qq"], "123456")
        self.assertIn("timestamp", data)

    async def test_subscribe_price_alerts_invokes_callback(self):
        message = {
            "type": "message",
            "data": json.dumps(
                {
                    "product_id": 1,
                    "product_name": "Test Game",
                    "platform": "steam",
                    "url": "https://example.com/game",
                    "current_price": 49.99,
                    "target_price": 50.0,
                    "trigger_reason": "target_price_reached",
                    "user_qq": "123456",
                    "timestamp": "2026-04-08T12:00:00",
                }
            ),
        }
        pubsub = FakePubSub([message])
        fake_redis = FakeRedis(pubsub=pubsub)
        callback = AsyncMock()

        with patch("app.notifications.get_redis", AsyncMock(return_value=fake_redis)):
            await NotificationService.subscribe_price_alerts(callback)

        self.assertEqual(pubsub.subscribed_channel, PRICE_ALERT_CHANNEL)
        callback.assert_awaited_once()
        self.assertTrue(pubsub.closed)


if __name__ == "__main__":
    unittest.main()
