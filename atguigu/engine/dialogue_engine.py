"""
处理消息
"""
from atguigu.domain.message import UserMessage
from atguigu.domain.state import DialogueState


class DialogueEngine:
    def handle_message(self, user_message:UserMessage, dialogue_state:DialogueState) -> UserMessage:
        #1.准备当前会话和本轮对话记录
        #获取最近的一次session
        #获取不到，没有session，创建新的session
        #获取到，判断session是否过期，过期创建新的session，没有过期继续使用当前的session
        #如何判断是否过期：60分钟不活跃自动过期
        pass