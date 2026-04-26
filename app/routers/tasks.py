"""定时任务相关的 API 路由"""
from fastapi import APIRouter

from app.notifications import NotificationService
from app.tasks.price_checker import check_all_prices

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("/check-prices")
async def trigger_price_check():
    """手动触发价格检查任务。"""
    summary = await check_all_prices()
    return {
        "message": "价格检查任务执行完成",
        "status": "completed",
        "summary": summary,
    }


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
