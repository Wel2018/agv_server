import sys
import threading
import numpy as np
from rich import print
from toolbox.core.time_op import get_time_str
# from toolbox.robot.franka_arm_client import FrankaArmClient
from toolbox.qt import qtbase
from .ui.ui_form import Ui_DemoWindow
# from toolbox.robot.robot_collect import FrankaCollector
# from .setting import SettingWindow
from . import AppConfig, logger, VERBOSE, THREAD_DEBUG, APPCFG
# from .bgtask.spacemouse import SpaceMouseListener


class WorkMode:
    """遥操作工作模式"""
    idle = 0
    forward = 1
    backward = 2 
    left = 3
    right = 4


class MainWindow(qtbase.IMainWindow):
    """应用具体实现"""
    # 定时器和线程名称
    TH_COLLECT = "collect"
    TH_SYNC = "sync"
    TH_CAM = "cam3d"
    TH_CTL_MODE = "teleop_ctl_mode"
    TIMER_ROBOT_STATE = "robot_state"

    is_quit_confirm = 0  # 程序退出确认
    is_keyboard_ctrl = 1  # 键盘控制开关
    is_collect_data = 0  # 数据集收集开关
    is_gripper_open = 1  # 当前夹爪状态
    is_mirror = 0  # 是否镜像操控 
    is_debug = 0
    is_going_to_init_pos = 0
    is_estop = 0
    VERBOSE = VERBOSE

    def __init__(self, parent = None):
        ui = self.ui = Ui_DemoWindow()
        super().__init__(ui, parent)

        # 初始化
        self.init(
            confcache_name="agv_teleop",
            apptitle=AppConfig.title,
            ui_logger=ui.txt_log,
            logger=logger,
            fontsize=AppConfig.fontsize,
        )

        # 子页面
        # self.setting_wd = SettingWindow(self)
        # self.kb_mapp = self.setting_wd.keyboard_mapp

        # 绑定点击事件
        # self.bind_clicked(ui.btn_setting, lambda: self.setting_wd.showNormal())
        self.bind_clicked(ui.btn_clear, self.clean_log)
        self.bind_clicked(ui.btn_goto, self.play)
        self.bind_clicked(ui.btn_estop, self.estop)
        self.bind_clicked(ui.btn_cancel, self.cancel)

        # 设置勾选状态
        self.set_check(ui.is_keyboard_ctrl, self.is_keyboard_ctrl)
        self.set_check(ui.is_collect_data, self.is_collect_data)
        self.set_check(ui.is_mirror, self.is_mirror)
        # self.bind_checked(ui.is_collect_data, self.collect_data)
        
        self.mode = WorkMode.idle
        
        # 遥操作控制步长改变
        # 线速度、角速度
        self.pos_vel = ui.step_posi_vel.value()
        self.rot_vel = ui.step_angle_vel.value()
        self.max_duration = 1000*60
        
        # 在 lambda 表达式中不能使用赋值语句
        self.bind_val_changed(
            ui.step_posi_vel, 
            lambda val: \
                setattr(self, 'pos_vel', round(val,3))
        )
        
        self.bind_val_changed(
            ui.step_angle_vel, 
            lambda val: \
                setattr(self, 'rot_vel', round(val,3))
        )

        # 摄像头
        zero_img = np.zeros((480, 640, 3), dtype=np.uint8)
        self.zero_img = qtbase.QPixmap(qtbase.cv2qt(zero_img))
        self.reset_viz()

        #self.tcost = Timecost(0, 1)
        self.pressed_keys = set()
        
        # 机械臂控制 --------------------
        # self.arm = FrankaArmClient()
        # self.arm.gozero()

        # 底盘控制 -------------------
        from .agv import AgvHttpClient
        self.agv = AgvHttpClient()
        #res = self.agv.get_robot_res()
        #self.add_log(f"agv={res}")
        markers = self.agv.list_map_marker()
        mk = markers['results'].keys() # type: ignore
        print(mk)
        self.add_log(f"agv targets={mk}")
        
        self.add_log("程序初始化完成")
        
        # 检查服务器是否能够正常连接
        # self.add_timer(self.TIMER_ROBOT_STATE, 100, self.refresh_state, 1)


    def play(self):
        """执行任务理解逻辑"""
        target = self.ui.target.text()
        self.add_log(f"agv goto {target}")
        self.agv.nav_to_target(target)


    def estop(self):
        if not self.is_estop:
            self.add_log("进入急停模式")
            self.agv.force_stop(1)
            self.is_estop = 1
        else:
            self.add_log("退出急停模式")
            self.agv.force_stop(0)
            self.is_estop = 0

    def cancel(self):
        self.add_log("取消当前动作")
        res = self.agv.cancel_move()
        print(res)


    def reset_viz(self):
        self.pix_left = self.zero_img
        self.pix_right = self.zero_img

    
    def refresh_state(self):
        ...

    def keyboard_ctl(self, state):
        #state: 0 未勾选, 1 半勾选, 2 勾选
        if state == 2:
            self.is_keyboard_ctrl = 1
            self.add_log("开启遥操作模式")
        else:
            self.is_keyboard_ctrl = 0
            self.add_log("关闭遥操作模式")
        

    def get_empty_incr(self):
        incr = {
            "linear_v": .0,
            "angular_v": .0,
        }
        return incr
    
    def add_key(self, key: str):
        if key not in self.pressed_keys:
            self.pressed_keys.add(key)
            # print(f"key add {key}")
            # pressed_keys={'D', 'W'}
        self.set_ctl_cmd(str(list(self.pressed_keys)))
        
    
    def remove_key(self, key: str):
        self.pressed_keys.discard(key)
        self.set_ctl_cmd(str(list(self.pressed_keys)))
        
    
    def get_cmd(self, key: str):
        if key == "W":
            return WorkMode.forward
        elif key == "S":
            return WorkMode.backward
        elif key == "A":
            return WorkMode.left
        elif key == "D":
            return WorkMode.right
        else:
            return WorkMode.idle


    def keyPressEvent(self, event: qtbase.QKeyEvent):
        """按下按键：键盘打开 caps lock 模式，可以实现长按模式
        （即按住 A，只会触发一次 keyPressEvent，不会连续触发，松开也是只触发一次）
        - 键盘长按会在第一次 isAutoRepeat=False, 之后是 True
        """
        if not self.is_keyboard_ctrl:
            return
        
        if event.isAutoRepeat():
            key = event.text().upper()
            self.add_key(key)

            if self.VERBOSE:
                print(f"keyPressEvent {event}")
            
            incr = self.get_empty_incr()
            
            # 遍历当前按下的按键
            print(f"k={self.pressed_keys}")
            for key in self.pressed_keys:
                # 如果当前按下的按键已经绑定
                # ['forward', 'backward', 'left', 'right', '']
                cmd = self.get_cmd(key)
                speed = 0.2

                if cmd == WorkMode.idle:
                    ...
                elif cmd == WorkMode.forward:
                    incr['linear_v'] = speed
                elif cmd == WorkMode.backward:
                    incr['linear_v'] = -speed
                elif cmd == WorkMode.left:
                    incr['angular_v'] = speed
                elif cmd == WorkMode.right:
                    incr['angular_v'] = -speed
                else:
                    raise ValueError(f"cmd={cmd}")

            print(f"速度控制 {incr}")
            # end for
            self.agv.velocity_control(
                incr['linear_v'], # type: ignore
               incr['angular_v'], # type: ignore
            )

        return super().keyPressEvent(event)
    
    
    def keyReleaseEvent(self, event):
        """松开按键"""
        if not self.is_keyboard_ctrl:
            return
        incr = self.get_empty_incr()
        
        if not event.isAutoRepeat():
            key = event.text().upper()
            self.remove_key(key)
            #cmd = self.get_cmd(key)
            #print(f"cmd={cmd} key={key}")
            #self.agv.velocity_control_stop()
            # 遍历当前按下的按键
            print(f"k={self.pressed_keys}")
            
            for key in self.pressed_keys:
                # 如果当前按下的按键已经绑定
                # ['forward', 'backward', 'left', 'right', '']
                cmd = self.get_cmd(key)
                speed = 0.2

                if cmd == WorkMode.idle:
                    ...
                elif cmd == WorkMode.forward:
                    incr['linear_v'] = speed
                elif cmd == WorkMode.backward:
                    incr['linear_v'] = -speed
                elif cmd == WorkMode.left:
                    incr['angular_v'] = speed
                elif cmd == WorkMode.right:
                    incr['angular_v'] = -speed
                else:
                    raise ValueError(f"cmd={cmd}")

            print(f"速度控制 {incr}")
            # end for
            self.agv.velocity_control(
                incr['linear_v'], # type: ignore
               incr['angular_v'], # type: ignore
            )
            

    def set_ctl_cmd(self, cmd: str):
        self.ui.ctl_state.setText(cmd)
        # res = api.set_data("ctl", cmd)
    
    def set_op_cmd(self, cmd: str):
        self.ui.ctl_state.setText(cmd)
        # res = api.set_data("op", cmd)

    def get_obs(self, frames: dict):
        self.pix_left = qtbase.QPixmap(qtbase.cv2qt(frames['v1']))
        self.pix_right = qtbase.QPixmap(qtbase.cv2qt(frames['v2']))

    def paintEvent(self, event: qtbase.QtGui.QPaintEvent) -> None:
        """图像显示区支持自适应缩放"""
        ui = self.ui
        self._resize_and_scaled(ui.lb_left, ui.wd_left, self.pix_left)
        self._resize_and_scaled(ui.lb_right, ui.wd_right, self.pix_right)
        return super().paintEvent(event)

    def close_ready(self):
        ...
    
    
def main():
    qapp = qtbase.QApplication(sys.argv)
    # 设置全局默认字体
    qapp.setFont(qtbase.QFont("微软雅黑", 11))
    mapp = MainWindow()
    mapp.show()
    sys.exit(qapp.exec())
