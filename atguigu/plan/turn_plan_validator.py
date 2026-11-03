"""
这个模块作用：对文本消息意图识别结果进行校验
"""
from atguigu.domain.state import DialogueState
from atguigu.plan.command import Command, StartFlowCommand, ResumeTaskCommand, CancelTaskCommand
from atguigu.plan.models import TurnPlan, TurnPlanValidationResult, ClarifyReason, TaskTurnPlan
from atguigu.task.flow.models import FlowCatalog


class TurnPlanValidator:
    # 意图识别结果：turn_plan:TurnPlan
    # 所有流程数据 flow_catalog
    def validate(self, turn_plan: TurnPlan,
                 flow_catalog: FlowCatalog,
                 state: DialogueState) -> TurnPlanValidationResult:
        active_tracks: list[str] = []
        # 1.判断意图识别之后，是否识别到内容
        if turn_plan.task is not None:
            active_tracks.append("task")

        if turn_plan.knowledge is not None:
            active_tracks.append("knowledge")

        if turn_plan.chitchat is not None:
            active_tracks.append("chitchat")

        if not active_tracks:  # 什么方向都没有识别到
            return TurnPlanValidationResult(
                valid=False,
                reason=ClarifyReason.MISSING_TRACK
            )
        # 2.如果识别到内容，识别方向是否大于1个
        if len(active_tracks) > 1:
            return TurnPlanValidationResult(
                valid=False,
                reason=ClarifyReason.MULTIPLE_TRACKS
            )
        # 3.如果识别到只有一个
        track = active_tracks[0]
        # 4.判断一个方向的类型
        if track == "task":
            return self._validation_task(turn_plan.task,
                                         flow_catalog,
                                         state)
        if track == "knowledge":
            return self._validation_knowledge(turn_plan)

        return TurnPlanValidationResult(
            valid=True
        )

    def _validation_task(self, task: TaskTurnPlan,
                         flow_catalog: FlowCatalog,
                         state: DialogueState) -> TurnPlanValidationResult:
        # 1. TaskTurnPlan获取commands列表
        if task.commands is None:
            return TurnPlanValidationResult(
                valid=False,
                reason=ClarifyReason.MISSING_TASK_COMMANDS
            )
        for command in task.commands:
            # 如果是开始流程start_flow 看流程id在yaml中是否存在
            if isinstance(command, StartFlowCommand):
                flow_id = command.flow
                if flow_id not in flow_catalog.flows:
                    return TurnPlanValidationResult(
                        valid=False,
                        reason=ClarifyReason.INVALID_TASK_COMMAND
                    )

            # 如果是恢复流程resume_task 看流程id在pause 和 yaml中是否存在
            if isinstance(command, ResumeTaskCommand):
                # 获取恢复任务id
                task_id = command.task_id
                # 从中断列表中获取所有任务id，变成新列表[1,2,3]
                all_paused_task_id = [paused.task_id for paused in state.tasks.paused]
                if task_id not in all_paused_task_id:
                    return TurnPlanValidationResult(
                        valid=False,
                        reason=ClarifyReason.INVALID_TASK_COMMAND
                    )
            # 如果是取消流程cancel_task，看流程在active和pause中是否存在
            if isinstance(command, CancelTaskCommand):
                # 获取任务id
                task_id = command.task_id
                # 从中断列表中获取所有任务id，变成新列表[1,2,3]
                all_task_id = [paused.task_id for paused in state.tasks.paused]
                # 从活跃任务获取任务id
                if state.tasks.active:
                    all_task_id.append(state.tasks.active.task_id)

                if task_id not in all_task_id:
                    return TurnPlanValidationResult(
                        valid=False,
                        reason=ClarifyReason.INVALID_TASK_COMMAND
                    )

        return TurnPlanValidationResult(
            valid=True
        )

    # todo
    def _validation_knowledge(self):
        return TurnPlanValidationResult(
            valid=True
        )
