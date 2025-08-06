"""底盘控制客户端"""

from toolbox.comm.http_op import HttpRequest
from toolbox.comm.server_echo import ServerEcho
import threading
import asyncio
import websockets
from rich import print


class AgvHttpClient:
    """底盘控制客户端"""
    
    def __init__(self, ip="127.0.0.1", port=29000) -> None:
        self.req = HttpRequest(ip=ip, port=port)
        self.status = {}
        self.ctl_cmd = {}
        
        echo = ServerEcho()
        second = echo.ping(ip)
        print(f"连接底盘 {second} 秒")
        if second < 1:
            self.ws_thread = threading.Thread(
                target=_velocity_control_ws, args=(self,), daemon=True)
            self.ws_thread.start()
        else:
            raise Exception("底盘未连接")

    def get_robot_res(self):
        return self.req.get("ctl/get_robot_res")
    
    def cancel_move(self):
        return self.req.get("ctl/cancel_move")
    
    def velocity_control_stop(self):
        return self.req.get("ctl/velocity_control_stop")
        
    def list_map_marker(self):
        return self.req.get("ctl/list_map_marker")
        
    def list_map(self):
        return self.req.get("ctl/list_map")

    def force_stop(self, flag=1):
        return self.req.post("ctl/force_stop", json={
            "flag": flag
        })

    def nav_to_target(self, name="1234"):
        return self.req.post("ctl/nav_to_target", json={
            "name": name
        })
    
    def velocity_control(self, linear_v=0, angular_v=0):
        return self.req.post("ctl/velocity_control", json={
            "linear_v": linear_v,
            "angular_v": angular_v,
        })
    

def _velocity_control_ws(client: AgvHttpClient):
    async def connect_ws():
        ip = client.req.ip
        port = client.req.port
        uri = f"ws://{ip}:{port}/ctl/velocity_control_ws"
        
        async with websockets.connect(uri) as websocket:
            while True:
                # 发送控制指令
                await websocket.send(
                    str(client.ctl_cmd), text=True
                )
                
                # 接收机器人状态
                msg = await websocket.recv()
                print("Received:", msg)
                client.status.update(eval(msg))

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(connect_ws())

