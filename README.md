# AGV Server 项目说明

## 启动底盘服务脚本

> 包括机械臂、灵巧手、夹爪、底盘的访问和控制

```sh
bash run.sh
```

> API 文档见 http://192.168.31.177:29000/docs


## 获取全局数据状态

```python
url = "http://192.168.31.177:29000/get_data"
res = requests.get(url)
```

响应值格式参考：

```json
{
  "fall_detector_status": 0,  // 跌落状态
  // 底盘状态
  "agv": {
    "command": "/api/robot_status",
    "error_message": "",
    "results": {
      "charge_state": false,
      "chargepile_id": "0",
      "chassis_lift_state": 2,
      "collision_state": 0,
      "current_floor": 1,
      "current_pose": {
        "theta": -1.6533,
        "x": 0.2913,
        "y": 0.4408
      },
      "error_code": "00000000",
      "estop_state": false,
      "extraData": "",
      "hall_state": 0,
      "hand_charge": false,
      "hard_estop_abolish_state": false,
      "hard_estop_state": false,
      "is_paused": false,
      "move_retry_times": 0,
      "move_status": "idle",
      "move_target": "",
      "outTaskId": "",
      "power_percent": 15,
      "running_status": "idle",
      "soft_estop_state": false,
      "target_floor": 0,
      "task_id": "",
      "ts": 1761126310.2995
    },
    "status": "OK",
    "type": "response",
    "uuid": ""
  },
  // 左臂状态
  "arm_L": {
    "joint": [
      12.932999610900879,
      -35.02299880981445,
      -80.63400268554688,
      134.70399475097656,
      24.969999313354492,
      -260.48699951171875
    ],
    "pose": [
      0.433992,
      0.055335,
      0.264149,
      2.5,
      0.602,
      2.035
    ],
    "err": {
      "err_len": 1,
      "err": [
        "0"
      ]
    }
  },
  // 右臂状态
  "arm_R": { ... }
}
```

## 摄像头流式访问

```python
stream = requests.get("http://192.168.31.177:29000/video", stream=True)
bytes_data = b""
for chunk in stream.iter_content(chunk_size=1024):
    if not self.is_run:
        break
    bytes_data += chunk
    a = bytes_data.find(b'\xff\xd8')  # JPEG start
    b = bytes_data.find(b'\xff\xd9')  # JPEG end
    if a != -1 and b != -1:
        jpg = bytes_data[a:b+2]
        bytes_data = bytes_data[b+2:]
        np_img = np.frombuffer(jpg, dtype=np.uint8)
        frame = cv2.imdecode(np_img, cv2.IMREAD_COLOR)
```
