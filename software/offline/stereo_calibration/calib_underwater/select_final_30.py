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
import re
import shutil
from pathlib import Path

CSV_PATH = Path(_hardwarex_path('calib_candidates/scan_log.csv'))
SRC_LEFT = Path(_hardwarex_path('calib_candidates/left'))
SRC_RIGHT = Path(_hardwarex_path('calib_candidates/right'))

OUT_ROOT = Path(_hardwarex_path('calib_final'))
OUT_LEFT = OUT_ROOT / "left"
OUT_RIGHT = OUT_ROOT / "right"
OUT_LIST = OUT_ROOT / "selected_list.txt"

OUT_LEFT.mkdir(parents=True, exist_ok=True)
OUT_RIGHT.mkdir(parents=True, exist_ok=True)

MIN_COMMON = 7
TARGET_NUM = 30
MIN_GAP_SAME_BAG = 20


def parse_name(fname: str):
    m = re.match(r"([^_]+)_(\d+)\.[A-Za-z0-9]+$", fname)
    if not m:
        return None, None
    bag = m.group(1)
    num = int(m.group(2))
    return bag, num


def is_far_enough(num, selected_nums, min_gap):
    for s in selected_nums:
        if abs(num - s) < min_gap:
            return False
    return True


def main():
    rows = []

    with open(CSV_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if int(row["keep"]) != 1:
                continue

            fname = row["filename"]
            left_tags = int(row["left_tags"])
            right_tags = int(row["right_tags"])
            common = int(row["common_tags"])

            bag, num = parse_name(fname)
            if bag is None:
                continue

            rows.append({
                "fname": fname,
                "bag": bag,
                "num": num,
                "left_tags": left_tags,
                "right_tags": right_tags,
                "common": common
            })

    # 先按质量排序
    rows.sort(key=lambda x: (-x["common"], -x["left_tags"], -x["right_tags"], x["fname"]))

    selected = []
    selected_nums_by_bag = {}

    # 第一轮：优先选 common >= MIN_COMMON
    for row in rows:
        if row["common"] < MIN_COMMON:
            continue

        bag = row["bag"]
        num = row["num"]

        if bag not in selected_nums_by_bag:
            selected_nums_by_bag[bag] = []

        if not is_far_enough(num, selected_nums_by_bag[bag], MIN_GAP_SAME_BAG):
            continue

        selected.append(row)
        selected_nums_by_bag[bag].append(num)

        if len(selected) >= TARGET_NUM:
            break

    # 第二轮：如果不够，再从 common 较低的里补
    if len(selected) < TARGET_NUM:
        already = set(r["fname"] for r in selected)

        for row in rows:
            if row["fname"] in already:
                continue

            bag = row["bag"]
            num = row["num"]

            if bag not in selected_nums_by_bag:
                selected_nums_by_bag[bag] = []

            if not is_far_enough(num, selected_nums_by_bag[bag], MIN_GAP_SAME_BAG):
                continue

            selected.append(row)
            selected_nums_by_bag[bag].append(num)

            if len(selected) >= TARGET_NUM:
                break

    # 复制
    with open(OUT_LIST, "w", encoding="utf-8") as f:
        for row in selected:
            fname = row["fname"]
            shutil.copy2(SRC_LEFT / fname, OUT_LEFT / fname)
            shutil.copy2(SRC_RIGHT / fname, OUT_RIGHT / fname)

            line = f"{fname} bag={row['bag']} num={row['num']} left={row['left_tags']} right={row['right_tags']} common={row['common']}"
            print(line)
            f.write(line + "\n")

    print("\n===================================")
    print(f"Selected pairs: {len(selected)}")
    print(f"Saved left  : {OUT_LEFT}")
    print(f"Saved right : {OUT_RIGHT}")
    print(f"Saved list  : {OUT_LIST}")
    print("===================================")


if __name__ == "__main__":
    main()
