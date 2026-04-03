#!/usr/bin/env python3
"""
提取视频帧的辅助脚本
使用方法: python extract_frames.py <video-file> [interval-seconds] [output-dir] [--workdir <path>]
示例: python extract_frames.py video.mp4
      python extract_frames.py video.mp4 15
      python extract_frames.py video.mp4 15 my_frames
"""

import sys
import subprocess
import os
import argparse


def extract_frames(
    video_file,
    interval_seconds=15,
    output_dir="frames",
    keyframes_only=False,
    workdir="/tmp/video-understanding",
):
    """
    从视频中提取帧

    Args:
        video_file: 视频文件路径
        interval_seconds: 每隔多少秒提取一帧（默认 15 秒）
        output_dir: 输出目录
        keyframes_only: 是否只提取关键帧（I 帧）
        workdir: 工作目录
    """
    full_output_dir = os.path.join(workdir, output_dir)
    os.makedirs(full_output_dir, exist_ok=True)
    print(f"输出目录: {full_output_dir}")

    # 获取视频时长
    duration = get_video_duration(video_file)
    if duration:
        print(f"视频时长: {duration:.1f} 秒 ({duration / 60:.1f} 分钟)")
        expected_frames = int(duration / interval_seconds) + 1
        print(f"预期提取帧数: ~{expected_frames}")

    if keyframes_only:
        print("正在提取关键帧（I 帧）...")
        cmd = [
            "ffmpeg",
            "-i",
            video_file,
            "-vf",
            "select='eq(pict_type,PICT_TYPE_I)'",
            "-vsync",
            "vfr",
            os.path.join(full_output_dir, "keyframe_%04d.jpg"),
            "-y",
        ]
    else:
        print(f"正在提取帧（每 {interval_seconds} 秒一帧）...")
        fps = 1.0 / interval_seconds
        cmd = [
            "ffmpeg",
            "-i",
            video_file,
            "-vf",
            f"fps={fps}",
            "-q:v",
            "2",
            os.path.join(full_output_dir, "frame_%04d.jpg"),
            "-y",
        ]

    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)

        # 统计提取的帧数
        frames = [f for f in os.listdir(full_output_dir) if f.endswith(".jpg")]
        print(f"成功提取 {len(frames)} 帧")

        return full_output_dir, frames

    except subprocess.CalledProcessError as e:
        print(f"提取帧失败: {e}")
        print(f"错误输出: {e.stderr}")
        return None, None


def get_video_duration(video_file):
    """获取视频时长（秒）"""
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        video_file,
    ]

    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        return float(result.stdout.strip())
    except:
        return None


def get_frame_timestamps(output_dir, interval_seconds=15):
    """
    为提取的帧生成时间戳信息

    Returns:
        list: 帧信息列表，每项包含 {'file': filename, 'timestamp_seconds': seconds, 'timestamp': 'HH:MM:SS'}
    """
    frames = sorted([f for f in os.listdir(output_dir) if f.endswith(".jpg")])

    frame_info = []
    for i, frame_file in enumerate(frames):
        timestamp_seconds = i * interval_seconds
        hours = int(timestamp_seconds / 3600)
        minutes = int((timestamp_seconds % 3600) / 60)
        seconds = int(timestamp_seconds % 60)
        timestamp = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

        frame_info.append(
            {
                "file": frame_file,
                "index": i + 1,
                "timestamp_seconds": timestamp_seconds,
                "timestamp": timestamp,
            }
        )

    return frame_info


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="提取视频帧的辅助脚本")
    parser.add_argument(
        "--workdir",
        type=str,
        default="/tmp/video-understanding/",
        help="工作目录（默认: /tmp/video-understanding/）",
    )
    parser.add_argument("--keyframes", action="store_true", help="只提取关键帧（I 帧）")
    parser.add_argument("video_file", help="视频文件路径")
    parser.add_argument(
        "interval_seconds",
        nargs="?",
        type=float,
        default=15,
        help="每隔多少秒提取一帧（默认 15 秒）",
    )
    parser.add_argument(
        "output_dir", nargs="?", default="frames", help="输出目录（默认: frames）"
    )

    args = parser.parse_args()

    workdir = args.workdir
    os.makedirs(workdir, exist_ok=True)

    video_file = args.video_file
    interval_seconds = args.interval_seconds
    output_dir = args.output_dir
    keyframes_only = args.keyframes

    if not os.path.exists(video_file):
        print(f"错误: 文件不存在: {video_file}")
        sys.exit(1)

    # 提取帧
    full_output_dir, frames = extract_frames(
        video_file, interval_seconds, output_dir, keyframes_only, workdir
    )

    if full_output_dir and frames:
        # 生成时间戳信息
        # 注意：关键帧模式下无法仅凭固定间隔推导精确时间戳，因此不写伪造时间。
        if keyframes_only:
            frame_info = [
                {
                    "file": frame,
                    "index": i + 1,
                    "timestamp_seconds": None,
                    "timestamp": None,
                }
                for i, frame in enumerate(sorted(frames))
            ]
        else:
            frame_info = get_frame_timestamps(full_output_dir, interval_seconds)

        # 保存帧信息
        import json

        with open(
            os.path.join(full_output_dir, "frame_info.json"), "w", encoding="utf-8"
        ) as f:
            json.dump(frame_info, f, ensure_ascii=False, indent=2)

        print(f"\n帧信息已保存到: {full_output_dir}/frame_info.json")
        print(f"前 5 帧:")
        for info in frame_info[:5]:
            print(f"  {info['timestamp']} - {info['file']}")
