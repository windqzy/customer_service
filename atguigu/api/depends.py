from collections.abc import AsyncIterator

from fastapi import Depends, Request
from httpx import AsyncClient
from langchain_core.language_models import BaseChatModel
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from atguigu.chichat.chitchat import ChitChat
from atguigu.clarify.clarify_response import ClarifyResponse
from atguigu.engine.dialogue_engine import DialogueEngine
from atguigu.knowledge.handler import KonwledgeHandler
from atguigu.knowledge.provider import ApiProductProvider, ApiOrderProvider, FAQProvider, RAGProvider
from atguigu.knowledge.registry import KnowledgeProviderRegistry
from atguigu.knowledge.responder import KnowledgeResponer
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


# 从当前应用中取出启动时已创建的资源。
def get_session_factory(request: Request) -> async_sessionmaker[AsyncSession]:
    return request.app.state.async_session_factory


def get_http_client(request: Request) -> AsyncClient:
    return request.app.state.http_client


def get_llm(request: Request) -> BaseChatModel:
    return request.app.state.llm


# 工厂由应用共享，每次请求创建自己的 session，请求结束时自动关闭。
async def get_sesssion(
        session_factory: async_sessionmaker[AsyncSession] = Depends(get_session_factory),
) -> AsyncIterator[AsyncSession]:
    async with session_factory() as session:
        yield session


# 注入repository对象
async def get_dialogue_repository(session: AsyncSession = Depends(get_sesssion)) -> DialogueRepository:
    return DialogueRepository(
        session=session
    )


# 注入turn_planner对象
async def get_turn_planner(llm: BaseChatModel = Depends(get_llm)) -> TurnPlanner:
    return TurnPlanner(llm=llm)


# 注入turn_planner_validator对象
async def get_turn_planner_validator() -> TurnPlanValidator:
    return TurnPlanValidator()


async def get_command_processor() -> CommandProcessor:
    return CommandProcessor()


async def get_task_lifecycle_responder() -> TaskLifecycleResponder:
    return TaskLifecycleResponder()


async def get_response_render() -> ResponseRender:
    return ResponseRender()


async def get_action_registry(
        http_client: AsyncClient = Depends(get_http_client),
) -> ActionRegistry:
    # 创建注册表，并注册已有的业务 Action
    registry = ActionRegistry()
    # action_register(registry, http_client)  # 原手动注册方式
    auto_action_register(registry, http_client)
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


async def get_chit_chat(llm: BaseChatModel = Depends(get_llm)) -> ChitChat:
    return ChitChat(llm=llm)


async def get_clarify_response(llm: BaseChatModel = Depends(get_llm)) -> ClarifyResponse:
    return ClarifyResponse(llm=llm)


# 注册知识查询来源
async def get_knowledge_registry(
        http_client: AsyncClient = Depends(get_http_client),
) -> KnowledgeProviderRegistry:
    return KnowledgeProviderRegistry(provider_objs=[
        ApiProductProvider(http_client=http_client),
        ApiOrderProvider(http_client=http_client),
        FAQProvider(),
        RAGProvider(),
    ])


async def get_knowledge_responder(llm: BaseChatModel = Depends(get_llm)) -> KnowledgeResponer:
    return KnowledgeResponer(llm=llm)


async def get_knowledge_handler(
        knowledge_registry: KnowledgeProviderRegistry = Depends(get_knowledge_registry),
        knowledge_responer: KnowledgeResponer = Depends(get_knowledge_responder),
) -> KonwledgeHandler:
    return KonwledgeHandler(
        knowledge_registry=knowledge_registry,
        knowledge_responer=knowledge_responer,
    )


# 注入引擎层对象
async def get_dialogue_engine(turn_planner: TurnPlanner = Depends(get_turn_planner),
                              turn_planner_validator: TurnPlanValidator = Depends(
                                  get_turn_planner_validator),
                              task_handler: TaskHandler = Depends(get_task_handler),
                              chit_chat: ChitChat = Depends(get_chit_chat),
                              clarify_response: ClarifyResponse = Depends(get_clarify_response),
                              knowledge_handler: KonwledgeHandler = Depends(get_knowledge_handler)) -> DialogueEngine:
    return DialogueEngine(
        turn_planner=turn_planner,
        turn_planner_validator=turn_planner_validator,
        task_handler=task_handler,
        chit_chat=chit_chat,
        clarify_response=clarify_response,
        knowledge_handler=knowledge_handler
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
    │       └── get_session_factory() → app.state.async_session_factory
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
        ├── get_knowledge_handler() → KonwledgeHandler
        │   ├── get_knowledge_registry() → KnowledgeProviderRegistry
        │   │   ├── ApiProductProvider
        │   │   ├── ApiOrderProvider
        │   │   ├── FAQProvider
        │   │   └── RAGProvider
        │   └── get_knowledge_responder() → KnowledgeResponer
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
                        └── auto_action_register(registry, http_client) 自动扫描注册
                            ├── LogisticsTrackingAction
                            └── LookupOrderStatusAction

API 只声明自己要什么，FastAPI 沿着 Depends 递归创建 Session、Repository、Planner、Engine，最后组装成 Service。
资源顺序：lifespan 创建 → app.state 保存 → Depends 获取 → 构造函数注入。
get_action_registry 和 get_knowledge_registry 共用 get_http_client() 提供的应用级客户端。
Planner、ChitChat、ClarifyResponse、KnowledgeResponer 共用 get_llm() 提供的模型。
"""
