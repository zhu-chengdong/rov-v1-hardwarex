#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import os
import sys

import cv2
import numpy as np
import rosbag
from cv_bridge import CvBridge


def build_camera_matrix(intrinsics):
    fx, fy, cx, cy = intrinsics
    return np.array([
        [fx, 0.0, cx],
        [0.0, fy, cy],
        [0.0, 0.0, 1.0]
    ], dtype=np.float64)


def build_dist_coeffs(distortion_coeffs):
    # OpenCV distortion: [k1, k2, p1, p2, k3]
    k1, k2, p1, p2 = distortion_coeffs
    return np.array([k1, k2, p1, p2, 0.0], dtype=np.float64)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Rectify stereo images in a ROS1 bag using underwater stereo calibration parameters, "
                    "while removing old air-based rectified topics."
    )
    parser.add_argument("--inbag", required=True, help="Input ROS bag")
    parser.add_argument("--outbag", required=True, help="Output ROS bag")

    parser.add_argument("--left_topic", default="/camera/left/image_raw",
                        help="Left raw image topic")
    parser.add_argument("--right_topic", default="/camera/right/image_raw",
                        help="Right raw image topic")

    parser.add_argument("--left_rect_topic", default="/camera/left/image_rect_underwater",
                        help="Left underwater rectified image topic")
    parser.add_argument("--right_rect_topic", default="/camera/right/image_rect_underwater",
                        help="Right underwater rectified image topic")

    # 要删除的旧空气校正话题
    parser.add_argument("--drop_left_old_rect_topic", default="/camera/left/image_rect",
                        help="Old air-based left rectified topic to remove")
    parser.add_argument("--drop_right_old_rect_topic", default="/camera/right/image_rect",
                        help="Old air-based right rectified topic to remove")

    parser.add_argument("--image_width", type=int, default=1280)
    parser.add_argument("--image_height", type=int, default=800)

    return parser.parse_args()


def main():
    args = parse_args()

    if not os.path.isfile(args.inbag):
        print(f"[ERROR] Input bag does not exist: {args.inbag}")
        sys.exit(1)

    image_size = (args.image_width, args.image_height)

    # --------------------------------------------------
    # 水下第三轮标定结果
    # --------------------------------------------------
    left_intrinsics = [1032.61282, 1048.21655, 606.955302, 553.973799]
    left_distortion = [0.30383851, -0.07981107, 0.03260515, -0.00549176]

    right_intrinsics = [1033.00296, 1043.60581, 653.657101, 550.384815]
    right_distortion = [0.25296930, 0.03115622, 0.02931121, 0.00362864]

    # cam1 relative to cam0
    T_c1_c0 = np.array([
        [0.99784407, -0.02230725, -0.06172200, -0.10010260],
        [0.02356253,  0.99952854,  0.01968506, -0.00042900],
        [0.06125378, -0.02109694,  0.99789924, -0.01306743],
        [0.0,         0.0,         0.0,         1.0]
    ], dtype=np.float64)

    K1 = build_camera_matrix(left_intrinsics)
    D1 = build_dist_coeffs(left_distortion)

    K2 = build_camera_matrix(right_intrinsics)
    D2 = build_dist_coeffs(right_distortion)

    R = T_c1_c0[:3, :3]
    T = T_c1_c0[:3, 3].reshape(3, 1)

    # --------------------------------------------------
    # stereoRectify
    # --------------------------------------------------
    R1, R2, P1, P2, Q, roi1, roi2 = cv2.stereoRectify(
        K1, D1, K2, D2,
        image_size,
        R, T,
        flags=cv2.CALIB_ZERO_DISPARITY,
        alpha=0
    )

    map1_left, map2_left = cv2.initUndistortRectifyMap(
        K1, D1, R1, P1, image_size, cv2.CV_16SC2
    )
    map1_right, map2_right = cv2.initUndistortRectifyMap(
        K2, D2, R2, P2, image_size, cv2.CV_16SC2
    )

    print("[INFO] Rectification parameters computed.")
    print("[INFO] R1 =\n", R1)
    print("[INFO] R2 =\n", R2)
    print("[INFO] P1 =\n", P1)
    print("[INFO] P2 =\n", P2)
    print("[INFO] Q  =\n", Q)
    print("[INFO] roi1 =", roi1)
    print("[INFO] roi2 =", roi2)

    bridge = CvBridge()

    total_left = 0
    total_right = 0
    rect_left = 0
    rect_right = 0
    dropped_old_rect = 0

    with rosbag.Bag(args.outbag, "w") as outbag:
        with rosbag.Bag(args.inbag, "r") as inbag:
            for topic, msg, t in inbag.read_messages():

                # 先过滤掉旧空气校正话题
                if topic == args.drop_left_old_rect_topic or topic == args.drop_right_old_rect_topic:
                    dropped_old_rect += 1
                    continue

                # 左原始图像 -> 新水下校正图像
                if topic == args.left_topic:
                    total_left += 1
                    try:
                        cv_img = bridge.imgmsg_to_cv2(msg, desired_encoding="mono8")
                        rect_img = cv2.remap(
                            cv_img, map1_left, map2_left, interpolation=cv2.INTER_LINEAR
                        )
                        rect_msg = bridge.cv2_to_imgmsg(rect_img, encoding="mono8")
                        rect_msg.header = msg.header
                        outbag.write(args.left_rect_topic, rect_msg, t)
                        rect_left += 1
                    except Exception as e:
                        print(f"[WARN] Failed to rectify left frame at {t.to_sec():.6f}: {e}")

                    # 保留原始左图
                    outbag.write(topic, msg, t)

                # 右原始图像 -> 新水下校正图像
                elif topic == args.right_topic:
                    total_right += 1
                    try:
                        cv_img = bridge.imgmsg_to_cv2(msg, desired_encoding="mono8")
                        rect_img = cv2.remap(
                            cv_img, map1_right, map2_right, interpolation=cv2.INTER_LINEAR
                        )
                        rect_msg = bridge.cv2_to_imgmsg(rect_img, encoding="mono8")
                        rect_msg.header = msg.header
                        outbag.write(args.right_rect_topic, rect_msg, t)
                        rect_right += 1
                    except Exception as e:
                        print(f"[WARN] Failed to rectify right frame at {t.to_sec():.6f}: {e}")

                    # 保留原始右图
                    outbag.write(topic, msg, t)

                else:
                    # 其他非旧校正话题原样写回（例如 IMU）
                    outbag.write(topic, msg, t)

    print("\n[INFO] Done.")
    print(f"[INFO] Left  frames: total={total_left}, rectified={rect_left}")
    print(f"[INFO] Right frames: total={total_right}, rectified={rect_right}")
    print(f"[INFO] Dropped old rectified msgs: {dropped_old_rect}")
    print(f"[INFO] Output bag: {args.outbag}")

    print("\n[INFO] Original topics kept:")
    print(f"       {args.left_topic}")
    print(f"       {args.right_topic}")

    print("\n[INFO] New underwater rectified topics added:")
    print(f"       {args.left_rect_topic}")
    print(f"       {args.right_rect_topic}")

    print("\n[INFO] Old air-based rectified topics removed:")
    print(f"       {args.drop_left_old_rect_topic}")
    print(f"       {args.drop_right_old_rect_topic}")

    print("\n[INFO] Then run ORB-SLAM3 with rectify flag = false.")


if __name__ == "__main__":
    main()
