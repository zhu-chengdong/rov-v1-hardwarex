# 离线处理工具使用与证据

本目录提供现有工具的静态接口和参数对应。源码13个Python文件已通过AST语法解析，没有执行bag处理、标定或评测。机载部署另见deployment.md；算法结果仍引用独立York-Tank研究。

## 目录与输入

将HARDWAREX_WORK_ROOT设为自己的独立数据目录，将ROV_REPO_ROOT设为解压包的software/offline目录。输入输出字段和源文件对应见data_layout.md及PATH_CLEANUP.json。依赖索引见imports_by_file.json；dependencies_observed.json保存历史x86_64笔记本的观察版本，不能当成Jetson锁定安装清单。

拆分脚本接收--inbag和--outbag，输入默认2560×800 mono8、/camera/image_raw，在1280列分为左右图像并复制/imu/data。拼接图左半幅对应机器人左相机。非预期尺寸、编码、步长或长度将跳过并输出警告，其他未指定话题不自动保留。

水下校正脚本接收--inbag和--outbag，在保留原始左右图像的同时新增/camera/left/image_rect_underwater和/camera/right/image_rect_underwater，丢弃指定的旧空气校正话题，保留其余话题。内部参数与v3的18对标定报告一致。原始参数YAML与已校正参数YAML应按输入图像状态使用，具体数值对应见processing_evidence.md。

## 两种导出方式

stereo_to_image.py按header时间进行一对一配对，接受时间差不超过0.02 s，左右同用左图时间并保留9位小数。process_yorktank_bags.py过滤校正话题和IMU后逐路导出，左右分别使用自身header命名，不执行前一脚本的配对。后者遇到已有filtered bag会跳过过滤。输出使用独立新目录，避免旧图混入。

fix_imu_time.py会同时改写IMU header及bag时间，不能作为默认同步操作。test_time_gap.py统计bag记录时间t，不能证明曝光同步或UTC精度。

## 标定与GT

三轮30、25、18对报告属于标定迭代，不对应三个机械档位。相机标定板6×6、tag36h11、标签边长0.044 m、间距比0.3，GT板为3×3。人工选图依据作者确认记录；当前程序阈值不替代全部历史操作日志。

GT相机导出和RTAB-Map辅助程序均按单独用途提供，没有完整GT求解器、ORB-SLAM3或SVO Pro实现。本硬件工具包的清洁环境端到端运行未检查。
