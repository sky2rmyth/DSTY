"""数据下载与存储模块。"""

from __future__ import annotations

from pathlib import Path
import pandas as pd

from nba_api.stats.endpoints import leaguegamelog

from src.time_utils import convert_us_to_utc_and_beijing


DATA_DIR = Path("data")
RAW_FILE = DATA_DIR / "games_raw.csv"


RENAME_MAP = {
    "GAME_ID": "比赛ID",
    "GAME_DATE": "比赛日期",
    "TEAM_ID": "球队ID",
    "TEAM_ABBREVIATION": "球队",
    "TEAM_NAME": "球队全称",
    "MATCHUP": "对阵",
    "WL": "胜负",
    "MIN": "比赛分钟",
    "PTS": "得分",
    "FGM": "投篮命中",
    "FGA": "投篮出手",
    "FG_PCT": "投篮命中率",
    "FG3M": "三分命中",
    "FG3A": "三分出手",
    "FG3_PCT": "三分命中率",
    "FTM": "罚球命中",
    "FTA": "罚球出手",
    "FT_PCT": "罚球命中率",
    "OREB": "前场篮板",
    "DREB": "后场篮板",
    "REB": "总篮板",
    "AST": "助攻",
    "STL": "抢断",
    "BLK": "盖帽",
    "TOV": "失误",
    "PF": "犯规",
    "PLUS_MINUS": "正负值",
}


def _to_us_eastern_str(game_date_str: str) -> str:
    """将NBA日期字符串转为美国东部时间字符串（默认中午12点，避免日期跨日歧义）。"""
    date_value = pd.to_datetime(game_date_str).strftime("%Y-%m-%d")
    return f"{date_value} 12:00:00"


def download_games_history(season: str = "2024-25", season_type: str = "Regular Season") -> pd.DataFrame:
    """下载NBA历史比赛数据并保存至CSV。"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    endpoint = leaguegamelog.LeagueGameLog(
        season=season,
        season_type_all_star=season_type,
        player_or_team_abbreviation="T",
    )
    df = endpoint.get_data_frames()[0].copy()

    df = df.rename(columns={k: v for k, v in RENAME_MAP.items() if k in df.columns})

    time_rows = df["比赛日期"].apply(_to_us_eastern_str).apply(convert_us_to_utc_and_beijing)
    df["UTC时间"] = time_rows.apply(lambda x: x["utc_time"])
    df["北京时间"] = time_rows.apply(lambda x: x["bj_time_str"])
    df["北京日期"] = time_rows.apply(lambda x: x["bj_date"])

    df.to_csv(RAW_FILE, index=False, encoding="utf-8-sig")
    return df


def load_games_raw() -> pd.DataFrame:
    """读取本地原始比赛数据，如果不存在则自动下载。"""
    if not RAW_FILE.exists():
        return download_games_history()
    return pd.read_csv(RAW_FILE)
