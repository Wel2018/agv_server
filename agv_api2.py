import asyncio
import json
import threading
import time
from typing import Any
import cv2
from fastapi import APIRouter
from fastapi import WebSocket
from fastapi import WebSocketDisconnect
from fastapi.responses import StreamingResponse
# from attrs import asdict, define, field

router = APIRouter()
from rich import print
from .sdk.agv_slamtech_api import SlamTechApi
# from .sdk.hand import DexterousHand
# from .sdk.realman_arm import RealmanArmClient
# from .sdk.realsense_cam import RealSenseCam


#########################################################################
# 全局数据

class GData:
    # arm_L = RealmanArmClient("192.168.10.20")
    # arm_R = RealmanArmClient("192.168.10.19")
    # hand = DexterousHand("192.168.10.19")
    agv = SlamTechApi
    # agv = None
    # cam = RealSenseCam()
    print("✅ GData 初始化完成")
    shared_data: dict[str, Any] = {  # noqa: RUF012
        "fall_detector_status": 0,
    }


def create_reply(data: dict = {}, is_ok=1):
    metadata = {
        "is_ok": is_ok, # 响应状态
        # inp=inp, # 输入参数
        # timestamp=get_time_str(),
    }
    # metadata.update(data)
    return data


def parse_res(res: str):
    try:
        res = res.replace("true", "True")
        res = res.replace("false", "False")
        res = res.replace("\n", "")
        res_dict: dict = eval(res)
        return res_dict
    except Exception as e:
        return {"res": res}


#########################################################################
# 机械臂
@router.post("/arm_config", summary="机械臂配置")
async def arm_config(data: dict):
    return {}


@router.post("/arm_control", summary="机械臂控制")
async def arm_control(data: dict):
    return {}


@router.get("/arm_get_curr", summary="机械臂控制")
async def arm_get_curr():
    return {}


@router.get("/arm_estop", summary="机械臂急停")
async def arm_estop():
    return {}


#########################################################################
# 灵巧手/夹爪

# @router.post("/gripper_control", summary="夹爪控制")
# async def gripper_control(data: dict):
#     res = {}
#     return create_reply(res)


# @router.post("/hand_control", summary="灵巧手控制")
# async def hand_control(data: dict):
#     res = {}
#     return create_reply(res)


#########################################################################
# 底盘

@router.get("/get_curr", summary="获取当前的底盘状态")
async def get_curr():
    res = GData.agv.get_localization_pose()


@router.get("/marker_query", summary="列举地图位置")
async def marker_query():
    return GData.agv.get_map_pois()


@router.get("/cancel_move", summary="取消移动")
async def cancel_move():
    return GData.agv.stop_current_action()


@router.post("/force_stop", summary="急停")
async def force_stop(data: dict):
    return GData.agv.stop_current_action()


@router.post("/nav_to_target", summary="导航到指定位置")
async def nav_to_target(data: dict):
    raise NotImplementedError


#########################################################################
# 测试接口

@router.get("/get_data", summary="获取数据")
async def get_data():
    """获取共享数据
    ```json
    ```
    """
    # 将底盘状态写入
    res = GData.agv.get_localization_pose()
    GData.shared_data["agv"] = res
    return create_reply(GData.shared_data)


@router.post("/set_data", summary="写入数据")
async def set_data(data: dict):
    # print(f"set_data: data={data}")
    GData.shared_data.update(data)
    # print(f"shared_data={GData.shared_data}")
    return create_reply()


@router.get("/echo", summary="联通性测试")
async def echo():
    from datetime import datetime
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    timestamp_ms = int(time.time() * 1000)
    # print(timestamp_ms)  # 例如：1730618884512
    return create_reply({
        "timestamp": now_str,
        "timestamp_ms": timestamp_ms,
    })
