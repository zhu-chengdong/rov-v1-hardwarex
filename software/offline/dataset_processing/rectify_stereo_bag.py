#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import os
import sys

import cv2
import numpy as np
import rosbag
from cv_bridge import CvBridge
from sensor_msgs.msg import Image

# 这个脚本是给双目图像去畸变，并给出相关参数，重写yaml文件

def build_camera_matrix(intrinsics):
    fx, fy, cx, cy = intrinsics
    return np.array([
        [fx, 0.0, cx],
        [0.0, fy, cy],
        [0.0, 0.0, 1.0]
    ], dtype=np.float64)


def build_dist_coeffs(distortion_coeffs):
    # Kalibr radtan: [k1, k2, p1, p2]
    k1, k2, p1, p2 = distortion_coeffs
    return np.array([k1, k2, p1, p2, 0.0], dtype=np.float64)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Rectify stereo images in a ROS1 bag using Kalibr parameters."
    )
    parser.add_argument("--inbag", required=True, help="Input raw ROS bag")
    parser.add_argument("--outbag", required=True, help="Output rectified ROS bag")

    parser.add_argument("--left_topic", default="/camera/left/image_raw",
                        help="Left raw image topic")
    parser.add_argument("--right_topic", default="/camera/right/image_raw",
                        help="Right raw image topic")

    parser.add_argument("--left_rect_topic", default="/camera/left/image_rect",
                        help="Left rectified image topic")
    parser.add_argument("--right_rect_topic", default="/camera/right/image_rect",
                        help="Right rectified image topic")

    parser.add_argument("--image_width", type=int, default=1280)
    parser.add_argument("--image_height", type=int, default=800)

    return parser.parse_args()


def main():
    args = parse_args()

    if not os.path.isfile(args.inbag):
        print(f"[ERROR] Input bag does not exist: {args.inbag}")
        sys.exit(1)

    image_size = (args.image_width, args.image_height)

    # -----------------------------
    # Kalibr parameters from your file
    # -----------------------------
    left_intrinsics = [918.1980846779677, 913.4184461788421,
                       628.8940872510458, 412.9263238949233]
    left_distortion = [0.0618410330441939, -0.07647686780950973,
                       -0.0011737591925196828, 0.0020008817285008577]

    right_intrinsics = [928.638048732993, 923.7413147689151,
                        649.5173315281456, 426.1879414790194]
    right_distortion = [0.06593908853890194, -0.08784869457491752,
                        0.0003183573247158998, 0.0007720276387766815]

    # cam1 relative to cam0
    T_c1_c0 = np.array([
        [0.9991514519384755, -0.02288283454851392, -0.03424546644826839, -0.10097956752196743],
        [0.02303002343641552,  0.9997271287470184,  0.003909740113922653, -0.0012352915026068781],
        [0.03414665590877517, -0.004695096406422527, 0.9994058044458117, -0.002178696959650018],
        [0.0, 0.0, 0.0, 1.0]
    ], dtype=np.float64)

    K1 = build_camera_matrix(left_intrinsics)
    D1 = build_dist_coeffs(left_distortion)

    K2 = build_camera_matrix(right_intrinsics)
    D2 = build_dist_coeffs(right_distortion)

    R = T_c1_c0[:3, :3]
    T = T_c1_c0[:3, 3].reshape(3, 1)

    # stereoRectify
    # alpha=0 means crop more and remove invalid borders
    # alpha=-1 means keep more FOV
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
    print("[INFO] P1 =\n", P1)
    print("[INFO] P2 =\n", P2)
    print("[INFO] Q  =\n", Q)

    bridge = CvBridge()

    total_left = 0
    total_right = 0
    rect_left = 0
    rect_right = 0

    with rosbag.Bag(args.outbag, "w") as outbag:
        for topic, msg, t in rosbag.Bag(args.inbag, "r").read_messages():
            # left image
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

                # 同时保留原消息
                outbag.write(topic, msg, t)

            # right image
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

                # 同时保留原消息
                outbag.write(topic, msg, t)

            else:
                # 其他话题原样写回
                outbag.write(topic, msg, t)

    print("\n[INFO] Done.")
    print(f"[INFO] Left  frames: total={total_left}, rectified={rect_left}")
    print(f"[INFO] Right frames: total={total_right}, rectified={rect_right}")
    print(f"[INFO] Output bag: {args.outbag}")
    print("\n[INFO] Use these rectified topics later:")
    print(f"       {args.left_rect_topic}")
    print(f"       {args.right_rect_topic}")
    print("\n[INFO] Then run ORB-SLAM3 with rectify flag = false.")


if __name__ == "__main__":
    main()
