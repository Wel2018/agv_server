import asyncio
import json
import time
from fastapi import APIRouter
from fastapi import WebSocket
from fastapi import WebSocketDisconnect
# from attrs import asdict, define, field
router = APIRouter()
from .sdk.agv_yunji import AgvYunjiWater
from rich import print


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
    print(f"get_robot_status: {res}")
    return create_reply(res)


# @router.websocket("/get_curr_ws")
# async def get_curr_ws(ws: WebSocket):
#     await ws.accept()
#     try:
#         while 1:
#             res = GData.agv.get_robot_status()
#             res = parse_res(res)
#             # print(res)
#             # msg = await ws.receive_text()
#             await ws.send_text(json.dumps(res))
#             await asyncio.sleep(30/1000)
#             # print(f"msg={msg}")
#     except Exception as e:
#         print(f"ws closed: {e}")


@router.websocket("/get_curr_ws")
async def get_curr_ws(ws: WebSocket):
    await ws.accept()

    async def send_loop():
        """循环发送数据给客户端"""
        while True:
            res = GData.agv.get_robot_status()
            res = parse_res(res)
            await ws.send_text(json.dumps(res))
            await asyncio.sleep(0.03)  # 30ms

    async def receive_loop():
        """循环接收客户端消息"""
        while True:
            try:
                msg = await ws.receive_text()
                print(f"Received from client: {msg}")
                # TODO: 可以根据 msg 内容做处理，例如控制机器人等
            except WebSocketDisconnect:
                print("WebSocket disconnected (receive)")
                break
            except Exception as e:
                print(f"Receive error: {e}")
                break

    # 创建两个并发任务
    send_task = asyncio.create_task(send_loop())
    recv_task = asyncio.create_task(receive_loop())

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


@router.get("/velocity_control_stop", summary="速度控制-停")
async def velocity_control_stop():
    res = GData.agv.velocity_control_stop()
    res = parse_res(res)
    print(f"velocity_control_stop: {res}")
    return create_reply(res)


@router.websocket("/velocity_control_ws")
async def velocity_control_ws(websocket: WebSocket):
    """实时速度控制，并实时返回机器人坐标和状态信息
    当前只适配一个客户端的情况
    """
    await websocket.accept()
    try:
        while True:
            # 实时速度控制
            data = await websocket.receive_text()
            cmd_dict: dict = eval(json.loads(data))
            linear_v = cmd_dict.get("linear_v", 0)
            angular_v = cmd_dict.get("angular_v", 0)
            res = GData.agv.velocity_control(linear_v, angular_v)
            res = parse_res(res)
            print(f"velocity_control: {res}")
            
            # 返回机器人坐标和状态信息
            # data = json.dumps(data)
            status = GData.agv.get_robot_status()
            await websocket.send_text(status)
            # print(time.time(), state)
            await asyncio.sleep(5/1000)  # 每 5ms 发送一次
    except Exception as e:
        print(f"[velocity_control_ws] error: {e}")
