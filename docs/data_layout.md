# 处理数据目录布局

HARDWAREX_WORK_ROOT由复用者设为自己独立数据工作目录的绝对路径。下表的路径均相对于该目录，来源为程序中的字面量读取，不是V1完整历史数据清单。

| 程序 | 环境变量 | 相对位置 |
|---|---|---|
| dataset_processing/fix_imu_time.py | HARDWAREX_WORK_ROOT | bags/newbag/dataset/sequence_08/5_lr_rect_underwater.bag |
| dataset_processing/fix_imu_time.py | HARDWAREX_WORK_ROOT | bags/newbag/dataset/sequence_08/5_lr_rect_underwater_fixed.bag |
| dataset_processing/stereo_to_image.py | HARDWAREX_WORK_ROOT | York-Tank/rosbags/1_reference1.bag |
| dataset_processing/stereo_to_image.py | HARDWAREX_WORK_ROOT | York-Tank/sequences/1_reference1 |
| dataset_processing/test_time_gap.py | HARDWAREX_WORK_ROOT | bags/rosbag/dataset/sequence_02/2_lr_rect_underwater.bag |
| dataset_processing/test_time_gap.py | HARDWAREX_WORK_ROOT | bags/rosbag/gt/sequence_02/2.bag |
| dataset_processing/York-Tank/docs/process_yorktank_bags.py | HARDWAREX_WORK_ROOT | York-Tank |
| stereo_calibration/calib_underwater/calibration.py | HARDWAREX_WORK_ROOT | calib_final_v3/left |
| stereo_calibration/calib_underwater/calibration.py | HARDWAREX_WORK_ROOT | calib_final_v3/right |
| stereo_calibration/calib_underwater/scan_candidates.py | HARDWAREX_WORK_ROOT | bags/test_09/left |
| stereo_calibration/calib_underwater/scan_candidates.py | HARDWAREX_WORK_ROOT | bags/test_09/right |
| stereo_calibration/calib_underwater/scan_candidates.py | HARDWAREX_WORK_ROOT | calib_candidates |
| stereo_calibration/calib_underwater/select_final_30.py | HARDWAREX_WORK_ROOT | calib_candidates/left |
| stereo_calibration/calib_underwater/select_final_30.py | HARDWAREX_WORK_ROOT | calib_candidates/right |
| stereo_calibration/calib_underwater/select_final_30.py | HARDWAREX_WORK_ROOT | calib_candidates/scan_log.csv |
| stereo_calibration/calib_underwater/select_final_30.py | HARDWAREX_WORK_ROOT | calib_final |
| york_tank_gt/bag_to_images.py | HARDWAREX_WORK_ROOT | bags/newbag/gt/sequence_08/3 |
| york_tank_gt/bag_to_images.py | HARDWAREX_WORK_ROOT | bags/newbag/gt/sequence_08/3.bag |
| slam_evaluation/rtabmap_yorktank/yorktank_rtabmap_full.launch | HARDWAREX_WORK_ROOT | rtabmap_yorktank/results/1_reference1/rtabmap.db |

拆分及校正脚本另以--inbag和--outbag接收路径。其输出父目录须预先存在并使用新文件名。上述提取未运行程序，没有创建数据输出，也未建立全流程运行证明。
