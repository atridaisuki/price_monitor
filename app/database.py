from sqlmodel import SQLModel
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
import os

DATABASE_URL=os.getenv("DATABASE_URL","postgresql+asyncpg://admin:mypassword@localhost:5432/monitor_db")
DB_INIT_MODE = os.getenv("DB_INIT_MODE", "migrate_only").lower()

#连接池
#echo打印sql日志，future使用SQLAlchemy 2.0风格
#可添加pool_size连接池大小，max_overflow最大溢出连接数，pool_timeout等待可用连接的超时时间
engine=create_async_engine(DATABASE_URL,echo=True,future=True)

# 创建 session maker（用于定时任务）
async_session_maker = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def init_db():
    if DB_INIT_MODE != "create_all":
        print(f"跳过 SQLModel.create_all，当前 DB_INIT_MODE={DB_INIT_MODE}，请优先使用 Alembic 迁移初始化数据库")
        return

    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

async def get_session() -> AsyncSession:
    async with async_session_maker() as session:
        yield session
