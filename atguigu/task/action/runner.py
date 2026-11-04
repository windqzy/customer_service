from atguigu.domain.state import DialogueState
from atguigu.task.action.base import ActionResult, ActionBase, Action
from atguigu.task.action.registry import ActionRegistry


class ActionRunner:
    def __init__(self, registry: ActionRegistry):
        self.registry = registry

    # 对外调用，由FlowExcutor调用的方法
    async def run(self, state: DialogueState,
                  action_base: ActionBase) -> ActionResult:
        # 1.从action_base对象获取action的name值
        action_name = action_base.action_name
        # 2.根据action的name值找到对应的action对象
        action: Action = self.registry.get_action(action_name)
        # 3.调用action对象的方法
        action_result = await action.run(state)
        # 4.返回结果
        return action_result
