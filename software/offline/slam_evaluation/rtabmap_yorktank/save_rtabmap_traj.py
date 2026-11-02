#!/usr/bin/env python3

import rospy
import sys
import math
from nav_msgs.msg import Odometry

if len(sys.argv) != 2:
    print("Usage: python3 save_rtabmap_traj.py output.txt")
    sys.exit(1)

output_file = sys.argv[1]

f = open(output_file, "w")

valid_count = 0
invalid_count = 0


def odom_callback(msg):
    global valid_count, invalid_count

    p = msg.pose.pose.position
    q = msg.pose.pose.orientation

    # RTAB-Map lost tracking时会输出无效四元数 0 0 0 0
    qnorm = math.sqrt(
        q.x*q.x +
        q.y*q.y +
        q.z*q.z +
        q.w*q.w
    )

    if qnorm < 1e-6:
        invalid_count += 1
        return

    values = [
        p.x, p.y, p.z,
        q.x, q.y, q.z, q.w
    ]

    if not all(math.isfinite(v) for v in values):
        invalid_count += 1
        return

    timestamp = msg.header.stamp.to_sec()

    f.write(
        "%.9f %.9f %.9f %.9f %.9f %.9f %.9f %.9f\n" %
        (
            timestamp,
            p.x, p.y, p.z,
            q.x, q.y, q.z, q.w
        )
    )

    f.flush()
    valid_count += 1


def shutdown():
    f.close()

    print("")
    print("Valid poses :", valid_count)
    print("Invalid poses:", invalid_count)
    print("Saved to    :", output_file)


rospy.init_node("save_rtabmap_traj")

rospy.Subscriber(
    "/rtabmap_stereo_odom",
    Odometry,
    odom_callback,
    queue_size=1000
)

rospy.on_shutdown(shutdown)

print("Waiting for /rtabmap_stereo_odom ...")

rospy.spin()
