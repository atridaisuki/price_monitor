"""调试用 API 路由，生产环境可不注册"""
from fastapi import APIRouter

from app.notifications import NotificationService

router = APIRouter(prefix="/debug", tags=["debug"])


@router.post("/test-notification")
async def test_notification():
    """测试通知系统（发送测试消息）"""
    success = await NotificationService.publish_price_alert(
        product_id=0,
        product_name="测试商品",
        current_price=99.99,
        target_price=100.00,
        url="https://example.com",
        platform="test",
        trigger_reason="manual_test",
        user_qq=None,
    )

    return {
        "message": "测试通知已发送" if success else "测试通知发送失败",
        "success": success,
    }
