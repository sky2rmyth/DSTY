"""预测与记录模块。"""

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
from nba_api.stats.endpoints import scoreboardv2

from src.feature_engineering import build_match_features, feature_columns
from src.modeling import load_models
from src.time_utils import BEIJING_ZONE, convert_to_beijing_time, now_beijing_date_str


DATA_DIR = Path("data")
HISTORY_FILE = DATA_DIR / "prediction_history.csv"
MARKET_FILE = DATA_DIR / "market_lines_today.csv"


def _fetch_schedule_candidates() -> pd.DataFrame:
    """抓取候选比赛赛程（覆盖北京时间今日可能对应的美国日期）。"""
    bj_now = datetime.now(BEIJING_ZONE)
    us_dates = {
        (bj_now - timedelta(days=1)).strftime("%m/%d/%Y"),
        bj_now.strftime("%m/%d/%Y"),
    }

    all_rows = []
    for us_date in us_dates:
        board = scoreboardv2.ScoreboardV2(game_date=us_date)
        game_header = board.game_header.get_data_frame()
        if game_header.empty:
            continue
        lines = board.line_score.get_data_frame()

        for _, g in game_header.iterrows():
            game_id = g["GAME_ID"]
            game_time_et = str(g.get("GAME_STATUS_TEXT", "")).strip()
            if ":" in game_time_et:
                us_time_str = datetime.strptime(us_date, "%m/%d/%Y").strftime("%Y-%m-%d") + f" {game_time_et}:00"
            else:
                us_time_str = datetime.strptime(us_date, "%m/%d/%Y").strftime("%Y-%m-%d") + " 19:00:00"

            bj_info = convert_to_beijing_time(us_time_str)

            game_lines = lines[lines["GAME_ID"] == game_id]
            if game_lines.empty:
                continue
            home_row = game_lines[game_lines["TEAM_ABBREVIATION"] == g["HOME_TEAM_ABBREVIATION"]]
            away_row = game_lines[game_lines["TEAM_ABBREVIATION"] == g["VISITOR_TEAM_ABBREVIATION"]]
            if home_row.empty or away_row.empty:
                continue

            all_rows.append(
                {
                    "比赛ID": game_id,
                    "北京时间": bj_info["bj_time_str"],
                    "北京日期": bj_info["bj_date"],
                    "主队": g["HOME_TEAM_ABBREVIATION"],
                    "客队": g["VISITOR_TEAM_ABBREVIATION"],
                    "比赛": f"{g['VISITOR_TEAM_ABBREVIATION']} vs {g['HOME_TEAM_ABBREVIATION']}",
                    "实际分差": float(home_row.iloc[0].get("PTS", 0)) - float(away_row.iloc[0].get("PTS", 0)),
                    "实际总分": float(home_row.iloc[0].get("PTS", 0)) + float(away_row.iloc[0].get("PTS", 0)),
                }
            )

    return pd.DataFrame(all_rows)


def _load_market_lines() -> pd.DataFrame:
    """读取市场盘口。"""
    if MARKET_FILE.exists():
        return pd.read_csv(MARKET_FILE)
    return pd.DataFrame(columns=["比赛", "市场让分", "市场总分"])


def _append_prediction_history(pred_df: pd.DataFrame) -> None:
    """追加预测历史记录。"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    base_cols = [
        "北京时间",
        "比赛",
        "模型预测让分",
        "市场让分",
        "让分优势",
        "模型预测总分",
        "市场总分",
        "大小分优势",
        "是否建议下注",
        "实际分差",
        "实际总分",
        "是否命中让分",
        "是否命中大小分",
    ]

    export_df = pred_df.copy()
    for col in ["实际分差", "实际总分", "是否命中让分", "是否命中大小分"]:
        if col not in export_df.columns:
            export_df[col] = None

    export_df = export_df[base_cols]
    if HISTORY_FILE.exists():
        old_df = pd.read_csv(HISTORY_FILE)
        export_df = pd.concat([old_df, export_df], ignore_index=True)
        export_df = export_df.drop_duplicates(subset=["北京时间", "比赛"], keep="last")

    export_df.to_csv(HISTORY_FILE, index=False, encoding="utf-8-sig")


def predict_today(features_df: pd.DataFrame) -> pd.DataFrame:
    """识别北京时间今日比赛并输出预测。"""
    today_bj = now_beijing_date_str()
    schedule_df = _fetch_schedule_candidates()
    today_schedule = schedule_df[schedule_df["北京日期"] == today_bj].copy()

    if today_schedule.empty:
        return pd.DataFrame(
            columns=[
                "比赛",
                "北京时间",
                "模型预测让分",
                "市场让分",
                "让分优势",
                "模型预测总分",
                "市场总分",
                "大小分优势",
                "是否建议下注",
            ]
        )

    model_df = features_df.sort_values("北京时间").drop_duplicates(subset=["比赛"], keep="last")
    merged = today_schedule.merge(model_df, on=["比赛", "主队", "客队"], how="left", suffixes=("", "_hist"))
    feat_cols = feature_columns()
    merged[feat_cols] = merged[feat_cols].fillna(model_df[feat_cols].median())

    spread_model, total_model = load_models()
    merged["模型预测让分"] = spread_model.predict(merged[feat_cols]).round(2)
    merged["模型预测总分"] = total_model.predict(merged[feat_cols]).round(2)

    market_df = _load_market_lines()
    merged = merged.merge(market_df, on="比赛", how="left")
    merged["市场让分"] = merged["市场让分"].fillna(merged["模型预测让分"].round(1))
    merged["市场总分"] = merged["市场总分"].fillna(merged["模型预测总分"].round(1))

    merged["让分优势"] = (merged["模型预测让分"] - merged["市场让分"]).round(2)
    merged["大小分优势"] = (merged["模型预测总分"] - merged["市场总分"]).round(2)
    merged["是否建议下注"] = (
        (merged["让分优势"].abs() >= 1.5) | (merged["大小分优势"].abs() >= 3.0)
    ).map({True: "是", False: "否"})

    out_cols = [
        "比赛",
        "北京时间",
        "模型预测让分",
        "市场让分",
        "让分优势",
        "模型预测总分",
        "市场总分",
        "大小分优势",
        "是否建议下注",
        "实际分差",
        "实际总分",
    ]
    out_df = merged[out_cols].copy()

    _append_prediction_history(out_df)
    return out_df[out_cols[:-2]]
