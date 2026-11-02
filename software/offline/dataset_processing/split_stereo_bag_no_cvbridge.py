#!/usr/bin/env python3
import argparse
import os
import sys

import rosbag
from sensor_msgs.msg import Image

#这个脚本是把ov9281采集到的一张图切割成两张图，两个topic

def has_image_fields(msg) -> bool:
    need = ["width", "height", "encoding", "step", "data", "header"]
    return all(hasattr(msg, k) for k in need)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--inbag", required=True, help="input .bag path")
    ap.add_argument("--outbag", required=True, help="output .bag path")
    ap.add_argument("--in_image_topic", default="/camera/image_raw")
    ap.add_argument("--left_topic", default="/camera/left/image_raw")
    ap.add_argument("--right_topic", default="/camera/right/image_raw")
    ap.add_argument("--imu_topic", default="/imu/data")
    ap.add_argument("--width", type=int, default=2560)
    ap.add_argument("--height", type=int, default=800)
    ap.add_argument("--split", type=int, default=1280, help="left width; right width = width - split")
    args = ap.parse_args()

    if not os.path.isfile(args.inbag):
        print(f"[ERROR] input bag not found: {args.inbag}", file=sys.stderr)
        sys.exit(1)

    if args.split <= 0 or args.split >= args.width:
        print("[ERROR] invalid split value", file=sys.stderr)
        sys.exit(1)

    left_w = args.split
    right_w = args.width - args.split

    n_img_in = 0
    n_left = 0
    n_right = 0
    n_imu = 0
    n_skipped = 0

    print(f"[INFO] inbag : {args.inbag}")
    print(f"[INFO] outbag: {args.outbag}")
    print(f"[INFO] image topic: {args.in_image_topic} -> {args.left_topic}, {args.right_topic}")
    print(f"[INFO] imu topic  : {args.imu_topic}")
    print(f"[INFO] expected: {args.width}x{args.height} mono8, split={args.split}")

    with rosbag.Bag(args.inbag, "r") as inbag, rosbag.Bag(args.outbag, "w") as outbag:
        for topic, msg, t in inbag.read_messages(topics=[args.in_image_topic, args.imu_topic]):

            # Copy IMU as-is
            if topic == args.imu_topic:
                outbag.write(args.imu_topic, msg, t)
                n_imu += 1
                continue

            # Split image
            if topic != args.in_image_topic:
                continue

            n_img_in += 1

            if not has_image_fields(msg):
                print(f"[WARN] message at #{n_img_in} lacks Image-like fields, skip", file=sys.stderr)
                n_skipped += 1
                continue

            enc = str(msg.encoding).lower()
            if enc != "mono8":
                print(f"[WARN] encoding={msg.encoding} at #{n_img_in}, expected mono8. skip", file=sys.stderr)
                n_skipped += 1
                continue

            if int(msg.width) != args.width or int(msg.height) != args.height:
                print(f"[WARN] size {msg.width}x{msg.height} at #{n_img_in}, expected {args.width}x{args.height}. skip",
                      file=sys.stderr)
                n_skipped += 1
                continue

            if int(msg.step) != args.width:
                print(f"[WARN] step={msg.step} at #{n_img_in}, expected {args.width}. skip", file=sys.stderr)
                n_skipped += 1
                continue

            data = msg.data
            expected_len = args.height * int(msg.step)
            if len(data) != expected_len:
                print(f"[WARN] data len={len(data)} at #{n_img_in}, expected {expected_len}. skip", file=sys.stderr)
                n_skipped += 1
                continue

            # Row-by-row split
            left_bytes = bytearray(args.height * left_w)
            right_bytes = bytearray(args.height * right_w)

            for r in range(args.height):
                row_start = r * int(msg.step)
                left_bytes[r * left_w:(r + 1) * left_w] = data[row_start:row_start + left_w]
                right_bytes[r * right_w:(r + 1) * right_w] = data[row_start + left_w:row_start + args.width]

            # Build left/right ROS Image messages
            left_msg = Image()
            left_msg.header = msg.header  # keep stamp
            left_msg.height = args.height
            left_msg.width = left_w
            left_msg.encoding = "mono8"
            left_msg.is_bigendian = getattr(msg, "is_bigendian", 0)
            left_msg.step = left_w
            left_msg.data = bytes(left_bytes)

            right_msg = Image()
            right_msg.header = msg.header  # keep stamp
            right_msg.height = args.height
            right_msg.width = right_w
            right_msg.encoding = "mono8"
            right_msg.is_bigendian = getattr(msg, "is_bigendian", 0)
            right_msg.step = right_w
            right_msg.data = bytes(right_bytes)

            outbag.write(args.left_topic, left_msg, t)
            outbag.write(args.right_topic, right_msg, t)
            n_left += 1
            n_right += 1

    print("\n[DONE]")
    print(f"  images in   : {n_img_in}")
    print(f"  left out    : {n_left}")
    print(f"  right out   : {n_right}")
    print(f"  imu out     : {n_imu}")
    print(f"  skipped img : {n_skipped}")
    if n_left != n_img_in or n_right != n_img_in:
        print("[WARN] left/right counts != image input count. Check warnings.", file=sys.stderr)


if __name__ == "__main__":
    main()
