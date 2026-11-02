#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os as _hardwarex_os

def _hardwarex_path(relative_path):
    # Explicit workspace for private data and generated outputs.
    work_root = _hardwarex_os.environ["HARDWAREX_WORK_ROOT"]
    if not _hardwarex_os.path.isabs(work_root):
        raise ValueError("HARDWAREX_WORK_ROOT must be an absolute path")
    return _hardwarex_os.path.join(work_root, relative_path)

import os
import rosbag
import cv2
from cv_bridge import CvBridge


# =========================
# 路径（直接写死）
# =========================
bag_path = _hardwarex_path('York-Tank/rosbags/1_reference1.bag')
output_dir = _hardwarex_path('York-Tank/sequences/1_reference1')

# =========================
# topics
# =========================
left_topic  = "/camera/left/image_rect_underwater"
right_topic = "/camera/right/image_rect_underwater"

# =========================
# 输出文件夹
# =========================
left_dir  = os.path.join(output_dir, "left")
right_dir = os.path.join(output_dir, "right")

os.makedirs(left_dir, exist_ok=True)
os.makedirs(right_dir, exist_ok=True)

bridge = CvBridge()

left_buffer = {}
right_buffer = {}

print("Reading bag...")

with rosbag.Bag(bag_path, "r") as bag:
    for topic, msg, t in bag.read_messages(topics=[left_topic, right_topic]):

        # 使用图像自身 header 时间戳
        timestamp = msg.header.stamp.to_sec()

        try:
            img = bridge.imgmsg_to_cv2(msg, desired_encoding="mono8")
        except Exception:
            img = bridge.imgmsg_to_cv2(msg, desired_encoding="bgr8")

        if topic == left_topic:
            left_buffer[timestamp] = img
        elif topic == right_topic:
            right_buffer[timestamp] = img


print("Matching stereo pairs...")

left_times = sorted(left_buffer.keys())
right_times = sorted(right_buffer.keys())

i, j = 0, 0
pair_count = 0

max_time_diff = 0.02   # 20 ms

while i < len(left_times) and j < len(right_times):

    t_l = left_times[i]
    t_r = right_times[j]

    dt = abs(t_l - t_r)

    if dt <= max_time_diff:

        img_l = left_buffer[t_l]
        img_r = right_buffer[t_r]

        # COLMAP 可以接受这种文件名
        # 左右图必须同名，方便后续 stereo matching
        filename = f"{t_l:.9f}.png"

        cv2.imwrite(os.path.join(left_dir, filename), img_l)
        cv2.imwrite(os.path.join(right_dir, filename), img_r)

        pair_count += 1
        i += 1
        j += 1

    elif t_l < t_r:
        i += 1
    else:
        j += 1


print("Done.")
print(f"Left images:  {len(os.listdir(left_dir))}")
print(f"Right images: {len(os.listdir(right_dir))}")
print(f"Matched stereo pairs: {pair_count}")
print(f"Output directory: {output_dir}")
