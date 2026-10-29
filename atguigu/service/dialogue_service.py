"""
业务逻辑层，推进业务实现
首先调用 repository层 操作数据库
其次 调用engine层 处理消息
"""

from atguigu.domain.message import UserMessage, ProcessResult
from atguigu.domain.state import DialogueState
from atguigu.engine.dialogue_engine import DialogueEngine
from atguigu.repository.dialogue_repository import DialogueRepository


class DialogueService:
    def __init__(self, repository: DialogueRepository,
                 engine: DialogueEngine):
        self.repository = repository
        self.engine = engine

    async def run(self, user_message: UserMessage,
                  ) -> ProcessResult:
        # 1.从UserMessage里面得到获取到用户id，调用respository层方法，根据用户id查询用户历史的处理数据
        sender_id = user_message.sender_id
        dialogue_state: DialogueState = await self.repository.load(sender_id)
        # 2.调用engine引擎层中的方法处理消息，返回处理结果
        process_result: ProcessResult = await self.engine.handle_message(user_message, dialogue_state)
        # 3.保存最新的数据到state中
        await self.repository.save_or_update(dialogue_state)
        # 4.返回处理结果
        return process_result
