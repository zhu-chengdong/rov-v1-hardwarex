#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os as _hardwarex_os

def _hardwarex_path(relative_path):
    # Explicit workspace for private data and generated outputs.
    work_root = _hardwarex_os.environ["HARDWAREX_WORK_ROOT"]
    if not _hardwarex_os.path.isabs(work_root):
        raise ValueError("HARDWAREX_WORK_ROOT must be an absolute path")
    return _hardwarex_os.path.join(work_root, relative_path)

import os
from pathlib import Path

import cv2
import numpy as np
from pupil_apriltags import Detector


# =========================================================
# 1. 路径（写死）
# =========================================================
LEFT_DIR  = Path(_hardwarex_path('calib_final_v3/left'))
RIGHT_DIR = Path(_hardwarex_path('calib_final_v3/right'))

# =========================================================
# 2. AprilGrid 参数（Kalibr）
# =========================================================
TAG_COLS = 6
TAG_ROWS = 6
TAG_SIZE = 0.044       # m
TAG_SPACING = 0.3      # ratio

# =========================================================
# 3. 检测 / 筛选参数
# =========================================================
MIN_COMMON_TAGS = 7
IMG_EXTS = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff"}

# =========================================================
# 4. AprilTag 检测器
# =========================================================
detector = Detector(
    families="tag36h11",
    nthreads=4,
    quad_decimate=1.0,
    quad_sigma=0.0,
    refine_edges=1,
    decode_sharpening=0.25,
    debug=0
)


# =========================================================
# 工具函数
# =========================================================
def build_aprilgrid_object_points():
    """
    为每个 tag id 构建其4个角点的3D坐标。
    角点顺序与 pupil_apriltags 返回一致，按：
        top-left, top-right, bottom-right, bottom-left
    坐标系：
        x 向右
        y 向下
        z = 0
    整块板以几何中心为原点
    """
    obj_map = {}

    pitch = TAG_SIZE * (1.0 + TAG_SPACING)   # tag中心间距
    board_w = (TAG_COLS - 1) * pitch + TAG_SIZE
    board_h = (TAG_ROWS - 1) * pitch + TAG_SIZE

    cx = board_w / 2.0
    cy = board_h / 2.0

    tag_id = 0
    for r in range(TAG_ROWS):
        for c in range(TAG_COLS):
            x0 = c * pitch
            y0 = r * pitch
            x1 = x0 + TAG_SIZE
            y1 = y0 + TAG_SIZE

            pts = np.array([
                [x0 - cx, y0 - cy, 0.0],   # top-left
                [x1 - cx, y0 - cy, 0.0],   # top-right
                [x1 - cx, y1 - cy, 0.0],   # bottom-right
                [x0 - cx, y1 - cy, 0.0],   # bottom-left
            ], dtype=np.float32)

            obj_map[tag_id] = pts
            tag_id += 1

    return obj_map


def load_pairs(left_dir: Path, right_dir: Path):
    left_files = sorted([p.name for p in left_dir.iterdir() if p.suffix.lower() in IMG_EXTS])
    right_files = sorted([p.name for p in right_dir.iterdir() if p.suffix.lower() in IMG_EXTS])
    common = sorted(list(set(left_files) & set(right_files)))
    return common


def detect_tags(img_gray):
    results = detector.detect(img_gray, estimate_tag_pose=False)
    tag_dict = {}

    for r in results:
        tid = int(r.tag_id)
        corners = np.asarray(r.corners, dtype=np.float32)
        if corners.shape != (4, 2):
            continue
        tag_dict[tid] = corners

    return tag_dict


def collect_points_for_pair(img_l, img_r, obj_map):
    tags_l = detect_tags(img_l)
    tags_r = detect_tags(img_r)

    ids_l = set(tags_l.keys())
    ids_r = set(tags_r.keys())
    common_ids = sorted(list(ids_l & ids_r))

    obj_pts = []
    img_pts_l = []
    img_pts_r = []

    for tid in common_ids:
        if tid not in obj_map:
            continue

        obj_pts.append(obj_map[tid])
        img_pts_l.append(tags_l[tid])
        img_pts_r.append(tags_r[tid])

    if len(obj_pts) == 0:
        return common_ids, None, None, None

    obj_pts = np.concatenate(obj_pts, axis=0).astype(np.float32)
    img_pts_l = np.concatenate(img_pts_l, axis=0).astype(np.float32)
    img_pts_r = np.concatenate(img_pts_r, axis=0).astype(np.float32)

    return common_ids, obj_pts, img_pts_l, img_pts_r


def print_matrix(name, mat):
    print(f"\n{name} =")
    print(np.array2string(mat, precision=8, suppress_small=False))


# =========================================================
# 主程序
# =========================================================
def main():
    if not LEFT_DIR.exists():
        print(f"ERROR: left 路径不存在: {LEFT_DIR}")
        return
    if not RIGHT_DIR.exists():
        print(f"ERROR: right 路径不存在: {RIGHT_DIR}")
        return

    pair_names = load_pairs(LEFT_DIR, RIGHT_DIR)
    if len(pair_names) == 0:
        print("ERROR: 没有找到同名左右图像对")
        return

    print(f"Total candidate pairs: {len(pair_names)}")

    obj_map = build_aprilgrid_object_points()

    object_points_all = []
    image_points_left_all = []
    image_points_right_all = []

    valid_names = []
    image_size = None

    for fname in pair_names:
        lpath = LEFT_DIR / fname
        rpath = RIGHT_DIR / fname

        img_l = cv2.imread(str(lpath), cv2.IMREAD_GRAYSCALE)
        img_r = cv2.imread(str(rpath), cv2.IMREAD_GRAYSCALE)

        if img_l is None or img_r is None:
            print(f"[SKIP] {fname}: imread failed")
            continue

        current_size_l = (img_l.shape[1], img_l.shape[0])
        current_size_r = (img_r.shape[1], img_r.shape[0])

        if current_size_l != current_size_r:
            print(f"[SKIP] {fname}: left/right image size mismatch")
            continue

        if image_size is None:
            image_size = current_size_l

        if current_size_l != image_size:
            print(f"[SKIP] {fname}: image size mismatch with dataset")
            continue

        common_ids, obj_pts, img_pts_l, img_pts_r = collect_points_for_pair(img_l, img_r, obj_map)

        if obj_pts is None or len(common_ids) < MIN_COMMON_TAGS:
            print(f"[SKIP] {fname}: common tags = {len(common_ids)}")
            continue

        object_points_all.append(obj_pts)
        image_points_left_all.append(img_pts_l)
        image_points_right_all.append(img_pts_r)
        valid_names.append(fname)

        print(f"[KEEP] {fname}: common tags = {len(common_ids)}, points = {len(obj_pts)}")

    print("\n====================================")
    print(f"Valid stereo pairs: {len(valid_names)}")
    print("====================================")

    if len(valid_names) < 10:
        print("ERROR: 有效图像对太少，不建议继续标定")
        return

    # -----------------------------------------------------
    # 1) 单目标定初值
    # -----------------------------------------------------
    fx_init = 1000.0
    fy_init = 1000.0
    cx_init = image_size[0] / 2.0
    cy_init = image_size[1] / 2.0

    K_init = np.array([
        [fx_init, 0.0, cx_init],
        [0.0, fy_init, cy_init],
        [0.0, 0.0, 1.0]
    ], dtype=np.float64)

    D_init = np.zeros((5, 1), dtype=np.float64)

    calib_flags = (
        cv2.CALIB_USE_INTRINSIC_GUESS |
        cv2.CALIB_FIX_K3
    )

    # -----------------------------------------------------
    # 2) 左单目标定
    # -----------------------------------------------------
    print("\nRunning left camera calibration...")
    ret_l, K1, D1, rvecs_l, tvecs_l = cv2.calibrateCamera(
        objectPoints=object_points_all,
        imagePoints=image_points_left_all,
        imageSize=image_size,
        cameraMatrix=K_init.copy(),
        distCoeffs=D_init.copy(),
        flags=calib_flags
    )

    # -----------------------------------------------------
    # 3) 右单目标定
    # -----------------------------------------------------
    print("Running right camera calibration...")
    ret_r, K2, D2, rvecs_r, tvecs_r = cv2.calibrateCamera(
        objectPoints=object_points_all,
        imagePoints=image_points_right_all,
        imageSize=image_size,
        cameraMatrix=K_init.copy(),
        distCoeffs=D_init.copy(),
        flags=calib_flags
    )

    # -----------------------------------------------------
    # 4) 双目标定
    # -----------------------------------------------------
    print("Running stereo calibration...")
    stereo_criteria = (
        cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER,
        100,
        1e-6
    )

    stereo_flags = cv2.CALIB_FIX_INTRINSIC

    ret_s, K1s, D1s, K2s, D2s, R, T, E, F = cv2.stereoCalibrate(
        objectPoints=object_points_all,
        imagePoints1=image_points_left_all,
        imagePoints2=image_points_right_all,
        cameraMatrix1=K1,
        distCoeffs1=D1,
        cameraMatrix2=K2,
        distCoeffs2=D2,
        imageSize=image_size,
        criteria=stereo_criteria,
        flags=stereo_flags
    )

    baseline = float(np.linalg.norm(T))

    # -----------------------------------------------------
    # 5) 打印结果
    # -----------------------------------------------------
    print("\n================ CALIBRATION RESULT ================")
    print(f"Image size                : {image_size}")
    print(f"Used stereo pairs         : {len(valid_names)}")
    print(f"Left reprojection error   : {ret_l:.6f}")
    print(f"Right reprojection error  : {ret_r:.6f}")
    print(f"Stereo reprojection error : {ret_s:.6f}")
    print(f"Baseline length (m)       : {baseline:.9f}")

    print_matrix("K1 (left)", K1s)
    print_matrix("D1 (left)", D1s)

    print_matrix("K2 (right)", K2s)
    print_matrix("D2 (right)", D2s)

    print_matrix("R", R)
    print_matrix("T", T)
    print_matrix("E", E)
    print_matrix("F", F)

    print("\nUsed image pairs:")
    for name in valid_names:
        print(name)

    print("\nDone.")


if __name__ == "__main__":
    main()
