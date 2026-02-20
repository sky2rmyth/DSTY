"""特征工程模块：构建NBA预测训练数据。"""

from __future__ import annotations

import numpy as np
import pandas as pd


INITIAL_ELO = 1500.0
HOME_ADVANTAGE_ELO = 60.0
K_FACTOR = 20.0


def _is_home(matchup: str) -> int:
    """判断是否主场。"""
    return 1 if " vs. " in str(matchup) else 0


def _opponent_team(matchup: str) -> str:
    """从对阵字段提取对手简称。"""
    parts = str(matchup).replace(" vs. ", " @ ").split(" @ ")
    return parts[1].strip() if len(parts) == 2 else ""


def _calc_possessions(df: pd.DataFrame) -> pd.Series:
    """估算回合数。"""
    return df["投篮出手"] + 0.44 * df["罚球出手"] - df["前场篮板"] + df["失误"]


def add_team_level_features(df_raw: pd.DataFrame) -> pd.DataFrame:
    """在球队比赛粒度下增加滚动与体能特征。"""
    df = df_raw.copy()
    df["比赛日期"] = pd.to_datetime(df["比赛日期"])
    df = df.sort_values(["球队", "比赛日期"])

    df["是否主场"] = df["对阵"].apply(_is_home)
    df["对手"] = df["对阵"].apply(_opponent_team)
    df["回合数"] = _calc_possessions(df).replace(0, np.nan)
    df["进攻效率"] = df["得分"] / df["回合数"] * 100

    grouped = df.groupby("球队", group_keys=False)
    df["最近10场均分"] = grouped["得分"].apply(lambda s: s.shift(1).rolling(10, min_periods=3).mean())
    df["最近10场净胜分"] = grouped["正负值"].apply(lambda s: s.shift(1).rolling(10, min_periods=3).mean())
    df["最近10场状态"] = (df["最近10场净胜分"] > 0).astype(int)
    df["进攻效率_近10"] = grouped["进攻效率"].apply(lambda s: s.shift(1).rolling(10, min_periods=3).mean())
    df["Pace"] = grouped["回合数"].apply(lambda s: s.shift(1).rolling(10, min_periods=3).mean())

    prev_date = grouped["比赛日期"].shift(1)
    df["休息天数"] = (df["比赛日期"] - prev_date).dt.days.fillna(5).clip(lower=0)
    df["是否背靠背"] = (df["休息天数"] <= 1).astype(int)

    return df


def add_dynamic_elo(df_team: pd.DataFrame) -> pd.DataFrame:
    """按比赛顺序计算动态ELO。"""
    df = df_team.copy().sort_values(["比赛日期", "比赛ID", "球队"])

    elo_map: dict[str, float] = {}
    pre_elo_values = []

    for _, row in df.iterrows():
        team = row["球队"]
        opp = row["对手"]
        team_elo = elo_map.get(team, INITIAL_ELO)
        opp_elo = elo_map.get(opp, INITIAL_ELO)

        pre_elo_values.append(team_elo)

        home_bonus = HOME_ADVANTAGE_ELO if row["是否主场"] == 1 else -HOME_ADVANTAGE_ELO
        expected = 1 / (1 + 10 ** (-(team_elo + home_bonus - opp_elo) / 400))
        actual = 1.0 if row.get("胜负", "L") == "W" else 0.0

        new_team_elo = team_elo + K_FACTOR * (actual - expected)
        elo_map[team] = new_team_elo

    df["动态ELO"] = pre_elo_values
    return df


def build_match_features(df_raw: pd.DataFrame) -> pd.DataFrame:
    """将球队粒度数据聚合为比赛粒度特征。"""
    team_df = add_dynamic_elo(add_team_level_features(df_raw))
    team_df = team_df.sort_values(["比赛ID", "是否主场"], ascending=[True, False])

    rows = []
    for game_id, g in team_df.groupby("比赛ID"):
        if len(g) != 2:
            continue
        home = g[g["是否主场"] == 1]
        away = g[g["是否主场"] == 0]
        if home.empty or away.empty:
            continue

        h = home.iloc[0]
        a = away.iloc[0]

        row = {
            "比赛ID": game_id,
            "北京日期": h["北京日期"],
            "北京时间": h["北京时间"],
            "主队": h["球队"],
            "客队": a["球队"],
            "比赛": f"{a['球队']} vs {h['球队']}",
            "动态ELO差": h["动态ELO"] - a["动态ELO"],
            "最近10场状态差": h["最近10场状态"] - a["最近10场状态"],
            "进攻效率差": h["进攻效率_近10"] - a["进攻效率_近10"],
            "防守效率差": a["进攻效率_近10"] - h["进攻效率_近10"],
            "Pace均值": np.nanmean([h["Pace"], a["Pace"]]),
            "主场优势": 1,
            "休息天数差": h["休息天数"] - a["休息天数"],
            "背靠背差": h["是否背靠背"] - a["是否背靠背"],
            "实际分差": h["得分"] - a["得分"],
            "实际总分": h["得分"] + a["得分"],
        }
        rows.append(row)

    features_df = pd.DataFrame(rows)
    numeric_cols = [
        "动态ELO差",
        "最近10场状态差",
        "进攻效率差",
        "防守效率差",
        "Pace均值",
        "主场优势",
        "休息天数差",
        "背靠背差",
    ]
    features_df[numeric_cols] = features_df[numeric_cols].fillna(features_df[numeric_cols].median())
    return features_df


def feature_columns() -> list[str]:
    """返回模型使用的特征列。"""
    return [
        "动态ELO差",
        "最近10场状态差",
        "进攻效率差",
        "防守效率差",
        "Pace均值",
        "主场优势",
        "休息天数差",
        "背靠背差",
    ]
