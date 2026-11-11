"""
实现订单状态的查询

"""
from atguigu.conf.config import settings
from atguigu.domain.state import DialogueState
from atguigu.task.action.base import Action, ActionResult


class LookupOrderStatusAction(Action):
    name = "action_lookup_order_status"

    # 实现抽象方法
    async def run(self, state: DialogueState) -> ActionResult:
        # 获取订单编号
        order_number = state.tasks.active.slots.get('order_number')
        # 拼接远程地址
        url = f'{settings.commerce_api_base_url}/orders/{order_number}/status'
        # 远程调用
        response = await self.http_client.get(url)
        data = response.json().get('data')
        if not isinstance(data, dict) or not data:
            return ActionResult(slots_update={
                'order_status': '未知的订单状态',
                'order_summary': f'未查询到{order_number}的订单状态',
            })
        return ActionResult(
            slots_update={
                'order_status': data.get('status', '未知的订单状态'),
                'order_summary': data.get('status_desc', '未知的订单状态描述')
            }
        )
