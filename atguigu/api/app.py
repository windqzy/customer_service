"""
使用fastapi构建接口
"""
from contextlib import AsyncExitStack, asynccontextmanager

from fastapi import FastAPI

from atguigu.api.chat_router import chat_router
from atguigu.utils.database import init_db_engine, close_db_engine
from atguigu.utils.http_client import init_http_client, close_http_client
from atguigu.utils.llm_client import init_llm


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动：创建应用共享资源，保存到 app.state。
    # ExitStack 保证退出时依次释放资源，初始化中途失败也会清理已创建的资源。
    async with AsyncExitStack() as stack:
        engine, session_factory = init_db_engine()
        stack.push_async_callback(close_db_engine, engine)
        app.state.async_session_factory = session_factory

        http_client = init_http_client()
        stack.push_async_callback(close_http_client, http_client)
        app.state.http_client = http_client
        app.state.llm = await stack.enter_async_context(init_llm())

        # 到这里初始化完成，FastAPI 才开始接收请求；退出后释放资源。
        yield

app = FastAPI(lifespan=lifespan)
app.include_router(chat_router)
