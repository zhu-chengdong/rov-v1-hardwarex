#!/usr/bin/env python3
import os as _hardwarex_os

def _hardwarex_path(relative_path):
    # Explicit workspace for private data and generated outputs.
    work_root = _hardwarex_os.environ["HARDWAREX_WORK_ROOT"]
    if not _hardwarex_os.path.isabs(work_root):
        raise ValueError("HARDWAREX_WORK_ROOT must be an absolute path")
    return _hardwarex_os.path.join(work_root, relative_path)

import rosbag
import cv2
import os
from cv_bridge import CvBridge

# 这个脚本是用来提取图像的，ov2311的bag先转化为图片之后，再去制作gt
# =========================
# 参数（直接改这里）
# =========================
bag_path = _hardwarex_path('bags/newbag/gt/sequence_08/3.bag')                 # 你的bag路径
output_dir = _hardwarex_path('bags/newbag/gt/sequence_08/3')                 # 输出文件夹
topic_name = "/camera/image_raw"      # 你的图像topic

# =========================
# 初始化
# =========================
os.makedirs(output_dir, exist_ok=True)
bridge = CvBridge()

bag = rosbag.Bag(bag_path, 'r')

count = 0
saved = 0

print("Start extracting images...")

for topic, msg, t in bag.read_messages(topics=[topic_name]):

    count += 1

    try:
        # ===== 核心：保持原始编码 =====
        if msg.encoding == "mono8":
            img = bridge.imgmsg_to_cv2(msg, desired_encoding="mono8")
        else:
            img = bridge.imgmsg_to_cv2(msg, desired_encoding="bgr8")

    except Exception as e:
        print("Convert failed:", e)
        continue

    # ===== 时间戳（关键）=====
    timestamp = msg.header.stamp.to_sec()

    filename = os.path.join(output_dir, f"{timestamp:.6f}.png")

    # ===== 保存 =====
    ok = cv2.imwrite(filename, img)

    if ok:
        saved += 1
    else:
        print("Write failed:", filename)

    if saved % 100 == 0:
        print(f"Saved {saved} images...")

bag.close()

print("Done.")
print("Total read:", count)
print("Total saved:", saved)
