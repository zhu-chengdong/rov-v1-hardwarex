#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os as _hardwarex_os

def _hardwarex_path(relative_path):
    # Explicit workspace for private data and generated outputs.
    work_root = _hardwarex_os.environ["HARDWAREX_WORK_ROOT"]
    if not _hardwarex_os.path.isabs(work_root):
        raise ValueError("HARDWAREX_WORK_ROOT must be an absolute path")
    return _hardwarex_os.path.join(work_root, relative_path)

import rosbag
import genpy
from copy import deepcopy

INPUT_BAG = _hardwarex_path('bags/newbag/dataset/sequence_08/5_lr_rect_underwater.bag')
OUTPUT_BAG = _hardwarex_path('bags/newbag/dataset/sequence_08/5_lr_rect_underwater_fixed.bag')
IMU_TOPIC = "/imu/data"


def main():
    imu_msgs = []

    # 第一步：读取所有 IMU 消息，统计首尾时间
    with rosbag.Bag(INPUT_BAG, "r") as bag:
        for topic, msg, t in bag.read_messages():
            if topic == IMU_TOPIC:
                imu_msgs.append(deepcopy(msg))

    if len(imu_msgs) < 2:
        raise RuntimeError("IMU 消息数量不足，无法重建时间戳。")

    n = len(imu_msgs)
    t0 = imu_msgs[0].header.stamp.to_sec()
    tN = imu_msgs[-1].header.stamp.to_sec()
    dt = (tN - t0) / (n - 1)

    print("IMU message count:", n)
    print("First IMU stamp  :", t0)
    print("Last IMU stamp   :", tN)
    print("Rebuilt dt       :", dt)

    # 第二步：重写 bag
    imu_idx = 0
    with rosbag.Bag(INPUT_BAG, "r") as inbag, rosbag.Bag(OUTPUT_BAG, "w") as outbag:
        for topic, msg, t in inbag.read_messages():
            if topic == IMU_TOPIC:
                new_msg = deepcopy(msg)
                new_time = t0 + imu_idx * dt
                new_stamp = genpy.Time.from_sec(new_time)

                # 只改 IMU 消息内部的 header.stamp
                new_msg.header.stamp = new_stamp

                # 写回 bag 时，这里也用新的 IMU 时间
                outbag.write(topic, new_msg, new_stamp)
                imu_idx += 1
            else:
                # 其他 topic 完全不动，原消息 + 原 bag 时间
                outbag.write(topic, msg, t)

    print("Done.")
    print("Output bag:", OUTPUT_BAG)
    print("Fixed IMU messages:", imu_idx)


if __name__ == "__main__":
    main()
