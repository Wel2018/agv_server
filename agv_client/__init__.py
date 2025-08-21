"""云迹 Water AGV 遥操作调试程序"""

from toolbox.qt import qtbase
from toolbox.core.logbase import get_logger


q_appcfg = qtbase.QAppConfig(
    name = "AGV 遥操作调试程序 (for 云迹 Water)",
    name_en = "Water AGV teleop",
    date="2025-08-18",
    version = "1.0.0",
    fontsize = 14,
    slot="agv_client",
    APPCFG_DICT=qtbase.get_appcfg(__file__),
)

print(f"AppConfig={q_appcfg}")
logger = get_logger(q_appcfg.slot)
