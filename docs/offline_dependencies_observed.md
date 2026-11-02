# 软件依赖与当前主机观测

下列依赖来自静态 import、ROS launch 与包数据库。版本只描述当前 Ubuntu 20.04.6 x86_64 笔记本，不能作为 Jetson Orin Nano 或 V1 原始机载环境的版本清单，也不构成已验证的安装配方。本次没有安装依赖或改变环境。

| 用途 | 源码依赖 | 当前笔记本观测 |
|---|---|---|
| 标定 | Python、NumPy、OpenCV、pupil_apriltags | Python 3.8.10；用户 NumPy 1.24.4；opencv-python 4.13.0.92；pupil_apriltags 1.0.4.post11 |
| bag 拆分及矫正 | rosbag、sensor_msgs、NumPy、OpenCV、cv_bridge | ROS Noetic；rosbag 1.17.4；cv_bridge 1.16.2；系统 OpenCV 4.2.0 |
| 时间修正与统计 | rosbag、genpy、NumPy | 版本及 import 对应关系见 JSON；实际运行环境 TO VERIFY |
| 图像与 CSV 导出 | rosbag、OpenCV、cv_bridge，标准库 csv、subprocess、os | 与上述相同；process_yorktank_bags.py 会调用 rosbag filter |
| RTAB-Map 评估 | rospy、sensor_msgs、nav_msgs、rtabmap_odom、rtabmap_launch | 当前安装 RTAB-Map ROS 相关组件；各包精确版本见 JSON |

imports_by_file.json 逐文件列出 import。dependencies_observed.json 保留 Python 包的用户级、系统级或 ROS 作用域及 APT 完整版本；个人安装路径已移除。标准库不列为需要安装的第三方包。SciPy、dt-apriltags 等即使在主机安装，也不据此认定为这 27 文件的必需依赖。

系统 NumPy 1.17.4 和用户 NumPy 1.24.4 并存，系统 OpenCV 4.2.0 和用户 opencv-python 4.13.0.92 并存。实际 cv2/NumPy 加载版本、cv_bridge 兼容性和原标定时版本均为 TO VERIFY，未执行这些工程进行验证。

本次扫描未在笔记本找到明确 Chrony、Arducam、MAVLink、ArduSub 部署证据，不推导这些功能在机器人上缺失。Jetson 的 Ubuntu/L4T/JetPack、ROS、相机 SDK、MAVLink 与同步依赖版本必须另行采集。
