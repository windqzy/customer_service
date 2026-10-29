from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from atguigu.engine.dialogue_engine import DialogueEngine
from atguigu.plan.turn_planner import TurnPlanner
from atguigu.repository.dialogue_repository import DialogueRepository
from atguigu.service.dialogue_service import DialogueService
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

# 注入引擎层对象
async def get_dialogue_engine(turn_planner:TurnPlanner= Depends(get_turn_planner)) -> DialogueEngine:
    return DialogueEngine(
        turn_planner=turn_planner
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
