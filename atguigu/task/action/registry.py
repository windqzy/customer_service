"""
创建字典：
注册action方法
获取action方法
"""
from atguigu.task.action.base import Action


class ActionRegistry:
    def __init__(self):
        #字典key 是Action的name属性值
        #字典value 是Action对象
        self.actions:dict[str, Action] = {}

    #1.向字典放数据(注册)
    def register_action(self, action: Action):
        self.actions[action.name] = action

    #2.从字典获取数据(根据name)
    def get_action(self, name: str) -> Action:
        return self.actions.get(name)
