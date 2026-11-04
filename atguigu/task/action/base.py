"""
Action基类 name属性和抽象方法
数据模型
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from atguigu.domain.state import DialogueState


# 封装yaml文件action的名称
@dataclass
class ActionBase:
    action_name: str


# 封装action远程调用结果
@dataclass
class ActionResult:
    #定义一个叫 slots_update 的字典字段；创建对象时如果没有传值，就给它一个新的空字典。
    slots_update: dict[str,Any] = field(default_factory=dict)

@dataclass
class Action(ABC):
    name=''
    #抽象方法
    @abstractmethod
    async def run(self,state: DialogueState)->ActionResult:
        pass