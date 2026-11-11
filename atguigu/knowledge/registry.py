"""
这个模块 用于provider对象注册，注册到字典里面
"""
from atguigu.knowledge.provider import KnowledgeProvider


class KnowledgeProviderRegistry:
    # 传入所有provider对象列表，遍历得到每个provider对象
    def __init__(self,provider_objs:list[KnowledgeProvider]):
        self._provider_obj_id = {
            provider_obj.provider_id : provider_obj
             for provider_obj in provider_objs
        }

    # 根据key provider_id获取provider对象的方法
    def get_provider(self,provider_id:str) -> KnowledgeProvider:
        return self._provider_obj_id[provider_id]

# 【一句话】这个类是“查询窗口通讯录”：根据编号找到对应的 Provider 对象。
#
# 创建 Registry 时传入对象列表：
# [商品查询对象, 订单查询对象, FAQ对象, RAG对象]
#                  ↓ __init__ 中的字典推导式
# {'api.product': 商品查询对象, 'api.order': 订单查询对象, ...}
#
# get_provider('api.order') → 拿到订单查询对象
# 调用方再 await provider.run(...) → 才真正开始查询。
#
# 记住：Registry 负责“找到谁”，Provider 负责“怎么查”。
# 它保存的是传入的对象，不会自动创建对象或扫描包。
# 编号不存在会抛 KeyError；编号重复时，后面的对象会覆盖前面的。
