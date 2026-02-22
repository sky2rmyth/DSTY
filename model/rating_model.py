from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass
class TeamProfile:
    team: str
    offense_rating: float
    defense_rating: float
    pace: float


class TeamStrengthModel:
    """基于历史赛果生成简易球队强度参数，可持续重校准。"""

    def fit(self, results_df: pd.DataFrame) -> dict[str, TeamProfile]:
        if results_df.empty:
            return {}

        home_rows = results_df[["home_team", "home_score", "away_score"]].rename(
            columns={"home_team": "team", "home_score": "points_for", "away_score": "points_against"}
        )
        away_rows = results_df[["away_team", "away_score", "home_score"]].rename(
            columns={"away_team": "team", "away_score": "points_for", "home_score": "points_against"}
        )

        team_df = pd.concat([home_rows, away_rows], ignore_index=True)
        grouped = team_df.groupby("team", as_index=False).agg(
            points_for=("points_for", "mean"),
            points_against=("points_against", "mean"),
            games=("team", "count"),
        )

        league_avg = grouped["points_for"].mean() if not grouped.empty else 112.0
        profiles: dict[str, TeamProfile] = {}
        for _, row in grouped.iterrows():
            offense = row["points_for"] - league_avg
            defense = league_avg - row["points_against"]
            pace = 97 + min(row["games"], 20) * 0.2
            profiles[row["team"]] = TeamProfile(
                team=row["team"],
                offense_rating=float(offense),
                defense_rating=float(defense),
                pace=float(pace),
            )

        return profiles

    @staticmethod
    def default_profile(team: str) -> TeamProfile:
        return TeamProfile(team=team, offense_rating=0.0, defense_rating=0.0, pace=100.0)
