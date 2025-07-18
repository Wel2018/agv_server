import socket
import json
import time
from rich import print
# from pprint import pprint as print


class AgvSocket:
    host = '192.168.10.10'
    port = 31001

    def __init__(self) -> None:
        self.cli = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.cli.connect((self.host, self.port))

    def req(self, cmd: str):
        #查询底盘的地图列表指令
        # point = '/api/map/list'
        # point = '/api/map/list_info'
        # point = '/api/software/check_for_update'
        # point = '/api/request_data?topic=robot_status&frequency=1'
        # point = '/api/robot_status'
        # point = '/api/diagnosis/get_result'
        # point = '/api/get_power_status'

        #发送指令
        self.cli.send(cmd.encode('utf-8'))

        #接收底盘返回
        res = self.cli.recv(1024).decode()
        # data = eval(data)
        # print(data)

        # point2= '/api/move?marker=071901'
        # cli.send(point2.encode('utf-8'))
        # data1 = cli.recv(1024).decode()
        # point3='/api/move?marker=071902'
        # cli.send(point3.encode('utf-8'))
        # data1 = cli.recv(1024).decode()
        return res

    def __del__(self):
        self.cli.close()


class AgvWrapper:

    def __init__(self) -> None:
        self.sock = AgvSocket()
        

    def _send_cmd(self, cmd: str):
        return self.sock.req(cmd)
    
    def nav_to_target(self, name: str):
        """导航到指定位置"""
        return self._send_cmd(cmd=f"/api/move?marker={name}")

    def get_robot_status(self):
        """获取状态信息"""
        # /api/request_data?topic=robot_status&frequency=1
        # 请求server以1HZ的频率发送机器⼈全局状态
        # /api/request_data?topic=robot_velocity&frequency=0.5
        # 请求server以0.5HZ的频率发送机器⼈当前速度
        self._send_cmd("/api/request_data?topic=robot_status&frequency=1")
        return self._send_cmd("/api/robot_status")

    def set_p(self, k, v):
        # /api/set_params?max_speed_linear=0.5
        # 设置机器⼈最⼤⾏进速度为0.5⽶/秒
        return self._send_cmd(f"/api/set_params?{k}={v}")

    def get_p(self):
        # /api/get_params
        return self._send_cmd(f"/api/get_params")

    def list_map(self):
        # /api/map/list
        return self._send_cmd(f"/api/map/list")
    
    def list_map_marker(self):
        return self._send_cmd(f"/api/markers/query_list")

    def force_stop(self, flag=1):
        """急停"""
        # /api/estop?flag=true //进⼊急停模式
        # /api/estop?flag=false //退出急停模式
        if flag:
            return self._send_cmd("/api/estop?flag=true")
        else:
            return self._send_cmd("/api/estop?flag=false")

    def cancel_move(self):
        return self._send_cmd("/api/move/cancel")

    def velocity_control(self, linear_v=.0, angular_v=.0):
        # /api/joy_control?angular_velocity=0.5&linear_velocity=0.2
        # 机器⼈以⻆速度0.5rad/s逆时针转动，同时以线速度0.2m/s前进。
        return self._send_cmd(f"/api/joy_control?angular_velocity={angular_v}&linear_velocity={linear_v}")

    def velocity_control_stop(self):
        return self.velocity_control(0, 0)
