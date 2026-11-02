#!/usr/bin/env python3

import rospy
from sensor_msgs.msg import Image, CameraInfo

FX = 1347.52248
FY = 1347.52248
CX = 493.020039
CY = 549.608562
BASELINE = 0.10095282

WIDTH = 1280
HEIGHT = 800

pub_left = None
pub_right = None

def make_info(header, right=False):
    msg = CameraInfo()

    msg.header = header
    msg.width = WIDTH
    msg.height = HEIGHT

    msg.distortion_model = "plumb_bob"
    msg.D = [0.0, 0.0, 0.0, 0.0, 0.0]

    msg.K = [
        FX, 0.0, CX,
        0.0, FY, CY,
        0.0, 0.0, 1.0
    ]

    msg.R = [
        1.0, 0.0, 0.0,
        0.0, 1.0, 0.0,
        0.0, 0.0, 1.0
    ]

    tx = -FX * BASELINE if right else 0.0

    msg.P = [
        FX, 0.0, CX, tx,
        0.0, FY, CY, 0.0,
        0.0, 0.0, 1.0, 0.0
    ]

    return msg

def left_cb(img):
    pub_left.publish(make_info(img.header, False))

def right_cb(img):
    pub_right.publish(make_info(img.header, True))

if __name__ == "__main__":
    rospy.init_node("yorktank_camera_info")

    pub_left = rospy.Publisher(
        "/yorktank/left/camera_info",
        CameraInfo,
        queue_size=20
    )

    pub_right = rospy.Publisher(
        "/yorktank/right/camera_info",
        CameraInfo,
        queue_size=20
    )

    rospy.Subscriber(
        "/camera/left/image_rect_underwater",
        Image,
        left_cb,
        queue_size=20
    )

    rospy.Subscriber(
        "/camera/right/image_rect_underwater",
        Image,
        right_cb,
        queue_size=20
    )

    rospy.spin()
