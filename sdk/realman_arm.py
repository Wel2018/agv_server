# 官方文档：https://develop.realman-robotics.com/robot/apipython/classes/roboticArm/
# 安装：pip install Robotic_Arm
# Successfully installed Robotic_Arm-1.1.1
from Robotic_Arm.rm_robot_interface import * # type: ignore
import numpy as np
from rich import print


"""
current c api version:  1.1.1
机械臂ID： 1

================== Arm Software Information ==================
Arm Model:  RML63III-BI
Algorithm Library Version:  1.5.5-c0d52d18
Control Layer Software Version:  V1.7.1
Dynamics Version:  2
Planning Layer Software Version:  V1.7.1
==============================================================
"""


# 绕 X 轴的旋转矩阵生成函数
def rotx(theta):
    """生成绕 X 轴旋转的 3x3 旋转矩阵，theta 为弧度"""
    return np.array([
        [1, 0, 0],
        [0, np.cos(theta), -np.sin(theta)],
        [0, np.sin(theta), np.cos(theta)]
    ])


def roty(theta):
    """生成绕 Y 轴旋转的 3x3 旋转矩阵，theta 为弧度"""
    return np.array([
        [np.cos(theta), 0, -np.sin(theta)],
        [0, 1, 0],
        [np.sin(theta), 0, np.cos(theta)]
    ])


def rotz(theta):
    """生成绕 Z 轴旋转的 3x3 旋转矩阵，theta 为弧度"""
    return np.array([
        [np.cos(theta), -np.sin(theta), 0],
        [np.sin(theta), np.cos(theta), 0],
        [0, 0, 1],
    ]
    )


def pose_by_rot(pose: list, rot_axis='x', theta=0.01):
    """绕轴旋转"""
    # 提取 pose 并处理精度
    # pose0 = response.get("arm_state", {}).get("pose", [0, 0, 0, 0, 0, 0])
    position = pose[:3]  # [x, y, z]
    # prec = 0.001
    prec = 1
    rpy = [x * prec for x in pose[3:]]  # [roll, pitch, yaw] 乘以精度 0.001 转换为弧度

    # 步骤 2: 将 RPY 转换为旋转矩阵 R0
    arm_model = rm_robot_arm_model_e.RM_MODEL_RM_65_E
    # arm_model = rm_robot_arm_model_e.RM_MODEL_RM_63_III_E # type: ignore
    force_type = rm_force_type_e.RM_MODEL_RM_B_E # type: ignore
    algo_handle = Algo(arm_model, force_type) # type: ignore
    R0 = algo_handle.rm_algo_euler2matrix(rpy)  # R0 为 rm_matrix_t 类型

    # 打印 R0.data
    # 直接打印 4×4 矩阵
    # if len(R0.data) == 16:  # 如果是一维数组
    #     print("R0 (4x4 Matrix):")
    #     for i in range(4):
    #         row_start = i * 4
    #         row = R0.data[row_start: row_start + 4]  # 提取每一行
    #         print("[", end=" ")
    #         for val in row:
    #             print(f"{val:8.4f}", end=" ")
    #         print("]")

    # 提取 3×3 旋转矩阵
    # 方法1：调用专用函数获取数据
    # if hasattr(R0, 'to_list'):
    #     R_list = R0.to_list()  # 转换为 Python 列表
    #     R_3x3 = [R_list[i][:3] for i in range(3)]

    # 方法2：使用 NumPy 转换（推荐）
    R_np = np.array(R0.data).reshape(4, 4)  # 转为 4×4 numpy 数组
    R_3x3 = R_np[:3, :3]  # 切片取 3×3
    # print(R_3x3)

    rot_method = rotx
    if rot_axis == 'x':
        rot_method = rotx
    elif rot_axis == 'y':
        rot_method = roty
    elif rot_axis == 'z':
        rot_method = rotz

    dR = rot_method(theta)  # 绕 X 轴旋转，角度为 sin(t)
    # dR = roty(np.sin(t))  # 绕 X 轴旋转，角度为 sin(t)
    # dR = rotz(np.sin(t))  #绕 Z 轴旋转，角度为 sin（t）

    # 计算更新后的旋转矩阵 R
    # R = np.dot(dR, np.array(R0.data)[:3, :3])  # 只取 R0.data 的 3x3 旋转部分
    R = np.dot(dR, R_3x3)  # 只取 R0.data 的 3x3 旋转部分

    # 打印 R
    # print(f"\nTime: {t:.2f}, R:")
    # for row in R:
    #     print([f"{x:.6f}" for x in row])

    # 将 R 转换为位姿
    data = [[R[0][0], R[0][1], R[0][2], 0],
            [R[1][0], R[1][1], R[1][2], 0],
            [R[2][0], R[2][1], R[2][2], 0],
            [0, 0, 0, 1]]
    
    mat = rm_matrix_t(4, 4, data) # type: ignore
    new_pose = algo_handle.rm_algo_matrix2pos(mat)  # 转换为 [x, y, z, roll, pitch, yaw]
    # scaled_list = list(map(lambda val: val / 1000000, position))  # 用 map 处理
    # scaled_list = list(map(lambda val: val / 1.0, position))  # 用 map 处理
    # print("缩放后的列表:", scaled_list)
    new_pose[:3] = position  # 保持原始位置 [x, y, z]

    # 打印新位姿
    # print(f"New pose: {new_pose}")
    return new_pose


class RealmanArmClient:

    def __init__(self, ip="192.168.10.19") -> None:
        self.robot = RoboticArm(rm_thread_mode_e.RM_TRIPLE_MODE_E) # type: ignore
        self.handle = self.robot.rm_create_robot_arm(ip, 8080)
        ret = self.robot.rm_get_total_tool_frame()
        # print(f"rm_get_total_tool_frame={ret}")
        # self.robot.rm_change_tool_frame("hhltest2")
        # self.robot.rm_change_tool_frame("Arm_Tip")
        # self.robot.rm_change_work_frame("Arm_Tip")

        software_info = self.robot.rm_get_arm_software_info()
        if software_info[0] == 0:
            print("\n================== Arm Software Information ==================")
            print(f"机械臂ID：{self.handle.id}")
            print("机械臂型号: ", software_info[1]['product_version'])
            print("算法库版本: ", software_info[1]['algorithm_info']['version'])
            print("控制层软件版本: ", software_info[1]['ctrl_info']['version'])
            print("Dynamics Version: ", software_info[1]['dynamic_info']['model_version'])
            print("规划层软件版本: ", software_info[1]['plan_info']['version'])
            print("==============================================================\n")
        else:
            print("\nFailed to get arm software information, Error code: ", software_info[0], "\n")
        # self.gozero()
        print(f"✅ 机械臂 {ip} 初始化完成")
    
    def gozero(self):
        ret = self.robot.rm_movej([
            116,
            45,
            -120,
            110,
            25,
            -87
        ], 
        # ret = self.robot.rm_movej([
        #     90.42400360107422, 
        #     48.599998474121094, 
        #     -119.23500061035156, 
        #     175.34500122070312, 
        #     17.634000778198242, 
        #     -148.9080047607422
        # ], 
            20, 0, 0, 1)

    def move_p_canfd(self, pose: list):
        # self.robot.rm_movej_p
        ret = self.robot.rm_movep_canfd(pose, False, 1, 60)
        print(f"MOVE_P: {pose}, ret={ret}")

    def gripper_open(self):
        ret = self.robot.rm_set_gripper_release(500, True, 10)

    def gripper_close(self):
        ret = self.robot.rm_set_gripper_pick(500, 200, True, 10)

    def __del__(self):
        ret = self.robot.rm_delete_robot_arm()

    def get_pose(self):
        return self.robot.rm_get_current_arm_state()
    