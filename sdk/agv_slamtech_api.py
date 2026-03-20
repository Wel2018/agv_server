import uuid
import requests
from toolbox.core.log import printc
from .helper import request_handler

AGV_IP = "192.168.11.1"
AGV_PORT = 1448


class SlamTechApi:
    """思岚科技底盘控制 API"""
    # http://192.168.11.1:1448/index.html

    @staticmethod
    def uri_pre():
        """接口前缀"""
        return f"http://{AGV_IP}:{AGV_PORT}"

    @classmethod
    # @request_handler(timeout=1, max_retry=3)
    def stop_current_action(cls):
        res = requests.delete(
                f"{cls.uri_pre()}/api/core/motion/v1/actions/:current",
            )
        printc(f"终止当前 action res={res.text}")
        return res

    @classmethod
    # @request_handler(timeout=1, max_retry=3)
    def get_current_action_status(cls, action_id):
    # GET /api/core/motion/v1/actions/{action_id}
    # DELETE /api/core/motion/v1/actions/:current
        res = requests.get(
                f"{cls.uri_pre()}/api/core/motion/v1/actions/{action_id}"
            )
        printc(f"获取当前 action(id={action_id}) 的状态 res={res.text}")
        # return res.json()
        return res

    @classmethod
    # @request_handler(timeout=1, max_retry=3)
    def agv_move_cmd(cls, linear_v=0, angular_v=0, duration=500, **kwargs):  # noqa: ARG003, C901, PLR0912
        """
        AGV运动指令发送函数，通过线速度和角速度匹配theta值
        :param linear_v: 线速度（>0前进，<0后退，=0静止）
        :param angular_v: 角速度（>0左转，<0右转，=0无旋转）
        :param duration: 运动持续时间（ms）
        :param kwargs: 额外扩展参数
        :return: 请求响应结果

        用theta传参控制运动方向，参考值：
        前进（↑）：0
        后退（↓）：3.14
        原地左转（←）：1.56
        原地右转（→）0：-1.56
        前左转（←↑）：0.785
        前右转（↑→）：-0.785
        后左转（←↓）：2.356
        后右转（↓→）：3.93
        """
        # 1. 初始化theta值
        theta = None
        
        # 2. 根据linear_v和angular_v判断运动方向，匹配对应的theta
        linear_v_zero = abs(linear_v) < 1e-6  # 浮点型判零（避免精度问题）
        angular_v_zero = abs(angular_v) < 1e-6
        
        if linear_v_zero and angular_v_zero:
            # 边界情况：静止，无运动指令
            # printc("提示：线速度和角速度均为0，AGV保持静止，不发送运动请求")
            # 终止当前action
            res = requests.delete(
                f"{cls.uri_pre()}/api/core/motion/v1/actions/:current",
                timeout=10
            )
            printc(f"终止当前action res={res.text}")
            return res

        elif not linear_v_zero and angular_v_zero:
            # 纯前进/纯后退（无旋转）
            if linear_v > 0:  # noqa: SIM108
                theta = 0.0  # 前进
            else:
                theta = 3.14  # 后退
        elif linear_v_zero and not angular_v_zero:
            # 原地左转/原地右转（无直线运动）
            if angular_v > 0:  # noqa: SIM108
                theta = 1.56  # 原地左转
            else:
                theta = -1.56  # 原地右转
        else:
            # 组合运动（直线+旋转）
            if linear_v > 0:
                # 前进+旋转
                if angular_v > 0:
                    theta = 0.785  # 前左转
                else:
                    theta = -0.785  # 前右转
            else:
                # 后退+旋转
                if angular_v > 0:
                    theta = 2.356  # 后左转
                else:
                    theta = 3.93  # 后右转
        
        # 3. 构造请求参数并发送POST请求
        try:
            res = requests.post(
                f"{cls.uri_pre()}/api/core/motion/v1/actions",
                json={
                    "action_name": "slamtec.agent.actions.MoveByAction",
                    "options": {
                        "theta": theta,
                        "duration": duration,  # 运动持续时间（ms）
                        # **kwargs  # 传入额外扩展参数（如果有）
                    },
                },
                timeout=10
            )
            printc(f"MoveByAction res={res.text}")
            return res
        except requests.exceptions.Timeout:
            printc("错误：请求超时（超过10秒），未收到AGV响应", "error")
            return None
        except requests.exceptions.ConnectionError:
            printc("错误：无法连接到AGV接口，请检查网络或接口地址", "error")
            return None
    
    @classmethod
    # @request_handler(timeout=1, max_retry=3)
    def agv_nav_cmd(cls, x=0, y=0, yaw=0, **kwargs):
        """
        - slamtec.agent.actions.MoveToAction ⾃主导航移动
        - slamtec.agent.actions.MultiFloorMoveAction ⾃主导航移动，⽀持跨楼层、POI⽬标点、多级调度
        - slamtec.agent.actions.MultiFloorBackHomeAction 跨楼层⾃主回桩
        - slamtec.agent.actions.SeriesMoveToAction 包含多个⽬标点的⾃主导航移动
        - slamtec.agent.actions.MoveByAction 遥控移动,需要定时调⽤以达到连续运动效果
        - slamtec.agent.actions.GoHomeAction ⾃主回桩
        - slamtec.agent.actions.RotateToAction 原地旋转，转到指定⻆度
        - slamtec.agent.actions.RotateAction 原地旋转，转动指定⻆度
        - slamtec.agent.actions.MoveToTagAction ⼆维码精准对接
        - slamtec.agent.actions.BackOffFromTagAction 从⼆维码前后退,防⽌碰撞。
        - slamtec.agent.actions.RecoverLocalizationAction 重定位
        - slamtec.agent.actions.ManualRelocalizationAction ⼿动重定位
        - slamtec.agent.actions.SweepAction 覆盖规划运动，适⽤于清扫、消毒等场景，所需
        - 固件版本为4.4
        - slamtec.agent.actions.ReturnToParkingAction ⾃主返航回到待命点（POI类型为
        PARKING），⽀持多机避障和排队功能（需要Lora模块），所需固件版本为4.5.5
        """
        if x == 0 or y == 0 or yaw == 0:
            printc("错误：请指定目标位置")
            return None
        try:
            res = requests.post(
                f"{cls.uri_pre()}/api/core/motion/v1/actions",
                json={
                    "action_name": "slamtec.agent.actions.MoveToAction",
                    "options": {
                        "target": {
                            "x": x,
                            "y": y,
                            # "yaw": yaw,
                            "z": 0,
                            # "poi_name": poi_name,
                        },
                        "move_options": {
                            # 导航模式：0：自由导航 1：严格轨道 2:轨道优先
                            "mode": 0,
                            # 标志
                            "flags": [
                                "with_yaw",  # 精确到角
                                "precise",  # 精确到点
                                # "fail_retry_count",  # 指定搜路失败后的重试次数，不指定时采⽤默认配置
                                # "find_path_ignoring_dynamic_obstacles", # 搜路时忽略动态障碍物，适⽤于⼈群拥挤、通道狭窄的区域
                            ],
                            "yaw": yaw,   # 到⽬标点后机器⼈的朝向，精确到⻆
                            # 可接受的到点范围，当⽬标点被占据时，机器⼈离⽬标点距离在该范围内都算成功，默认值为0.1⽶或0.18⽶，该值不影响机器⼈到点精度。
                            "acceptable_precision": 0.1,
                            "fail_retry_count": 0,   # 失败重试次数
                        },
                        # **kwargs  # 传入额外扩展参数（如果有）
                    },
                },
                timeout=10,
            )
            printc(f"MultiFloorMoveAction res={res.text}")
            return res
        except requests.exceptions.Timeout:
            printc("错误：请求超时（超过10秒），未收到AGV响应", "error")
            return None
        except requests.exceptions.ConnectionError:
            printc("错误：无法连接到AGV接口，请检查网络或接口地址", "error")
            return None

    @classmethod
    # @request_handler(timeout=1, max_retry=3)
    def agv_go_home_cmd(cls, **kwargs):
        try:
            res = requests.post(
                f"{cls.uri_pre()}/api/core/motion/v1/actions",
                json={
                    "action_name": "slamtec.agent.actions.GoHomeAction",
                    "gohome_options": {
                        "flags": "dock",
                        "back_to_landing": bool(1),
                        "charging_retry_count": 0,
                        "move_options": {
                            # 导航模式：0：自由导航 1：严格轨道 2:轨道优先
                            "mode": 0,
                        },
                    },
                },
            )
            printc(f"MultiFloorMoveAction res={res.text}")
            return res
        except requests.exceptions.Timeout:
            printc("错误：请求超时（超过10秒），未收到AGV响应", "error")
            return None
        except requests.exceptions.ConnectionError:
            printc("错误：无法连接到AGV接口，请检查网络或接口地址", "error")
            return None


    @classmethod
    # @request_handler(timeout=1, max_retry=3)
    def get_robot_info(cls, server_url=None):
        """
        获取机器人信息
        :param server_url: 自定义服务器URL，如果为None则使用默认的AGV_IP和AGV_PORT
        :return: 机器人信息字典，如果请求失败则返回None
        """
        try:
            # 使用自定义URL或默认URL
            if server_url:
                api_url = f"{server_url}/api/core/system/v1/robot/info"
            else:
                api_url = f"{cls.uri_pre()}/api/core/system/v1/robot/info"
                
            res = requests.get(api_url, timeout=10)
            if res.status_code == 200:
                return res.json()
            else:
                printc(f"获取机器人信息失败，HTTP错误码：{res.status_code}")
                return None
        except requests.exceptions.Timeout:
            printc("获取机器人信息超时（超过10秒）", "error")
            return None
        except requests.exceptions.ConnectionError:
            printc("无法连接到机器人接口，请检查网络或接口地址", "error")
            return None
        except Exception as e:
            printc(f"获取机器人信息时发生错误：{str(e)}", "error")
            return None
    
    @classmethod
    # @request_handler(timeout=1, max_retry=3)
    def get_localization_pose(cls, server_url=None):
        """
        获取机器人定位姿态信息
        :param server_url: 自定义服务器URL，如果为None则使用默认的AGV_IP和AGV_PORT
        :return: 定位姿态信息字典，如果请求失败则返回None
        """
        try:
            # 使用自定义URL或默认URL
            if server_url:
                api_url = f"{server_url}/api/core/slam/v1/localization/pose"
            else:
                api_url = f"{cls.uri_pre()}/api/core/slam/v1/localization/pose"
                
            res = requests.get(api_url, timeout=10)
            if res.status_code == 200:
                return res.json()
            else:
                printc(f"获取定位姿态信息失败，HTTP错误码：{res.status_code}")
                return None
        except requests.exceptions.Timeout:
            printc("获取定位姿态信息超时（超过10秒）", "error")
            return None
        except requests.exceptions.ConnectionError:
            printc("无法连接到机器人接口，请检查网络或接口地址", "error")
            return None
        except Exception as e:
            printc(f"获取定位姿态信息时发生错误：{str(e)}", "error")
            return None
    
    @classmethod
    # @request_handler(timeout=1, max_retry=3)
    def get_map_pois(cls, server_url=None):
        """
        获取地图点位信息
        :param server_url: 自定义服务器URL，如果为None则使用默认的AGV_IP和AGV_PORT
        :return: 地图点位列表，如果请求失败则返回None
        """
        try:
            # 使用自定义URL或默认URL
            if server_url:
                api_url = f"{server_url}/api/core/artifact/v1/pois"
            else:
                api_url = f"{cls.uri_pre()}/api/core/artifact/v1/pois"
                
            res = requests.get(api_url, timeout=10)
            if res.status_code == 200:
                return res.json()
            else:
                printc(f"获取地图点位信息失败，HTTP错误码：{res.status_code}")
                return None
        except requests.exceptions.Timeout:
            printc("获取地图点位信息超时（超过10秒）", "error")
            return None
        except requests.exceptions.ConnectionError:
            printc("无法连接到机器人接口，请检查网络或接口地址", "error")
            return None
        except Exception as e:
            printc(f"获取地图点位信息时发生错误：{str(e)}", "error")
            return None

    @classmethod
    # @request_handler(timeout=1, max_retry=3)
    def add_poi(cls, x=0, y=0, yaw=0, display_name="", poi_type=""):
        """
        添加地图点位信息
        :param x: 点位X坐标
        :param y: 点位Y坐标
        :param yaw: 点位Yaw角度
        :param metadata: 点位元数据，字典格式
        :return: 如果添加成功则返回True，否则返回False
        """
        if display_name == "":
            printc("点位名称不能为空")
            return False
        # if poi_type == "":
        #     printc("点位类型不能为空")
        #     return False
        try:
            # 调用方应当随机生成一个UUID作为id, metadata中的display_name用于界面显示, type用于区分POI类型。
            # 在建图过程中添加POI时，建议不包含Pose，此时会用机器人当前位置创建POI，并且记录传感器观测信息，在闭环后会进行位姿调整。
            # 使用自定义URL或默认URL
            metadata = {
                "display_name": display_name,
                "type": poi_type,
            }
            pose = {
                "x": x,
                "y": y,
                "yaw": yaw,
            }

            api_url = f"{cls.uri_pre()}/api/core/artifact/v1/pois"
            if x == 0 and y == 0 and yaw == 0:
                res = requests.post(api_url, json={
                    "id": uuid.uuid4().hex,
                    "metadata": metadata,
                })
            else:
                res = requests.post(api_url, json={
                    "id": uuid.uuid4().hex,
                    "pose": pose,
                    "metadata": metadata,
                })

            if res.status_code == 200:
                return res.json()
            else:
                printc(f"获取地图点位信息失败，HTTP错误码：{res.status_code}", "error")
                return None
        except requests.exceptions.Timeout:
            printc("获取地图点位信息超时（超过10秒）", "error")
            return None
        except requests.exceptions.ConnectionError:
            printc("无法连接到机器人接口，请检查网络或接口地址", "error")    
            return None
        except Exception as e:
            printc(f"获取地图点位信息时发生错误：{str(e)}", "error")
            return None
