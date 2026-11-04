# 历史处理记录与现存程序的对应

本轮只读检查公开程序、三轮标定报告、既有部署记录和作者确认，没有执行工程脚本、处理bag、重跑标定或操作Jetson。程序接口、参数一致性和历史实际执行记录分别评价。

| 环节 | 公开源包文件 | 输入输出与规则 | 时间或参数语义 | 证据 | 使用边界 |
|---|---|---|---|---|---|
| 采集 | software/onboard/mono_cam_cpp/src/mono_cam_cpp_node.cpp | 2560×800 mono8，/camera/image_raw | 读取帧后取主机ROS时间 | 节点源码、既有日志与作者命令 | 源码接口与历史运行入口已找到，曝光级同步误差未测 |
| 拆分 | software/offline/dataset_processing/split_stereo_bag_no_cvbridge.py | 在1280列拆成两幅1280×800图像；仅保留指定图像与IMU | 左右沿用同一header及bag时间 | 代码静态核查；作者确认左半幅为左相机 | 非mono8、尺寸、步长或数据长度不符会跳过；输出不自动保留其他话题 |
| 水下校正 | software/offline/dataset_processing/rectify_stereo_bag_underwater.py | 原始左右图像→新增image_rect_underwater话题 | 保留header及bag时间；保留原图；移除指定旧空气校正话题 | v3报告与脚本内参、畸变、R、T数值逐项一致 | 逐帧异常会警告，输出bag存在不等于每帧成功 |
| 导出方式A | software/offline/dataset_processing/stereo_to_image.py | 按左右header时间一对一配对，接受差值≤0.02 s | 两个文件同用左图时间，9位小数 | 脚本静态接口 | 20 ms是接受阈值，不是实测同步精度；已存在输出目录可能混入旧图 |
| 导出方式B | software/offline/dataset_processing/York-Tank/docs/process_yorktank_bags.py | 过滤左右水下校正话题和IMU，逐路导出图像及imu.csv | 左右分别用各自header时间命名，9位小数 | 脚本静态接口 | 本脚本不执行方式A的一对一配对；已有filtered bag会跳过滤包，输出应使用独立新目录 |
| 已校正参数 | software/offline/stereo_calibration/York-Tank/calibration/ov9281_underwater_rect.yaml | 已校正图像的共同内参、零畸变 | 基线0.10095282 m | 与yorktank_camera_info.py的FX/FY/CX/CY/BASELINE一致 | 原始参数YAML虽含Rectified注释，其畸变非零，应按数值和输入状态区分 |
| IMU时间重建 | software/offline/dataset_processing/fix_imu_time.py | 仅将IMU重排为首末时间之间的等间隔 | 同时改写IMU header及bag记录时间，其他话题原样 | 源码明确如此 | 不是默认同步步骤，不证明历史序列均用过 |
| 时间统计 | software/offline/dataset_processing/test_time_gap.py | 读取bag记录时间t并计算帧间隔 | 与图像header时间来源分别记录 | 源码read_topic_times使用t.to_sec() | 统计结果不等同曝光同步或UTC校准证明 |
| 上方GT相机 | software/offline/york_tank_gt/bag_to_images.py及ov2311.yaml | 导出上方相机图像和保存配置 | 按header命名 | 源文件已包含 | 未包含完整GT求解器、ORB-SLAM3或SVO Pro；科研结果引用原York-Tank论文与数据 |
| 历史同步 | docs/deployment.md与既有Chrony配置 | 支持已配置时间服务的说明 | 10月31日墙钟回退与无外部源属于该次核查状态 | 既有配置及当次只读报告 | 没有各历史任务偏差或每条命令清单，不补写UTC精度，也不向作者重复索取 |

## 三轮标定

| 版本 | 图像对数 | 估计基线 m | 对应文件 |
|---|---|---|---|
| v1 | 30 | 0.144241224 | software/offline/stereo_calibration/calib_final/calibration_result.txt |
| v2 | 25 | 0.121947074 | software/offline/stereo_calibration/calib_final/calibration_result_v2.txt |
| v3 | 18 | 0.10095282 | software/offline/stereo_calibration/calib_final_v3/calibration_result_v3.txt |

三轮图像名称具有30⊃25⊃18的包含关系。两步分别移除5对和7对，具体名单见calibration_version_index.csv及对应报告；第三轮参数与水下校正脚本、原始参数YAML在保存精度内完全一致。已校正YAML的共同内参与CameraInfo辅助脚本也一致。

作者已说明按清晰度、标签可识别数量和角度位置进行人工筛选，并确认所述历史任务未更换最终标定文件。这些回答保留为操作事实，不再重复追问。现存程序select_final_30.py先按共同标签数优选，必要时会放宽阈值补足候选；当前标定脚本的阈值为7。这两个程序快照不能自行恢复每一次人工操作。

本轮确认两个容易误用的地方。第一，ov9281_underwater.yaml中仍有Rectified stereo images注释，但保存的是带非零畸变的原始内参；ov9281_underwater_rect.yaml才是已校正图像参数。第二，stereo_to_image.py和process_yorktank_bags.py是两种不同的导出方式，不能合并叙述为同一条已经逐序列验证的执行链。

## 历史记录的收口方式

U04涉及历史输出的逐项输入、命令与版本日志，U09涉及历史时钟对端与偏差。现有证据可支撑源文件和参数对应，不能恢复没有保存的逐任务审计。后续正文可保留已证明的接口与科研用途，将细目放在本说明中；未保存的历史细节保持未记录状态。

York-Tank正式论文与完整16序列发布是独立引用对象，硬件包不是完整算法评测复现包。既有数据DOI为10.5281/zenodo.23347574，本轮网页读取未取得记录全文，不把在线访问写成已重新核验成功。原项目中的已发布证据和本轮GitHub源包检查分开记录。

## 可移植数据目录

公开说明曾引用docs/PATH_CLEANUP.json、imports_by_file.json和dependencies_observed.json，但三份文件未随v0.1.0提供。本版根据现存程序AST提取相对数据布局和依赖索引，另保存原有x86_64笔记本依赖观察，并明确与Jetson环境分开；没有据观察文件制造锁定依赖或宣称新机安装成功。

输出使用独立新目录。导出方式B遇到既有filtered bag会跳过过滤；两种导出都可能在已有图像目录中保留旧文件。复用说明已提示这些行为，未修改原程序或增加一键执行脚本。清洁环境运行检查标记NOT CHECKED。
