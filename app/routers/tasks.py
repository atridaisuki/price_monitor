"""定时任务相关的 API 路由"""
from fastapi import APIRouter

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
