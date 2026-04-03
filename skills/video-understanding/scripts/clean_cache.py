#!/usr/bin/env python3
"""
清理缓存文件的辅助脚本
使用方法: python clean_cache.py [--all] [--workdir <path>]

选项:
  --all    清理所有缓存，包括 OCR 帧和临时目录
  --workdir <path>  工作目录（默认: /tmp/video-understanding/）
  不带参数  只清理视频和音频缓存
"""

import os
import shutil
import sys
import argparse


# 基础缓存文件
BASIC_CACHE_FILES = [
    "video.mp4",
    "video.webm",
    "audio.wav",
    "audio.mp3",
    "audio_16k.wav",
    "transcript.txt",
    "asr_result.json",
    "video_analysis.json",
]

# 基础缓存目录
BASIC_CACHE_DIRS = [
    "chunks",
    "bailian_chunks",
]

# 完整清理时的额外目录
EXTRA_CACHE_DIRS = [
    "frames",
]


def clean_cache(clean_all=False, workdir="/tmp/video-understanding/"):
    """清理缓存文件"""
    os.makedirs(workdir, exist_ok=True)
    os.chdir(workdir)

    files_to_remove = BASIC_CACHE_FILES.copy()
    dirs_to_remove = BASIC_CACHE_DIRS.copy()

    if clean_all:
        dirs_to_remove.extend(EXTRA_CACHE_DIRS)

    removed_files = []
    removed_dirs = []

    # 删除文件
    for f in files_to_remove:
        if os.path.exists(f):
            os.remove(f)
            removed_files.append(f)

    # 删除目录
    for d in dirs_to_remove:
        if os.path.exists(d):
            shutil.rmtree(d)
            removed_dirs.append(d)

    print(f"缓存清理完成! (工作目录: {workdir})")
    print(f"  删除文件: {len(removed_files)}")
    if removed_files:
        for f in removed_files:
            print(f"    - {f}")

    print(f"  删除目录: {len(removed_dirs)}")
    if removed_dirs:
        for d in removed_dirs:
            print(f"    - {d}/")

    if not removed_files and not removed_dirs:
        print("  (无缓存文件需要清理)")

    return len(removed_files) + len(removed_dirs)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="清理缓存文件的辅助脚本")
    parser.add_argument(
        "--workdir",
        type=str,
        default="/tmp/video-understanding/",
        help="工作目录（默认: /tmp/video-understanding/）",
    )
    parser.add_argument(
        "--all", action="store_true", help="清理所有缓存，包括 OCR 帧和临时目录"
    )

    args = parser.parse_args()

    if args.all:
        print("清理所有缓存（包括 OCR 帧）...")
    else:
        print("清理视频和音频缓存...")

    clean_cache(args.all, args.workdir)
