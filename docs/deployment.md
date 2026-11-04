# 机载部署与使用入口

现有环境为Jetson Orin Nano Developer Kit 8GB、Ubuntu20.04.6 LTS/aarch64、L4T35.5.0、ROS Noetic、Python3.8.10。C++相机链接OpenCV4.5.4，Python OpenCV4.2.0。来源为10月31日只读核查；ArduSub4.5.6/VECTORED来自10月14日历史遥测，不能表述为本轮在线读飞控。

在既有ROS/catkin环境中，历史入口为roscore、rosrun mono_cam_cpp mono_cam_cpp_node，通信桥为python3 bridge_raw.py，可选IMU为roslaunch xsens_mti_driver xsens_mti_node.launch。第三方ROS/驱动和Xsens上游不随包许可，按原项目获取。

采集前设置采用作者已确认的命令。

```bash
v4l2-ctl -d /dev/video0 -c frame_rate=20
v4l2-ctl -d /dev/video0 -c exposure=681
v4l2-ctl -d /dev/video0 -c analogue_gain=100
```

相机输出2560×800 mono8至/camera/image_raw。历史录包入口为rosbag record /camera/image_raw /imu/data，具体输出目录由任务确定；两组电池、图像/IMU话题和可选模块范围分别记录。相机节点源码中的循环等待值不替代20 Hz相机设置。左右图拆分及标定对应见offline_processing.md。

通信桥串口/dev/ttyUSB0、57600 bit/s、UDP绑定0.0.0.0:14550，先收到地面对端数据后向其返回串口数据。FT232RL接TELEM1，八路位置见output_mapping.csv。QGroundControl4.2.4，运动通过映射手柄，解锁采用QGC滑动解锁，两灯在界面输入PWM7/PWM8值分别调光。

Jetson按作者确认的默认最高功率设置运行，风扇采用系统默认配置；不附未经提供的profile编号或功率数值。10月31日未枚举video0、墙钟回退及无外部时间源属于该次只读快照，不作为旧试验的每次运行状态或新增补测要求。

使用结束时先拔手柄减少误触，远程停止采集节点和记录，关闭Jetson并观察指示灯，然后回收至工作面、开后盖、分别断开6S XT90和Jetson DC，再移动载荷架。拔手柄不是已验证的急停实现。

本说明给出现有入口，没有整机一键启动或新机安装验收记录，也没有逐任务UTC偏差实测。本次未执行启动、控制、录包或关机命令。
