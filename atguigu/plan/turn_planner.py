"""
这个模块作用：对文本类型消息调用llm意图识别
"""
import json
from dataclasses import asdict

from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from openai.types.conversations import conversation

from atguigu.domain.message import UserMessage
from atguigu.domain.state import DialogueState
from atguigu.plan.models import TurnPlan
from atguigu.prompts import history_builder
from atguigu.prompts.history_builder import HistoryBuilder
from atguigu.prompts.loader import load_prompt
from atguigu.task.flow.models import FlowCatalog, Flow
from atguigu.utils.llm_client import llm


class TurnPlanner:
    # 用户消息 user_message:UserMessage
    # 流程数据 flow_catalog:FlowCatalog
    # 历史数据 state:DialogueState
    async def plan(self, user_message: UserMessage,
                   flow_catalog: FlowCatalog,
                   state: DialogueState) -> TurnPlan:
        # 加载提示词
        # 加载提示词文件内容
        prompt_text = load_prompt('turn_plan')
        # 提示词读取字符串内容，创建langchain提示词对象
        prompt = PromptTemplate.from_template(prompt_text, template_format="jinja2")
        # 创建调用链条
        chain = prompt | llm | JsonOutputParser()
        # 调用llm实现
        # 准备调用llm需要的数据
        rendered_user_message = HistoryBuilder.render_user_message(user_message)
        # 历史记录
        turns = state.shared.sessions[-1].turns
        conversation_history = HistoryBuilder.build(turns)
        #任务流程
        task_state_json = json.dumps(
            asdict(state.tasks) if state.tasks else None,
        )
        #yaml中所有流程的数据
        flows:dict[str,Flow] = flow_catalog.flows
        # 遍历所有流程字典，得到每个flow数据，从每个流程数据获取流程id，name，description
        # flows_json = [ {
        #     "id":flow.id,
        #     "name":flow.name,
        #     "description":flow.description,
        # } for flow in  flows.values()]

        flows_json = [
            {k: v for k, v in asdict(flow).items()
             if k != 'steps'
             }
            for flow in flows.values()
        ]

        # 聚焦对象，封装对象类型消息
        focused_object_json = json.dumps(asdict(state.shared.focused_object)
                                         if state.shared.focused_object else None)

        result = await chain.ainvoke(input={
            "user_message": rendered_user_message,
            "conversation_history":conversation_history,
            "focused_object_json":focused_object_json,
            "task_state_json":task_state_json,
            "knowledge_intents_json":{},#todo 后续完善
            "flows_json":flows_json
        })

        #把llm结果转换成TurnPlan对象
        return TurnPlan.from_dict(result)
