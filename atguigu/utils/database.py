"""
操作数据库的工具类
"""
import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from atguigu.conf.config import settings

# 1.创建两个变量
# 引擎对象
engine: AsyncEngine | None = None
# session会话:工厂获取session对象
async_session_factory: async_sessionmaker[AsyncSession] = None


# 两个方法
# 1.创建engine和async_session对象
def init_db_engine():
    global engine, async_session_factory
    # 创建engine对象
    engine = create_async_engine(
        settings.database_url,  # 必须
        echo=True,  # 可选 测试使用
    )
    # 创建async_session对象，通过工厂方式来创建
    async_session_factory = async_sessionmaker(engine,
                                       expire_on_commit=False)


# 2.关闭方法
async def close_db_engine():
    await engine.dispose()

#测试方法
async def test():
    #初始化
    init_db_engine()
    #获取session会话,从工厂中获取一个对象
    async with async_session_factory() as session:
        #执行
        result = await session.execute(text("select 1"))
        print(result.fetchone())
    await close_db_engine()
if __name__ == '__main__':
    asyncio.run(test())



