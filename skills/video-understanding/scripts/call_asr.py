#!/usr/bin/env python3
"""
调用 ASR 服务的辅助脚本（支持 Bailian API 回退 + 长音频自动分割）
使用方法: python call_asr.py <audio-file> <asr-url> [model-name] [--workdir <path>]
示例: python call_asr.py audio.mp3 http://192.168.71.57:8002
      python call_asr.py audio.mp3 http://192.168.71.57:8002 qwen3asr

ASR 回退机制:
  1. 优先使用 LAN ASR 服务（--asr-url 指定）
  2. 首次失败后重试一次（等待 2 秒）
  3. 若仍然失败，自动回退到 Bailian API (BAILIAN_API_KEY)

长音频处理:
  - Bailian qwen3-asr-flash 模型限制：最长 5 分钟（300 秒）
  - 超过 290 秒的音频会自动分割成多个 chunk 分别处理
  - 分割后分别转录，最后合并结果
"""

import sys
import requests
import json
import os
import time
import base64
import subprocess
import argparse


# Bailian API 配置
BAILIAN_API_BASE = "https://dashscope.aliyuncs.com/compatible-mode/v1"
BAILIAN_ASR_MODEL = "qwen3-asr-flash"

# Bailian qwen3-asr-flash 限制：最长 5 分钟（300 秒），安全值 290 秒
MAX_CHUNK_DURATION = 290


def get_bailian_api_key():
    """获取 Bailian API Key"""
    return os.environ.get("BAILIAN_API_KEY") or os.environ.get("DASHSCOPE_API_KEY")


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
        print(f"获取音频时长失败: {e}")
        return None


def split_audio(input_file, output_dir, chunk_duration=MAX_CHUNK_DURATION):
    """
    分割音频为多个 chunk

    Args:
        input_file: 输入音频文件
        output_dir: 输出目录
        chunk_duration: 每个 chunk 的最大时长（秒）

    Returns:
        list: chunk 文件路径列表
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

    print(f"音频总时长: {total_duration:.1f} 秒，需要分割为 {num_chunks} 个 chunk")

    chunk_files = []
    for i in range(num_chunks):
        start_time = i * chunk_duration
        output_file = os.path.join(output_dir, f"chunk_{i:03d}.mp3")

        if os.path.exists(output_file):
            print(f"  Chunk {i + 1}/{num_chunks} 已存在，跳过")
            chunk_files.append(output_file)
            continue

        print(f"  分割 Chunk {i + 1}/{num_chunks}...")
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
        else:
            print(
                f"    分割失败: {result.stderr[:200] if result.stderr else 'unknown error'}"
            )

    return chunk_files


def list_models(asr_url):
    """列出可用模型"""
    try:
        response = requests.get(f"{asr_url}/v1/models", timeout=30)
        response.raise_for_status()
        data = response.json()
        print("可用模型:")
        for model in data.get("data", []):
            print(f"  - {model['id']}")
        return data
    except Exception as e:
        print(f"获取模型列表失败: {e}")
        return None


def call_lan_asr(audio_file, asr_url, model_name=None, response_format="json"):
    """调用 LAN ASR 服务，返回 (success, result_or_error)"""

    # 如果没有指定模型，先获取可用模型
    if not model_name:
        try:
            response = requests.get(f"{asr_url}/v1/models", timeout=30)
            if response.status_code == 200:
                data = response.json()
                if data.get("data"):
                    model_name = data["data"][0]["id"]
                    print(f"✓ 自动检测到 LAN ASR 模型: {model_name}")
            else:
                print(
                    f"⚠️ 获取模型列表失败 (HTTP {response.status_code})，将使用默认模型"
                )
                model_name = "whisper-1"
        except requests.exceptions.ConnectionError as e:
            print(f"⚠️ 无法连接到 LAN ASR 服务 ({asr_url})")
            print(f"   错误: {e}")
            model_name = "whisper-1"
        except Exception as e:
            print(f"⚠️ 获取 LAN 模型列表失败: {e}")
            print(f"   提示: 如果 LAN ASR 可用但模型名不正确，请手动指定模型名")
            model_name = "whisper-1"

    if not model_name:
        model_name = "whisper-1"

    print(f"正在调用 LAN ASR 服务: {asr_url}")
    print(f"音频文件: {audio_file}")
    print(f"模型: {model_name}")

    try:
        with open(audio_file, "rb") as f:
            files = {"file": f}
            data = {"model": model_name, "response_format": response_format}

            response = requests.post(
                f"{asr_url}/v1/audio/transcriptions",
                files=files,
                data=data,
                timeout=900,  # 15 分钟超时
            )

        if response.status_code == 200:
            result = response.json()
            return True, result
        else:
            return False, f"HTTP {response.status_code}: {response.text[:200]}"

    except requests.exceptions.Timeout:
        return False, "请求超时"
    except requests.exceptions.ConnectionError as e:
        return False, f"连接失败: {str(e)}"
    except Exception as e:
        return False, f"调用错误: {str(e)}"


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


def call_bailian_asr_single(audio_file):
    """
    调用 Bailian ASR API 转录单个音频文件

    使用 /chat/completions 端点 + input_audio content type
    参考: https://help.aliyuncs.com/zh/model-studio/qwen-asr-api-reference
    """
    api_key = get_bailian_api_key()
    if not api_key:
        return False, "未找到 BAILIAN_API_KEY 或 DASHSCOPE_API_KEY 环境变量"

    file_size_mb = os.path.getsize(audio_file) / (1024 * 1024)

    try:
        # 构建 Base64 Data URL
        data_uri = encode_audio_base64(audio_file)

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
                        {"type": "input_audio", "input_audio": {"data": data_uri}}
                    ],
                }
            ],
        }

        response = requests.post(
            f"{BAILIAN_API_BASE}/chat/completions",
            headers=headers,
            json=payload,
            timeout=900,  # 15 分钟超时
        )

        if response.status_code == 200:
            result = response.json()
            if result.get("choices") and len(result["choices"]) > 0:
                text = result["choices"][0].get("message", {}).get("content", "")
                return True, {"text": text, "raw_response": result}
            else:
                return False, f"响应格式错误: {result}"
        else:
            error_msg = (
                response.json()
                if response.headers.get("content-type", "").startswith(
                    "application/json"
                )
                else response.text
            )
            return False, f"HTTP {response.status_code}: {str(error_msg)[:500]}"

    except requests.exceptions.Timeout:
        return False, "请求超时"
    except requests.exceptions.ConnectionError as e:
        return False, f"连接失败: {str(e)}"
    except Exception as e:
        return False, f"调用错误: {str(e)}"


def call_bailian_asr(
    audio_file, workdir="/tmp/video-understanding", response_format="json"
):
    """
    调用 Bailian ASR API，自动处理长音频分割

    - 如果音频超过 290 秒，自动分割为多个 chunk
    - 分别转录每个 chunk，最后合并结果
    """
    os.makedirs(workdir, exist_ok=True)
    print(f"\n正在调用 Bailian ASR API...")
    print(f"模型: {BAILIAN_ASR_MODEL}")
    print(f"API 端点: {BAILIAN_API_BASE}/chat/completions")

    # 检查音频时长
    duration = get_audio_duration(audio_file)
    if not duration:
        return False, "无法获取音频时长"

    print(f"音频时长: {duration:.1f} 秒")

    # 如果音频太短，直接返回
    if duration <= MAX_CHUNK_DURATION:
        print(f"音频在 {MAX_CHUNK_DURATION} 秒限制内，直接转录")
        return call_bailian_asr_single(audio_file)

    # 需要分割
    print(f"\n音频超过 {MAX_CHUNK_DURATION} 秒限制，需要分割...")
    chunk_dir = os.path.join(workdir, "bailian_chunks")

    chunk_files = split_audio(audio_file, chunk_dir, MAX_CHUNK_DURATION)
    if not chunk_files:
        return False, "音频分割失败"

    # 转录每个 chunk
    results = []
    for i, chunk_file in enumerate(chunk_files):
        print(
            f"\n转录 Chunk {i + 1}/{len(chunk_files)}: {os.path.basename(chunk_file)}"
        )

        # 如果是原始文件（未分割），直接转录
        if chunk_file == audio_file:
            success, result = call_bailian_asr_single(chunk_file)
        else:
            success, result = call_bailian_asr_single(chunk_file)

        if success:
            text = result.get("text", "")
            results.append(text)
            print(f"  -> {len(text)} 字符")
        else:
            print(f"  -> 转录失败: {result}")
            # 继续处理其他 chunk
            results.append(f"[转录失败: {result}]")

    # 合并结果
    combined_text = "\n\n".join(results)

    return True, {
        "text": combined_text,
        "chunks": len(chunk_files),
        "raw_response": {"chunks_results": results},
    }


def call_asr(
    audio_file,
    asr_url,
    model_name=None,
    workdir="/tmp/video-understanding",
    response_format="json",
):
    """
    调用 ASR 服务，带智能回退:
    1. 优先尝试 LAN ASR
    2. 首次失败后重试一次
    3. 若仍然失败，回退到 Bailian API（自动处理长音频分割）
    """
    os.makedirs(workdir, exist_ok=True)

    # 检查文件大小
    file_size_mb = os.path.getsize(audio_file) / (1024 * 1024)
    print(f"文件大小: {file_size_mb:.2f} MB")

    if file_size_mb > 50:
        print("⚠️ 警告: 文件超过 50MB，可能会失败")
        print("建议: 使用 prepare_audio.py 压缩音频")

    result = None
    service_used = None

    # 第一步：尝试 LAN ASR
    print("\n" + "=" * 60)
    print("第一步：尝试 LAN ASR 服务")
    print("=" * 60)

    lan_success, lan_result = call_lan_asr(
        audio_file, asr_url, model_name, response_format
    )

    if lan_success:
        result = lan_result
        service_used = "lan"
        print(f"\n✓ LAN ASR 成功!")
    else:
        print(f"\n✗ LAN ASR 失败: {lan_result}")

        # 第二步：重试一次 LAN ASR
        print("\n" + "=" * 60)
        print("第二步：重试 LAN ASR（等待 2 秒）")
        print("=" * 60)
        time.sleep(2)

        lan_success, lan_result = call_lan_asr(
            audio_file, asr_url, model_name, response_format
        )

        if lan_success:
            result = lan_result
            service_used = "lan"
            print(f"\n✓ LAN ASR 重试成功!")
        else:
            print(f"\n✗ LAN ASR 重试失败: {lan_result}")

            # 第三步：回退到 Bailian API
            print("\n" + "=" * 60)
            print("第三步：回退到 Bailian ASR API")
            print("=" * 60)

            bailian_success, bailian_result = call_bailian_asr(
                audio_file, workdir, response_format
            )

            if bailian_success:
                result = bailian_result
                service_used = "bailian"
                print(f"\n✓ Bailian ASR 成功!")
            else:
                print(f"\n✗ Bailian ASR 也失败了: {bailian_result}")
                return None

    if result is None:
        print("\n错误: 所有 ASR 方式均失败")
        return None

    # 统一输出格式（确保与原 LAN ASR 接口一致）
    # Bailian 返回格式: {"text": "..."}
    # 确保返回的对象有 text 字段
    if "text" not in result:
        result["text"] = ""

    # 保存结果
    output_file = os.path.join(workdir, "asr_result.json")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"\nASR 完成! 服务: {service_used}")
    print(f"结果已保存到: {output_file}")

    # 也保存纯文本版本
    if "text" in result:
        text_file = os.path.join(workdir, "transcript.txt")
        with open(text_file, "w", encoding="utf-8") as f:
            f.write(result["text"])
        print(f"纯文本转录已保存到: {text_file}")

        # 显示文本预览
        text = result["text"]
        preview = text[:500] + "..." if len(text) > 500 else text
        print("\n转录预览:")
        print(preview)

    # 添加元数据
    result["_service"] = service_used
    result["_model"] = model_name or "auto"

    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="调用 ASR 服务的辅助脚本")
    parser.add_argument(
        "--workdir",
        type=str,
        default="/tmp/video-understanding/",
        help="工作目录（默认: /tmp/video-understanding/）",
    )
    parser.add_argument("--list-models", action="store_true", help="只列出模型")
    parser.add_argument("audio_file", nargs="?", help="音频文件路径")
    parser.add_argument("asr_url", nargs="?", help="ASR 服务 URL")
    parser.add_argument("model_name", nargs="?", default=None, help="模型名称（可选）")

    args = parser.parse_args()

    workdir = args.workdir
    os.makedirs(workdir, exist_ok=True)

    if args.list_models:
        if not args.asr_url:
            print("使用方法: python call_asr.py --list-models <asr-url>")
            sys.exit(1)
        list_models(args.asr_url)
    else:
        if not args.audio_file or not args.asr_url:
            print(
                "使用方法: python call_asr.py <audio-file> <asr-url> [model-name] [--workdir <path>]"
            )
            print("示例: python call_asr.py audio.mp3 http://192.168.71.57:8002")
            print(
                "      python call_asr.py audio.mp3 http://192.168.71.57:8002 qwen3asr"
            )
            print("\nASR 回退机制:")
            print("  1. 优先尝试 LAN ASR 服务")
            print("  2. 首次失败后重试一次（等待 2 秒）")
            print("  3. 若仍然失败，自动回退到 Bailian API (Qwen3-ASR-Flash)")
            print("  4. Bailian API 会自动处理长音频分割（每 chunk 290 秒）")
            print("\n只列出模型: python call_asr.py --list-models <asr-url>")
            sys.exit(1)

        if not os.path.exists(args.audio_file):
            print(f"错误: 文件不存在: {args.audio_file}")
            sys.exit(1)

        call_asr(args.audio_file, args.asr_url, args.model_name, workdir)
