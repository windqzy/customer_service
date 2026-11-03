"""
这个模块用于数据的渲染
"""
from jinja2 import Template

from atguigu.domain.message import BotMessage
from atguigu.domain.state import DialogueState
from atguigu.task.response.models import ResponseTemplate, ResponseMode


class ResponseRender:
    async def render(self, template: ResponseTemplate, state: DialogueState) -> BotMessage:
        if template.mode == ResponseMode.STATIC:
            # 创建template对象
            template = Template(template.text)
            """
          订单{{ slots.order_number }}
          当前状态是：{{ slots.order_status }}。
          {{ slots.order_summary }}"
            """
            render_text = template.render(slots=state.tasks.active.slots)
            return BotMessage(text=render_text)
        if template.mode == ResponseMode.REPHRASE:
            pass  # 调llm直接修改
        else:
            pass  # 调llm直接生成

"""
你不需要把每一个需要渲染的变量单独提取出来，
只需要把整个 slots 字典传给模板引擎，
它就能根据变量路径自动找到对应的值。

这其实是一个很重要的理解：模板负责定义“在哪里填什么”，
字典负责提供“可以填什么”。
"""

