"""
处理消息
"""
import time
import uuid
from dataclasses import asdict
from encodings import normalize_encoding
from pathlib import Path

from atguigu.chichat.chitchat import ChitChat
from atguigu.clarify.clarify_response import ClarifyResponse
from atguigu.domain.message import UserMessage, MessageType, ProcessResult, BotMessage
from atguigu.domain.state import DialogueState, Turn, FocusedObject
from atguigu.plan.command import SetSlotsCommand
from atguigu.plan.models import TurnPlan, TurnPlanValidationResult, ClarifyReason
from atguigu.plan.turn_plan_validator import TurnPlanValidator
from atguigu.plan.turn_planner import TurnPlanner
from atguigu.task.flow.loader import FlowLoader
from atguigu.task.flow.models import FlowCatalog, Flow
from atguigu.task.flow.steps import FlowStep, CollectSlotStep
from atguigu.task.handler import TaskHandler


class DialogueEngine:

    def __init__(self, turn_planner: TurnPlanner,
                 turn_planner_validator: TurnPlanValidator,
                 task_handler: TaskHandler,
                 chit_chat: ChitChat,
                 clarify_response: ClarifyResponse):
        self.turn_planner = turn_planner
        self.turn_planner_validator = turn_planner_validator
        self.task_handler = task_handler
        self.chit_chat = chit_chat
        self.clarify_response = clarify_response

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

        # 2.对意图识别结果进行校验
        validation_result: TurnPlanValidationResult = self.turn_planner_validator.validate(
            turn_plan=turn_plan,
            flow_catalog=flow_catalog,
            state=dialogue_state)

        # 3.如果校验失败，执行反问澄清组件
        if not validation_result.valid:
            assert validation_result.reason is not None, "校验失败时必须提供澄清原因"
            result = await self.clarify_response.handle(state=dialogue_state,
                                         user_message=user_message,
                                         reason=validation_result.reason)
            return result

        # 4.如果校验成功，根据识别结果，执行不同个系统能力组件
        if turn_plan.task:  # 执行任务流程处理器
            result: list[BotMessage] = await self.task_handler.handle(
                commands=turn_plan.task.commands,
                state=dialogue_state,
                flow_catalog=flow_catalog
            )

        elif turn_plan.knowledge:  # 执行知识检索处理器
            result = []  # TODO：知识检索尚未实现
        else:  # 执行闲聊
            result = await self.chit_chat.handle(
                state=dialogue_state,
                user_message=user_message,
            )
        return result

    # 处理对象类型消息的方法
    async def _handle_object_message(self, user_message:UserMessage,
                                     state:DialogueState) -> list[BotMessage]:
        path = Path(__file__).parents[2] / 'flow_config' / 'user_flows.yml'
        flow_catalog: FlowCatalog = FlowLoader().load(path)

        #1.把对象类型的消息封装到focused_object里面去
        state.shared.focused_object = FocusedObject(
            **asdict(user_message.object)
        )
        #2.判断是否匹配当前任务正在的槽位数据
        is_fill:bool = self.is_can_fill_slots(state,flow_catalog)
        if is_fill: #匹配
            # 获取槽位字典数据
            slots = {}
            if user_message.object.type == 'order':
                slots = {'order_number':user_message.object.id}
            if user_message.object.type == 'product':
                slots = {'product_id':user_message.object.id}
            #因为对象类型消息没有意图识别，无法直接调用TaskHandler方法
            #手动的那个创建意图识别结果对象，为了可以调用TaskHandler方法
            #槽位数据 SetSlotsCommand
            command = SetSlotsCommand(
                command = 'set_slots',
                slots = slots
            )


            #调用TaskHandler方法
            return await self.task_handler.handle(
                commands=[command],
                state=state,
                flow_catalog=flow_catalog
            )

        else: #无法匹配
            #收到的对象不能直接用于当前任务补槽，就先问用户“你想对这个对象做什么”。
            return await self.clarify_response.handle(state=state,
                                               user_message=user_message,
                                               reason=ClarifyReason.OBJECT_REQUIRES_INTENT)
    """
    第一轮：
    用户：“我要查物流。”
        ↓
    模型规划 start_flow(logistics_tracking)
        ↓
    创建物流任务
        ↓
    流程停在 collect(order_number)
        ↓
    机器人：“请告诉我你的订单号。”
        ↓
    保存任务进度
    
    第二轮：
    用户发送订单 1001 的卡片
        ↓
    记录 focused_object
        ↓
    确认当前正好需要 order_number
        ↓
    程序生成 set_slots(order_number="1001")
        ↓
    补齐参数，继续原来的物流任务
        ↓
    查询并回复物流结果
    

    """

    #用户刚发送的订单或商品卡片，能不能填入当前任务正在等待的那个槽位？
    def is_can_fill_slots(self, state:DialogueState,flow_catalog: FlowCatalog) -> bool:
        #1.当前是否有活跃任务
        active_task = state.tasks.active
        if not active_task:
            return False #此时没有活跃任务不知道用户想要干嘛 所以澄清回复
        #2.如果有活跃任务，活跃任务步骤类型应该是collect类型
        flow:Flow = flow_catalog.get_flow_by_id(active_task.flow_id)
        #获取active里面的step_id
        step_id = active_task.step_id
        #根据step_id获取步骤对象
        step:FlowStep = flow.get_step_by_id(step_id)

        #步骤类型 collect类型
        if not isinstance(step, CollectSlotStep):
            return False

        #如果需要订单号，对象类型消息order
        if step.slot_name == 'order_number' and state.shared.focused_object.type == 'order':
            return True
        #如果需要商品id，对象类型消息product
        if step.slot_name == 'product_id' and state.shared.focused_object.type == 'product':
            return True
        return False






