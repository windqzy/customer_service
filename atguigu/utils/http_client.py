"""
httpx远程调用工具类
"""
import asyncio

from httpx import AsyncClient

# import requests
# requests.get("http://localhost:11434",)
# requests.post("http://localhost:11434")

# 并行调用方法 gather()


# 创建http_client
http_client: AsyncClient | None = None


# 两个方法
# 1.创建对象
def init_http_client():
    global http_client
    http_client = AsyncClient(timeout=20.0)


# 关闭对象
async def close_http_client():
    await http_client.aclose()


async def test():
    init_http_client()
    result = await http_client.get('http://localhost:18081/orders/A20260405003')
    print(result.json())
    await close_http_client()

if __name__ == '__main__':
    asyncio.run(test())

