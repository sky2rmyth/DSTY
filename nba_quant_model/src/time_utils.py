"""时间工具模块：统一处理NBA美国东部时间到北京时间的转换。"""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

US_EASTERN = ZoneInfo("America/New_York")
UTC_ZONE = ZoneInfo("UTC")
BEIJING_ZONE = ZoneInfo("Asia/Shanghai")


def _parse_us_time(us_time_str: str) -> datetime:
    """解析美国东部时间字符串为带时区的datetime对象。"""
    candidate_formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M",
    ]
    cleaned = us_time_str.strip().replace("Z", "")

    for fmt in candidate_formats:
        try:
            dt = datetime.strptime(cleaned, fmt)
            return dt.replace(tzinfo=US_EASTERN)
        except ValueError:
            continue

    raise ValueError(f"无法解析美国东部时间字符串: {us_time_str}")


def convert_to_beijing_time(us_time_str: str) -> dict:
    """将美国东部时间转换为北京时间信息。

    参数:
        us_time_str: 美国东部时间字符串，例如 "2025-01-01 19:30:00"。

    返回:
        dict，包含:
        - bj_datetime: 北京时间datetime对象
        - bj_date: 北京日期字符串(YYYY-MM-DD)
        - bj_time_str: 北京时间字符串(YYYY-MM-DD HH:MM:SS)
    """
    us_dt = _parse_us_time(us_time_str)
    bj_dt = us_dt.astimezone(BEIJING_ZONE)

    return {
        "bj_datetime": bj_dt,
        "bj_date": bj_dt.strftime("%Y-%m-%d"),
        "bj_time_str": bj_dt.strftime("%Y-%m-%d %H:%M:%S"),
    }


def convert_us_to_utc_and_beijing(us_time_str: str) -> dict:
    """将美国东部时间同时转换为UTC与北京时间。"""
    us_dt = _parse_us_time(us_time_str)
    utc_dt = us_dt.astimezone(UTC_ZONE)
    bj_info = convert_to_beijing_time(us_time_str)
    return {
        "utc_time": utc_dt.strftime("%Y-%m-%d %H:%M:%S"),
        "bj_datetime": bj_info["bj_datetime"],
        "bj_date": bj_info["bj_date"],
        "bj_time_str": bj_info["bj_time_str"],
    }


def now_beijing_date_str() -> str:
    """获取当前北京时间日期字符串。"""
    return datetime.now(BEIJING_ZONE).strftime("%Y-%m-%d")
