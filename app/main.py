from fastapi import FastAPI
from app.database import init_db
from app import models
from app.routers import products, tasks
from app.tasks import start_scheduler, shutdown_scheduler
from app.redis_client import close_redis

app=FastAPI(title="Price Monitor")

# 注册 API 路由
app.include_router(products.router, prefix="/api")
app.include_router(tasks.router, prefix="/api")

@app.on_event("startup")
async def on_startup():
    await init_db()
    start_scheduler()  # 启动定时任务

@app.on_event("shutdown")
async def on_shutdown():
    shutdown_scheduler()  # 关闭定时任务
    await close_redis()  # 关闭 Redis 连接

@app.get("/")
def read_root():
    return {"Hello":"Price Monitor is Running"}