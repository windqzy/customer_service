from atguigu.domain.message import UserMessage, BotMessage
from atguigu.domain.state import DialogueState
from atguigu.task.flow.links import FlowStepLink, ConditionalLink, FallbackLink
from atguigu.task.flow.models import Flow, FlowCatalog
from atguigu.task.flow.steps import FlowStep, StartFlowStep, CollectSlotStep, ResponseFlowStep, ActionFlowStep, \
    EndFlowStep
from atguigu.task.response import response_render
from atguigu.task.response.response_render import ResponseRender


class FlowExecutor:
    def __init__(self, response_render: ResponseRender):
        self.response_render = response_render

    async def run_task(self, state: DialogueState,
                       flow_catalog: FlowCatalog) -> list[BotMessage]:
        # 1.定义返回的数据
        bot_messages: list[BotMessage] = []
        # 2.判断当前是否有活跃任务
        if not state.tasks.active:
            return bot_messages  # 没有活跃任务，直接返回空

        # 2.如果有活跃任务，获取当前activw里面的步骤，根据不同的步骤类型，做不同的步骤处理
        for _ in range(100):
            # 获取当前active里面的步骤对象
            ##根据flow_id 获取flow对象
            flow: Flow = flow_catalog.get_flow_by_id(state.tasks.active.flow_id)
            ##根据step_id 获取步骤对象
            step: FlowStep = flow.get_step_by_id(state.tasks.active.step_id)
            # 根据不同的步骤类型，做不同处理
            """
            start本身什么也不错，为了推进下一步
            下一步：有条件跳转
                    无条件跳转
            """
            if isinstance(step, StartFlowStep):
                self._run_next_step(step, state)
                continue

            """
            在commandProcessor模块中，如果llm识别槽位数据，向state里面的active中设置
            collect：收集槽位数据
            实现：
            1.从active获取槽位数据
            2.如果active可以获取到，推进到下一步
            3.如果active获取不到，从对象消息获取，如果对象消息可以获取到，推进到下一步
            4.如果active和对象消息中都获取不到，给用户返回提示信息
            """
            if isinstance(step, CollectSlotStep):
                # 调用方法，从active或者对象消息获取槽位数据
                # 返回bool，如果可以获取到槽位数据返回True，如果获取不到返回False
                has_slots: bool = await self._run_collect_slots(step, state, bot_messages)
                if has_slots:  # True
                    self._run_next_step(step, state)
                    continue
                else:  # False
                    return bot_messages

            """
            action:调用具体业务方法，调用中台系统接口
            1.根据yaml文件action属性值，找到对应action对象
            2.调用对应action对象方法，实现远程调用得到结果
            3.返回查询结果 放到slots里面，方便下一步进行渲染
            """
            if isinstance(step, ActionFlowStep):
                action_name = step.action
                # todo
                # 推进下一步
                self._run_next_step(step, state)
                continue
            """
            response步骤：渲染数据，组装给用户返回数据
            这个步骤一般在action步骤后面，对action执行的结果进行渲染
            渲染数据的技术：jinja2
            """
            if isinstance(step, ResponseFlowStep):
                # 调用response_render中的方法进行渲染
                message: BotMessage = await self.response_render.render(
                    step.template,
                    state
                )
                # 放入bot_messages列表中
                bot_messages.append(message)
                self._run_next_step(step, state)
                continue

            if isinstance(step, EndFlowStep):
                # 清空active
                state.tasks.active = None
                # 返回前面步骤组装的结果
                return bot_messages

    # 推进到下一步
    def _run_next_step(self, step: FlowStep, state: DialogueState):
        next_step_id = self._get_next_step(step.next, state)
        state.tasks.active.step_id = next_step_id

    async def _run_collect_slots(self, step: CollectSlotStep, state: DialogueState,
                                 bot_messages: list[BotMessage]) -> bool:
        # 1.从state里面active里面先获取槽位数据
        slots: dict = state.tasks.active.slots
        # 根据slot_name到字典获取
        slot_value = slots.get(step.slot_name)

        # 2.如果获取不到，就去对象消息中获取，从对象消息中获取槽位数据更新state里面
        if not slot_value:
            self._get_slot_data_from_object_message(step, state)
        # 3.如果获取不到，则返回false，设置提示信息
        slot_value = state.tasks.active.slots.get(step.slot_name)
        if not slot_value:
            # 把提示信息设置到bot_messages里面去
            # 调用渲染方法
            message: BotMessage = await self.response_render.render(
                step.template,
                state
            )
            bot_messages.append(message)
            return False
        else:
            return True

    def _get_next_step(self, next: list[FlowStepLink], state: DialogueState) -> str:
        # 如果next里面是无条件跳转的情况
        if len(next) == 1:
            return next[0].target
        # 有条件跳转
        for link in next:
            # if then 判断if表达式是否成立
            if isinstance(link, ConditionalLink):
                has_slots = bool(eval(link.condition, {},
                                      {'slots': state.tasks.active.slots}))
                if has_slots:
                    return link.target
                continue
            # else
            if isinstance(link, FallbackLink):
                return link.target

    # 从对象消息中获取槽位数据，获取到了更新到state中
    def _get_slot_data_from_object_message(self, step, state):
        # 从state里面FocusedObject获取对象类型消息
        if not state.shared.focused_object:
            return

        # 如果focused_object里面有对象类型消息，槽位数据获取出来
        if step.slot_name == 'order_number' and step.shared.focused_object.type == 'order':
            # 设置到state里面去  state.shared.focused_object.id 这个就是对应的订单号
            state.tasks.active.slots.update({step.slot_name: state.shared.focused_object.id})
        # 此时的id对应商品id
        if step.slot_name == 'product_id' and step.shared.focused_object.type == 'product':
            state.tasks.active.slots.update({step.slot_name: state.shared.focused_object.id})


"""
这段代码是整个对话系统中**最硬核、最像“永动机”**的一部分。
如果你看前面那些 TaskState 觉得是“静态的仓库管理”，那么这个 FlowExecutor 就是一列**“一旦启动，不撞南墙不回头的高铁列车”**。
这列高铁的唯一使命，就是沿着铁轨（YAML 剧本），一站一站地往下开，直到遇到红灯（需要用户输入），或者到达终点！配合文本结构图，把这列疯狂的高铁给你画出来！
第一步：体验感代入 —— 疯狂的“自动闯关外挂”
把你写的这个对话系统，想象成一个**“文字冒险闯关游戏”**。
老王（用户）： 是电脑前的玩家。
YAML（FlowCatalog）： 是游戏地图。
TaskState.active： 记录了老王当前卡在哪个房间（比如第3关）。
FlowExecutor（你贴的这段代码）： 是一个**“自动挂机脚本”**！
这个“自动挂机脚本”的设计理念极其霸道：只要能往下走，就疯狂往下走，绝对不停！直到缺装备（缺 Slot）走不动了，才停下来等老王输入。
第二步：文本结构图 —— 自动挂机脚本的“无限循环”
这段代码最灵魂的地方，就是那个 for _ in range(100):。为什么是 100？因为怕地图写错了导致死循环，这叫“防暴毙机制”。
我们来看看这个外挂在循环里是怎么踢门的：
📥 【启动外挂：老王当前在某关某室 (active.step_id)】
                         │
                         ▼
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃                  🤖 自动挂机脚本 (FlowExecutor)                  ┃
┃                                                                 ┃
┃ 🔄 【开启循环，极限推图 (for _ in range 100)】                     ┃
┃                                                                 ┃
┃ 👁️ 看一眼当前在哪个房间？(获取 step)                               ┃
┃                                                                 ┃
┃ 🚪 遇到 5 种不同类型的房间，脚本做出不同的动作：                     ┃
┃                                                                 ┃
┃ 🟢 房间 1：【Start (起点室)】                                    ┃
┃    脚本动作：什么都不干，直接踢开下一扇门！(`_run_next_step`)      ┃
┃    状态：继续循环 (continue 🔄)                                  ┃
┃                                                                 ┃
┃ 🟡 房间 2：【Collect (收费站 / 槽位收集)】 ⚠️全场唯一卡脖子的地方！ ┃
┃    脚本动作：搜老王的包（查 state），看有没有过路费（槽位数据）。  ┃
┃    ┣━ 💰 有钱 (True)：交费，踢开下一扇门！(continue 🔄)           ┃
┃    ┗━ ❌ 没钱 (False)：停止推图！给老王弹个窗：“请交钱！”        ┃
┃       状态：退出循环，交还控制权！(return bot_messages 📤)       ┃
┃                                                                 ┃
┃ 🔵 房间 3：【Action (打怪室 / 后端接口)】                        ┃
┃    脚本动作：调用系统大招把怪秒了，把掉落的装备捡进包里(slots)。   ┃
┃    状态：踢开下一扇门，继续循环 (continue 🔄)                    ┃
┃                                                                 ┃
┃ 🟣 房间 4：【Response (发广播室 / 渲染回复)】                    ┃
┃    脚本动作：拿大喇叭喊一句“老王牛逼，爆了把屠龙刀”(渲染消息)。    ┃
┃    状态：把话塞进列表，踢开下一扇门，继续循环 (continue 🔄)      ┃
┃                                                                 ┃
┃ 🏁 房间 5：【End (通关终点室)】                                  ┃
┃    脚本动作：把老王的通关记录清空 (`active = None`)，打完收工。  ┃
┃    状态：彻底退出循环！(return bot_messages 📤)                  ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
"""
