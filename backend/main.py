import sys
sys.path.append("../")
import platform
import signal
import uvicorn
import logging
from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI
# from fastapi.responses import *
# from fastapi import *
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from rich import print
import multiprocessing as mp
import asyncio
from config import AppConfig, get_origins


from fastapi import applications
from fastapi.openapi.docs import get_swagger_ui_html


def swagger_monkey_patch(*args, **kwargs):
    return get_swagger_ui_html(
        *args, **kwargs,
        swagger_js_url="https://cdn.staticfile.net/swagger-ui/5.1.0/swagger-ui-bundle.min.js",
        swagger_css_url="https://cdn.staticfile.net/swagger-ui/5.1.0/swagger-ui.min.css")

applications.get_swagger_ui_html = swagger_monkey_patch # type: ignore


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

# 挂载路由
from api import router as agv_api
app.include_router(agv_api, prefix="/ctl", tags=["agv_api"])


# 启动服务器
def run_uvcorn(cfg: AppConfig):
    # print(config.to_dict())
    print(f"服务地址：{cfg.hostname}")
    uvicorn.run(
        cfg.uvicorn_app_url,
        host=cfg.host,
        port=cfg.port, 
        reload=bool(1),
        # reload_dirs="./backend",
        # reload_delay=3, 
        log_level=logging.WARN,
    )


def main(args=[]):
    port = 29000
    cfg = AppConfig(
        "main:app",
        is_encrypt=0,
        port=port,
    )
    run_uvcorn(cfg)
    # print("关闭服务...")


if __name__ == '__main__':
    args = sys.argv[1:]
    main(args)
