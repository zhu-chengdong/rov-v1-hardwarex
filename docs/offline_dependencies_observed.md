# 软件环境与依赖范围

Jetson既有核查为Ubuntu 20.04.6 LTS、aarch64、L4T35.5.0、ROS Noetic、Python3.8.10，机载C++ OpenCV4.5.4、Python OpenCV4.2.0。实际相机驱动包为5.10.192-tegra-35.5.0-20240307165425。相机设置与默认最高功率及默认风扇采用作者已确认记录，不再要求设备当前读数。

docs/imports_by_file.json来自公开13个离线Python脚本的AST导入提取；docs/PATH_CLEANUP.json和data_layout.md说明工作目录布局。docs/dependencies_observed.json保留既有x86_64笔记本Python/APT观察版本，含作用域说明，不能据此判断Jetson缺少功能或认定新机安装成功。

标定依赖NumPy、OpenCV和pupil_apriltags；ROS bag处理依赖rosbag、sensor_msgs、cv_bridge及对应ROS环境；RTAB-Map辅助资料依赖相应ROS包。标准库不作为另行安装项。本包没有经过验证的统一锁定环境，也没有一键安装与端到端重跑结果，现有版本按各自来源分开登记。
