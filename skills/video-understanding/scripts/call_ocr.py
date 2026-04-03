#!/usr/bin/env python3
"""
调用 VLM（视觉语言模型）进行 OCR 的辅助脚本（v2，支持智能回退）
使用方法: python call_ocr.py <frame-directory> <vlm-url> [--model <model-name>] [--retry] [--workdir <path>]
示例: python call_ocr.py frames http://192.168.71.57:8001
      python call_ocr.py frames http://192.168.71.57:8001 --model qwen-vl
      python call_ocr.py frames http://192.168.71.57:8001 --retry

OCR 回退机制:
  1. 优先使用指定的 LAN OCR 服务
  2. 首次失败后重试一次
  3. 若仍然失败，脚本会写入 need_vlm_fallback.json 并返回退出码 2
  4. 上层调用者应检测此信号并触发 VLM SubAgent 进行 OCR
"""

import sys
import os
import json
import requests
import base64
import time
from datetime import datetime
from pathlib import Path
import argparse


def encode_image_to_base64(image_path):
    """将图片编码为 base64"""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def call_vlm_ocr_single(image_file, vlm_url, model_name=None):
    """对单张图片调用 VLM 进行 OCR"""
    try:
        # 编码图片
        base64_image = encode_image_to_base64(image_file)

        # 先获取可用模型（如果没有指定）
        if not model_name:
            try:
                response = requests.get(f"{vlm_url}/v1/models", timeout=30)
                if response.status_code == 200:
                    data = response.json()
                    if data.get("data"):
                        model_name = data["data"][0]["id"]
            except:
                model_name = "default"

        if not model_name:
            model_name = "default"

        # 构建 VLM 请求
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
                    },
                    {
                        "type": "text",
                        "text": 'You are performing OCR on a textbook page. Follow these rules: 1. **Ignore headers**: Skip the page number, chapter number (e.g., "CHAPTER 1"), and chapter title at the top of the page (the content above the first horizontal divider line). 2. **Main text**: Extract in reading order, top-to-bottom, single-column layout. 3. **TABLES**: If a table exists, use markdown table format with | separators. 4. **Headers**: Use ## for section headers, **text** for bold, *text* for italic. 5. **Footnotes**: If superscript footnote markers exist, use [^N] in body and [^N]: content at END. 6. **Ignore**: Decorative elements, horizontal bars, ornaments, graphs, diagrams, and figures. Do not describe them—skip them entirely. 7. **CRITICAL**: Output ONLY extracted text. Do NOT repeat or hallucinate content. Do not include any description of images or graphics. 8. If text is unclear, indicate with [unclear] rather than guess.',
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
            result = response.json()
            # 提取文字内容
            if result.get("choices") and len(result["choices"]) > 0:
                text = result["choices"][0].get("message", {}).get("content", "")
                return {"text": text, "raw_result": result}
            else:
                return {"error": "No choices in response", "raw_result": result}
        else:
            return {"error": f"HTTP {response.status_code}", "response": response.text}
    except Exception as e:
        return {"error": str(e)}


def call_ocr_directory(
    frame_dir,
    vlm_url,
    frame_info_file=None,
    max_frames=None,
    model_name=None,
    retry=False,
):
    """
    对目录中的所有帧调用 VLM 进行 OCR（支持重试和回退）

    Args:
        frame_dir: 帧目录
        vlm_url: VLM 服务 URL
        frame_info_file: 帧信息文件（frame_info.json）
        max_frames: 最大处理帧数（可选，用于测试）
        model_name: 模型名称（可选）
        retry: 是否在失败后重试一次

    Returns:
        (success: bool, output_file: str or None, results: list or None)
    """

    print(f"正在处理目录: {frame_dir}")

    # 获取所有帧文件
    frame_files = sorted(
        [
            f
            for f in os.listdir(frame_dir)
            if (f.endswith(".jpg") or f.endswith(".png")) and not f.startswith(".")
        ]
    )

    if not frame_files:
        print("错误: 未找到 JPG 文件")
        return False, None, None

    print(f"找到 {len(frame_files)} 帧")

    # 限制处理帧数
    if max_frames:
        frame_files = frame_files[:max_frames]
        print(f"限制处理前 {max_frames} 帧")

    # 加载帧信息（如果有）
    frame_info = {}
    if frame_info_file and os.path.exists(frame_info_file):
        try:
            with open(frame_info_file, "r", encoding="utf-8") as f:
                info_list = json.load(f)
                for info in info_list:
                    frame_info[info["file"]] = info
        except Exception as e:
            print(f"警告: 加载帧信息失败: {e}")

    # 处理每一帧
    results = []
    start_time = datetime.now()

    print("开始 VLM OCR 处理...")
    for i, frame_file in enumerate(frame_files):
        frame_path = os.path.join(frame_dir, frame_file)

        print(f"  处理 {i + 1}/{len(frame_files)}: {frame_file}")

        ocr_result = call_vlm_ocr_single(frame_path, vlm_url, model_name)

        # 构建结果
        result = {
            "frame": frame_file,
            "frame_index": i + 1,
            "success": "error" not in ocr_result,
            "error": ocr_result.get("error"),
            "text": ocr_result.get("text", ""),
            "result": ocr_result,
        }

        # 添加时间戳信息（如果有）
        if frame_file in frame_info:
            info = frame_info[frame_file]
            result["timestamp_seconds"] = info.get("timestamp_seconds")
            result["timestamp"] = info.get("timestamp")

        results.append(result)

    processing_time = (datetime.now() - start_time).total_seconds()

    # 统计
    success_count = sum(1 for r in results if r["success"])

    # 检查是否有失败
    if success_count == 0 and retry:
        # 所有帧都失败了，尝试重试
        print(f"\n所有帧 OCR 均失败，准备重试...")
        time.sleep(2)  # 等待 2 秒后重试

        # 重新处理
        results = []
        start_time = datetime.now()

        for i, frame_file in enumerate(frame_files):
            frame_path = os.path.join(frame_dir, frame_file)

            print(f"  重试处理 {i + 1}/{len(frame_files)}: {frame_file}")

            ocr_result = call_vlm_ocr_single(frame_path, vlm_url, model_name)

            result = {
                "frame": frame_file,
                "frame_index": i + 1,
                "success": "error" not in ocr_result,
                "error": ocr_result.get("error"),
                "text": ocr_result.get("text", ""),
                "result": ocr_result,
            }

            if frame_file in frame_info:
                info = frame_info[frame_file]
                result["timestamp_seconds"] = info.get("timestamp_seconds")
                result["timestamp"] = info.get("timestamp")

            results.append(result)

        processing_time = (datetime.now() - start_time).total_seconds()
        success_count = sum(1 for r in results if r["success"])

    print(f"\nVLM OCR 处理完成!")
    print(f"  总帧数: {len(results)}")
    print(f"  成功: {success_count}")
    print(f"  失败: {len(results) - success_count}")
    print(f"  处理时间: {processing_time:.1f} 秒")

    # 检查最终结果
    if success_count == 0:
        # 所有方式都失败了，写入回退标记
        print("\nOCR 全部失败，标记需要 VLM SubAgent 回退...")

        fallback_marker = os.path.join(frame_dir, "need_vlm_fallback.json")
        with open(fallback_marker, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "need_fallback": True,
                    "frame_dir": frame_dir,
                    "frame_count": len(frame_files),
                    "lan_error": results[0].get("error") if results else "Unknown",
                    "timestamp": datetime.now().isoformat(),
                },
                f,
                ensure_ascii=False,
                indent=2,
            )

        return False, None, results

    # 保存结果
    output_file = os.path.join(frame_dir, "ocr_results.json")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(
            {
                "success": True,
                "service_url": vlm_url,
                "service_type": "vlm",
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

    print(f"结果已保存到: {output_file}")

    # 提取所有文字并保存
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
        print(f"OCR 文字已保存到: {text_file}")

        # 显示预览
        print(f"\nOCR 文字预览:\n{''.join(all_text[:3])}...")

    return True, output_file, results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="调用 VLM 进行 OCR 的辅助脚本")
    parser.add_argument(
        "--workdir",
        type=str,
        default="/tmp/video-understanding/",
        help="工作目录（默认: /tmp/video-understanding/）",
    )
    parser.add_argument("--model", type=str, default=None, help="模型名称（可选）")
    parser.add_argument(
        "--max-frames", type=int, default=None, help="最大处理帧数（可选，用于测试）"
    )
    parser.add_argument("--retry", action="store_true", help="是否在失败后重试一次")
    parser.add_argument("frame_dir", help="帧目录路径")
    parser.add_argument("vlm_url", help="VLM 服务 URL")

    args = parser.parse_args()

    workdir = args.workdir
    os.makedirs(workdir, exist_ok=True)

    # 检查 frame_dir 是否是绝对路径，如果不是，尝试相对于 workdir
    frame_dir = args.frame_dir
    if not os.path.isabs(frame_dir):
        candidate = os.path.join(workdir, frame_dir)
        if os.path.isdir(candidate):
            frame_dir = candidate

    if not os.path.isdir(frame_dir):
        print(f"错误: 目录不存在: {frame_dir}")
        sys.exit(1)

    # 查找帧信息文件
    frame_info_file = os.path.join(frame_dir, "frame_info.json")
    if not os.path.exists(frame_info_file):
        frame_info_file = None

    success, output_file, results = call_ocr_directory(
        frame_dir,
        args.vlm_url,
        frame_info_file,
        args.max_frames,
        args.model,
        args.retry,
    )

    if not success:
        if results is not None:
            # 有结果但全部失败，需要回退
            print("\nOCR 失败，需要 VLM SubAgent 回退")
            sys.exit(2)  # 2 表示需要回退
        else:
            # 完全没有结果（如未找到文件）
            sys.exit(1)
