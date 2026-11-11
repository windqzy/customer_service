import uvicorn

from atguigu.conf.config import settings

if __name__ == '__main__':
    
    # init_db_engine()
    # init_http_client()
    uvicorn.run("atguigu.api.app:app",
                host=settings.app_host,
                port=settings.app_port,
                # reload=True
                )

"""
开启 reload=True 后，会有两个不同职责的进程：

监听进程：监控代码文件变化，变化后重启服务进程。
服务进程：加载 FastAPI 应用、处理请求。这是独立的子进程。Uvicorn 官方说明
你的 init_db_engine() 在父进程中执行。子进程重新导入代码时，
不会执行 if __name__ == '__main__': 里的初始化，所以它的：

async_session_factory = None

仍然为空。老师说的“不是一个对象”，结合你的代码，更准确地理解是：两个进程拥有各自的内存，
父进程初始化的数据库对象没有自动出现在子进程里。
正确的调整方向是：在 FastAPI 的 lifespan 中初始化和关闭数据库，让每个服务进程自己完成初始化；
启动时将资源保存到 app.state；请求到来后，由 Depends 获取并注入业务对象。
main.py 只启动服务，不负责创建数据库和 HTTP 客户端。


"""
