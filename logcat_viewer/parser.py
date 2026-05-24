"""日志解析模块 — 从 Android logcat 文件中提取结构化数据。

支持两种格式:
1. JSON 格式 (.logcat) — Android Studio 导出格式
2. 纯文本格式 (.txt, .log, .new-log 等) — adb logcat 命令输出
"""

from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


_LEVEL_COLORS_FULL: dict[str, str] = {
    "VERBOSE": "#D9D9D9",
    "DEBUG":   "#BDD7EE",
    "INFO":    "#C6EFCE",
    "WARN":    "#FFEB9C",
    "ERROR":   "#FFC7CE",
    "FATAL":   "#FF4444",
    "ASSERT":  "#FF4444",
}

LEVEL_ABBREV: dict[str, str] = {
    "VERBOSE": "V",
    "DEBUG":   "D",
    "INFO":    "I",
    "WARN":    "W",
    "ERROR":   "E",
    "FATAL":   "F",
    "ASSERT":  "S",
}

LEVEL_COLORS: dict[str, str] = {
    **_LEVEL_COLORS_FULL,
    **{v: _LEVEL_COLORS_FULL[k] for k, v in LEVEL_ABBREV.items()},
}

COLUMNS: list[str] = [
    "#", "Timestamp", "Level", "PID", "TID",
    "Application", "Process", "Tag", "Message",
]

COL_INDEX = 0
COL_TIMESTAMP = 1
COL_LEVEL = 2
COL_PID = 3
COL_TID = 4
COL_APPLICATION = 5
COL_PROCESS = 6
COL_TAG = 7
COL_MESSAGE = 8

_TEXT_LOG_PATTERN = re.compile(
    r'^(\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\.\d+)\s+'  
    r'(\d+)\s+'                                   
    r'(\d+)\s+'                                   
    r'([VDIWEFS])\s+'                             
    r'(\S+)\s*:\s*'                               
    r'(.*)$'                                      
)

_ENCODINGS = ["utf-8", "utf-8-sig", "gbk", "gb2312", "gb18030", "latin-1"]


class ParseError(Exception):
    """日志解析错误。"""


def _detect_encoding(path: Path) -> str:
    """检测文件编码。"""
    with open(path, "rb") as f:
        raw = f.read(4096)
    
    for encoding in _ENCODINGS:
        try:
            raw.decode(encoding)
            return encoding
        except (UnicodeDecodeError, LookupError):
            continue
    
    return "utf-8"


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


def _is_json_file(path: Path) -> bool:
    """检测文件是否为 JSON 格式。"""
    try:
        with open(path, "r", encoding="utf-8") as f:
            first_char = f.read(1)
            return first_char in ("{", "[")
    except Exception:
        return False


def read_logcat_text(path: str | Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """读取纯文本格式的 logcat 文件。

    格式: MM-DD HH:MM:SS.mmmmmm  PID  TID LEVEL TAG: MESSAGE
    示例: 05-11 14:16:31.172382  4601  5530 I OTA::   : message here

    Args:
        path: 日志文件路径。

    Returns:
        (metadata, entries) 元组。
    """
    path = Path(path)
    logger.info(f"开始解析纯文本日志: {path}")

    if not path.exists():
        raise FileNotFoundError(f"文件不存在: {path}")
    if not path.is_file():
        raise ParseError(f"路径不是文件: {path}")

    encoding = _detect_encoding(path)
    logger.info(f"检测到文件编码: {encoding}")

    entries: list[dict[str, Any]] = []
    file_mtime_year = datetime.fromtimestamp(path.stat().st_mtime).year
    current_year = datetime.now().year
    inferred_year = min(file_mtime_year, current_year)
    last_month = 0
    pending_message_lines: list[str] = []

    def _flush_pending_message() -> None:
        if entries and pending_message_lines:
            entries[-1]["message"] = entries[-1]["message"] + "\n" + "\n".join(pending_message_lines)
            pending_message_lines.clear()

    def _infer_year(month: int) -> int:
        nonlocal last_month, inferred_year
        if last_month > 0 and month > last_month + 1:
            if month == 1 and last_month == 12:
                inferred_year += 1
        last_month = month
        return inferred_year

    try:
        with open(path, "r", encoding=encoding, errors="replace") as f:
            for line_num, line in enumerate(f, start=1):
                line = line.rstrip("\n\r")
                if not line.strip():
                    continue

                match = _TEXT_LOG_PATTERN.match(line)
                if match:
                    _flush_pending_message()
                    ts_str, pid, tid, level, tag, message = match.groups()
                    try:
                        month = int(ts_str.split("-")[0])
                        year = _infer_year(month)
                    except (ValueError, IndexError):
                        year = inferred_year
                    full_ts = f"{year}-{ts_str}"
                    try:
                        dt = datetime.strptime(full_ts, "%Y-%m-%d %H:%M:%S.%f")
                        timestamp = dt.strftime("%Y-%m-%d %H:%M:%S.") + f"{dt.microsecond // 1000:03d}"
                    except ValueError:
                        timestamp = ts_str

                    entries.append({
                        "index":       len(entries) + 1,
                        "timestamp":   timestamp,
                        "level":       level,
                        "pid":         pid,
                        "tid":         tid,
                        "application": "",
                        "process":     "",
                        "tag":         tag.strip(),
                        "message":     message,
                    })
                else:
                    if entries:
                        pending_message_lines.append(line)
                    else:
                        logger.debug(f"跳过无法解析的行 #{line_num}: {line[:50]}...")

            _flush_pending_message()

    except OSError as exc:
        raise ParseError(f"无法读取文件 ({path.name}): {exc}") from exc

    metadata: dict[str, Any] = {
        "source": "text",
        "filename": path.name,
    }

    logger.info(f"解析完成: 共 {len(entries)} 条日志")
    return metadata, entries


def read_logcat(path: str | Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """自动检测格式并读取 logcat 文件。

    支持:
    - JSON 格式 (.logcat) — Android Studio 导出
    - 纯文本格式 (.txt, .log, .new-log 等) — adb logcat 输出

    Args:
        path: 日志文件路径。

    Returns:
        (metadata, entries) 元组。

    Raises:
        ParseError: 解析失败。
        FileNotFoundError: 文件不存在。
    """
    path = Path(path)

    if _is_json_file(path):
        logger.info("检测到 JSON 格式，使用 JSON 解析器")
        return read_logcat_json(path)
    else:
        logger.info("检测到纯文本格式，使用文本解析器")
        return read_logcat_text(path)
