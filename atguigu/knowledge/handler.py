"""
这个模块 对外调用knowledge方法
"""
from atguigu.domain.message import BotMessage, UserMessage
from atguigu.domain.state import DialogueState
from atguigu.knowledge.intents import KNOWLEDGE_INTENTS
from atguigu.knowledge.provider import KnowledgeProvider, KnowledgeChunk
from atguigu.knowledge.registry import KnowledgeProviderRegistry
from atguigu.knowledge.responder import KnowledgeResponer


class KonwledgeHandler:
    def __init__(self,knowledge_registry:KnowledgeProviderRegistry,
                 knowledge_responer:KnowledgeResponer):
        self.knowledge_registry = knowledge_registry
        self.knowledge_responer = knowledge_responer

    """
    1 获取意图识别结果  list[str]   ["product_info",refund_policy]
    2 根据意图识别结果值，找到答案位置 provider_ids值 可能有多个 去重处理
    3 根据provider_ids值 找到对应provider对象 
    4 调用provider对象的业务方法得到结果
    5 把provider返回结果，调用llm修改，修改之后最终返回用户
    """
    # 参数：意图识别结果 list[str]
    async def handle(self,intents_knowledge:list[str],
                     state:DialogueState,
                     user_message:UserMessage)->list[BotMessage]:
        # 1 获取意图识别结果
        # list[str]["product_info", "faq.default", "rag.default"]
        # 2 根据意图识别结果值，找到答案位置 provider_ids值
        # 可能有多个 去重处理
        provider_ids:list[str] = self.get_provider_ids(intents_knowledge)

        # ["api.product", "faq.default", "rag.default"]

        # 3 根据provider_ids值 找到对应provider对象
        # 4 调用provider对象的业务方法得到结果
        final_result:list[KnowledgeChunk] = []
        for provider_id in provider_ids:
            # 找到对应provider对象, KnowledgeProviderRegistry
            provider:KnowledgeProvider \
                =  self.knowledge_registry.get_provider(provider_id)
            # 调用provider对象的业务方法得到结果
            chunks = await provider.run(state=state,user_message=user_message)
            final_result.extend(chunks)

        # 5 把provider返回结果，调用llm修改，修改之后最终返回用户
        bot_message:BotMessage = await self.knowledge_responer.run(
            chunks=final_result,
            state=state,user_message=user_message)
        return [bot_message]


    # 2 根据意图识别结果值，找到答案位置 provider_ids值
    # 可能有多个 去重处理
    def get_provider_ids(self,
                  intents_knowledge:list[str])->list[str]:
        # ["product_info", "refund_policyt"]
        final_result:list[str] = []
        for intent in intents_knowledge:
            final_result.extend(KNOWLEDGE_INTENTS[intent].provider_ids)
        # 去重处理 final_result
        # set可以去重，set里面数据是无序
        return list(set(final_result))

        # 可以去重，有序的
        # list(dict.fromkeys(final_result))

# 【一句话】Handler 是知识咨询的“协调员”：安排查资料，再安排生成回复。
# 医院类比：秦志颖提出咨询 → 协调员找对应窗口取资料 → 交给讲解人员回答。
#
# 已识别的意图，例如 refund_policy
#       ↓ get_provider_ids：查 intents 配置，取出来源编号并去重
# faq.default、rag.default
#       ↓ Registry：按编号找到 Provider 对象
#       ↓ Provider.run：逐个查询，extend 合并资料片段
#       ↓ Responder.run：把全部资料整理成一条回复
#       ↓ return [bot_message]：用列表返回这条回复
#
# __init__ 接收“窗口通讯录”和“回复生成器”，保存起来供 handle 使用。
# 注意：这里接收的是意图编号，不是 Provider 编号；它不负责识别意图。
# 当前会依次调用所有选中的 Provider，并非 FAQ 查不到才调用 RAG。
# set 只负责来源编号去重，不保证顺序，也不会去重查询结果的内容。
