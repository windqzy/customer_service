"""
创建路由器
"""
import uuid

from fastapi import APIRouter, Depends

from atguigu.api.depends import get_dialogue_service
from atguigu.api.schemas import ChatRequest, ChatResponse, ChatMessage
from atguigu.service.dialogue_service import DialogueService

chat_router = APIRouter()


# 注入service对象 使用service对象
@chat_router.post('/api/chat')
async def chat(chat_request: ChatRequest,
               service: DialogueService = Depends(get_dialogue_service)) -> ChatResponse:
    # 1.获取浏览器提交过来的消息 文本类型 和 对象类型

    # 2.调用sevice方法实现功能
    # await service.run()

    # 3.todo 返回结果
    return ChatResponse(
        sender_id=chat_request.sender_id,
        message_id=str(uuid.uuid4()),
        messages=[ChatMessage(text="hello 这是一个测试", object=None), ]
    )
