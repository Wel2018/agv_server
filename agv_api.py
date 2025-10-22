import asyncio
import json
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
from .sdk.agv_yunji import AgvYunjiWater
from .sdk.hand import DexterousHand
from .sdk.realman_arm import RealmanArmClient
from .sdk.realsense_cam import RealSenseCam


#########################################################################
# 全局数据

class GData:
    arm_L = RealmanArmClient("192.168.10.20")
    arm_R = RealmanArmClient("192.168.10.19")
    hand = DexterousHand("192.168.10.19")
    agv = AgvYunjiWater()
    cam = RealSenseCam()
    print("✅ GData 初始化完成")
    shared_data: dict[str, Any] = {
        "fall_detector_status": 0
    }


def create_reply(data: dict = {}, is_ok=1):
    metadata = dict(
        is_ok=is_ok, # 响应状态
        # inp=inp, # 输入参数
        # timestamp=get_time_str(),
    )
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

@router.post("/arm_control", summary="机械臂控制")
async def arm_control(data: dict):
    res = {}
    ret, pose_L = GData.arm_L.get_pose()
    ret, pose_R = GData.arm_R.get_pose()
    res["pose_L"] = pose_L
    res["pose_R"] = pose_R
    return create_reply(res)


#########################################################################
# 灵巧手/夹爪

@router.post("/gripper_control", summary="夹爪控制")
async def gripper_control(data: dict):
    res = {}
    GData.arm_L.gripper_open()
    GData.arm_L.gripper_close()
    return create_reply(res)


@router.post("/hand_control", summary="灵巧手控制")
async def hand_control(data: dict):
    res = {}
    GData.hand.open_all()
    GData.hand.close_all()
    GData.hand.close_finger(0, 50)
    return create_reply(res)


#########################################################################
# 读取 D535 摄像头数据


def gen_frames():
    while True:
        data = GData.cam.read() # type: ignore
        if len(data) == 0:
            continue
        
        frame = data['color']
        # success, frame = cap.read()
        # if not success:
        #     break
        # else:
        # 转换为 JPEG 格式
        ret, buffer = cv2.imencode('.jpg', frame)

        if not ret:
            continue

        # 使用 yield 逐帧输出 MJPEG 流
        yield (
            b'--frame\r\n'
            b'Content-Type: image/jpeg\r\n\r\n' +
            buffer.tobytes() +
            b'\r\n'
        )


@router.get("/video")
def video_feed():
    return StreamingResponse(
        gen_frames(), 
        media_type="multipart/x-mixed-replace; boundary=frame")


#########################################################################
# 底盘

@router.get("/get_curr", summary="获取当前的底盘状态")
async def get_curr():
    res = GData.agv.get_robot_status()
    res = parse_res(res)
    # print(f"get_robot_status: {res}")
    return create_reply(res)


@router.websocket("/get_curr_ws")
async def get_curr_ws(ws: WebSocket):
    await ws.accept()

    async def send_loop():
        """循环发送数据给客户端"""
        while True:
            try:
                res = GData.agv.get_robot_status()
                res = parse_res(res)
                # print(f"send_loop={res}")
                await ws.send_text(json.dumps(res))
                await asyncio.sleep(0.1)  # 30ms
            except WebSocketDisconnect:
                print("WebSocket disconnected (send)")
                break

    async def recv_loop():
        """循环接收客户端消息"""
        while True:
            try:
                msg = await ws.receive_text()
                # print(f"receive_loop: {msg}")
                data = eval(msg)
                res = GData.agv.velocity_control(data["linear_v"], data["angular_v"])
                # print("recv_loop res=", res)
                # await asyncio.sleep(0.03)  # 30ms
            except WebSocketDisconnect:
                print("WebSocket disconnected (receive)")
                break
            except Exception as e:
                print(f"Receive error: {e}")
                break

    # 创建两个并发任务
    send_task = asyncio.create_task(send_loop())
    recv_task = asyncio.create_task(recv_loop())

    # 等待任一任务结束
    done, pending = await asyncio.wait(
        [send_task, recv_task],
        return_when=asyncio.FIRST_COMPLETED,
    )

    # 清理另一个未完成的任务
    for task in pending:
        task.cancel()
    print("WebSocket closed")


@router.get("/get_p", summary="获取参数")
async def get_p():
    res = GData.agv.get_p()
    res = parse_res(res)
    print(f"get_p: {res}")
    return create_reply(res)


@router.get("/marker_query", summary="列举地图位置")
async def marker_query():
    res = GData.agv.marker_query()
    res = parse_res(res)
    print(f"marker_query: {res}")
    return create_reply(res)


@router.get("/list_map", summary="列举地图位置")
async def list_map():
    res = GData.agv.list_map()
    res = parse_res(res)
    print(f"list_map: {res}")
    return create_reply(res)


@router.get("/cancel_move", summary="取消移动")
async def cancel_move():
    res = GData.agv.cancel_move()
    res = parse_res(res)
    print(f"cancel_move: {res}")
    return create_reply(res)


@router.post("/cmd", summary="cmd")
async def cmd(data: dict):
    """直接运行指令"""
    res = GData.agv._send_cmd(data['cmd'])
    res = parse_res(res)
    return create_reply(res)


@router.post("/set_p", summary="配置参数")
async def set_p(data: dict):
    res = {}
    for k in data.keys():
        v = data[k]
        res = GData.agv.set_p(k, v)
        res = parse_res(res)
        print(f"set_p: {res}")
    return create_reply(res)


@router.post("/force_stop", summary="急停")
async def force_stop(data: dict):
    flag = data.get("flag", 1)
    res = GData.agv.force_stop(flag)
    res = parse_res(res)
    print(f"force_stop: {res}")
    return create_reply(res)


@router.post("/nav_to_target", summary="导航到指定位置")
async def nav_to_target(data: dict):
    name = data.get("name", "charge")
    res = GData.agv.nav_to_target(name)
    res = parse_res(res) # type: ignore
    print(f"nav_to_target: {res}")
    return create_reply(res)


@router.post("/velocity_control", summary="速度控制")
async def velocity_control(data: dict):
    linear_v = data.get("linear_v", 0)
    angular_v = data.get("angular_v", 0)
    res = GData.agv.velocity_control(linear_v, angular_v)
    res = parse_res(res)
    print(f"velocity_control: {res}")
    return create_reply(res)


@router.get("/velocity_control_stop", summary="速度控制正常停止")
async def velocity_control_stop():
    res = GData.agv.velocity_control_stop()
    res = parse_res(res)
    print(f"velocity_control_stop: {res}")
    return create_reply(res)


#########################################################################
# 测试接口

@router.get("/get_data", summary="获取数据")
async def get_data():
    """获取共享数据
    ```json
    {
      "fall_detector_status": 0,  # 跌倒检测状态
      "agv": {  # 底盘状态
        "command": "/api/robot_status",
        ...
      },
      "arm_L": {  # 左臂状态
         ...
      },
      "arm_R": {  # 右臂状态
        "joint": [],
        "pose": [],
        "err": ..
      }
    }
    ```
    """
    # 将底盘状态写入
    GData.shared_data["agv"] = GData.agv.get_robot_status()
    # GData.shared_data["arm"] = GData.arm_L.get_pose()
    ret, pose_L = GData.arm_L.get_pose()
    ret, pose_R = GData.arm_R.get_pose()
    GData.shared_data.update({
        "arm_L": pose_L,
        "arm_R": pose_R,
    })
    return create_reply(GData.shared_data)


@router.post("/set_data", summary="写入数据")
async def set_data(data: dict):
    print(f"set_data: data={data}")
    GData.shared_data.update(data)
    # print(f"shared_data={GData.shared_data}")
    return create_reply(GData.shared_data)
