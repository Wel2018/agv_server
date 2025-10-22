# from projects.agv_server.sdk.realman_arm import RealmanArmClient
# arm_L = RealmanArmClient("192.168.10.20")
# arm_R = RealmanArmClient("192.168.10.19")
# ret, p1 = arm_L.get_pose()
# ret, p2 = arm_R.get_pose()
# print("L:", p1)
# print("R:", p2)

import os
import sys


# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__))))
# robotic_arm_controller.rm_robot_interface import *
sys.path.append("/home/sy/wk/roh_with_rm65/RM-API2")
# sys.path.append("/home/sy/wk/projects/agv_server")
# from projects.agv_server.sdk.hand import DexterousHand
from common.robotic_arm import * # type: ignore


class RobotArmController:
    def __init__(self, ip, port=8080, level=3, mode=2):
        self.thread_mode = rm_thread_mode_e(mode) # type: ignore
        self.robot = RoboticArm(self.thread_mode) # type: ignore
        self.handle = self.robot.rm_create_robot_arm(ip, port)

        if self.handle.id == -1:
            print("\nFailed to connect to the robot arm\n")
            exit(1)
        else:
            print(f"\nSuccessfully connected to the robot arm: {self.handle.id}\n")


arm = RobotArmController("192.168.10.19")
print(arm.robot.rm_get_current_arm_state())
