from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Any

import pandas as pd
import requests
from zoneinfo import ZoneInfo

LOGGER = logging.getLogger(__name__)
BJ_TZ = ZoneInfo("Asia/Shanghai")


@dataclass
class GameInfo:
    game_id: str
    game_date_utc: str
    game_time_bj: str
    home_team: str
    away_team: str
    spread_line: float
    total_line: float


class NBADataFetcher:
    """负责获取NBA赛程、盘口和赛果。"""

    def __init__(self, timeout: int = 15) -> None:
        self.timeout = timeout
        self.base_url = "https://www.balldontlie.io/api/v1"

    def fetch_tomorrow_games_with_odds(self, beijing_now: datetime | None = None) -> pd.DataFrame:
        now = beijing_now or datetime.now(BJ_TZ)
        target_day = (now + timedelta(days=1)).date()

        games = self._fetch_games_by_date(target_day)
        if not games:
            return pd.DataFrame(columns=list(GameInfo.__annotations__.keys()))

        records: list[dict[str, Any]] = []
        for g in games:
            game_id = str(g["id"])
            utc_time = g["date"]
            bj_time = self._utc_to_beijing(utc_time)
            home = g["home_team"]["full_name"]
            away = g["visitor_team"]["full_name"]

            spread_line, total_line = self._derive_mock_lines(home, away)
            records.append(
                GameInfo(
                    game_id=game_id,
                    game_date_utc=utc_time,
                    game_time_bj=bj_time,
                    home_team=home,
                    away_team=away,
                    spread_line=spread_line,
                    total_line=total_line,
                ).__dict__
            )

        return pd.DataFrame(records)

    def fetch_yesterday_results(self, beijing_now: datetime | None = None) -> pd.DataFrame:
        now = beijing_now or datetime.now(BJ_TZ)
        target_day = (now - timedelta(days=1)).date()

        games = self._fetch_games_by_date(target_day)
        rows = []
        for g in games:
            home_score = g.get("home_team_score")
            away_score = g.get("visitor_team_score")
            if home_score is None or away_score is None:
                continue
            if home_score == 0 and away_score == 0:
                continue

            rows.append(
                {
                    "game_id": str(g["id"]),
                    "game_date_utc": g["date"],
                    "home_team": g["home_team"]["full_name"],
                    "away_team": g["visitor_team"]["full_name"],
                    "home_score": home_score,
                    "away_score": away_score,
                    "total_score": home_score + away_score,
                }
            )

        return pd.DataFrame(rows)

    def _fetch_games_by_date(self, day: date) -> list[dict[str, Any]]:
        endpoint = f"{self.base_url}/games"
        params = {"dates[]": day.isoformat(), "per_page": 100}
        try:
            response = requests.get(endpoint, params=params, timeout=self.timeout)
            response.raise_for_status()
            payload = response.json()
            return payload.get("data", [])
        except Exception as exc:  # noqa: BLE001
            LOGGER.warning("获取赛程失败: %s", exc)
            return []

    @staticmethod
    def _utc_to_beijing(utc_ts: str) -> str:
        dt = datetime.fromisoformat(utc_ts.replace("Z", "+00:00"))
        return dt.astimezone(BJ_TZ).strftime("%Y-%m-%d %H:%M")

    @staticmethod
    def _derive_mock_lines(home_team: str, away_team: str) -> tuple[float, float]:
        """从队名稳定生成演示盘口，方便无付费赔率源下长期运行。"""
        token = sum(ord(c) for c in (home_team + away_team))
        spread = round(((token % 21) - 10) * 0.5, 1)
        total = round(212 + (token % 25) * 0.5, 1)
        return spread, total
