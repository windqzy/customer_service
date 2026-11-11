"""
这个模块 调用llm，把provider返回结果修改
"""
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate

from atguigu.domain.message import BotMessage, UserMessage
from atguigu.domain.state import DialogueState
from atguigu.knowledge.provider import KnowledgeChunk
from atguigu.prompts.history_builder import HistoryBuilder
from atguigu.prompts.loader import load_prompt
from langchain_core.language_models import BaseChatModel


class KnowledgeResponer:
    def __init__(self, llm: BaseChatModel):
        self.llm = llm

    async def run(self,chunks:list[KnowledgeChunk],
                  state:DialogueState,
                  user_message:UserMessage)->BotMessage:
        # 加载提示词模版
        prompt_text = load_prompt("knowledge_respond")
        prompt = PromptTemplate.from_template(prompt_text,
                                     template_format="jinja2")
        # 创建调用链
        chain = prompt | self.llm | StrOutputParser()
        # 调用
        result = await chain.ainvoke({
            # provider返回结果
            "knowledge_content":"\n".join(
                chunk.content for chunk in chunks
            ),
            "history":HistoryBuilder.build(state.shared.sessions[-1].turns),
            "user_message":HistoryBuilder.render_user_message(user_message),
        })

        return BotMessage(text=result)

# 【一句话】把 Provider 查到的资料，交给大模型整理成用户能读懂的回复。
# 医院类比：Provider 取回报告，Responder 根据报告和你的问题组织讲解。
#
# run 接收三个东西：
# ├── chunks：查到的资料片段
# ├── state：从中读取当前会话的历史问答
# └── user_message：用户这次问了什么
#
# 资料片段用换行拼起来 + 历史问答 + 当前问题
#                     ↓ 填入 knowledge_respond 提示词模板
#                   prompt → llm → StrOutputParser()
#                     ↓             把模型输出转成字符串
#                  BotMessage(text=result)
#
# | 表示串起处理步骤；await chain.ainvoke(...) 表示异步执行这条链。
# 记住：Provider 负责“查资料”，这里负责“根据资料组织回复”，不负责检索。
# 当前返回的是一个 BotMessage，不是消息列表；读取历史前需要已有会话。
