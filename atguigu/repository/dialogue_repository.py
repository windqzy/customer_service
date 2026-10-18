"""
操作数据库

"""
from pydantic import TypeAdapter
from sqlalchemy import select
from sqlalchemy.dialects.mysql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from atguigu.domain.state import DialogueState
from atguigu.repository.orm.dialogue_states import DialogueStates

# 序列化和反序列化操作
dialogue_state_adapter = TypeAdapter(DialogueState)


class DialogueRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    # 根据用户id查询历史记录
    async def load(self, sender_id: str) -> DialogueState:
        # 方式一
        # sql = 'SELECT * FROM dialogue_states WHERE sender_id = :sender_id'
        # result = self.session.execute(sql, {'sender_id': sender_id})

        # 方式二:orm方式实现
        sql = select(DialogueStates).where(DialogueStates.sender_id == sender_id)
        result = await self.session.execute(sql)
        record: DialogueStates | None = result.scalar_one_or_none()

        # record处理
        if record is not None:
            # 将JSON字符串转换成DialogueState对象
            dialogue_state: DialogueState = dialogue_state_adapter.validate_json(record.state_json)
            return dialogue_state
        else:  # 返回空的对象
            return DialogueState(sender_id=sender_id)

    # 保存最新数据
    async def save_or_update(self, state: DialogueState):
        # 1.将state对象转换为json字符串
        state_json: str = dialogue_state_adapter.dump_json(state).decode('utf-8')
        # 2.orm：构建添加sql语句
        sql = insert(DialogueStates).values(
            sender_id=state.sender_id,
            state_json=state_json
        )
        # 3.存在id则更新 不存在则添加
        on_duplicate_key = sql.on_duplicate_key_update(
            state_json=state_json
        )
        # 4.执行且提交
        await self.session.execute(on_duplicate_key)
        await self.session.commit()
        