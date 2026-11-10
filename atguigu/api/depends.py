from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from atguigu.chichat.chitchat import ChitChat
from atguigu.clarify.clarify_response import ClarifyResponse
from atguigu.engine.dialogue_engine import DialogueEngine
from atguigu.plan.turn_plan_validator import TurnPlanValidator
from atguigu.plan.turn_planner import TurnPlanner
from atguigu.repository.dialogue_repository import DialogueRepository
from atguigu.service.dialogue_service import DialogueService
# from atguigu.task.action.builder import action_register
from atguigu.task.action.builder import auto_action_register
from atguigu.task.action.registry import ActionRegistry
from atguigu.task.action.runner import ActionRunner
from atguigu.task.command.processor import CommandProcessor
from atguigu.task.flow.executor import FlowExecutor
from atguigu.task.handler import TaskHandler
from atguigu.task.response.response_render import ResponseRender
from atguigu.task.tasklifecycle.task_lifecycle_responder import TaskLifecycleResponder
from atguigu.utils.database import async_session_factory


# 注入session
async def get_sesssion() -> AsyncSession:
    async with async_session_factory() as session:
        yield session


# 注入repository对象
async def get_dialogue_repository(session: AsyncSession = Depends(get_sesssion)) -> DialogueRepository:
    return DialogueRepository(
        session=session
    )


# 注入turn_planner对象
async def get_turn_planner() -> TurnPlanner:
    return TurnPlanner()


# 注入turn_planner_validator对象
async def get_turn_planner_validator() -> TurnPlanValidator:
    return TurnPlanValidator()


async def get_command_processor() -> CommandProcessor:
    return CommandProcessor()


async def get_task_lifecycle_responder() -> TaskLifecycleResponder:
    return TaskLifecycleResponder()


async def get_response_render() -> ResponseRender:
    return ResponseRender()


async def get_action_registry() -> ActionRegistry:
    # 创建注册表，并注册已有的业务 Action
    registry = ActionRegistry()
    # action_register(registry)  # 原手动注册方式
    auto_action_register(registry)
    return registry


async def get_action_runner(
        registry: ActionRegistry = Depends(get_action_registry),
) -> ActionRunner:
    return ActionRunner(registry=registry)


async def get_flow_executor(response_render: ResponseRender = Depends(get_response_render),
                            action_runner:ActionRunner=Depends(get_action_runner)) -> FlowExecutor:
    return FlowExecutor(
        response_render=response_render,
        action_runner=action_runner
    )


# 注入task_handler对象
async def get_task_handler(command_processor: CommandProcessor = Depends(get_command_processor),
                           task_lifecycle_responder: TaskLifecycleResponder = Depends(
                               get_task_lifecycle_responder),
                           flow_executor: FlowExecutor = Depends(get_flow_executor)) -> TaskHandler:
    return TaskHandler(
        command_processor=command_processor,
        task_lifecycle_responder=task_lifecycle_responder,
        flow_executor=flow_executor
    )


async def get_chit_chat() -> ChitChat:
    return ChitChat()


async def get_clarify_response() -> ClarifyResponse:
    return ClarifyResponse()


# 注入引擎层对象
async def get_dialogue_engine(turn_planner: TurnPlanner = Depends(get_turn_planner),
                              turn_planner_validator: TurnPlanValidator = Depends(
                                  get_turn_planner_validator),
                              task_handler: TaskHandler = Depends(get_task_handler),
                              chit_chat: ChitChat = Depends(get_chit_chat),
                              clarify_response: ClarifyResponse = Depends(get_clarify_response)) -> DialogueEngine:
    return DialogueEngine(
        turn_planner=turn_planner,
        turn_planner_validator=turn_planner_validator,
        task_handler=task_handler,
        chit_chat=chit_chat,
        clarify_response=clarify_response
    )


# 注入service对象
# 方法一：
# async def get_dialogue_service()-> DialogueService:
#     return DialogueService(
#         engine=get_dialogue_engine(),
#         repository=get_dialogue_repository()
#     )

# 方法二：
async def get_dialogue_service(repository: DialogueRepository = Depends(get_dialogue_repository),
                               engine: DialogueEngine = Depends(get_dialogue_engine)) -> DialogueService:
    return DialogueService(
        engine=engine,
        repository=repository
    )


"""
chat 接口
└── get_dialogue_service() → DialogueService
    │
    ├── get_dialogue_repository() → DialogueRepository
    │   └── get_sesssion() → AsyncSession
    │       └── async_session_factory()
    │
    └── get_dialogue_engine() → DialogueEngine
        │
        ├── get_turn_planner() → TurnPlanner
        │
        ├── get_turn_planner_validator() → TurnPlanValidator
        │
        ├── get_chit_chat() → ChitChat
        │
        ├── get_clarify_response() → ClarifyResponse
        │
        └── get_task_handler() → TaskHandler
            │
            ├── get_command_processor() → CommandProcessor
            │
            ├── get_task_lifecycle_responder()
            │   └── TaskLifecycleResponder
            │
            └── get_flow_executor() → FlowExecutor
                │
                ├── get_response_render() → ResponseRender
                │
                └── get_action_runner() → ActionRunner
                    │
                    └── get_action_registry() → ActionRegistry
                        └── auto_action_register(registry) 自动扫描注册
                            ├── LogisticsTrackingAction
                            └── LookupOrderStatusAction

API 只声明自己要什么，FastAPI 沿着 Depends 递归创建 Session、Repository、Planner、Engine，最后组装成 Service。
"""
