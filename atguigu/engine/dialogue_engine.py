"""
处理消息
"""
import time
import uuid
from pathlib import Path

from atguigu.domain.message import UserMessage, MessageType, ProcessResult, BotMessage
from atguigu.domain.state import DialogueState, Turn
from atguigu.plan.models import TurnPlan
from atguigu.plan.turn_planner import TurnPlanner
from atguigu.task.flow.loader import FlowLoader
from atguigu.task.flow.models import FlowCatalog


class DialogueEngine:

    def __init__(self, turn_planner: TurnPlanner):
        self.turn_planner = turn_planner

    async def handle_message(self, user_message: UserMessage,
                             dialogue_state: DialogueState) -> ProcessResult:
        # 1.准备当前会话和本轮对话记录
        # 获取最近的一次session
        # 获取不到，没有session，创建新的session
        # 获取到，判断session是否过期，过期创建新的session，没有过期继续使用当前的session
        # 如何判断是否过期：60分钟不活跃自动过期
        self._prepare_current_session(dialogue_state)

        # 2.判断是文本消息还是对象消息 MessageType判断
        if user_message.type == MessageType.TEXT:
            # 文本类型
            messages: list[BotMessage] = await self._handle_text_message(user_message, dialogue_state)
        else:
            # 对象类型
            messages: list[BotMessage] = await self._handle_object_message(user_message, dialogue_state)

        # 提交本轮记录，更新到state中去
        turn = Turn(
            turn_id=str(uuid.uuid4()),
            # 用户提问
            user_message=user_message,
            # #客服回复
            bot_message=messages
        )
        dialogue_state.shared.sessions[-1].turns.append(turn)

        # 返回处理结果
        return ProcessResult(
            sender_id=user_message.sender_id,
            message_id=user_message.message_id,
            messages=messages
        )

    def _prepare_current_session(self, state: DialogueState):
        # 1.准备当前会话和本轮对话记录
        # 获取最近的一次session
        # 获取不到，没有session，创建新的session
        # 获取到，判断session是否过期，过期创建新的session，没有过期继续使用当前的session
        # 如何判断是否过期：60分钟不活跃自动过期
        if not state.shared.sessions:
            # 获取不到当前session
            state.shared.create_session()
        else:  # 获取当前session
            current_session = state.shared.sessions[-1]
            # 判断当前的session是否过期 last_activity_at 最后一次活跃时间
            # 使用当前时间 - 最后一次活跃时间 大于60分钟 过期了
            # 当前时间 1970-01-01 秒
            now = time.time()
            if now - current_session.last_activity_at > 60 * 60:
                # 清空之前的任务
                state.clear_current_task()
                # 过期了 生成新的session
                state.shared.create_session()
            else:
                # 没过期 使用当前session
                # 更新last_activity_at 最后一次活跃时间
                current_session.last_activity_at = now

    # 处理文本类型消息的方法
    async def _handle_text_message(self, user_message: UserMessage, dialogue_state: DialogueState) -> list[BotMessage]:
        # 获取yaml的所有流程数据
        path = Path(__file__).parents[2] / 'flow_config' / 'user_flows.yml'
        flow_catalog: FlowCatalog = FlowLoader().load(path)
        # 1.调用llm进行意图识别
        # 识别文本消息执行哪个系统能力，任务流程，知识检索，闲聊
        turn_plan: TurnPlan = await self.turn_planner.plan(user_message=user_message,
                                                           flow_catalog=flow_catalog,
                                                           state=dialogue_state
                                                           )
        print(turn_plan)

        # 2.
        print('test')

    # 处理对象类型消息的方法
    async def _handle_object_message(self, user_message, dialogue_state) -> list[BotMessage]:
        pass
