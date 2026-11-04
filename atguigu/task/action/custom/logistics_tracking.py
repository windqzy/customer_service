"""
查询物流
"""
from atguigu.conf.config import Settings, settings
from atguigu.domain.state import DialogueState
from atguigu.task.action.base import Action, ActionResult
from atguigu.utils.http_client import http_client


class LogisticsTrackingAction(Action):

    name = "action_lookup_logistics"

    #实现抽象方法
    async def run(self, state: DialogueState) -> ActionResult:
        #获取订单编号
        order_number = state.tasks.active.slots.get('order_number')
        #拼接远程地址
        url = f'{settings.commerce_api_base_url}/orders/{order_number}/logistics'
        #远程调用
        response = await http_client.get(url)
        data = response.json().get('data',f'未查询到{order_number}的物流信息')
        return ActionResult(
            slots_update={
                'logistics_company': data.get('logistics_company','未知的物流公司'),
                'tracking_number':data.get('tracking_number','未知的物流编号'),
                'logistics_status':data.get('status','未知的物流状态')
            }
        )

