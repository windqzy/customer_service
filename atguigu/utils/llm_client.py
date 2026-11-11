"""
这个模块，创建llm的对象
"""
import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from langchain.chat_models import init_chat_model
from langchain_core.language_models import BaseChatModel
from openai import DefaultHttpxClient, DefaultAsyncHttpxClient

from atguigu.conf.config import settings

# 由 lifespan 创建模型；退出时关闭模型使用的同步、异步 HTTP 客户端。
@asynccontextmanager
async def init_llm() -> AsyncIterator[BaseChatModel]:
    with DefaultHttpxClient() as http_client:
        async with DefaultAsyncHttpxClient() as http_async_client:
            yield init_chat_model(
                model=settings.LLM_MODEL,
                model_provider='openai',
                api_key=settings.llm_api_key,
                base_url=settings.llm_base_url,
                reasoning_effort='none',  # GPT-5.4 使用 temperature 时需要设为 none
                temperature=0,
                http_client=http_client,
                http_async_client=http_async_client,
            )

# 保留本地 Ollama 配置参考；切回时需调整 init_llm 内的模型创建与客户端管理，
# 并将 LLM_MODEL 改回 qwen3:14b，不再创建模块级全局 llm。
# llm = init_chat_model(
#     model=settings.LLM_MODEL,
#     model_provider="ollama",
#     base_url="http://localhost:11434",
#     temperature=0
# )
if __name__ == "__main__":
    async def test():
        async with init_llm() as llm:
            print((await llm.ainvoke('你是谁')).content)

    asyncio.run(test())
