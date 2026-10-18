from sqlalchemy import String, Text
from sqlalchemy.orm import mapped_column, Mapped

from atguigu.repository.orm.base import Base


class DialogueStates(Base):
    # 当前类和哪个表对应
    __tablename__ = 'dialogue_states'
    # 和字段对应 数据类型 和 主键 非空
    sender_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    state_json: Mapped[str] = mapped_column(Text, nullable=False)

