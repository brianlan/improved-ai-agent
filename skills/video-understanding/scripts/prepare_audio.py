#!/usr/bin/env python3
"""
准备音频用于 ASR 的辅助脚本
使用方法: python prepare_audio.py <input-video-or-audio> [output-name] [--workdir <path>]
"""

import sys
import subprocess
import os
import argparse


def extract_audio(input_file, output_name="audio", workdir="/tmp/video-understanding"):
    """从视频中提取音频"""
    os.makedirs(workdir, exist_ok=True)
    output_wav = os.path.join(workdir, f"{output_name}.wav")

    print(f"正在从 {input_file} 提取音频...")

    cmd = [
        "ffmpeg",
        "-i",
        input_file,
        "-vn",
        "-acodec",
        "pcm_s16le",
        "-ar",
        "16000",
        "-ac",
        "1",
        output_wav,
        "-y",
    ]

    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(f"音频提取成功: {output_wav}")
        return output_wav
    except subprocess.CalledProcessError as e:
        print(f"提取失败: {e}")
        return None


def compress_audio(
    input_wav,
    output_name="audio",
    bitrate="32k",
    sample_rate=16000,
    workdir="/tmp/video-understanding",
):
    """压缩音频以减小文件大小"""
    os.makedirs(workdir, exist_ok=True)
    output_mp3 = os.path.join(workdir, f"{output_name}.mp3")

    print(f"正在压缩音频: {input_wav} -> {output_mp3}")

    cmd = [
        "ffmpeg",
        "-i",
        input_wav,
        "-ac",
        "1",
        "-ar",
        str(sample_rate),
        "-codec",
        "libmp3lame",
        "-b:a",
        bitrate,
        output_mp3,
        "-y",
    ]

    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)

        # 显示文件大小
        input_size = os.path.getsize(input_wav) / (1024 * 1024)
        output_size = os.path.getsize(output_mp3) / (1024 * 1024)

        print(f"压缩成功!")
        print(f"原始大小: {input_size:.2f} MB")
        print(f"压缩后大小: {output_size:.2f} MB")
        print(f"压缩率: {(1 - output_size / input_size) * 100:.1f}%")

        return output_mp3
    except subprocess.CalledProcessError as e:
        print(f"压缩失败: {e}")
        return None


def get_audio_duration(input_file):
    """获取音频时长"""
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        input_file,
    ]

    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        duration = float(result.stdout.strip())
        return duration
    except:
        return None


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="准备音频用于 ASR 的辅助脚本")
    parser.add_argument(
        "--workdir",
        type=str,
        default="/tmp/video-understanding/",
        help="工作目录（默认: /tmp/video-understanding/）",
    )
    parser.add_argument("input_file", help="输入视频或音频文件")
    parser.add_argument(
        "output_name", nargs="?", default="audio", help="输出文件名（不含扩展名）"
    )

    args = parser.parse_args()

    workdir = args.workdir
    os.makedirs(workdir, exist_ok=True)

    input_file = args.input_file
    output_name = args.output_name

    # 如果输入是视频，先提取音频
    if input_file.lower().endswith((".mp4", ".mkv", ".avi", ".mov", ".webm")):
        print("检测到视频文件，先提取音频...")
        wav_file = extract_audio(input_file, output_name, workdir)
        if wav_file:
            # 显示时长
            duration = get_audio_duration(wav_file)
            if duration:
                print(f"音频时长: {duration:.1f} 秒 ({duration / 60:.1f} 分钟)")

            # 压缩音频
            compress_audio(wav_file, output_name, workdir=workdir)
    else:
        # 假设已经是音频文件，直接压缩
        print("检测到音频文件，直接压缩...")

        # 显示时长
        duration = get_audio_duration(input_file)
        if duration:
            print(f"音频时长: {duration:.1f} 秒 ({duration / 60:.1f} 分钟)")

        # 如果是 WAV，直接压缩
        if input_file.lower().endswith(".wav"):
            compress_audio(input_file, output_name, workdir=workdir)
        else:
            # 先转为 WAV 再压缩
            wav_file = extract_audio(input_file, output_name, workdir)
            if wav_file:
                compress_audio(wav_file, output_name, workdir=workdir)
