import cv2
import pyrealsense2 as rs
import numpy as np


class RealSenseCam:
    """头部相机"""
    
    def __init__(self) -> None:
        # ====== 1️⃣ 创建配置 ======
        pipeline = rs.pipeline() # type: ignore
        config = rs.config() # type: ignore

        # 启用 RGB + 深度 + 红外
        config.enable_stream(rs.stream.color, 1280, 720, rs.format.bgr8, 30) # type: ignore
        config.enable_stream(rs.stream.depth, 848, 480, rs.format.z16, 30) # type: ignore

        # config.enable_stream(rs.stream.infrared, 1, 640, 480, rs.format.y8, 30) # type: ignore

        # ====== 2️⃣ 启动管道 ======
        pipeline.start(config)

        # 创建对齐器，让深度对齐到彩色图
        align_to = rs.stream.color # type: ignore
        self.align = rs.align(align_to) # type: ignore
        print("✅ RealSense D455 已启动")

        self.pipeline = pipeline
        self.config = config
        self.frames = self.pipeline.wait_for_frames()
        self.aligned_frames = self.align.process(self.frames)
    
    def get_depth(self, x: int, y: int):
        depth_frame = self.aligned_frames.get_depth_frame()
        depth = depth_frame.get_distance(int(x), int(y))
        return depth

    def read(self):
        # ====== 3️⃣ 获取帧 ======
        self.frames = self.pipeline.wait_for_frames()
        self.aligned_frames = self.align.process(self.frames)
        self.aligned_frames.keep()

        depth_frame = self.aligned_frames.get_depth_frame()
        color_frame = self.aligned_frames.get_color_frame()
        # ir_frame = frames.get_infrared_frame()

        if not depth_frame or not color_frame:
            return {}

        # ====== 4️⃣ 转换为 numpy 数组 ======
        color_image = np.asanyarray(color_frame.get_data())
        depth_image = np.asanyarray(depth_frame.get_data())
        # ir_image = np.asanyarray(ir_frame.get_data())
        # ir = cv2.cvtColor(ir_image, cv2.COLOR_GRAY2BGR)

        # ====== 5️⃣ 可视化 ======
        # 将深度图归一化为伪彩色
        depth_colormap = cv2.applyColorMap(
            cv2.convertScaleAbs(depth_image, alpha=0.03),
            cv2.COLORMAP_JET
        )

        img0 = color_image
        # img1 = ir
        img2 = depth_colormap
        
        data = {
            "color": img0,
            # "ir": img1,
            "depth": img2,
        }
        return data
