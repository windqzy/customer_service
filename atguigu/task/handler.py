"""
这个模块作用：执行任务流程，调用三个组件实现过程
commandProcessor
TaskLifecycle
FlowExecutor
"""
from atguigu.domain.message import BotMessage
from atguigu.domain.state import DialogueState
from atguigu.plan.command import Command
from atguigu.task.command.processor import CommandProcessor
from atguigu.task.flow.executor import FlowExecutor
from atguigu.task.flow.models import FlowCatalog
from atguigu.task.tasklifecycle import task_lifecycle_responder
from atguigu.task.tasklifecycle.models import TaskEvent
from atguigu.task.tasklifecycle.task_lifecycle_responder import TaskLifecycleResponder


class TaskHandler:
    def __init__(self, command_processor: CommandProcessor,
                 task_lifecycle_responder: TaskLifecycleResponder,
                 flow_executor: FlowExecutor):
        self.command_processor = command_processor
        self.task_lifecycle_responder = task_lifecycle_responder
        self.flow_executor = flow_executor

    # 这个方法在engine层调用，实现任务流程处理
    async def handle(self, commands: list[Command],
                     state: DialogueState,
                     flow_catalog: FlowCatalog) -> list[BotMessage]:
        # 1.commandProcessor更新state数据
        events: list[TaskEvent] = await self.command_processor.run(commands=commands
                                                                   , state=state,
                                                                   flow_catalog=flow_catalog)

        # 2.根据commandProcessor返回的结果，调用TaskLifecycleResponder生成中文的提示
        messages: list[BotMessage] = await self.task_lifecycle_responder.responder(events=events,
                                                                                   flow_catalog=flow_catalog)
        # 3.调用FlowExecutor推进步骤实现
        bot_messages: list[BotMessage] = await self.flow_executor.run_task(state=state, flow_catalog=flow_catalog)

        # 4.合并2和3的结果
        messages.extend(bot_messages)
        # 5.返回结果
        return messages
