from fastapi import FastAPI
from app.database import init_db
from app import models
from app.routers import products

app=FastAPI(title="Price Monitor")

# 注册 API 路由
app.include_router(products.router, prefix="/api")

@app.on_event("startup")
async def on_startup():
    await init_db()

@app.get("/")
def read_root():
    return {"Hello":"Price Monitor is Running"}