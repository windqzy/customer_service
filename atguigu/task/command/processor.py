"""
这个模块是TaskHandler里面的commandProcessor模块
作用：根据意图识别结果更新state状态数据
"""
from atguigu.domain.state import DialogueState, TaskInstance
from atguigu.plan.command import Command, StartFlowCommand, SetSlotsCommand, ResumeTaskCommand, CancelTaskCommand
from atguigu.task.flow.models import FlowCatalog, Flow
from atguigu.task.tasklifecycle.models import TaskEvent


class CommandProcessor():
    # commands:意图识别结果列表
    async def run(self, commands: list[Command],
                  state: DialogueState,
                  flow_catalog: FlowCatalog) -> list[TaskEvent]:
        events: list[TaskEvent] = []
        # 遍历commands
        for command in commands:
            event: TaskEvent = self._execute_command(command, state, flow_catalog)
            if event:
                events.append(event)
        return events

    # 处理command
    def _execute_command(self, command: Command, state: DialogueState,
                         flow_catalog: FlowCatalog) -> TaskEvent:
        # 根据不同类型command做不同处理
        if isinstance(command, StartFlowCommand):
            # 根据流程id 获取流程对象
            flow_id = command.flow
            flow: Flow = flow_catalog.get_flow_by_id(flow_id)
            # 根据流程id 获取流程里面  开始的步骤id
            start_step = flow.get_start_step()

            # TaskInstance对象 创建激活的任务
            task = TaskInstance(
                flow_id=flow_id,
                step_id=start_step.id
            )
            # 把创建的任务更新到state里面的active里面
            event: TaskEvent = state.tasks.start_task(task)
            return event

        # 设置槽位数据，不需要中文提示
        if isinstance(command, SetSlotsCommand):
            # 更新state里面active槽位
            state.tasks.active.slots.update(command.slots)
            return None

        if isinstance(command, ResumeTaskCommand):
            event: TaskEvent = state.tasks.resume_task(command.task_id)
            return event

        if isinstance(command, CancelTaskCommand):
            event: TaskEvent = state.tasks.cancel_task(command.task_id)
            return event
        raise TypeError(f'Unknown command type')


"""
第一层：建院初期（系统启动，全是静态规则）
体检中心刚开业，连个苍蝇都没有，我们要先定规矩。
YAML（院长手写的草稿本）： 院长在草纸上歪歪扭扭地写：“咱们搞个‘入职体检’。第一步抽血，第二步验尿，结束。”
FlowLoader（打字员）： 院长字太草了，打字员把草稿敲进电脑里。
FlowCatalog（《全院体检套餐白皮书》）： 最终打印出来的一本厚厚的大字典。放在大堂的玻璃柜里，不可修改。
Flow（某一个具体套餐）： 白皮书里的第一章：【入职体检套餐】。
FlowStep（具体的科室门）： 抽血室、B超室。
FlowSlot（体检单上的必填空白）： 血压（）、身高（）。
性光顿悟： 这一层全是“死物”，是打印出来的书。店里现在一个客人都没有。Flow 永远是一本书，它绝对不记录客人的名字！
第二层：客人进店（运行态产生，TaskInstance 登场）
现在，客人老王（用户）推门进来了。
用户说话： 老王捂着肚子大喊：“哎哟，我肚子疼，我要办入职！”
Planner（分诊台护士长 —— 大脑）： 护士长一听，脑子飞速一转，做出了决定。
Command（护士长开的【行动指令条】）： 护士长撕下一张便利贴，写上两句话丢给前台小妹：
start_flow: 给他上【入职体检套餐】！
set_slots: 备注上他【肚子疼】！
CommandProcessor（前台打单小妹）： 小妹接过便利贴，从抽屉里拿出一张全新的空白表格，夹在硬纸板夹子上。
★ TaskInstance（老王手里的【专属体检夹子】）： 这个极其重要！小妹把夹子塞进老王手里。
夹子上写着：
flow_id = 正在做【入职体检套餐】
step_id = 当前排队在【第一步：抽血室】
slots = 【肚子疼：是】
性光顿悟： TaskInstance 就是老王手里端着的那个“专属体检夹子”！ 夹子跟着老王走，上面记录了老王查到哪一步了，抽血出了什么结果。100 个客人进店，就有 100 个夹子，但柜台里的《体检套餐白皮书（Flow）》永远只有那 1 本！
第三层：推着客人走（FlowExecutor 苦力干活）
老王拿着夹子站在大厅发呆，不知道往哪走。
FlowExecutor（楼层无情引导员）： 这个人是个极度守规矩的“瞎子”。他根本不管老王是谁，他只做三个机械动作：
看夹子（看 TaskInstance）： 他一把抢过老王手里的夹子，看了一眼：“哦，你要做【入职体检】，当前在【第一步：抽血】。”
翻字典（找 Flow）： 他掏出那本厚厚的《白皮书》，翻到【入职体检】那一章，确认了一下第一步确实是抽血。
一脚踹进去（执行 Step）： 他一把将老王推进抽血室（Action），门一关。
改夹子进度： 抽完血，引导员拿笔在老王的夹子上把“第一步”划掉，写上 step_id = 第二步：B超。
如果老王抽血的时候，发现血压这栏已经填过了（slots 里有数据），引导员就会直接跳过量血压，一脚把他踹进下一个屋子。
终极一图流映射（直接保存在脑子里）
下次你代码写晕了，或者看日志报错了，直接套这个表：
源码里的高级词汇	豪华体检中心的大白话模型	它是干嘛的？
YAML / JSON	院长手写的草稿本	纯文本规则
Flow / Catalog	《体检套餐白皮书》	死规矩，全局唯一，不存私人信息
Planner	分诊台护士长	听客人的话，决定要干啥
Command	护士长手写的“行动便利贴”	决定这一下要改变什么状态
TaskInstance	老王手里端着的“专属体检表”	这是核心！记录老王走到了哪一步
slots	专属体检表上的“填空区”	记录老王真实的血压、身高、症状
FlowExecutor	楼层无情的引导员	看一眼老王的表，翻一眼白皮书，踹老王进下一个屋子




没问题！光用文字描述确实容易“脑补不出来”。

咱们这次彻底抛弃程序员的思维，用**“看话剧 / 电视台直播间”的体验感，再配合【文本结构图】**，让你像看电影一样，亲眼看到这几行代码在内存里是怎么运转的。

第一步：体验感代入 —— 电视台直播间

把你正在写的这套 AI 系统，想象成一个**“电视台的直播间”**。

1.  老王（用户）： 是电视机前的观众。
2.  TaskState（状态机）： 是后台导播间的**“画面切换台”**。
3.  TaskEvent（那4个类）： 是导播打印出来、递给前台主持人的**“提词卡片”**。
4.  大模型/话术引擎： 是前台的新闻主持人。

第二步：文本结构图 —— 导播间的“神级微操”

现在，老王打来热线电话，要求查“物流”（新任务 B）。 我们来看看你贴的那段 start_task 代码，在物理世界里到底长什么样：

       📥 【外界指令：开启新任务 B (查物流)】
                         │
                         ▼
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃         🖥️ 导播间 (TaskState.start_task)             ┃
┃                                                     ┃
┃  导播看了一眼当前的主屏幕 (if self.active:)         ┃
┃                                                     ┃
┣━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫
┃ 场景 1：屏幕有画面 ┃ 场景 2：屏幕是黑的 (else)          ┃
┃ (正播着 A: 退货)   ┃ (没有活跃任务)                     ┃
┣━━━━━━━━━━━━━━━━╋━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫
┃ ① 把 A(退货) 录像  ┃ ① 直接把 B(查物流) 推上主屏幕      ┃
┃    存入 [暂停硬盘] ┃                                    ┃
┃    (paused.append) ┃                                    ┃
┃                    ┃                                    ┃
┃ ② 把 B(查物流) 推上┃ ② 打印提词卡片：                   ┃
┃    主屏幕(active)  ┃    🎫【TaskStarted】             ┃
┃                    ┃    内容：任务 B                  ┃
┃ ③ 打印提词卡片：   ┃                                    ┃
┃    🎫【TaskSwitched】┃                                    ┃
┃    内容：旧=A, 新=B┃                                    ┃
┗━━━━━━━━┳━━━━━━━┻━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━┛
         │                      │
         └──────────┐           │
                    ▼           ▼
        📤 【输出口：飞出一张提词卡片 (TaskEvent)】

第三步：前台主持人的“看卡片说话”（闭环体验）

后台导播（TaskState）干完活了，飞出了一张卡片（return TaskSwitched 或 return TaskStarted）。

这才是这段代码的终极目的！

这张卡片通过系统，传到了前台新闻主持人（大模型/回复渲染器）的手里。主持人根本不知道后台导播刚才按了什么按钮，他只负责“看卡片说话”。

             🎫 飞来的提词卡片 (TaskEvent)
                         │
                         ▼
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃              🎙️ 前台新闻主持人 (话术引擎)             ┃
┃                                                     ┃
┃ 主持人低头看了一眼手里是什么类型的卡片 (TypeAlias)：    ┃
┃                                                     ┃
┃ 🔹 如果是 🎫【TaskStarted】卡片：                     ┃
┃    照念：“好的，现在为您开启【查物流】服务...”        ┃
┃                                                     ┃
┃ 🔹 如果是 🎫【TaskSwitched】卡片：                    ┃
┃    照念：“好的，已为您暂停【退货】，现在切换到【查物流】”┃
┃                                                     ┃
┃ 🔹 如果是 🎫【TaskResumed】卡片：                     ┃
┃    照念：“物流查完了，我们继续刚才的【退货】流程吧...”  ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

第四步：回头再看代码，瞬间破案

有了这个物理画面，我们再看你迷惑的那两行代码：

1. 为什么要有那四个小类（Started/Switched...）？ 因为后台导播操作完之后，必须把**“发生了什么事”**记录在纸上递出去。如果你只
return True，主持人拿到一张白纸，他就不知道该对观众说什么了。

2. 为什么要有 TaskEvent:TypeAlias = (A | B | C | D)？ 因为主持人（外层代码）接收卡片的时候，他需要一个统称。
TypeAlias 就是用来告诉电脑：“接下来飞过来的这张卡片（变量），虽然不知道具体是哪种情况，但它绝对逃不出这 4 种类型！” 它就像一个信封，里面装着 4
种可能的信纸。

3. TaskLifecycle 为什么只有 flow_id 和 task_id？ 因为主持人念稿子，只需要念名字（比如“查物流”、“退货”）。
他不需要知道老王的退货单里到底填了哪些详细信息（不需要整个 TaskInstance）。所以抽出了一个极简的
TaskLifecycle（名字标签）写在提词卡片上，减轻传输负担。

终极顿悟： 你之前懵，是因为你一直盯着**“内存数据怎么改”。 现在你跳出来，把它看成是一套“前后台通讯协议”**： TaskState
是哑巴，它只负责改数据；改完数据后，它必须生成一张小票（TaskEvent），甩给负责说话的模块，让系统表现得像一个高情商的人类。

这个图和体验感，在你脑子里跑通了吗？

"""
