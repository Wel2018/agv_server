import sys
sys.path.append("../")
import platform
import signal
import uvicorn
import logging
from rich import print
from .config import AppConfig, get_origins

from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


def create_app(origins: list):
    """创建全局唯一实例"""
    #app = FastAPI(on_startup=[on_startup])
    app = FastAPI()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        # allow_origin_regex="*",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    return app


# uvicorn 模式下，app 必须放在全局作用域中，不能放在 main 函数中！
app = create_app(get_origins(1))

# 挂载静态文件目录，模拟静态资源服务器
# app.mount("/tmp", StaticFiles(directory="tmp"), name="static")

print("挂载路由...")
from .agv_api import router as agv_api
app.include_router(agv_api, prefix="", tags=["agv_api"])


# 启动服务器
def run_uvcorn(cfg: AppConfig):
    print(f"服务地址：{cfg.hostname}")
    uvicorn.run(
        cfg.uvicorn_app_url,
        host=cfg.host,
        port=cfg.port,
    )


def main(args=[]):
    port = 29000
    cfg = AppConfig(
        "agv_server.app:app",
        is_encrypt=0,
        port=port,
    )
    print("启动服务...")
    run_uvcorn(cfg)
    print("关闭服务...")


if __name__ == '__main__':
    args = sys.argv[1:]
    main(args)
