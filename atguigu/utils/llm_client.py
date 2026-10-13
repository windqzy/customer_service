"""
这个模块，创建llm的对象
"""
from langchain.chat_models import init_chat_model
from langchain_core.language_models import BaseChatModel

from atguigu.conf.config import Settings, settings

# llm:BaseChatModel = init_chat_model(
#     model=settings.LLM_MODEL,
#     model_provider='openai',
#     api_key=settings.llm_api_key,
#     base_url=settings.llm_base_url,
#     temperature = 0
# )

llm = init_chat_model(
    model=settings.LLM_MODEL,
    model_provider="ollama",
    base_url="http://localhost:11434",
    temperature=0
)
if __name__ == "__main__":
    print(llm.invoke('你是谁').content)
