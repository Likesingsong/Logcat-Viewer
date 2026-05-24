"""日志解析模块 — 从 Android Studio JSON logcat 文件中提取结构化数据."""

from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


# ── 日志级别 → 颜色（与 logcat2excel.py 保持一致）──────────────────────────
LEVEL_COLORS: dict[str, str] = {
    "VERBOSE": "#D9D9D9",
    "DEBUG":   "#BDD7EE",
    "INFO":    "#C6EFCE",
    "WARN":    "#FFEB9C",
    "ERROR":   "#FFC7CE",
    "FATAL":   "#FF4444",
    "ASSERT":  "#FF4444",
    # 单字母缩写
    "V": "#D9D9D9",
    "D": "#BDD7EE",
    "I": "#C6EFCE",
    "W": "#FFEB9C",
    "E": "#FFC7CE",
    "F": "#FF4444",
    "S": "#FF4444",
}

# 日志条目的列定义
COLUMNS: list[str] = [
    "#", "Timestamp", "Level", "PID", "TID",
    "Application", "Process", "Tag", "Message",
]

# 列索引常量，避免魔术数字
COL_INDEX = 0
COL_TIMESTAMP = 1
COL_LEVEL = 2
COL_PID = 3
COL_TID = 4
COL_APPLICATION = 5
COL_PROCESS = 6
COL_TAG = 7
COL_MESSAGE = 8


class ParseError(Exception):
    """日志解析错误。"""


def _decode_unicode(s: str) -> str:
    """解码 \\uXXXX 转义序列（如 \\u003e → >），保留已有 Unicode 字符不变。"""
    def replace_unicode_escape(match):
        hex_val = match.group(1)
        try:
            return chr(int(hex_val, 16))
        except ValueError:
            return match.group(0)
    
    return re.sub(r'\\u([0-9a-fA-F]{4})', replace_unicode_escape, s)


def _ts_to_str(seconds: int, nanos: int) -> str:
    """将 epoch 秒 + 纳秒转为 YYYY-MM-DD HH:MM:SS.mmm 格式（本地时间）。"""
    dt = datetime.fromtimestamp(seconds, tz=timezone.utc).astimezone()
    ms = nanos // 1_000_000
    return dt.strftime("%Y-%m-%d %H:%M:%S") + f".{ms:03d}"


def read_logcat_json(path: str | Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """读取 JSON logcat 文件。

    Args:
        path: .logcat 文件路径。

    Returns:
        (metadata, entries) 元组。
        entries 中每项包含: index, timestamp, level, pid, tid,
                         application, process, tag, message。

    Raises:
        ParseError: 文件不存在、JSON 格式错误、或缺失必要字段。
        FileNotFoundError: 文件不存在。
    """
    path = Path(path)
    logger.info(f"开始解析文件: {path}")
    
    if not path.exists():
        raise FileNotFoundError(f"文件不存在: {path}")
    if not path.is_file():
        raise ParseError(f"路径不是文件: {path}")

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as exc:
        raise ParseError(f"JSON 解析失败 ({path.name}): {exc}") from exc
    except UnicodeDecodeError as exc:
        raise ParseError(f"文件编码不支持 ({path.name}): {exc}") from exc
    except OSError as exc:
        raise ParseError(f"无法读取文件 ({path.name}): {exc}") from exc

    if not isinstance(data, dict):
        raise ParseError(f"JSON 顶层应为对象，实际为 {type(data).__name__}")

    metadata: dict[str, Any] = data.get("metadata", {})
    raw_messages: list[dict] = data.get("logcatMessages", [])

    if not isinstance(raw_messages, list):
        raise ParseError(f"logcatMessages 应为数组，实际为 {type(raw_messages).__name__}")

    entries: list[dict[str, Any]] = []
    for i, item in enumerate(raw_messages, start=1):
        if not isinstance(item, dict):
            logger.warning(f"跳过非字典类型的日志条目 #{i}")
            continue

        header: dict = item.get("header", {}) or {}
        ts: dict = header.get("timestamp", {}) or {}

        entries.append({
            "index":       i,
            "timestamp":   _ts_to_str(
                ts.get("seconds", 0),
                ts.get("nanos", 0),
            ),
            "level":       header.get("logLevel", ""),
            "pid":         header.get("pid", ""),
            "tid":         header.get("tid", ""),
            "application": header.get("applicationId", ""),
            "process":     header.get("processName", ""),
            "tag":         header.get("tag", ""),
            "message":     _decode_unicode(item.get("message", "")),
        })

    logger.info(f"解析完成: 共 {len(entries)} 条日志")
    return metadata, entries


def level_color(level: str) -> str:
    """根据日志级别返回对应的十六进制颜色值，未识别则返回空字符串。"""
    return LEVEL_COLORS.get(str(level).upper().strip(), "")
