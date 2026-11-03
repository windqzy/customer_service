"""
根据CommandProcessor返回结果，生成不同中文提示
"""
from atguigu.domain.message import BotMessage
from atguigu.task.flow.models import FlowCatalog, Flow
from atguigu.task.tasklifecycle.models import TaskEvent, TaskStarted, TaskSwitched, TaskResumed, TaskCancelled


class TaskLifecycleResponder:
    async def responder(self,events:list[TaskEvent],
                        flow_catalog:FlowCatalog)->list[BotMessage]:
        messages:list[BotMessage] = []
        for event in events:
            bot_message:BotMessage = self.execute_task_event(event,flow_catalog)
            messages.append(bot_message)
        return messages

    def execute_task_event(self, event:TaskEvent,flow_catalog:FlowCatalog)->BotMessage:
        if isinstance(event,TaskStarted):
            # 根据flow_id获取流程名称
            flow:Flow = flow_catalog.get_flow_by_id(event.task.flow_id)
            return BotMessage(text=f"好的，现在开始执行 {flow.name}")

        if isinstance(event,TaskSwitched):
            previous: Flow = flow_catalog.get_flow_by_id(
                               event.previous.flow_id)
            current: Flow = flow_catalog.get_flow_by_id(
                                event.current.flow_id)
            return BotMessage(text=f"好的，先把{previous.name}暂停"
                                   f"现在开始执行{current.name}")

        if isinstance(event,TaskResumed):
            # 根据flow_id获取流程名称
            flow: Flow = flow_catalog.get_flow_by_id(event.task.flow_id)
            return BotMessage(text=f"好的，继续刚才 {flow.name}")

        if isinstance(event,TaskCancelled):
            # 根据flow_id获取流程名称
            flow: Flow = flow_catalog.get_flow_by_id(event.task.flow_id)
            return BotMessage(text=f"好的，把{flow.name}取消")

        raise TypeError("未知变化")