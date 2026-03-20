import time
import os
import sys


try:
    sys.path.append("/home/sy/wk/roh_with_rm65/RM-API2")
    # sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    # sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'roh_with_rm65/RM-API2')))
    from common.roh_registers_v1 import *
    from common.robotic_arm import *
except ImportError as e:
    print(f"[ERROR] Failed to import RM-API2 modules: {e}")
    raise e


class DexterousHand:
    """
    灵巧手控制类：支持五指独立控制、整体开合、旋转拇指根部等操作。
    """

    def __init__(self, arm_ip: str, com_port: int = 1, roh_addr: int = 2, delay: float = 1.0):
        self.arm_ip = arm_ip
        self.com_port = com_port
        self.roh_addr = roh_addr
        self.delay = delay

        # 初始化机械臂通讯
        self.robot = RobotArmController(arm_ip, 8080, 3)
        self.robot.Close_Modbustcp_Mode()
        self.robot.Set_Modbus_Mode(com_port, 115200, 1)
        print(f"✅ 机械臂灵巧手 {arm_ip} 初始化完成")
        self.arm = self.robot

    # -------------------------------------------------------------
    # 底层寄存器操作
    # -------------------------------------------------------------
    def _write_registers(self, address, values):
        params = rm_peripheral_read_write_params_t()
        params.port = self.com_port
        params.device = self.roh_addr
        params.address = address
        params.num = len(values)

        values_bytes = []
        for v in values:
            values_bytes.extend([(v >> 8) & 0xFF, v & 0xFF])

        ret = self.robot.Write_Registers(params, values_bytes)
        if ret != 0:
            print(f"[ERROR] Write_Registers failed: {ret}")
            return False
        return True

    def _read_registers(self, address, num):
        params = rm_peripheral_read_write_params_t()
        params.port = self.com_port
        params.device = self.roh_addr
        params.address = address
        params.num = num

        tag, ret = self.robot.Read_Registers(params)
        if tag != 0:
            print(f"[ERROR] Read_Registers failed: {tag}")
            return None

        data = [(ret[i] | (ret[i + 1] << 8)) for i in range(0, num * 2, 2)]
        return data

    # -------------------------------------------------------------
    # 手指控制方法
    # -------------------------------------------------------------
    def open_all(self):
        """打开所有手指"""
        print("[ACTION] Open all fingers")
        self._write_registers(ROH_FINGER_POS_TARGET0, [0, 0, 0, 0, 0])
        time.sleep(self.delay)

    def close_all(self):
        """闭合所有手指"""
        print("[ACTION] Close all fingers")
        self._write_registers(ROH_FINGER_POS_TARGET0, [0, 65535, 65535, 65535, 65535])
        # time.sleep(self.delay)
        # self._write_registers(ROH_FINGER_POS_TARGET0, [65535/2, 65535, 65535, 65535, 65535])
        time.sleep(self.delay)

    def move_finger(self, index: int, position: int):
        """
        控制单个手指（0-4为手指，5为拇指根部）
        position: 0~65535
        """
        if index < 0 or index > 5:
            print("[ERROR] Finger index out of range (0-5)")
            return
        print(f"[ACTION] Move finger {index} -> {position}")
        addr = ROH_FINGER_POS_TARGET0 + index
        self._write_registers(addr, [position])
        time.sleep(self.delay)

    def close_finger(self, index: int, degree: float = 100):
        """
        以百分比方式闭合单个手指
        degree: 0-100，对应 0~65535
        """
        pos = int(65535 * (degree / 100.0))
        self.move_finger(index, pos)

    def open_finger(self, index: int):
        """打开指定手指"""
        self.move_finger(index, 0)

    def rotate_thumb(self, degree: float = 100):
        """旋转拇指根部"""
        pos = int(65535 * (degree / 100.0))
        self._write_registers(ROH_FINGER_POS_TARGET5, [pos])
        time.sleep(self.delay)

    # -------------------------------------------------------------
    # 状态读取
    # -------------------------------------------------------------
    def get_target_positions(self):
        """读取目标位置"""
        return self._read_registers(ROH_FINGER_POS_TARGET0, 5)

    def get_current_positions(self):
        """读取当前实际位置"""
        return self._read_registers(ROH_FINGER_POS0, 5)

    # -------------------------------------------------------------
    # 综合动作示例
    # -------------------------------------------------------------
    def test_sequence(self, loops=5):
        for i in range(loops):
            print(f"\n--- Loop {i + 1} ---")

            # 拇指闭合-张开
            self.close_finger(0)
            self.open_finger(0)

            # 拇指旋转
            self.rotate_thumb(100)
            self.rotate_thumb(0)

            # 其他手指闭合-张开
            self._write_registers(ROH_FINGER_POS_TARGET1, [65535, 65535, 65535, 65535])
            time.sleep(self.delay)
            self._write_registers(ROH_FINGER_POS_TARGET1, [0, 0, 0, 0])
            time.sleep(self.delay)

            target = self.get_target_positions()
            current = self.get_current_positions()
            print(f"Target: {target}")
            print(f"Current: {current}")

        print("[INFO] Test sequence complete.")

    
    def test_seq(self):
        self.open_all()
        self.close_all()
        self.close_finger(0, 50)
