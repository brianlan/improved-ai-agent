#!/usr/bin/env python3
"""
下载视频的辅助脚本
使用方法: python download_video.py <video-url> [output-name] [--workdir <path]
"""

import sys
import subprocess
import os
import argparse


def download_video(url, output_name="video", workdir="/tmp/video-understanding"):
    """使用 yt-dlp 下载视频"""
    os.makedirs(workdir, exist_ok=True)
    print(f"正在下载视频: {url}")

    # 下载视频
    cmd = [
        "yt-dlp",
        url,
        "-o",
        os.path.join(workdir, f"{output_name}.%(ext)s"),
        "--no-playlist",
    ]

    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("视频下载成功!")
        # 找到下载的文件
        downloaded_files = [
            f
            for f in os.listdir(workdir)
            if f.startswith(output_name) and not f.endswith(".tmp")
        ]
        if downloaded_files:
            video_file = os.path.join(workdir, sorted(downloaded_files)[-1])
            print(f"下载的文件: {video_file}")
            return video_file
        return True
    except subprocess.CalledProcessError as e:
        print(f"下载失败: {e}")
        print(f"错误输出: {e.stderr}")
        return False


def download_audio_only(url, output_name="audio", workdir="/tmp/video-understanding"):
    """只下载音频"""
    os.makedirs(workdir, exist_ok=True)
    print(f"正在下载音频: {url}")

    cmd = [
        "yt-dlp",
        "-x",
        "--audio-format",
        "wav",
        url,
        "-o",
        os.path.join(workdir, f"{output_name}.%(ext)s"),
        "--no-playlist",
    ]

    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("音频下载成功!")
        downloaded_files = [
            f
            for f in os.listdir(workdir)
            if f.startswith(output_name) and not f.endswith(".tmp")
        ]
        if downloaded_files:
            audio_file = os.path.join(workdir, sorted(downloaded_files)[-1])
            print(f"下载的文件: {audio_file}")
            return audio_file
        return True
    except subprocess.CalledProcessError as e:
        print(f"下载失败: {e}")
        return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="下载视频或音频的辅助脚本")
    parser.add_argument(
        "--workdir",
        type=str,
        default="/tmp/video-understanding/",
        help="工作目录（默认: /tmp/video-understanding/）",
    )
    parser.add_argument("--audio-only", action="store_true", help="只下载音频")
    parser.add_argument("url", nargs="?", help="视频 URL")
    parser.add_argument(
        "output_name", nargs="?", default=None, help="输出文件名（不含扩展名）"
    )

    args = parser.parse_args()

    if not args.url:
        print(
            "使用方法: python download_video.py <video-url> [output-name] [--workdir <path>]"
        )
        print(
            "或者:   python download_video.py --audio-only <video-url> [output-name] [--workdir <path>]"
        )
        sys.exit(1)

    workdir = args.workdir
    os.makedirs(workdir, exist_ok=True)

    if args.audio_only:
        output_name = args.output_name if args.output_name else "audio"
        download_audio_only(args.url, output_name, workdir)
    else:
        output_name = args.output_name if args.output_name else "video"
        download_video(args.url, output_name, workdir)
