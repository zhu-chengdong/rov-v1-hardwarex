#!/usr/bin/env python3
import os as _hardwarex_os

def _hardwarex_path(relative_path):
    # Explicit workspace for private data and generated outputs.
    work_root = _hardwarex_os.environ["HARDWAREX_WORK_ROOT"]
    if not _hardwarex_os.path.isabs(work_root):
        raise ValueError("HARDWAREX_WORK_ROOT must be an absolute path")
    return _hardwarex_os.path.join(work_root, relative_path)

import os
import subprocess
import rosbag
import csv
import cv2
from cv_bridge import CvBridge


ROOT_DIR = _hardwarex_path('York-Tank')

RAW_BAG_DIR = os.path.join(ROOT_DIR, "rosbags")
FILTERED_BAG_DIR = os.path.join(ROOT_DIR, "filtered_rosbags")
SEQUENCE_DIR = os.path.join(ROOT_DIR, "sequences")

KEEP_TOPICS = [
    "/camera/left/image_rect_underwater",
    "/camera/right/image_rect_underwater",
    "/imu/data"
]

LEFT_TOPIC = "/camera/left/image_rect_underwater"
RIGHT_TOPIC = "/camera/right/image_rect_underwater"
IMU_TOPIC = "/imu/data"


def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)


def filter_bag(input_bag, output_bag):
    topic_expr = " or ".join(["topic == '{}'".format(t) for t in KEEP_TOPICS])
    cmd = [
        "rosbag", "filter",
        input_bag,
        output_bag,
        topic_expr
    ]

    print("\n[Filter]")
    print("Input :", input_bag)
    print("Output:", output_bag)

    subprocess.run(cmd, check=True)


def extract_bag(filtered_bag, sequence_name):
    bridge = CvBridge()

    seq_path = os.path.join(SEQUENCE_DIR, sequence_name)
    left_dir = os.path.join(seq_path, "left")
    right_dir = os.path.join(seq_path, "right")
    imu_file = os.path.join(seq_path, "imu.csv")

    ensure_dir(seq_path)
    ensure_dir(left_dir)
    ensure_dir(right_dir)

    left_count = 0
    right_count = 0
    imu_count = 0

    print("\n[Extract]")
    print("Bag:", filtered_bag)
    print("Sequence:", seq_path)

    with rosbag.Bag(filtered_bag, "r") as bag, open(imu_file, "w", newline="") as f:
        writer = csv.writer(f)

        writer.writerow([
            "timestamp",
            "orientation_x", "orientation_y", "orientation_z", "orientation_w",
            "angular_velocity_x", "angular_velocity_y", "angular_velocity_z",
            "linear_acceleration_x", "linear_acceleration_y", "linear_acceleration_z"
        ])

        for topic, msg, t in bag.read_messages(topics=KEEP_TOPICS):
            timestamp = msg.header.stamp.to_sec()

            if topic == LEFT_TOPIC:
                img = bridge.imgmsg_to_cv2(msg, desired_encoding="passthrough")
                img_name = "{:.9f}.png".format(timestamp)
                cv2.imwrite(os.path.join(left_dir, img_name), img)
                left_count += 1

            elif topic == RIGHT_TOPIC:
                img = bridge.imgmsg_to_cv2(msg, desired_encoding="passthrough")
                img_name = "{:.9f}.png".format(timestamp)
                cv2.imwrite(os.path.join(right_dir, img_name), img)
                right_count += 1

            elif topic == IMU_TOPIC:
                writer.writerow([
                    "{:.9f}".format(timestamp),
                    msg.orientation.x,
                    msg.orientation.y,
                    msg.orientation.z,
                    msg.orientation.w,
                    msg.angular_velocity.x,
                    msg.angular_velocity.y,
                    msg.angular_velocity.z,
                    msg.linear_acceleration.x,
                    msg.linear_acceleration.y,
                    msg.linear_acceleration.z
                ])
                imu_count += 1

    print("Left images :", left_count)
    print("Right images:", right_count)
    print("IMU msgs    :", imu_count)


def main():
    ensure_dir(FILTERED_BAG_DIR)
    ensure_dir(SEQUENCE_DIR)

    bag_files = sorted([
        f for f in os.listdir(RAW_BAG_DIR)
        if f.endswith(".bag")
    ])

    print("Found {} bag files.".format(len(bag_files)))

    for bag_file in bag_files:
        sequence_name = os.path.splitext(bag_file)[0]

        input_bag = os.path.join(RAW_BAG_DIR, bag_file)
        output_bag = os.path.join(FILTERED_BAG_DIR, bag_file)

        if not os.path.exists(output_bag):
            filter_bag(input_bag, output_bag)
        else:
            print("\n[Skip filter] Exists:", output_bag)

        extract_bag(output_bag, sequence_name)

    print("\nAll done.")


if __name__ == "__main__":
    main()
