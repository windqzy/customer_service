import time
import uuid
from asyncio import current_task
from dataclasses import dataclass, field
from atguigu.domain.message import UserMessage, BotMessage
from atguigu.task.tasklifecycle.models import TaskSwitched, TaskStarted, TaskLifecycle, TaskCancelled, TaskResumed


# 一轮对话，一个问题对应一个或者多个回答
@dataclass
class Turn:
    turn_id: str
    # 用户提问
    user_message: UserMessage
    # 客服回复
    bot_message: list[BotMessage] = field(default_factory=list)


# 会话对象
@dataclass
class Session:
    # session的id，区别不同session
    session_id: str
    # session创建时间戳
    started_at: float
    # session最后一次活跃时间
    last_activity_at: float
    # 关闭时间
    closed_at: float | None = None
    # 每个session会话多轮对话
    turns: list[Turn] = field(default_factory=list)


# 对象类型消息
@dataclass
class FocusedObject:
    type: str  # order   product
    id: str
    title: str | None = None
    attributes: dict = field(default_factory=dict)


# 三种能力都有数据：任务流程、知识问答、闲聊
@dataclass
class SharedState:
    # 对象类型消息
    focused_object: FocusedObject | None = None
    # 多个会话数据
    sessions: list[Session] = field(default_factory=list)

    def create_session(self):
        now = time.time()
        session = Session(
            session_id=str(uuid.uuid4()),
            started_at=now,
            last_activity_at=now,
        )
        self.sessions.append(session)


# 某个任务流程步骤相关数据
@dataclass
class TaskInstance:
    # 流程id，对应yaml文件  refund_request
    flow_id: str
    # 步骤id ,比如 start
    step_id: str | None = None
    # 当前任务id
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    # task_id: str | None = None
    # 槽位数据字典  {order_number : a10098765}
    slots: dict = field(default_factory=dict)

    def to_task_lifecycle(self) -> TaskLifecycle:
        return TaskLifecycle(
            flow_id=self.flow_id,
            task_id=self.task_id
        )


# 任务流程特有数据，流程步骤数据
@dataclass
class TaskState:
    # 当前正在运行（活跃）的任务
    active: TaskInstance | None = None
    # 中断（暂停）的任务
    paused: list[TaskInstance] = field(default_factory=list)

    def start_task(self, task):
        # 判断当前是否活跃任务
        if self.active:
            previous_task = self.active.to_task_lifecycle()
            # 把当前活跃任务暂停
            self.paused.append(self.active)

            # 把新任务变成活跃任务
            self.active = task
            current_task = self.active.to_task_lifecycle()

            return TaskSwitched(
                previous=previous_task,
                current=current_task
            )
        else:
            # 把新任务变成活跃任务
            self.active = task
            return TaskStarted(
                task=self.active.to_task_lifecycle()
            )

    def resume_task(self, task_id):
        resume_task_event = None
        resume_task = None
        # 从中断列表中获取到要恢复的任务
        for index, paused_task in enumerate(self.paused):
            if paused_task.task_id == task_id:
                # 从中断列表获取出来任务
                resume_task = self.paused.pop(index)
                resume_task_event = resume_task.to_task_lifecycle()
                break
        # 如果没有找到要恢复的额任务
        if resume_task is None:
            raise ValueError(f'要恢复的任务不存在')

        # 判断当前是否是存在活跃任务
        if self.active:
            previous_task = self.active.to_task_lifecycle()
            # 暂停当前的活跃任务
            self.paused.append(self.active)
            # 把恢复的任务变成活跃的任务
            self.active = resume_task
            return TaskSwitched(
                previous=previous_task,
                current=resume_task_event
            )
        else:
            # 当前没有活跃的任务，直接把恢复的任务变成活跃任务
            self.active = resume_task
            return TaskResumed(
                task=resume_task_event
            )

    def cancel_task(self, task_id):
        # 取消的任务：可能是当前的活跃任务，可能在中断列表里面
        # 1.判断当前的活跃任务是否是要取消的任务
        if self.active is not None and self.active.task_id == task_id:
            cancel_task = self.active.to_task_lifecycle()
            # 如果是，把当前活跃任务取消
            self.active = None
            return TaskCancelled(
                task=cancel_task
            )
        # 如果当前活跃任务不是要取消的任务，到中断列表获取要取消的任务
        else:
            # 把要取消的任务从中断列表中删除
            # paused:list[TaskInstance]
            for paused_task in self.paused:
                if paused_task.task_id == task_id:
                    cancel_task = paused_task.to_task_lifecycle()
                    self.paused.remove(paused_task)
                    return TaskCancelled(
                        task=cancel_task
                    )
        raise ValueError("取消的任务不存在")


@dataclass
class DialogueState:
    # 用户id
    sender_id: str
    # 三种能力都有数据：任务流程、知识问答、闲聊
    shared: SharedState = field(default_factory=SharedState)
    # 任务流程特有数据，流程步骤数据
    tasks: TaskState = field(default_factory=TaskState)

    # 清空当前执行的任务
    def clear_current_task(self):
        self.shared.focused_object = None
        self.tasks.active = None
        self.tasks.paused.clear()


"""
第一步：体验感代入 —— 导播间的“撕毁订单”行动
外界指令： 撕毁编号为 task_id 的订单。
导播的难题： 导播手里有两个地方存着订单。一个是**主屏幕（active）上正挂着的那份；另一个是暂停文件夹（paused 列表）**里压着的一堆。
导播的动作逻辑： 必须先看主屏幕是不是这个订单，如果不是，再去翻暂停文件夹。找到后，直接撕掉，并给前台主持人递一张名为 🎫【TaskCancelled】 的提词卡片。
第二步：文本结构图 —— 导播的“寻宝与撕毁”流程
code
Text
📥 【外界指令：取消指定的任务 (task_id)】
                         │
                         ▼
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃                🖥️ 导播间 (TaskState.cancel_task)                 ┃
┃                                                                 ┃
┃ 导播接到指令，开始找这份该死的订单：                               ┃
┃                                                                 ┃
┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫
┃ 🔍 第一找：看一眼主屏幕     ┃ 🔍 第二找：翻垃圾桶(暂停文件夹)      ┃
┃ (if active 且 id 匹配)     ┃ (else / for 循环遍历 paused 列表)  ┃
┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━╋━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫
┃ ① 确认主屏幕上就是这个订单！┃ ① 在主屏幕没找到，开始一张张翻     ┃
┃                            ┃    暂停文件夹(self.paused)。       ┃
┃ ② 动作：一把扯下屏幕画面    ┃                                    ┃
┃    (self.active = None)    ┃ ② 找到了那张单子 (if id 匹配)！    ┃
┃                            ┃                                    ┃
┃ ③ 写提词卡：抽出订单的名字  ┃ ③ 动作：把它从文件夹里抽出来撕掉   ┃
┃    (cancel_task = ...)     ┃    (self.paused.remove)          ┃
┃                            ┃                                    ┃
┃ ④ 递出卡片：                ┃ ④ 写提词卡：抽出订单的名字         ┃
┃    🎫【TaskCancelled】     ┃    (cancel_task = ...)           ┃
┃    内容：被取消的是 A       ┃                                    ┃
┃                            ┃ ⑤ 递出卡片：                       ┃
┃                            ┃    🎫【TaskCancelled】           ┃
┃                            ┃    内容：被取消的是 A              ┃
┗━━━━━━━━━━━━━┳━━━━━━━━━━━━━━┻━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━┛
              │                             │
              └──────────────┐              │
                             ▼              ▼
           📤 【输出口：飞出一张提词卡片 (TaskEvent)】
第三步：前台主持人的“看卡片说话”（闭环体验）
前台新闻主持人（大模型/话术引擎）接到了导播飞出来的这张卡片。
code
Text
🎫 飞来的提词卡片 (TaskEvent)
                         │
                         ▼
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃              🎙️ 前台新闻主持人 (话术引擎)             ┃
┃                                                     ┃
┃ 主持人低头一看，哎哟，是一张红色的取消卡片：            ┃
┃                                                     ┃
┃ 🔹 接到 🎫【TaskCancelled】卡片：                     ┃
┃    不管后台是怎么撕的单子，主持人只需要念出名字：        ┃
┃    “好的，已经为您**取消了**【某某】服务流程。您还有什么需要帮忙的吗？” ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛



第二步：文本结构图 —— 导播的“完美置换”流程
code
Text
📥 【外界指令：恢复指定的旧任务 (task_id)】
                         │
                         ▼
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃                🖥️ 导播间 (TaskState.resume_task)                 ┃
┃                                                                 ┃
┃ 🟢 阶段一：翻箱倒柜找单子 (for loop in self.paused)                ┃
┃                                                                 ┃
┃  导播在暂停文件夹里疯狂翻找...                                      ┃
┃  ► 找到了！把这单子抽出来拿在手里 (`pop`)，并抄下它的名字 (`resume_task_event`) ┃
┃  ► 如果翻遍了都没找到？直接报警！(`raise ValueError`)                 ┃
┃                                                                 ┃
┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫
┃ 🟢 阶段二：看主屏幕，准备狸猫换太子 (if self.active:)                ┃
┃                                                                 ┃
┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫
┃ 📺 场景 1：主屏幕正忙着       ┃ 📺 场景 2：主屏幕是空的            ┃
┃ (正播着 A: 查天气)          ┃ (没人在办业务)                     ┃
┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━╋━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫
┃ ① 抄下主屏幕 A 的名字        ┃ ① 手里拿的旧单子(退货)，直接推上   ┃
┃    (`previous_task`)       ┃    主屏幕！(`self.active = ...`) ┃
┃                            ┃                                    ┃
┃ ② 把 A(查天气) 粗暴地塞进    ┃ ② 写提词卡：                      ┃
┃    暂停文件夹(`append`)    ┃    🎫【TaskResumed】             ┃
┃                            ┃    内容：恢复了【退货】            ┃
┃ ③ 把手里拿的旧单子(退货)     ┃                                    ┃
┃    推上主屏幕(`self.active`)┃                                    ┃
┃                            ┃                                    ┃
┃ ④ 写提词卡：                ┃                                    ┃
┃    🎫【TaskSwitched】      ┃                                    ┃
┃    内容：旧=查天气, 新=退货 ┃                                    ┃
┗━━━━━━━━━━━━━┳━━━━━━━━━━━━━━┻━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━┛
              │                             │
              └──────────────┐              │
                             ▼              ▼
           📤 【输出口：飞出一张提词卡片 (TaskEvent)】
第三步：前台主持人的“看卡片说话”（闭环体验）
前台主持人（话术引擎）接到了导播飞出来的卡片。
code
Text
🎫 飞来的提词卡片 (TaskEvent)
                         │
                         ▼
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃              🎙️ 前台新闻主持人 (话术引擎)             ┃
┃                                                     ┃
┃ 🔹 如果接到 🎫【TaskSwitched】卡片：                  ┃
┃    主持人念：“好的，为您暂停【查天气】，我们继续刚才的【退货】。”┃
┃                                                     ┃
┃ 🔹 如果接到 🎫【TaskResumed】卡片：                   ┃
┃    主持人念：“好的，我们继续刚才的【退货】流程。”       ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

"""
