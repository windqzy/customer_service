"""
这个模块作用：对文本消息意图识别结果进行校验
"""
from atguigu.domain.state import DialogueState
from atguigu.plan.command import Command, StartFlowCommand, ResumeTaskCommand, CancelTaskCommand
from atguigu.plan.models import TurnPlan, TurnPlanValidationResult, ClarifyReason, TaskTurnPlan
from atguigu.task.flow.models import FlowCatalog


class TurnPlanValidator:
    # 意图识别结果：turn_plan:TurnPlan
    # 所有流程数据 flow_catalog:FlowCatalog
    def validate(self,turn_plan:TurnPlan,
                 flow_catalog:FlowCatalog,
                 state:DialogueState)->TurnPlanValidationResult:
        active_tracks:list[str] = []
        # 判断TurnPlan识别到方向是哪个
        if turn_plan.task is not None:
            active_tracks.append("task")

        if turn_plan.knowledge is not None:
            active_tracks.append("knowledge")

        if turn_plan.chitchat is not None:
            active_tracks.append("chitchat")

        # # 1 判断意图识别之后，是否识别内容
        if not active_tracks: # 什么没有识别到，校验失败
            return TurnPlanValidationResult(
                    valid=False,
                    reason=ClarifyReason.MISSING_TRACK
                )
        # 2 如果识别到内容，识别方向是否大于1个
        if len(active_tracks)>1:
            return TurnPlanValidationResult(
                valid=False,
                reason=ClarifyReason.MULTIPLE_TRACKS
            )

        # 3 如果识别方式只有 1 个
        track = active_tracks[0]
        # 4 判断一个方向类型，，
        # 如果任务流程
        if track == "task":
            return self._validation_task(
                turn_plan.task,
                flow_catalog,
                state
            )

        # 如果知识检索
        if track == "knowledge":
            return self._validation_knowledge()

        return TurnPlanValidationResult(
            valid=True,
        )

    # 任务流程校验
    def _validation_task(self,task:TaskTurnPlan,
                flow_catalog:FlowCatalog,
                state:DialogueState)->TurnPlanValidationResult:
        # 1 TaskTurnPlan获取commands列表
        if not task.commands:
            return TurnPlanValidationResult(
                valid=False,
                reason=ClarifyReason.INVALID_TASK_COMMAND)

        # 2 commands列表遍历，得到每个command，判断每个command类型
        for command in task.commands:
            # 1 start_flow
            # {"command": "start_flow", "flow": "<flow_id>"},
            if isinstance(command,StartFlowCommand):
                # 判断flow流程id 在yaml文件是否存在 flow_catalog
                flow_id = command.flow
                if flow_id not in flow_catalog.flows:
                    return TurnPlanValidationResult(
                        valid=False,
                        reason=ClarifyReason.INVALID_TASK_COMMAND
                    )

            # 2 resume_task
            # {"command": "resume_task", "task_id": "<task_id>"},
            ## 任务恢复前提条件：在中断列表paused有暂停任务
            if isinstance(command,ResumeTaskCommand):
                # 获取恢复任务id
                task_id = command.task_id
                # 从中断列表获取所有任务id ，变成新列表 [1,2,3]
                all_paused_task_id = [
                     paused.task_id
                    for paused in state.tasks.paused
                ]
                # 判断恢复任务id 在 中断列表是否存在
                if task_id not in all_paused_task_id:
                    return TurnPlanValidationResult(
                        valid=False,
                        reason=ClarifyReason.INVALID_TASK_COMMAND
                    )

            # 3 cancel_task
            if isinstance(command,CancelTaskCommand):
                task_id = command.task_id
                # 把中断列表里面任务id获取出来
                all_task_id = [
                    paused.task_id
                    for paused in state.tasks.paused
                ]
                # 从活跃任务获取任务id
                if state.tasks.active:
                    all_task_id.append(state.tasks.active.task_id)
                # 判断
                if task_id not in all_task_id:
                    return TurnPlanValidationResult(
                        valid=False,
                        reason=ClarifyReason.INVALID_TASK_COMMAND
                    )
        return TurnPlanValidationResult(
            valid=True,
        )

    # todo
    def _validation_knowledge(self):
        return TurnPlanValidationResult(
            valid=True,
        )

