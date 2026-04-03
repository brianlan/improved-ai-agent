#!/usr/bin/env python3
"""
视频理解完整流程脚本（v2.4，支持 ASR Bailian 回退 + 长音频自动分割 + VLM OCR 智能回退）
使用方法: python full_pipeline.py <video-url> <asr-url> [--ocr-url <vlm-url>] [--ocr-interval <seconds>] [--workdir <path>]
示例: python full_pipeline.py https://www.bilibili.com/video/BV1W2wtzkEBR http://192.168.71.57:8002
      python full_pipeline.py https://www.bilibili.com/video/BV1W2wtzkEBR http://192.168.71.57:8002 --ocr-url http://192.168.71.57:8001
      python full_pipeline.py https://www.bilibili.com/video/BV1W2wtzkEBR http://192.168.71.57:8002 --ocr-url http://192.168.71.57:8001 --ocr-interval 10

ASR 回退机制 (v2.3+):
  1. 优先使用 LAN ASR 服务（--asr-url 指定）
  2. 首次失败后重试一次（等待 2 秒）
  3. 若仍然失败，自动回退到 Bailian API (Qwen3-ASR-Flash)
  4. Bailian API 使用 BAILIAN_API_KEY 环境变量

OCR 回退机制:
  1. 优先使用 LAN OCR 服务（--ocr-url 指定）
  2. 首次失败后重试一次
  3. 若仍然失败，脚本会写入 need_vlm_fallback.json 并返回特定退出码
  4. 上层调用者（Agent）应检测此信号并触发 VLM SubAgent 进行 OCR

VLM SubAgent OCR 模式:
  python full_pipeline.py --vlm-subagent-ocr --frame-dir <dir> --frame-info <json-file>
  此模式由 Agent spawn 的 subagent 调用，直接使用内置 VLM 进行 OCR
"""

import sys
import os
import json
import subprocess
import threading
import base64
import requests
import time
import textwrap
from datetime import datetime
import argparse


# VLM 模型列表（按优先级顺序，用于 OCR 回退）
VLM_MODEL_LIST = ["ark/doubao-seed-2.0-lite", "tx/kimi-k2.5", "ark/kimi-k2.5"]

# Bailian ASR API 配置（用于 LAN ASR 失败时的回退）
BAILIAN_API_BASE = "https://dashscope.aliyuncs.com/compatible-mode/v1"
BAILIAN_ASR_MODEL = "qwen3-asr-flash"  # 正确的模型名

# Bailian qwen3-asr-flash 限制：最长 5 分钟（300 秒），安全值 290 秒
MAX_CHUNK_DURATION = 290


def get_bailian_api_key():
    """获取 Bailian API Key"""
    return os.environ.get("BAILIAN_API_KEY") or os.environ.get("DASHSCOPE_API_KEY")


def encode_audio_base64(file_path):
    """将音频文件编码为 Base64 Data URL"""
    with open(file_path, "rb") as f:
        audio_data = f.read()

    base64_str = base64.b64encode(audio_data).decode("utf-8")

    # 根据文件类型选择 MIME type
    if file_path.endswith(".mp3"):
        mime_type = "audio/mpeg"
    elif file_path.endswith(".wav"):
        mime_type = "audio/wav"
    elif file_path.endswith(".m4a"):
        mime_type = "audio/mp4"
    else:
        mime_type = "audio/mpeg"  # 默认

    return f"data:{mime_type};base64,{base64_str}"


def get_audio_duration(audio_path):
    """获取音频时长（秒）"""
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                audio_path,
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        return float(result.stdout.strip())
    except Exception as e:
        print(f"  获取音频时长失败: {e}")
        return None


def split_audio(input_file, output_dir, chunk_duration=MAX_CHUNK_DURATION):
    """
    分割音频为多个 chunk
    """
    os.makedirs(output_dir, exist_ok=True)

    total_duration = get_audio_duration(input_file)
    if not total_duration:
        return []

    num_chunks = int(total_duration // chunk_duration) + (
        1 if total_duration % chunk_duration > 0 else 0
    )

    if num_chunks <= 1:
        return [input_file]

    print(
        f"  [ASR 线程] 音频总时长: {total_duration:.1f} 秒，需要分割为 {num_chunks} 个 chunk"
    )

    chunk_files = []
    for i in range(num_chunks):
        start_time = i * chunk_duration
        output_file = os.path.join(output_dir, f"chunk_{i:03d}.mp3")

        if os.path.exists(output_file):
            chunk_files.append(output_file)
            continue

        print(f"  [ASR 线程] 分割 Chunk {i + 1}/{num_chunks}...")
        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            input_file,
            "-ss",
            str(start_time),
            "-t",
            str(chunk_duration),
            "-acodec",
            "libmp3lame",
            "-b:a",
            "128k",
            output_file,
        ]

        result = subprocess.run(cmd, capture_output=True, timeout=300)
        if result.returncode == 0 and os.path.exists(output_file):
            chunk_files.append(output_file)

    return chunk_files


def run_command(cmd, description="", timeout=300):
    """运行命令并返回结果"""
    if description:
        print(f"\n{description}...")

    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=timeout
        )
        if result.returncode != 0:
            print(f"  警告: 命令返回非零退出码: {result.returncode}")
        return result
    except subprocess.TimeoutExpired:
        print(f"  错误: 命令超时 ({timeout}秒)")
        return None


def download_video(url, workdir="/tmp/video-understanding"):
    """下载视频"""
    os.makedirs(workdir, exist_ok=True)
    print("\n" + "=" * 60)
    print("步骤 1/5: 下载视频")
    print("=" * 60)

    # 清理旧的 video.* 文件，避免 yt-dlp 跳过下载
    for f in os.listdir(workdir):
        if f.startswith("video.") and not f.endswith(".tmp"):
            print(f"  清理旧文件: {f}")
            os.remove(os.path.join(workdir, f))

    cmd = f'yt-dlp "{url}" -o "{os.path.join(workdir, "video.%(ext)s")}" --no-playlist --force-overwrites'
    result = run_command(cmd, "正在下载视频", timeout=600)

    # 找到下载的文件
    video_files = [
        f
        for f in os.listdir(workdir)
        if f.startswith("video.") and not f.endswith(".tmp")
    ]
    if video_files:
        video_file = os.path.join(workdir, sorted(video_files)[-1])
        print(f"  下载成功: {video_file}")
        return video_file

    print("  错误: 未找到下载的视频文件")
    return None


def get_video_duration(video_file):
    """获取视频时长"""
    cmd = f'ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "{video_file}"'
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=30
        )
        return float(result.stdout.strip())
    except:
        return None


def prepare_audio(video_file, workdir="/tmp/video-understanding"):
    """准备音频（在单独线程中运行）"""
    os.makedirs(workdir, exist_ok=True)
    print("  [ASR 线程] 正在提取音频...")

    # 提取 WAV
    wav_path = os.path.join(workdir, "audio.wav")
    cmd = f'ffmpeg -i "{video_file}" -vn -acodec pcm_s16le -ar 16000 -ac 1 "{wav_path}" -y'
    subprocess.run(cmd, shell=True, capture_output=True, timeout=300)

    if not os.path.exists(wav_path):
        return None, None

    # 获取音频时长
    duration = None
    try:
        cmd = f'ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "{wav_path}"'
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=30
        )
        duration = float(result.stdout.strip())
    except:
        pass

    # 压缩为 MP3
    mp3_path = os.path.join(workdir, "audio.mp3")
    print("  [ASR 线程] 正在压缩音频...")
    cmd = f'ffmpeg -i "{wav_path}" -ac 1 -ar 16000 -codec libmp3lame -b:a 32k "{mp3_path}" -y'
    subprocess.run(cmd, shell=True, capture_output=True, timeout=300)

    if os.path.exists(mp3_path):
        return mp3_path, duration

    return None, None


def extract_frames(video_file, interval_seconds=15, workdir="/tmp/video-understanding"):
    """提取视频帧（在单独线程中运行）"""
    os.makedirs(workdir, exist_ok=True)
    print(f"  [OCR 线程] 正在提取帧（每 {interval_seconds} 秒一帧）...")

    output_dir = os.path.join(workdir, "frames")
    os.makedirs(output_dir, exist_ok=True)

    fps = 1.0 / interval_seconds
    cmd = f'ffmpeg -i "{video_file}" -vf "fps={fps}" -q:v 2 "{output_dir}/frame_%04d.jpg" -y'
    subprocess.run(cmd, shell=True, capture_output=True, timeout=600)

    frames = sorted([f for f in os.listdir(output_dir) if f.endswith(".jpg")])

    # 生成帧信息
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

    with open(os.path.join(output_dir, "frame_info.json"), "w", encoding="utf-8") as f:
        json.dump(frame_info, f, ensure_ascii=False, indent=2)

    print(f"  [OCR 线程] 提取了 {len(frames)} 帧")
    return output_dir, frame_info


def encode_image_to_base64(image_path):
    """将图片编码为 base64"""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def call_vlm_ocr_with_fallback(frame_dir, vlm_url, frame_info, result_dict, lock):
    """
    调用 VLM OCR（线程函数），支持智能回退
    1. 优先尝试 LAN OCR 服务（带 1 次重试）
    2. 若失败，标记需要 VLM 回退
    """
    print(f"  [OCR 线程] 正在调用 OCR 服务...")

    start_time = datetime.now()
    frame_files = sorted(
        [
            f
            for f in os.listdir(frame_dir)
            if f.endswith(".jpg") and not f.startswith(".")
        ]
    )

    # 构建帧信息字典（兼容两种字段名：'frame' 和 'file'）
    frame_info_dict = {
        fi.get("frame") or fi.get("file"): fi
        for fi in frame_info
        if fi.get("frame") or fi.get("file")
    }

    # 第一步：尝试 LAN OCR 服务
    lan_ocr_success = False
    lan_error = None

    for attempt in range(2):  # 最多尝试 2 次（首次 + 1 次重试）
        if attempt > 0:
            print(f"  [OCR 线程] LAN OCR 首次失败，准备重试...")
            time.sleep(2)  # 等待 2 秒后重试

        lan_ocr_success, lan_error = _try_lan_ocr(
            frame_dir,
            frame_files,
            frame_info_dict,
            vlm_url,
            result_dict,
            lock,
            start_time,
        )

        if lan_ocr_success:
            print(f"  [OCR 线程] LAN OCR 成功!")
            return

    # 第二步：LAN OCR 失败，标记需要 VLM 回退
    if not lan_ocr_success:
        print(f"  [OCR 线程] LAN OCR 失败 ({lan_error})，标记需要 VLM SubAgent 回退...")

        # 写入回退标记文件
        fallback_marker = os.path.join(frame_dir, "need_vlm_fallback.json")
        with open(fallback_marker, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "need_fallback": True,
                    "frame_dir": frame_dir,
                    "frame_count": len(frame_files),
                    "lan_error": lan_error,
                    "timestamp": datetime.now().isoformat(),
                },
                f,
                ensure_ascii=False,
                indent=2,
            )

        # 保存帧信息供 subagent 使用
        frame_list = []
        for i, frame_file in enumerate(frame_files):
            fi = frame_info_dict.get(frame_file, {})
            frame_list.append(
                {
                    "frame": frame_file,
                    "frame_index": i + 1,
                    "timestamp": fi.get("timestamp", f"Frame {i + 1}"),
                    "timestamp_seconds": fi.get("timestamp_seconds", i * 15),
                }
            )

        with open(
            os.path.join(frame_dir, "frame_info.json"), "w", encoding="utf-8"
        ) as f:
            json.dump(frame_list, f, ensure_ascii=False, indent=2)

        with lock:
            result_dict["ocr"] = {
                "success": False,
                "error": f"LAN OCR 失败，需要 VLM SubAgent 回退: {lan_error}",
                "service_url": vlm_url,
                "service_type": "lan_vlm",
                "frames_extracted": len(frame_files),
                "frames_processed": 0,
                "need_vlm_fallback": True,
                "fallback_marker": fallback_marker,
                "results": [],
            }

        print(f"  [OCR 线程] 已写入回退标记: {fallback_marker}")


def _try_lan_ocr(
    frame_dir, frame_files, frame_info_dict, vlm_url, result_dict, lock, start_time
):
    """
    尝试使用 LAN OCR 服务
    返回: (success: bool, error_message: str)
    """
    # 先获取 VLM 模型
    model_name = None
    try:
        response = requests.get(f"{vlm_url}/v1/models", timeout=30)
        if response.status_code == 200:
            data = response.json()
            if data.get("data"):
                model_name = data["data"][0]["id"]
                print(f"  [OCR 线程] 使用 LAN OCR 模型: {model_name}")
    except Exception as e:
        return False, f"获取模型列表失败: {str(e)}"

    if not model_name:
        model_name = "default"

    results = []
    for i, frame_file in enumerate(frame_files):
        frame_path = os.path.join(frame_dir, frame_file)

        try:
            # 编码图片
            base64_image = encode_image_to_base64(frame_path)

            # 构建 VLM 请求
            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            },
                        },
                        {
                            "type": "text",
                            "text": "请识别这张图片中的所有文字内容。只返回识别到的文字，不要其他解释。",
                        },
                    ],
                }
            ]

            payload = {
                "model": model_name,
                "messages": messages,
                "max_tokens": 1024,
                "temperature": 0.1,
            }

            response = requests.post(
                f"{vlm_url}/v1/chat/completions", json=payload, timeout=120
            )

            if response.status_code == 200:
                vlm_result = response.json()
                if vlm_result.get("choices") and len(vlm_result["choices"]) > 0:
                    text = (
                        vlm_result["choices"][0].get("message", {}).get("content", "")
                    )
                    ocr_result = {"text": text, "raw_result": vlm_result}
                else:
                    ocr_result = {
                        "error": "No choices in response",
                        "raw_result": vlm_result,
                    }
            else:
                ocr_result = {
                    "error": f"HTTP {response.status_code}",
                    "response": response.text[:200],
                }
        except Exception as e:
            ocr_result = {"error": str(e)}

        result = {
            "frame": frame_file,
            "frame_index": i + 1,
            "success": "error" not in ocr_result,
            "error": ocr_result.get("error"),
            "text": ocr_result.get("text", ""),
            "result": ocr_result,
        }

        if frame_file in frame_info_dict:
            fi = frame_info_dict[frame_file]
            result["timestamp_seconds"] = fi.get("timestamp_seconds")
            result["timestamp"] = fi.get("timestamp")

        results.append(result)

    processing_time = (datetime.now() - start_time).total_seconds()
    success_count = sum(1 for r in results if r["success"])

    # 检查是否成功
    if success_count == 0:
        error_msg = (
            results[0].get("error", "Unknown error")
            if results
            else "No frames processed"
        )
        return False, error_msg

    # 保存结果
    output_file = os.path.join(frame_dir, "ocr_results.json")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(
            {
                "success": True,
                "service_url": vlm_url,
                "service_type": "lan_vlm",
                "model_name": model_name,
                "frames_extracted": len(frame_files),
                "frames_processed": len(results),
                "frames_successful": success_count,
                "processing_time_seconds": processing_time,
                "results": results,
            },
            f,
            ensure_ascii=False,
            indent=2,
        )

    # 提取文字
    all_text = []
    for result in results:
        if result["success"] and result.get("text"):
            text = result["text"].strip()
            if text:
                timestamp = result.get("timestamp", f"Frame {result['frame_index']}")
                all_text.append(f"[{timestamp}]\n{text}\n")

    if all_text:
        text_file = os.path.join(frame_dir, "ocr_text.txt")
        with open(text_file, "w", encoding="utf-8") as f:
            f.write("\n".join(all_text))

    with lock:
        result_dict["ocr"] = {
            "success": True,
            "error": None,
            "service_url": vlm_url,
            "service_type": "lan_vlm",
            "model_name": model_name,
            "frames_extracted": len(frame_files),
            "frames_processed": len(results),
            "frames_successful": success_count,
            "processing_time_seconds": processing_time,
            "results": results,
            "results_file": output_file,
        }

    print(
        f"  [OCR 线程] LAN OCR 完成! 成功: {success_count}/{len(results)}, 处理时间: {processing_time:.1f} 秒"
    )
    return True, None


def do_vlm_subagent_ocr(frame_dir, model_name=None):
    """
    执行 VLM SubAgent OCR（供 subagent 调用）
    按顺序尝试 VLM 模型列表中的模型

    Args:
        frame_dir: 帧目录
        model_name: 可选的指定模型名，不指定则按列表顺序尝试

    Returns:
        dict: OCR 结果
    """
    start_time = datetime.now()

    # 读取帧信息
    frame_info_file = os.path.join(frame_dir, "frame_info.json")
    frame_info_dict = {}
    if os.path.exists(frame_info_file):
        with open(frame_info_file, "r", encoding="utf-8") as f:
            frame_info_list = json.load(f)
            for fi in frame_info_list:
                # 兼容两种字段名：'frame' 和 'file'
                key = fi.get("frame") or fi.get("file")
                if key:
                    frame_info_dict[key] = fi

    # 获取帧文件列表
    frame_files = sorted(
        [
            f
            for f in os.listdir(frame_dir)
            if f.endswith(".jpg") and not f.startswith(".")
        ]
    )

    if not frame_files:
        return {"success": False, "error": "No frames found", "results": []}

    # 构建 OCR 提示词
    frame_list_json = json.dumps(
        [
            {
                "frame": f,
                "frame_index": i + 1,
                "timestamp": frame_info_dict.get(f, {}).get(
                    "timestamp", f"Frame {i + 1}"
                ),
                "timestamp_seconds": frame_info_dict.get(f, {}).get(
                    "timestamp_seconds", i * 15
                ),
            }
            for i, f in enumerate(frame_files)
        ],
        ensure_ascii=False,
        indent=2,
    )

    ocr_prompt = textwrap.dedent(f"""
    你是一个专门用于 OCR（光学字符识别）的 AI 助手。

    你的任务：识别视频帧图片中的文字内容。

    ## 输入信息
    - 帧目录: {frame_dir}
    - 帧文件列表（共 {len(frame_files)} 帧）:
    {frame_list_json}

    ## 处理要求
    1. 读取每一帧图片（完整路径：{frame_dir}/<frame_file>）
    2. 使用你的 VLM 能力识别图片中的所有文字
    3. 只返回识别到的文字，不要其他解释
    4. 如果某帧没有文字，返回空字符串

    ## 输出格式（必须严格遵循）
    你必须直接输出一个 JSON 对象，格式如下（不要有任何其他文字）:
    {{
        "results": [
            {{
                "frame": "frame_0001.jpg",
                "frame_index": 1,
                "timestamp": "00:00:15",
                "timestamp_seconds": 15,
                "success": true,
                "text": "识别到的文字内容"
            }},
            ...
        ]
    }}

    注意：
    - results 数组的顺序必须与输入的帧文件列表顺序一致
    - success 字段表示该帧是否成功识别（即使没有文字也应该是 true）
    - text 字段是识别到的文字（没有文字则为空字符串 ""）
    - 不要在 text 字段中添加任何解释或前缀
    - 直接输出 JSON，不要用 markdown 代码块包裹

    请开始处理。
    """).strip()

    # 选择要尝试的模型列表
    if model_name:
        models_to_try = [model_name]
    else:
        models_to_try = VLM_MODEL_LIST

    last_error = None

    for model in models_to_try:
        print(f"  [VLM SubAgent OCR] 尝试模型: {model}")

        try:
            # 构建 API 请求
            # 注意：这里需要根据实际的 VLM API 来调整
            # 由于模型是 ark/ 或 tx/ 前缀，可能需要不同的 API 端点
            # 这里假设使用 OpenAI 兼容格式

            results = []
            for i, frame_file in enumerate(frame_files):
                frame_path = os.path.join(frame_dir, frame_file)

                # 编码图片
                base64_image = encode_image_to_base64(frame_path)

                messages = [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                },
                            },
                            {
                                "type": "text",
                                "text": "请识别这张图片中的所有文字内容。只返回识别到的文字，不要其他解释。",
                            },
                        ],
                    }
                ]

                payload = {
                    "model": model,
                    "messages": messages,
                    "max_tokens": 1024,
                    "temperature": 0.1,
                }

                # 这里需要根据实际部署的 VLM 服务来调用
                # 由于是 subagent 模式，我们通过环境变量或配置获取 API endpoint
                # 默认使用 OpenAI 兼容格式
                api_base = os.environ.get(
                    "VLM_API_BASE", "https://ark.cn-beijing.volces.com/api/v3"
                )
                api_key = os.environ.get(
                    "ARK_API_KEY", os.environ.get("OPENAI_API_KEY", "")
                )

                if not api_key:
                    return {
                        "success": False,
                        "error": "No API key found in environment",
                        "results": [],
                    }

                response = requests.post(
                    f"{api_base}/chat/completions",
                    json=payload,
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    },
                    timeout=120,
                )

                if response.status_code == 200:
                    vlm_result = response.json()
                    if vlm_result.get("choices") and len(vlm_result["choices"]) > 0:
                        text = (
                            vlm_result["choices"][0]
                            .get("message", {})
                            .get("content", "")
                        )
                        ocr_result = {"text": text, "raw_result": vlm_result}
                    else:
                        ocr_result = {"error": "No choices in response"}
                else:
                    ocr_result = {
                        "error": f"HTTP {response.status_code}: {response.text[:200]}"
                    }

                result = {
                    "frame": frame_file,
                    "frame_index": i + 1,
                    "success": "error" not in ocr_result,
                    "error": ocr_result.get("error"),
                    "text": ocr_result.get("text", ""),
                    "result": ocr_result,
                }

                if frame_file in frame_info_dict:
                    fi = frame_info_dict[frame_file]
                    result["timestamp_seconds"] = fi.get("timestamp_seconds")
                    result["timestamp"] = fi.get("timestamp")

                results.append(result)

            processing_time = (datetime.now() - start_time).total_seconds()
            success_count = sum(1 for r in results if r["success"])

            # 保存结果
            output_file = os.path.join(frame_dir, "ocr_results.json")
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "success": True,
                        "service_url": "subagent",
                        "service_type": "vlm_subagent",
                        "model_name": model,
                        "frames_extracted": len(frame_files),
                        "frames_processed": len(results),
                        "frames_successful": success_count,
                        "processing_time_seconds": processing_time,
                        "results": results,
                    },
                    f,
                    ensure_ascii=False,
                    indent=2,
                )

            # 提取文字
            all_text = []
            for result in results:
                if result.get("success") and result.get("text"):
                    text = result["text"].strip()
                    if text:
                        timestamp = result.get(
                            "timestamp", f"Frame {result.get('frame_index', '?')}"
                        )
                        all_text.append(f"[{timestamp}]\n{text}\n")

            if all_text:
                text_file = os.path.join(frame_dir, "ocr_text.txt")
                with open(text_file, "w", encoding="utf-8") as f:
                    f.write("\n".join(all_text))

            # 清理回退标记文件
            fallback_marker = os.path.join(frame_dir, "need_vlm_fallback.json")
            if os.path.exists(fallback_marker):
                os.remove(fallback_marker)

            print(
                f"  [VLM SubAgent OCR] 成功! 模型: {model}, 成功: {success_count}/{len(results)}"
            )

            return {
                "success": True,
                "error": None,
                "service_type": "vlm_subagent",
                "model_name": model,
                "frames_extracted": len(frame_files),
                "frames_processed": len(results),
                "frames_successful": success_count,
                "processing_time_seconds": processing_time,
                "results": results,
                "results_file": output_file,
            }

        except Exception as e:
            last_error = str(e)
            print(f"  [VLM SubAgent OCR] 模型 {model} 失败: {last_error}")
            continue

    return {
        "success": False,
        "error": f"所有 VLM 模型均失败: {last_error}",
        "results": [],
    }


def call_asr_with_fallback(
    audio_file, asr_url, result_dict, lock, workdir="/tmp/video-understanding"
):
    """
    调用 ASR 服务（线程函数），带智能回退:
    1. 优先尝试 LAN ASR 服务
    2. 首次失败后重试一次（等待 2 秒）
    3. 若仍然失败，回退到 Bailian API (Qwen3-ASR-Flash)
    """
    os.makedirs(workdir, exist_ok=True)
    print("  [ASR 线程] 正在调用 ASR 服务...")

    start_time = datetime.now()
    lan_model_name = None

    # 第一步：尝试 LAN ASR
    print("  [ASR 线程] 第一步：尝试 LAN ASR 服务...")

    # 先获取 LAN 模型
    try:
        response = requests.get(f"{asr_url}/v1/models", timeout=30)
        if response.status_code == 200:
            data = response.json()
            if data.get("data"):
                lan_model_name = data["data"][0]["id"]
                print(f"  [ASR 线程] LAN ASR 模型: {lan_model_name}")
    except Exception as e:
        print(f"  [ASR 线程] 警告: 获取 LAN 模型列表失败: {e}")
        lan_model_name = "whisper-1"

    if not lan_model_name:
        lan_model_name = "whisper-1"

    lan_success = False
    lan_result = None
    lan_error = None

    try:
        with open(audio_file, "rb") as f:
            files = {"file": f}
            data = {"model": lan_model_name, "response_format": "json"}

            response = requests.post(
                f"{asr_url}/v1/audio/transcriptions",
                files=files,
                data=data,
                timeout=900,
            )

        if response.status_code == 200:
            lan_result = response.json()
            lan_success = True
            print("  [ASR 线程] ✓ LAN ASR 成功!")
        else:
            lan_error = f"HTTP {response.status_code}: {response.text[:200]}"
            print(f"  [ASR 线程] ✗ LAN ASR 失败: {lan_error}")
    except requests.exceptions.Timeout:
        lan_error = "请求超时"
        print(f"  [ASR 线程] ✗ LAN ASR 失败: {lan_error}")
    except requests.exceptions.ConnectionError as e:
        lan_error = f"连接失败: {str(e)}"
        print(f"  [ASR 线程] ✗ LAN ASR 失败: {lan_error}")
    except Exception as e:
        lan_error = str(e)
        print(f"  [ASR 线程] ✗ LAN ASR 失败: {lan_error}")

    # 第二步：如果失败，重试一次 LAN ASR
    if not lan_success:
        print("  [ASR 线程] 第二步：重试 LAN ASR（等待 2 秒）...")
        time.sleep(2)

        try:
            with open(audio_file, "rb") as f:
                files = {"file": f}
                data = {"model": lan_model_name, "response_format": "json"}

                response = requests.post(
                    f"{asr_url}/v1/audio/transcriptions",
                    files=files,
                    data=data,
                    timeout=900,
                )

            if response.status_code == 200:
                lan_result = response.json()
                lan_success = True
                print("  [ASR 线程] ✓ LAN ASR 重试成功!")
            else:
                lan_error = f"HTTP {response.status_code}: {response.text[:200]}"
                print(f"  [ASR 线程] ✗ LAN ASR 重试失败: {lan_error}")
        except requests.exceptions.Timeout:
            lan_error = "请求超时"
            print(f"  [ASR 线程] ✗ LAN ASR 重试失败: {lan_error}")
        except requests.exceptions.ConnectionError as e:
            lan_error = f"连接失败: {str(e)}"
            print(f"  [ASR 线程] ✗ LAN ASR 重试失败: {lan_error}")
        except Exception as e:
            lan_error = str(e)
            print(f"  [ASR 线程] ✗ LAN ASR 重试失败: {lan_error}")

    # 第三步：如果 LAN ASR 仍然失败，回退到 Bailian API
    bailian_success = False
    bailian_result = None
    bailian_error = None
    service_used = "lan"

    if not lan_success:
        print("  [ASR 线程] 第三步：回退到 Bailian ASR API...")

        api_key = get_bailian_api_key()
        if not api_key:
            bailian_error = "未找到 BAILIAN_API_KEY 或 DASHSCOPE_API_KEY 环境变量"
            print(f"  [ASR 线程] ✗ Bailian ASR 无法调用: {bailian_error}")
        else:
            # 检查音频时长，决定是否需要分割
            audio_duration = get_audio_duration(audio_file)

            if audio_duration and audio_duration > MAX_CHUNK_DURATION:
                print(
                    f"  [ASR 线程] 音频时长 {audio_duration:.1f} 秒 > {MAX_CHUNK_DURATION} 秒，需要分割..."
                )
                chunk_dir = os.path.join(workdir, "bailian_chunks")
                chunk_files = split_audio(audio_file, chunk_dir, MAX_CHUNK_DURATION)
            else:
                chunk_files = [audio_file]

            if not chunk_files:
                bailian_error = "音频分割失败"
                print(f"  [ASR 线程] ✗ Bailian ASR 无法调用: {bailian_error}")
            else:
                # 转录每个 chunk
                results = []
                all_success = True

                for i, chunk_file in enumerate(chunk_files):
                    if len(chunk_files) > 1:
                        print(f"  [ASR 线程] 转录 Chunk {i + 1}/{len(chunk_files)}...")

                    try:
                        data_uri = encode_audio_base64(chunk_file)

                        headers = {
                            "Authorization": f"Bearer {api_key}",
                            "Content-Type": "application/json",
                        }

                        payload = {
                            "model": BAILIAN_ASR_MODEL,
                            "messages": [
                                {
                                    "role": "user",
                                    "content": [
                                        {
                                            "type": "input_audio",
                                            "input_audio": {"data": data_uri},
                                        }
                                    ],
                                }
                            ],
                        }

                        response = requests.post(
                            f"{BAILIAN_API_BASE}/chat/completions",
                            headers=headers,
                            json=payload,
                            timeout=900,
                        )

                        if response.status_code == 200:
                            result = response.json()
                            if result.get("choices") and len(result["choices"]) > 0:
                                text = (
                                    result["choices"][0]
                                    .get("message", {})
                                    .get("content", "")
                                )
                                results.append(text)
                                print(f"    -> {len(text)} 字符")
                            else:
                                results.append(f"[响应格式错误]")
                                all_success = False
                        else:
                            results.append(f"[HTTP {response.status_code}]")
                            all_success = False

                    except requests.exceptions.Timeout:
                        results.append("[请求超时]")
                        all_success = False
                    except requests.exceptions.ConnectionError as e:
                        results.append(f"[连接失败: {str(e)}]")
                        all_success = False
                    except Exception as e:
                        results.append(f"[错误: {str(e)}]")
                        all_success = False

                if results:
                    combined_text = "\n\n".join(results)
                    bailian_result = {
                        "text": combined_text,
                        "raw_response": {"chunks_results": results},
                    }
                    bailian_success = True
                    service_used = "bailian"
                    print(f"  [ASR 线程] ✓ Bailian ASR 成功! ({len(results)} chunks)")

    processing_time = (datetime.now() - start_time).total_seconds()

    # 确定最终结果
    if lan_success:
        result = lan_result
        model_used = lan_model_name
        error_msg = None
    elif bailian_success:
        result = bailian_result
        model_used = BAILIAN_ASR_MODEL
        error_msg = None
    else:
        result = None
        model_used = lan_model_name if lan_model_name else BAILIAN_ASR_MODEL
        error_msg = f"LAN ASR 失败: {lan_error}; Bailian ASR 失败: {bailian_error}"

    # 保存结果
    if result:
        # 确保有 text 字段
        if "text" not in result:
            result["text"] = ""

        with lock:
            result_dict["asr"] = {
                "success": True,
                "error": None,
                "service_type": service_used,
                "service_url": asr_url if service_used == "lan" else BAILIAN_API_BASE,
                "model": model_used,
                "audio_file": audio_file,
                "processing_time_seconds": processing_time,
                "text": result.get("text", ""),
                "word_count": len(result.get("text", "").split()),
                "raw_result": result,
            }

            # 保存文件
            with open(
                os.path.join(workdir, "asr_result.json"), "w", encoding="utf-8"
            ) as f:
                json.dump(result, f, ensure_ascii=False, indent=2)

            if "text" in result:
                with open(
                    os.path.join(workdir, "transcript.txt"), "w", encoding="utf-8"
                ) as f:
                    f.write(result["text"])

            print(
                f"  [ASR 线程] 完成! 服务: {service_used}, 处理时间: {processing_time:.1f} 秒"
            )
    else:
        with lock:
            result_dict["asr"] = {
                "success": False,
                "error": error_msg,
                "service_type": service_used,
                "service_url": asr_url,
                "model": model_used,
            }
            print(f"  [ASR 线程] 失败: {error_msg}")


# 保留旧函数名作为别名（向后兼容）
def call_asr(
    audio_file, asr_url, result_dict, lock, workdir="/tmp/video-understanding"
):
    """调用 ASR（线程函数，带 Bailian 回退）"""
    call_asr_with_fallback(audio_file, asr_url, result_dict, lock, workdir)


def generate_output(
    result_dict, video_url, workdir="/tmp/video-understanding", duration=None
):
    """生成最终输出"""
    os.makedirs(workdir, exist_ok=True)
    print("\n" + "=" * 60)
    print("步骤 5/5: 生成最终输出")
    print("=" * 60)

    asr_data = result_dict.get("asr", {})
    ocr_data = result_dict.get("ocr", {})

    if not ocr_data:
        mode = "asr_only"
    elif ocr_data.get("success"):
        mode = "asr_ocr_parallel"
    elif ocr_data.get("need_vlm_fallback"):
        mode = "asr_with_ocr_fallback_needed"
    else:
        mode = "asr_with_ocr_failed"

    output = {
        "metadata": {
            "video_url": video_url,
            "video_title": "",
            "duration_seconds": duration,
            "duration_minutes": duration / 60 if duration else None,
            "processed_at": datetime.utcnow().isoformat() + "Z",
            "processor": "video-understanding-skill",
            "version": "2.4",
            "mode": mode,
        },
        "asr": asr_data,
        "ocr": ocr_data
        if ocr_data
        else {
            "success": False,
            "error": "OCR was not requested",
            "frames_processed": 0,
            "results": [],
        },
        "summary": {"key_topics": [], "main_points": [], "timestamps": []},
        "files": {
            "asr_result": os.path.join(workdir, "asr_result.json")
            if asr_data.get("success")
            else None,
            "transcript": os.path.join(workdir, "transcript.txt")
            if asr_data.get("success")
            else None,
            "ocr_results": ocr_data.get("results_file")
            if ocr_data.get("success")
            else None,
            "video_analysis": os.path.join(workdir, "video_analysis.json"),
        },
    }

    with open(os.path.join(workdir, "video_analysis.json"), "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print("  输出已生成:", os.path.join(workdir, "video_analysis.json"))
    return output


def main():
    parser = argparse.ArgumentParser(description="视频理解完整流程脚本")
    parser.add_argument(
        "--workdir",
        type=str,
        default="/tmp/video-understanding/",
        help="工作目录（默认: /tmp/video-understanding/）",
    )
    parser.add_argument(
        "--vlm-subagent-ocr", action="store_true", help="VLM SubAgent OCR 模式"
    )
    parser.add_argument(
        "--frame-dir",
        type=str,
        default=None,
        help="帧目录路径（用于 --vlm-subagent-ocr 模式）",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="模型名称（用于 --vlm-subagent-ocr 模式）",
    )
    parser.add_argument("--ocr-url", type=str, default=None, help="OCR 服务 URL")
    parser.add_argument(
        "--ocr-interval", type=float, default=15, help="OCR 截图间隔（秒）"
    )
    parser.add_argument("video_url", nargs="?", help="视频 URL")
    parser.add_argument("asr_url", nargs="?", help="ASR 服务 URL")

    args = parser.parse_args()
    workdir = args.workdir
    os.makedirs(workdir, exist_ok=True)

    # 检查是否是 VLM SubAgent OCR 模式
    if args.vlm_subagent_ocr:
        # SubAgent OCR 模式
        frame_dir = args.frame_dir

        if not frame_dir:
            print("错误: --vlm-subagent-ocr 模式需要 --frame-dir 参数")
            sys.exit(1)

        print(f"\n{'=' * 60}")
        print("VLM SubAgent OCR 模式")
        print(f"{'=' * 60}")
        print(f"帧目录: {frame_dir}")
        print(f"指定模型: {args.model or '按列表顺序尝试'}")

        result = do_vlm_subagent_ocr(frame_dir, args.model)

        if result.get("success"):
            print(f"\nVLM SubAgent OCR 完成!")
            print(f"  模型: {result.get('model_name')}")
            print(
                f"  成功: {result.get('frames_successful')}/{result.get('frames_processed')}"
            )
            print(f"  处理时间: {result.get('processing_time_seconds', 0):.1f} 秒")
            print(f"  结果文件: {result.get('results_file')}")
        else:
            print(f"\nVLM SubAgent OCR 失败: {result.get('error')}")
            sys.exit(1)

        sys.exit(0)

    # 正常视频处理流程
    if not args.video_url or not args.asr_url:
        print(
            "使用方法: python full_pipeline.py <video-url> <asr-url> [--ocr-url <vlm-url>] [--ocr-interval <seconds>] [--workdir <path>]"
        )
        print("\n示例:")
        print("  # 仅 ASR（默认）")
        print(
            "  python full_pipeline.py https://www.bilibili.com/video/BV1W2wtzkEBR http://192.168.71.57:8002"
        )
        print("\n  # ASR + OCR（并行执行，使用 LAN VLM）")
        print(
            "  python full_pipeline.py https://www.bilibili.com/video/BV1W2wtzkEBR http://192.168.71.57:8002 --ocr-url http://192.168.71.57:8001"
        )
        print("\n  # ASR + OCR，自定义截图间隔")
        print(
            "  python full_pipeline.py https://www.bilibili.com/video/BV1W2wtzkEBR http://192.168.71.57:8002 --ocr-url http://192.168.71.57:8001 --ocr-interval 10"
        )
        sys.exit(1)

    print("\n" + "=" * 60)
    print("视频理解完整流程 v2.3（ASR Bailian 回退 + VLM OCR 智能回退）")
    print("=" * 60)
    print(f"视频 URL: {args.video_url}")
    print(f"ASR 服务: {args.asr_url}")
    if args.ocr_url:
        print(f"OCR LAN VLM 服务: {args.ocr_url}")
        print(f"OCR 截图间隔: {args.ocr_interval} 秒")
        print("模式: ASR + OCR（并行执行，带回退）")
    else:
        print("模式: 仅 ASR")
    print(f"工作目录: {workdir}")

    # 步骤 1: 下载视频
    video_file = download_video(args.video_url, workdir)
    if not video_file:
        print("\n错误: 视频下载失败")
        sys.exit(1)

    # 获取视频时长
    duration = get_video_duration(video_file)
    if duration:
        print(f"\n视频时长: {duration:.1f} 秒 ({duration / 60:.1f} 分钟)")

    # 步骤 2: 准备音频（即使 OCR 也需要）
    print("\n" + "=" * 60)
    print("步骤 2/5: 准备音频")
    print("=" * 60)
    audio_file, audio_duration = prepare_audio(video_file, workdir)
    if not audio_file:
        print("\n错误: 音频准备失败")
        sys.exit(1)

    # 步骤 3-4: 并行执行 ASR 和 OCR（如果需要）
    print("\n" + "=" * 60)
    if args.ocr_url:
        print("步骤 3-4/5: 并行执行 ASR 和 OCR")
    else:
        print("步骤 3/5: ASR 语音识别")
    print("=" * 60)

    # 共享结果字典和锁
    result_dict = {}
    lock = threading.Lock()

    threads = []

    # ASR 线程（始终启动）
    asr_thread = threading.Thread(
        target=call_asr, args=(audio_file, args.asr_url, result_dict, lock, workdir)
    )
    threads.append(asr_thread)

    # OCR 线程（仅在需要时启动）
    ocr_thread = None
    frame_dir = None
    frame_info = None

    if args.ocr_url:
        # 先提取帧
        print("\n" + "=" * 60)
        print("步骤 2.5/5: 提取视频帧（用于 OCR）")
        print("=" * 60)
        frame_dir, frame_info = extract_frames(video_file, args.ocr_interval, workdir)

        if frame_dir and frame_info:
            ocr_thread = threading.Thread(
                target=call_vlm_ocr_with_fallback,
                args=(frame_dir, args.ocr_url, frame_info, result_dict, lock),
            )
            threads.append(ocr_thread)

    # 启动所有线程
    print("\n启动并行处理...")
    for thread in threads:
        thread.start()

    # 等待所有线程完成
    print("等待处理完成...")
    for thread in threads:
        thread.join()

    print("\n所有处理完成!")

    # 检查是否需要 VLM 回退
    need_vlm_fallback = False
    if args.ocr_url and result_dict.get("ocr", {}).get("need_vlm_fallback"):
        need_vlm_fallback = True
        print("\n" + "=" * 60)
        print("检测到 LAN OCR 失败，需要 VLM SubAgent 回退")
        print("=" * 60)

    # 步骤 5: 生成输出
    generate_output(
        result_dict, args.video_url, workdir, duration if duration else audio_duration
    )

    # 完成
    print("\n" + "=" * 60)
    print("完成!")
    print("=" * 60)
    print("\n生成的文件:")
    print(f"  - {os.path.join(workdir, 'asr_result.json')} (ASR 原始结果)")
    print(f"  - {os.path.join(workdir, 'transcript.txt')} (纯文本转录)")
    print(f"  - {os.path.join(workdir, 'video_analysis.json')} (完整分析结果)")
    if args.ocr_url:
        print(f"  - {os.path.join(frame_dir, 'ocr_results.json')} (OCR 结果)")
        print(f"  - {os.path.join(frame_dir, 'ocr_text.txt')} (OCR 文字)")
        if need_vlm_fallback:
            print(
                f"  - {os.path.join(frame_dir, 'need_vlm_fallback.json')} (VLM 回退标记)"
            )
            print("\n注意: 检测到需要 VLM SubAgent 回退，请使用以下命令执行 OCR:")
            print(
                f"  python full_pipeline.py --vlm-subagent-ocr --frame-dir {frame_dir} --model ark/doubao-seed-2.0-lite"
            )

    # 如果需要回退，以特定退出码退出
    if need_vlm_fallback:
        sys.exit(2)  # 2 表示需要 OCR 回退


if __name__ == "__main__":
    main()
