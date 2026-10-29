"""
这个模块 加载yaml文件，把yaml文件数据封装到FlowCatalog
"""
from pathlib import Path

import yaml

from atguigu.task.flow.models import FlowCatalog, FlowSlot, Flow
from atguigu.task.flow.steps import FlowStep


class FlowLoader:
    # 加载yaml文件
    def load(self, path: Path) -> FlowCatalog:
        # 读取yaml文件内容，返回文本
        flow_text = path.read_text(encoding='utf-8')
        # flow_text转换字典
        flow_dict = yaml.safe_load(flow_text)

        # 加载slots
        slots: dict[str, FlowSlot] = self._load_slots(flow_dict['slots'])

        # 加载flows
        flows: dict[str, Flow] = self._load_flows(flow_dict['flows'], slots)
        #catalog 就是 “目录、清单、分类汇总表”
        return FlowCatalog(
            flows=flows,
            slots=slots)

    # 加载槽位数据
    def _load_slots(self,
                    slots_data: dict[str, dict]) -> dict[str, FlowSlot]:
        # 定义字典，封装最终数据
        slots: dict[str, FlowSlot] = {}
        # 传入的字典遍历
        for slot_name, slot_data in slots_data.items():
            slots[slot_name] = FlowSlot(
                name=slot_name,
                **slot_data
            )
        return slots

    """
    
    class FlowSlot:
    name: str
    type: str = "any"
    label: str = ""
    description: str = ""

        flows
    │
    ├── "onboarding"    str
    │      → Flow(...)  object
    │
    ├── "order_status_query" 
    │      → Flow(...)
    │
    ├── "logistics_tracking"
    │      → Flow(...)
    │
    ├── "refund_request"
    │      → Flow(...)
    │
    ├── "similar_product_recommendation"
    │      → Flow(...)
    │
    └── "human_handoff"
           → Flow(...)
           
slots
│
├── "order_number"
│      → FlowSlot(...)
│
├── "order_status"
│      → FlowSlot(...)
│
├── "order_summary"
│      → FlowSlot(...)
│
├── "tracking_number"
│      → FlowSlot(...)
│
├── "logistics_company"
│      → FlowSlot(...)
│
├── "logistics_status"
│      → FlowSlot(...)
│
├── "product_id"
│      → FlowSlot(...)
│
├── "refund_reason"
│      → FlowSlot(...)
│
└── "recommendation_summary"
       → FlowSlot(...)
           
    """

    # 加载流程数据
    def _load_flows(self, flow_data: dict[str, dict],
                    slots: dict[str, FlowSlot]) -> dict[str, Flow]:
        # 定义空字典，封装最终数据
        flows: dict[str, Flow] = {}
        # 遍历flow_data流程字典数据
        for flow_id, flow_data in flow_data.items():
            # 加载槽位数据列表
            flow_slots: list[FlowSlot] = [
                # 从collect步骤获取slot_name
                ## 根据slot_name 到所有槽位字典，根据key获取对应对象
                slots[step['slot_name']]
                # 获取流程里面步骤列表
                for step in flow_data['steps']
                # 判断步骤类型 collect
                if step['type'] == 'collect'
            ]

            # 加载步骤数据
            steps: list[FlowStep] = [
                FlowStep.from_dict(flow_step)
                for flow_step in flow_data['steps']
            ]

            flow = Flow(
                id=flow_id,
                description=flow_data.get('description', ''),
                steps=steps,
                slots=flow_slots,
                name=flow_data.get('name', ''),
            )
            flows[flow_id] = flow
        return flows


if __name__ == "__main__":
    loader = FlowLoader()
    path = Path(__file__).parents[3] / 'flow_config' / 'user_flows.yml'

    res = loader.load(path)
    print(res)
