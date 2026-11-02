# 机载环境与启动入口

核查日期为2026年10月31日，作者操作与接线更新至11月2日。当前安装、历史运行和作者自述分开登记。

Jetson Orin Nano Developer Kit 8GB，WD_BLACK SN7100 1TB，Ubuntu20.04.6 LTS/aarch64，L4T35.5.0、内核5.10.192-tegra，ROS Noetic/Python3.8.10。C++ OpenCV4.5.4，Python cv2为4.2.0。驱动包5.10.192-tegra-35.5.0-20240307165425。须从Arducam取得匹配的驱动和DTB，本公开包不含内核/二进制。未验证新机端到端安装。

```bash
source /opt/ros/noetic/setup.bash
source ~/catkin_ws/devel/setup.bash
# 在分别的终端启动历史已有入口
roscore
rosrun mono_cam_cpp mono_cam_cpp_node
python3 /absolute/path/to/bridge_raw.py
rosbag record /camera/image_raw /imu/data
```

先将`software/onboard/mono_cam_cpp`放入自己的catkin工作空间并按ROS工具构建；这些入口从现有源码、命令及历史日志恢复，发布时未运行相机或控制。未发现专用一键启动服务。可选IMU需外部Xsens驱动，其实际历史入口为`roslaunch xsens_mti_driver xsens_mti_node.launch`，参数time_option=2、scan_for_devices=true、enable_deviceConfig=false；未复制上游驱动源。日志识别MTi-3-8A7G6、115200、固件1.20.1 build6231。配置中的100不作为实际写入100Hz的证明，York-Tank视觉流程未使用IMU。

相机默认/dev/video0、2560×800，发布/camera/image_raw、mono8、queue1，读取帧后取主机ROS时间。程序未加载标定或发布CameraInfo。左右软件拆分保留共同Header，不证明物理左右目编号或曝光级时间误差。安全循环500Hz不是500fps。历史frame_rate20/exposure681/gain100只作命令线索，有效值和单位待自然使用时查询；10月31日video0不存在，未启动或修理相机。

bridge_raw.py是pyserial/socket/select字节透传，ttyUSB0、57600、UDP0.0.0.0:14550，收到QGC后保存最后对端。当前设备身份FT232R为ttyUSB0、Xsens为ttyUSB1，重新部署须核对枚举。QGC当前4.2.4，XInput Controller #1，RollAxis2/PitchAxis3/YawAxis0/ThrottleAxis1，Axis1/3反向，仅为软件映射。

10月14日遥测记录ArduSub4.5.6、提交1a196cab、Frame VECTORED。恢复943项参数的私有原始证据未作为即用飞控配置分发；SERVO1—6_FUNCTION为33—38，7/8为134、MIN/MAX1100/1900、TRIM1800/1850。物理通道需追线，不能直接导入历史参数。灯光实际操作依作者手动QGC PWM输入记录。

当前Chrony有局域网本地回退配置，但核查时墙上时钟为1970年且无外部源，历史对端和偏差仍未闭合。图像和IMU使用主机ROS时间，不以当前配置证明绝对UTC准确。功率当前ID0/15W、风扇服务运行、默认quiet，活动profile和历史对应待核。录包实现默认缓存256MB、块768KB、不压缩不分包，不回填所有历史会话。

历史原始数据未包括在软件包内。水中温度1791s、图像27分43秒；室内温度7193s、图像58分36秒，后者bag.active未写最终索引。温度仅为已有辅助观察，不证明2小时连续双目采集或无热降频。
