import pyrealsense2 as rs
import numpy as np
import cv2


def main():
    # ====== 1️⃣ 创建配置 ======
    pipeline = rs.pipeline()
    config = rs.config()

    # 启用 RGB + 深度 + 红外
    config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
    config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
    config.enable_stream(rs.stream.infrared, 1, 640, 480, rs.format.y8, 30)

    # ====== 2️⃣ 启动管道 ======
    pipeline.start(config)

    # 创建对齐器，让深度对齐到彩色图
    align_to = rs.stream.color
    align = rs.align(align_to)

    print("✅ RealSense D435i 已启动，按 'q' 退出")

    try:
        while True:
            # ====== 3️⃣ 获取帧 ======
            frames = pipeline.wait_for_frames()
            aligned_frames = align.process(frames)

            depth_frame = aligned_frames.get_depth_frame()
            color_frame = aligned_frames.get_color_frame()
            ir_frame = frames.get_infrared_frame()

            if not depth_frame or not color_frame or not ir_frame:
                continue

            # ====== 4️⃣ 转换为 numpy 数组 ======
            color_image = np.asanyarray(color_frame.get_data())
            depth_image = np.asanyarray(depth_frame.get_data())
            ir_image = np.asanyarray(ir_frame.get_data())

            # ====== 5️⃣ 可视化 ======
            # 将深度图归一化为伪彩色
            depth_colormap = cv2.applyColorMap(
                cv2.convertScaleAbs(depth_image, alpha=0.03),
                cv2.COLORMAP_JET
            )

            # 三图拼接显示
            images = np.vstack((color_image, depth_colormap, cv2.cvtColor(ir_image, cv2.COLOR_GRAY2BGR)))

            cv2.imshow('RGB | Depth | Infrared', images)

            # 按 q 退出
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    finally:
        # ====== 6️⃣ 停止管道 ======
        pipeline.stop()
        cv2.destroyAllWindows()
        print("🛑 已关闭 RealSense 设备")


if __name__ == "__main__":
    main()
