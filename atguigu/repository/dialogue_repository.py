"""
操作数据库

"""
from sqlalchemy.ext.asyncio import AsyncSession


class DialogueRepository:
    def __init__(self,session:AsyncSession):
        self.session = session

    def load(self, sender_id):
        pass

    async def save(self, dialogue_state):
        pass
