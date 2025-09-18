import asyncio
import json
import time
from fastapi import APIRouter
from fastapi import WebSocket
from fastapi import WebSocketDisconnect
from fastapi.responses import StreamingResponse
# from attrs import asdict, define, field
router = APIRouter()
from .sdk.agv_yunji import AgvYunjiWater
from rich import print


import cv2
cap = cv2.VideoCapture(0)


def gen_frames():
    while True:
        success, frame = cap.read()
        if not success:
            break
        else:
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
    return StreamingResponse(gen_frames(), media_type="multipart/x-mixed-replace; boundary=frame")


def create_reply(data: dict = {}, is_ok=1):
    metadata = dict(
        is_ok=is_ok, # 响应状态
        # inp=inp, # 输入参数
        # timestamp=get_time_str(),
    )
    # metadata.update(data)
    return data


class GData:
    agv = AgvYunjiWater()
    print("agv init")


def parse_res(res: str):
    try:
        res = res.replace("true", "True")
        res = res.replace("false", "False")
        res = res.replace("\n", "")
        res_dict: dict = eval(res)
        return res_dict
    except Exception as e:
        return {"res": res}
    

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
    res = parse_res(res)
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
