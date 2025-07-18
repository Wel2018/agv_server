"""云迹 Water AGV 遥操作调试程序"""
import os
from toolbox.qt import qtbase
from toolbox.core.logbase import get_logger
from toolbox.core.file_op import yaml_load


AppConfig = qtbase.QAppConfig(
    name = "AGV 遥操作调试程序 (for 云迹 Water)",
    name_en = "Water AGV teleop",
    date="2025-07-17",
    version = "1.0.0",
    fontsize = 14
)
print(f"AppConfig={AppConfig}")


# 配置 -----------------------------------------------------------
logger = get_logger(prefix="", name="agv_teleop")
cur_dir = os.path.dirname(os.path.abspath(__file__))
APPCFG: dict = yaml_load(f"{cur_dir}/appcfg.yaml")
print(f"APPCFG={APPCFG}")
THREAD_DEBUG = APPCFG['THREAD_DEBUG']
VERBOSE = APPCFG['VERBOSE']
BENCHMARK = APPCFG['BENCHMARK']
