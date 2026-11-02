#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os as _hardwarex_os

def _hardwarex_path(relative_path):
    # Explicit workspace for private data and generated outputs.
    work_root = _hardwarex_os.environ["HARDWAREX_WORK_ROOT"]
    if not _hardwarex_os.path.isabs(work_root):
        raise ValueError("HARDWAREX_WORK_ROOT must be an absolute path")
    return _hardwarex_os.path.join(work_root, relative_path)

import csv
import shutil
from pathlib import Path

import cv2
import numpy as np
from pupil_apriltags import Detector

# =========================================================
# 1. 路径（写死）
# =========================================================
LEFT_DIR  = Path(_hardwarex_path('bags/test_09/left'))
RIGHT_DIR = Path(_hardwarex_path('bags/test_09/right'))

OUT_ROOT  = Path(_hardwarex_path('calib_candidates'))
OUT_LEFT  = OUT_ROOT / "left"
OUT_RIGHT = OUT_ROOT / "right"
OUT_CSV   = OUT_ROOT / "scan_log.csv"

IMG_EXTS = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff"}

# =========================================================
# 2. 阈值
# =========================================================
MIN_COMMON_TAGS = 4     # 先放宽到4，先把候选池找出来
MIN_LEFT_TAGS   = 4
MIN_RIGHT_TAGS  = 4

# =========================================================
# 3. 检测器
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
def load_pairs(left_dir: Path, right_dir: Path):
    left_files = sorted([p.name for p in left_dir.iterdir() if p.suffix.lower() in IMG_EXTS])
    right_files = sorted([p.name for p in right_dir.iterdir() if p.suffix.lower() in IMG_EXTS])
    common = sorted(list(set(left_files) & set(right_files)))
    return common

def detect_tag_ids(img_gray):
    results = detector.detect(img_gray, estimate_tag_pose=False)
    ids = set()
    for r in results:
        ids.add(int(r.tag_id))
    return ids

def main():
    if not LEFT_DIR.exists():
        print(f"ERROR: left 路径不存在: {LEFT_DIR}")
        return
    if not RIGHT_DIR.exists():
        print(f"ERROR: right 路径不存在: {RIGHT_DIR}")
        return

    OUT_LEFT.mkdir(parents=True, exist_ok=True)
    OUT_RIGHT.mkdir(parents=True, exist_ok=True)

    pair_names = load_pairs(LEFT_DIR, RIGHT_DIR)
    print(f"Total pairs: {len(pair_names)}")

    kept = 0
    skipped = 0

    with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "filename", "left_tags", "right_tags", "common_tags", "keep"
        ])

        for fname in pair_names:
            lpath = LEFT_DIR / fname
            rpath = RIGHT_DIR / fname

            img_l = cv2.imread(str(lpath), cv2.IMREAD_GRAYSCALE)
            img_r = cv2.imread(str(rpath), cv2.IMREAD_GRAYSCALE)

            if img_l is None or img_r is None:
                writer.writerow([fname, 0, 0, 0, 0])
                skipped += 1
                print(f"[SKIP] {fname}: imread failed")
                continue

            ids_l = detect_tag_ids(img_l)
            ids_r = detect_tag_ids(img_r)
            common_ids = ids_l & ids_r

            nl = len(ids_l)
            nr = len(ids_r)
            nc = len(common_ids)

            keep = (
                nl >= MIN_LEFT_TAGS and
                nr >= MIN_RIGHT_TAGS and
                nc >= MIN_COMMON_TAGS
            )

            writer.writerow([fname, nl, nr, nc, int(keep)])

            if keep:
                shutil.copy2(lpath, OUT_LEFT / fname)
                shutil.copy2(rpath, OUT_RIGHT / fname)
                kept += 1
                print(f"[KEEP] {fname}: left={nl}, right={nr}, common={nc}")
            else:
                skipped += 1
                print(f"[SKIP] {fname}: left={nl}, right={nr}, common={nc}")

    print("\n==============================")
    print(f"Total pairs : {len(pair_names)}")
    print(f"Kept        : {kept}")
    print(f"Skipped     : {skipped}")
    print(f"Saved left  : {OUT_LEFT}")
    print(f"Saved right : {OUT_RIGHT}")
    print(f"Saved csv   : {OUT_CSV}")
    print("==============================")

if __name__ == "__main__":
    main()
