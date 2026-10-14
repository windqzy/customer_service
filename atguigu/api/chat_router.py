"""
创建路由器
"""
import uuid
from dataclasses import asdict

from fastapi import APIRouter, Depends

from atguigu.api.depends import get_dialogue_service
from atguigu.api.schemas import ChatMessage, ChatRequest, ChatResponse, ChatObject
from atguigu.domain.message import UserMessage, ProcessResult, MessageType, MessageObject
from atguigu.service.dialogue_service import DialogueService

chat_router = APIRouter()


# 注入service对象 使用service对象
def _build_user_message(chat_request: ChatRequest) -> UserMessage:
    return UserMessage(
        sender_id=chat_request.sender_id,
        message_id=chat_request.message_id if chat_request.message_id else str(uuid.uuid4()),
        type=MessageType.TEXT if chat_request.text else MessageType.OBJECT,
        text=chat_request.text,
        object=MessageObject(id=chat_request.object.id,
                             type=chat_request.object.type,
                             title=chat_request.object.title,
                             attributes=chat_request.object.attributes
                             ) if chat_request.object else None
    )


def _build_chat_response(process_result: ProcessResult) -> ChatResponse:
    return ChatResponse(
        sender_id=process_result.sender_id,
        message_id=process_result.message_id,
        messages=[ChatMessage(
            text=bot_message.text,
            object=ChatObject(
                # 自动解包后相同属性赋值
                **asdict(bot_message.object)
            ) if bot_message.object else None,
        ) for bot_message in process_result.messages]
    )


@chat_router.post('/api/chat')
async def chat(chat_request: ChatRequest,
               service: DialogueService = Depends(get_dialogue_service)) -> ChatResponse:
    # 1.获取浏览器提交过来的消息 文本类型 和 对象类型
    # 1.1将ChatReqyest 转换成 UserMessage对象
    user_message: UserMessage = _build_user_message(chat_request)
    # 2.调用sevice方法实现功能
    # 2.1注入service对象，调用service的方法得到返回结果，结果类型是RrocessResult
    process_result: ProcessResult = await service.run(user_message)
    # 2.2ProcessResult转换成ChatResponse
    chat_response: ChatResponse = _build_chat_response(process_result)
    # 3.返回结果
    return chat_response
