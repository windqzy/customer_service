"""
闲聊
"""
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate

from atguigu.domain.message import UserMessage, BotMessage
from atguigu.domain.state import DialogueState
from atguigu.prompts.history_builder import HistoryBuilder
from atguigu.prompts.loader import load_prompt
from atguigu.utils.llm_client import llm


class ChitChat:
    async def handle(self, user_message: UserMessage,
                     state: DialogueState) -> list[BotMessage]:
        # 1.加载提示词
        prompt_text = load_prompt('chitchat_respond')
        # 把一段带占位符的文本，变成一个可以填入数据的“提示词模板对象”。
        prompt = PromptTemplate.from_template(template=prompt_text,
                                              template_format='jinja2'
                                              )
        # 2.创建调用链
        chain = prompt | llm | StrOutputParser()

        # 3.调用
        response = await chain.ainvoke(
            {
                'history': HistoryBuilder.build(state.shared.sessions[-1].turns),
                'user_message': HistoryBuilder.render_user_message(user_message)
            }
        )
        return [BotMessage(text=response)]
