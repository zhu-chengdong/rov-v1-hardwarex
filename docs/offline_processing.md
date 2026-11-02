# 实验文件的离线使用说明

以下接口与示例来自源码静态检查，尚未运行验证。它们用于独立的实验数据目录；机载入口另见deployment.md；本文只说明离线工具。

## 独立工作目录

```bash
export HARDWAREX_WORK_ROOT=/absolute/path/to/private_data_work
export ROV_REPO_ROOT=/absolute/path/to/rov-v1-hardwarex/software/offline
```

两个路径示例均为待替换占位符。HARDWAREX_WORK_ROOT 必须为绝对路径，承载输入数据和新输出，不指向源工程。含历史路径的 Python 文件显式读取该环境变量；未设置会报错。docs/PATH_CLEANUP.json 列出保留的数据相对布局。launch 中的数据库路径也使用该变量。

## bag 拆分与水下矫正

在自己的数据处理 shell 中加载所使用的 ROS 环境。当前笔记本已观测到的 ROS 路径示例是 /opt/ros/noetic/setup.bash，不代表 Jetson 路径或推荐依赖版本。

```bash
source /opt/ros/noetic/setup.bash
python3 "$ROV_REPO_ROOT/dataset_processing/split_stereo_bag_no_cvbridge.py" --inbag "$HARDWAREX_WORK_ROOT/input/raw_stereo.bag" --outbag "$HARDWAREX_WORK_ROOT/output/split_stereo.bag"
python3 "$ROV_REPO_ROOT/dataset_processing/rectify_stereo_bag_underwater.py" --inbag "$HARDWAREX_WORK_ROOT/output/split_stereo.bag" --outbag "$HARDWAREX_WORK_ROOT/output/rectified_underwater.bag"
```

输入数据不在仓库中；输出父目录需预先存在，输出使用新的文件名。拆分默认拼接图像 2560×800，切分列 1280，输入 /camera/image_raw，同时保留 /imu/data；10月14日记录已核对为2560×800 mono8；物理左右目对应仍待核。水下矫正脚本硬编码第三轮参数，保留原始左右图像，在输出中添加 /camera/left/image_rect_underwater 和 /camera/right/image_rect_underwater，并移除旧空气矫正话题。

rectify_stereo_bag.py 是另一套历史空气参数，不能直接当作水下流程。fix_imu_time.py 均匀重建输出 IMU header.stamp 与 bag 时间，是否符合实验条件及用于哪些序列为 TO VERIFY。test_time_gap.py 是时间统计，不能证明同步实现。

## 标定与数据转换

stereo_calibration/calib_underwater 中的 scan_candidates.py 读取 bags/test_09 图像，输出 calib_candidates；select_final_30.py 输出 calib_final；calibration.py 当前读取 calib_final_v3。缺少 18 对筛选依据，三者还不是已验证的一键复现链。板规格、历史版本和最终使用记录见标定核查。

dataset_processing 中的 stereo_to_image.py 导出并按时间差匹配左右图像；York-Tank/docs/process_yorktank_bags.py 调用 rosbag filter 并导出图像、IMU CSV。数据布局见路径记录；部分脚本有顶层文件输出操作，不能通过 import 试运行。

york_tank_gt/bag_to_images.py 按图像 header 时间保存图片，ov2311.yaml 保存相机配置；完整 GT 求解、尺度和验证流程尚未包含，均为 TO VERIFY。

## RTAB-Map 评估

slam_evaluation/rtabmap_yorktank 中的四个文件依赖已有 RTAB-Map 和 ROS 环境。CameraInfo 脚本订阅水下矫正图像并发布 /yorktank/left/camera_info 与 /yorktank/right/camera_info；两个 launch 可按绝对路径交给 roslaunch；save_rtabmap_traj.py 需要一个输出路径参数。完整离线回放编排尚未验证，运行输出置于独立工作目录。

已收集的机载入口及其证据范围见deployment.md。这里的离线示例不替代机载控制步骤。
