"""
这个模块，创建llm的对象
"""
from langchain.chat_models import init_chat_model
from langchain_core.language_models import BaseChatModel

from atguigu.conf.config import Settings, settings

# OpenAI：模型、密钥和接口地址从 .env 读取
llm:BaseChatModel = init_chat_model(
    model=settings.LLM_MODEL,
    model_provider='openai',
    api_key=settings.llm_api_key,
    base_url=settings.llm_base_url,
    reasoning_effort='none',  # GPT-5.4 使用 temperature 时需要设为 none
    temperature = 0
)

# 保留本地 Ollama 配置；切回时注释上面的初始化，并将 LLM_MODEL 改回 qwen3:14b。
# llm = init_chat_model(
#     model=settings.LLM_MODEL,
#     model_provider="ollama",
#     base_url="http://localhost:11434",
#     temperature=0
# )
if __name__ == "__main__":
    print(llm.invoke('你是谁').content)
