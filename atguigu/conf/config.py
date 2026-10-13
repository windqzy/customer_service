from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# 获取当前文件上两层目录，找到.env文件
ENV_DIR = Path(__file__).parents[2]
print(ENV_DIR)
ENV_FILE = ENV_DIR / '.env'
print(ENV_FILE)

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        #env文件的路径
        env_file=ENV_FILE,
        #编码方式
        env_file_encoding='utf-8',
        #配置文件属性数量和当前类属性数量可以不一致
        extra='ignore'
    )
    # 对应配置文件，创建对应属性:类型
    LLM_MODEL: str

    llm_api_key: str
    llm_base_url: str

    # 数据库
    database_url: str
    # 商城 API
    commerce_api_base_url: str
    # 服务器
    app_host: str
    app_port: int

settings = Settings()

if __name__ == '__main__':
    print(settings.LLM_MODEL)
    print(settings.llm_api_key)


