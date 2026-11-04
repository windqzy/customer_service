"""
扫描：注册到字典里面
"""
from atguigu.task.action.custom.logistics_tracking import LogisticsTrackingAction
from atguigu.task.action.custom.lookup_order_status import LookupOrderStatusAction
from atguigu.task.action.registry import ActionRegistry

#todo 包扫描
def action_register(actionRegistry:ActionRegistry):
    actionRegistry.register_action(LogisticsTrackingAction())
    actionRegistry.register_action(LookupOrderStatusAction())