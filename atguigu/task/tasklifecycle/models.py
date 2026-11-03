from dataclasses import dataclass
from typing_extensions import TypeAlias


@dataclass
class TaskLifecycle:
    flow_id:str
    task_id:str

#1.start_flow 新开始任务
@dataclass
class TaskStarted:
    task:TaskLifecycle
    #好的，现在开始 物流查询==flow_id

#2.切换
@dataclass
class TaskSwitched:
    previous:TaskLifecycle
    current:TaskLifecycle
    #好的，先把...暂停 现在开始...

#3.resume_task
@dataclass
class TaskResumed:
    task:TaskLifecycle
    #好的，继续刚才的...任务

#4.cancel_task
@dataclass
class TaskCancelled:
    task:TaskLifecycle
    #好的，取消...任务

TaskEvent:TypeAlias = (TaskStarted|TaskSwitched|TaskResumed|TaskCancelled)
