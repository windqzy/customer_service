from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from atguigu.engine.dialogue_engine import DialogueEngine
from atguigu.plan.turn_plan_validator import TurnPlanValidator
from atguigu.plan.turn_planner import TurnPlanner
from atguigu.repository.dialogue_repository import DialogueRepository
from atguigu.service.dialogue_service import DialogueService
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


async def get_flow_executor(response_render: ResponseRender = Depends(get_response_render)) -> FlowExecutor:
    return FlowExecutor(
        response_render=response_render
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


# 注入引擎层对象
async def get_dialogue_engine(turn_planner: TurnPlanner = Depends(get_turn_planner),
                              turn_planner_validator: TurnPlanValidator = Depends(
                                  get_turn_planner_validator),
                              task_handler: TaskHandler = Depends(get_task_handler)) -> DialogueEngine:
    return DialogueEngine(
        turn_planner=turn_planner,
        turn_planner_validator=turn_planner_validator,
        task_handler=task_handler
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
FastAPI 接口
   │
   ▼
get_dialogue_service()
   │
   ├───────────────┐
   ▼               ▼
get_dialogue_repository()   get_dialogue_engine() 
   │                         │                   │   
   ▼                         ▼                   ▼
get_session()            get_turn_planner()     get_task_handler()
   │                         │
   ▼                         ▼
AsyncSession             TurnPlanner
   │                         │
   ▼                         ▼
DialogueRepository       DialogueEngine
        \\                 /
         \\               /
          ▼             ▼
           DialogueService


API 只声明自己要什么，FastAPI 沿着 Depends 递归创建 Session、Repository、Planner、Engine，最后组装成 Service。
"""
