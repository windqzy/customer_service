import asyncio
import json
from abc import ABC, abstractmethod
from dataclasses import dataclass

from atguigu.conf.config import settings
from atguigu.domain.message import UserMessage
from atguigu.domain.state import DialogueState
from atguigu.utils.http_client import http_client


# 1 封装最终结果的类
@dataclass
class KnowledgeChunk:
    content: str = ""

# 创建基类
class KnowledgeProvider(ABC):
    provider_id:str=""

    @abstractmethod
    async def run(self,state:DialogueState,
                  user_message:UserMessage)->list[KnowledgeChunk]:
        pass

# 查询商品信息
# api.product
class ApiProductProvider(KnowledgeProvider):
    provider_id = "api.product"

    async def run(self,state:DialogueState,
                  user_message:UserMessage)->list[KnowledgeChunk]:
        # 1 从state里面获取商品类型对象里面id值
        focused_object = state.shared.focused_object
        if focused_object is None:
            return [KnowledgeChunk(content="请提供商品id",)]
        product_id = focused_object.id

        # 2 远程调用，根据商品id得到商品信息
        url = f"{settings.commerce_api_base_url}/products/{product_id}"
        response = await http_client.get(url)
        data = response.json().get("data","没有信息")
        result = json.dumps(data,ensure_ascii=False)
        return [KnowledgeChunk(content=result)]


# api.order
# 需求：查询订单信息，需要调用两个远程接口实现 ：查询订单状态 和 查询物流信息
# 把调用两个接口过程，使用并行方式实现  ，使用httpx封装的方法直接实现
class ApiOrderProvider(KnowledgeProvider):
    provider_id = "api.order"

    async def run(self,state:DialogueState,
                  user_message:UserMessage)->list[KnowledgeChunk]:
        # 1 从state里面获取订单类型对象里面id值
        focused_object = state.shared.focused_object
        if focused_object is None:
            return [KnowledgeChunk(content="请提供订单id", )]
        order_id = focused_object.id

        # 2 远程调用
        # 需要调用两个远程接口实现 ：查询订单状态 和 查询物流信息
        url1 = f"{settings.commerce_api_base_url}/orders/{order_id}/status"
        url2 = f"{settings.commerce_api_base_url}/orders/{order_id}/logistics"
        # 并行调用
        # 注意: gather返回值，和传入参数顺序有关的
        order_info,logistics_info = await asyncio.gather(
            http_client.get(url1), # 订单状态
            http_client.get(url2), # 物流信息
        )

        # 得到结果，返回
        result = json.dumps({
            "order_info":order_info.json().get("data","未知"),
            "logistics_info":logistics_info.json().get("data","未知")
        },ensure_ascii=False)
        return [KnowledgeChunk(content=result)]


# faq.default
"""
    1 把常见问题和对应答案存储数据库里面，
    # mysql数据库   向量数据库
    2 把用户提问到数据库匹配，如果可以匹配到返回问题对应答案
"""
class FAQProvider(KnowledgeProvider):
    provider_id = 'faq.default'

    async def run(self,
                       user_message: UserMessage,
                       state: DialogueState, ) -> list[KnowledgeChunk]:
        # TODO
        return [KnowledgeChunk(content="未检索到相关问题")]

# rag.default
"""
    之前完成智库项目
    调用智库项目接口实现
"""
class RAGProvider(KnowledgeProvider):
    provider_id = 'rag.default'

    async def run(self,
                       user_message: UserMessage,
                       state: DialogueState, ) -> list[KnowledgeChunk]:
        # RAG知识库查询知识接口（TODO）
        return [KnowledgeChunk(content="未检索到相关信息")]

# 【一句话】这个文件负责：去不同的地方查资料，再把资料带回来。
#
# 秦志颖去医院查报告：
#   就诊卡 → 查询窗口 → 查医院系统 → 拿到报告纸条
# 对应代码：
#   focused_object.id → Provider.run() → 请求接口 → KnowledgeChunk(content=资料)
#
# 这些类各管什么？
# KnowledgeProvider：所有查询窗口的统一规定——都要有 run 方法。
# ├── ApiProductProvider：查商品信息。
# ├── ApiOrderProvider：同时查订单状态和物流。
# ├── FAQProvider：查常见问题，目前还没实现查询。
# └── RAGProvider：查知识库，目前还没实现查询。
# KnowledgeChunk：装查询资料的“小纸条”，content 就是纸条上的文字。
#
# 以订单查询为例：
# 取订单号 → 同时查状态、查物流 → 合并结果 → 转成文字 → 装进纸条列表返回。
# asyncio.gather 就是“同时安排两个查询，等结果回来”。
# 没有订单对象时，直接返回“请提供订单id”。
#
# 记住：intents.py 是“去哪查”的目录，provider.py 是“实际去查”的工作人员。
# 调试时只盯三个东西：id 对不对 → 接口返回什么 → content 最后装了什么。
