#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os as _hardwarex_os

def _hardwarex_path(relative_path):
    # Explicit workspace for private data and generated outputs.
    work_root = _hardwarex_os.environ["HARDWAREX_WORK_ROOT"]
    if not _hardwarex_os.path.isabs(work_root):
        raise ValueError("HARDWAREX_WORK_ROOT must be an absolute path")
    return _hardwarex_os.path.join(work_root, relative_path)

import rosbag
import numpy as np


# =========================
# 写死路径
# =========================
SEQ_BAG = _hardwarex_path('bags/rosbag/dataset/sequence_02/2_lr_rect_underwater.bag')
GT_BAG  = _hardwarex_path('bags/rosbag/gt/sequence_02/2.bag')

LEFT_TOPIC  = "/camera/left/image_rect_underwater"
RIGHT_TOPIC = "/camera/right/image_rect_underwater"
GT_TOPIC    = "/camera/image_raw"


def read_topic_times(bag_path, topic_name):
    times = []
    with rosbag.Bag(bag_path, 'r') as bag:
        for topic, msg, t in bag.read_messages(topics=[topic_name]):
            times.append(t.to_sec())
    return np.array(times, dtype=np.float64)


def summarize_times(name, times, expected_fps=20.0):
    print("\n" + "=" * 70)
    print(name)
    print("=" * 70)

    if len(times) == 0:
        print("No messages found.")
        return None

    start = times[0]
    end = times[-1]
    duration = end - start

    print(f"start time         : {start:.6f}")
    print(f"end time           : {end:.6f}")
    print(f"duration           : {duration:.6f} s")
    print(f"frame count        : {len(times)}")

    result = {
        "start": start,
        "end": end,
        "count": len(times),
        "duration": duration
    }

    if len(times) >= 2:
        dt = np.diff(times)               # second
        dt_ms = dt * 1000.0              # ms

        mean_dt = np.mean(dt)
        std_dt = np.std(dt)
        min_dt = np.min(dt)
        max_dt = np.max(dt)

        mean_dt_ms = np.mean(dt_ms)
        std_dt_ms = np.std(dt_ms)
        min_dt_ms = np.min(dt_ms)
        max_dt_ms = np.max(dt_ms)

        fps = 1.0 / mean_dt if mean_dt > 0 else 0.0
        expected_dt_ms = 1000.0 / expected_fps

        print(f"mean dt            : {mean_dt:.6f} s   ({mean_dt_ms:.3f} ms)")
        print(f"std dt             : {std_dt:.6f} s   ({std_dt_ms:.3f} ms)")
        print(f"min dt             : {min_dt:.6f} s   ({min_dt_ms:.3f} ms)")
        print(f"max dt             : {max_dt:.6f} s   ({max_dt_ms:.3f} ms)")
        print(f"approx fps         : {fps:.3f} Hz")
        print(f"expected fps       : {expected_fps:.3f} Hz")
        print(f"expected dt        : {expected_dt_ms:.3f} ms")
        print(f"fps error          : {fps - expected_fps:+.3f} Hz")
        print(f"mean dt error      : {mean_dt_ms - expected_dt_ms:+.3f} ms")
        print(f"largest gap        : {max_dt_ms:.3f} ms")

        # 异常 gap: 大于 2 倍均值 或 大于 1.5 倍理论间隔
        abnormal_idx = np.where((dt > 2.0 * mean_dt) | (dt_ms > 1.5 * expected_dt_ms))[0]
        print(f"abnormal gaps      : {len(abnormal_idx)}")

        if len(abnormal_idx) > 0:
            print("first few abnormal gaps:")
            for idx in abnormal_idx[:10]:
                print(
                    f"  index {idx:6d}: "
                    f"t={times[idx]:.6f} -> {times[idx+1]:.6f}, "
                    f"dt={dt[idx]:.6f} s ({dt_ms[idx]:.3f} ms)"
                )

        result.update({
            "mean_dt": mean_dt,
            "std_dt": std_dt,
            "min_dt": min_dt,
            "max_dt": max_dt,
            "mean_dt_ms": mean_dt_ms,
            "std_dt_ms": std_dt_ms,
            "min_dt_ms": min_dt_ms,
            "max_dt_ms": max_dt_ms,
            "fps": fps,
            "abnormal_idx": abnormal_idx
        })

    return result


def compare_stereo_sync(left_times, right_times):
    print("\n" + "=" * 70)
    print("Stereo synchronization check")
    print("=" * 70)

    if len(left_times) == 0 or len(right_times) == 0:
        print("Left or right topic is empty.")
        return

    print(f"left frames         : {len(left_times)}")
    print(f"right frames        : {len(right_times)}")

    if len(left_times) != len(right_times):
        print("frame count match   : No")
    else:
        print("frame count match   : Yes")

    n = min(len(left_times), len(right_times))
    diff = np.abs(left_times[:n] - right_times[:n])
    diff_ms = diff * 1000.0

    print(f"paired frames       : {n}")
    print(f"mean |dt|           : {np.mean(diff):.9f} s   ({np.mean(diff_ms):.6f} ms)")
    print(f"std  |dt|           : {np.std(diff):.9f} s   ({np.std(diff_ms):.6f} ms)")
    print(f"max  |dt|           : {np.max(diff):.9f} s   ({np.max(diff_ms):.6f} ms)")

    bad = np.where(diff > 1e-3)[0]   # > 1 ms
    print(f"pairs with |dt| >1ms: {len(bad)}")

    if len(bad) > 0:
        print("first few unsynced pairs:")
        for idx in bad[:10]:
            print(
                f"  idx {idx:6d}: "
                f"left={left_times[idx]:.6f}, "
                f"right={right_times[idx]:.6f}, "
                f"|dt|={diff[idx]:.9f} s ({diff_ms[idx]:.6f} ms)"
            )


def compute_overlap(seq_times, gt_times):
    print("\n" + "=" * 70)
    print("Sequence-GT overlap")
    print("=" * 70)

    if len(seq_times) == 0 or len(gt_times) == 0:
        print("Sequence or GT topic is empty.")
        return None

    overlap_start = max(seq_times[0], gt_times[0])
    overlap_end = min(seq_times[-1], gt_times[-1])
    overlap_duration = overlap_end - overlap_start

    print(f"sequence start      : {seq_times[0]:.6f}")
    print(f"sequence end        : {seq_times[-1]:.6f}")
    print(f"gt start            : {gt_times[0]:.6f}")
    print(f"gt end              : {gt_times[-1]:.6f}")

    print(f"overlap start       : {overlap_start:.6f}")
    print(f"overlap end         : {overlap_end:.6f}")
    print(f"overlap duration    : {overlap_duration:.6f} s")

    if overlap_duration <= 0:
        print("valid overlap       : No")
    else:
        print("valid overlap       : Yes")

    return {
        "start": overlap_start,
        "end": overlap_end,
        "duration": overlap_duration
    }


def main():
    print("\nReading sequence bag topics...")
    left_times = read_topic_times(SEQ_BAG, LEFT_TOPIC)
    right_times = read_topic_times(SEQ_BAG, RIGHT_TOPIC)

    print("\nReading GT bag topic...")
    gt_times = read_topic_times(GT_BAG, GT_TOPIC)

    left_info = summarize_times(f"Sequence LEFT  : {LEFT_TOPIC}", left_times, expected_fps=20.0)
    right_info = summarize_times(f"Sequence RIGHT : {RIGHT_TOPIC}", right_times, expected_fps=20.0)
    gt_info = summarize_times(f"GT MONO        : {GT_TOPIC}", gt_times, expected_fps=20.0)

    compare_stereo_sync(left_times, right_times)
    overlap_info = compute_overlap(left_times, gt_times)

    print("\n" + "=" * 70)
    print("Quick conclusion")
    print("=" * 70)

    if left_info is not None and "fps" in left_info:
        print(f"LEFT  fps          : {left_info['fps']:.3f} Hz, max gap {left_info['max_dt_ms']:.3f} ms")
    if right_info is not None and "fps" in right_info:
        print(f"RIGHT fps          : {right_info['fps']:.3f} Hz, max gap {right_info['max_dt_ms']:.3f} ms")
    if gt_info is not None and "fps" in gt_info:
        print(f"GT    fps          : {gt_info['fps']:.3f} Hz, max gap {gt_info['max_dt_ms']:.3f} ms")
    if overlap_info is not None:
        print(f"Overlap duration   : {overlap_info['duration']:.3f} s")


if __name__ == "__main__":
    main()
