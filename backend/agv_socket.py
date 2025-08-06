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

    def request_data(self):
        """请求以指定频率返回数据
        ```
        请求server以1HZ的频率发送机器⼈全局状态
        /api/request_data?topic=robot_status&frequency=1
        
        请求server以0.5HZ的频率发送机器⼈当前速度
        /api/request_data?topic=robot_velocity&frequency=0.5
        ```
        """
        self._send_cmd("/api/request_data?topic=robot_status&frequency=100")


    def get_robot_status(self):
        """获取状态信息"""
        _data = {
           "type":"response",
           "command":"/api/robot_status",
           "uuid":"",
           "status":"OK",
           "error_message":"",
           "results": {
              "move_target":"target_name",
              "move_status":"running",
              "running_status":"running",
              "move_retry_times": 3, # 路径规划重试次数
              "soft_estop_state": "bool",  # 软件急停
              "hard_estop_state": "bool",  # 硬件急停
              "estop_state":"bool",  # soft_estop_state || hard_estop_state
              "charge_state": "bool",
              "power_percent": 100,
              "current_pose": {
                 "x":11.0,  # m
                 "y":11.0,  # m
                 "theta":0.5, # rad
              },
              "current_floor":16,
              "chargepile_id":"1234", # 充电状态下表示当前正在充电的充电桩ID
              "error_code":"00000000"  # 16进制错误码，总共8个字节表示
           }
        }
        
        # 
        _data_err = {
           "type":"response",
           "command":"/api/robot_status",
           "uuid":"",
           "status":"UNKNOWN_ERROR",
           "error_message":"xxxxx",
           "results": ""
        }
        
        # move_status: idle/suceeded/failed/canceld/running
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
        # 返回所有楼层的点位信息
        return self._send_cmd(f"/api/map/list")
    
    def marker_query(self):
        _data = {
            "type": "response",
            "command": "/api/markers/query_list",
            "uuid": "",
            "status": "OK",
            "error_message": "",
            "results": {
                "meeting_room": {
                    "floor": 1,
                    "pose": {
                        "orientation": {
                            "x": 0.0,
                            "y": 0.0,
                            "z": 0.0,
                            "w": 1.0
                        },
                        "position": {
                            "x": 0.0,
                            "y": 0.0,
                            "z": 0.0
                        }
                    }
                }
            }       
        }
        return self._send_cmd(f"/api/markers/query_list")
    
    def marker_insert(self, name: str, type: int = 1):
        """在机器人的当前位置和楼层标记锚点(marker)"""
        # type=11 表示充电桩
        # 0(一般点位)，1(前台点)，7(闸机),3(电梯外),4(电梯内),11(充电桩)
        cmd = f"/api/markers/insert?name={name}"
        if type != -1:
            cmd += "&type=" + str(type)
        return self._send_cmd(cmd)
        
    def marker_delete(self, name: str):
        return self._send_cmd(f"/api/markers/delete?name={name}")

    def map_query(self):
        # return self._send_cmd(f"/api/map/list")
        # return self._send_cmd(f"/api/map/list_info")
        return self._send_cmd(f"/api/map/get_current_map")
    
    def map_set(self, map_name, floor):
        return self._send_cmd(f"/api/map/set_current_map?map_name={map_name}&floor={floor}")

    def power(self, is_reboot=1):
        if is_reboot:
            return self._send_cmd(f"/api/shutdown?reboot=true")
        else:
            return self._send_cmd(f"/api/shutdown")

    def restart_service(self):
        return self._send_cmd(f"/api/software/restart")
    
    def led(self, luminance=50, color=[0, 100, 0]):
        """
        luminance: [0, 100] 亮度
        r,g,b: [0, 100]
        """
        r,g,b = color
        res1 = self._send_cmd(f"/api/LED/set_luminance?value={luminance}")
        res2 = self._send_cmd(f"/api/LED/set_color?r={r}&g={g}&b={b}")
        return res2
    
    def diagnosis(self):
        """自诊断"""
        _data = {
            "type": "response",    
            "command": "/api/diagnosis/get_result",    
            "uuid": "",    
            "status": "OK",    
            "error_message": "",    
            "results": {
                "sensor_core": {  # 诊断项:传感器板
                #  最近一次诊断结果，true->成功 false->失败
                "status": bool,
                "time_stamp": 1511235083.066043,  # 最近一次诊断时间
                "total_count": 4,  # 总诊断次数
                "success_count": 4
                }, # 诊断成功次数
            "motor_core_right": {...},  # 诊断项:右电机板
            "motor_core_left": {...},  # 诊断项:左电机板
            "radio_core": {...},  # 诊断项:无线板
            "power_core": {...}, # 诊断项:电源板
            "depth_camera": {...}, # 诊断项：深度摄像头
            "laser": {...}, # 诊断项：激光
            "IMU": {...}, # 诊断项: IMU        
            "CAN": {...}, # 诊断项: CAN模块
            "internet": {...}, # 诊断项: 互联网（ping baidu)
        }}
        
        return self._send_cmd(f"/api/diagnosis/get_result")
    
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
    