from __future__ import annotations

import logging
from datetime import datetime
from zoneinfo import ZoneInfo

import pandas as pd

from data.fetcher import NBADataFetcher
from database.csv_store import CSVDatabase
from model.rating_model import TeamProfile, TeamStrengthModel
from simulation.monte_carlo import NBAMonteCarloSimulator

BJ_TZ = ZoneInfo("Asia/Shanghai")
LOGGER = logging.getLogger(__name__)


def to_stars(prob: float) -> str:
    if prob >= 0.62:
        return "⭐⭐⭐"
    if prob >= 0.57:
        return "⭐⭐"
    if prob >= 0.53:
        return "⭐"
    return "-"


def pick_or_no_bet(home_team: str, away_team: str, prob_home_cover: float, threshold: float = 0.53) -> str:
    if prob_home_cover >= threshold:
        return f"{home_team} 让分"
    away_prob = 1 - prob_home_cover
    if away_prob >= threshold:
        return f"{away_team} 受让"
    return "No Bet"


def total_pick_or_no_bet(prob_over: float, threshold: float = 0.53) -> str:
    if prob_over >= threshold:
        return "大分"
    if (1 - prob_over) >= threshold:
        return "小分"
    return "No Bet"


def run_prediction_job() -> pd.DataFrame:
    now = datetime.now(BJ_TZ)
    fetcher = NBADataFetcher()
    store = CSVDatabase()
    model = TeamStrengthModel()
    sim = NBAMonteCarloSimulator(n_runs=10000)

    tomorrow_games = fetcher.fetch_tomorrow_games_with_odds(now)
    if tomorrow_games.empty:
        LOGGER.info("明日无比赛或数据获取失败")
        return tomorrow_games

    state_df = store.load_model_state()
    profiles = {
        row["team"]: TeamProfile(
            team=row["team"],
            offense_rating=float(row["offense_rating"]),
            defense_rating=float(row["defense_rating"]),
            pace=float(row["pace"]),
        )
        for _, row in state_df.iterrows()
    }

    rows = []
    for _, game in tomorrow_games.iterrows():
        home = profiles.get(game["home_team"], model.default_profile(game["home_team"]))
        away = profiles.get(game["away_team"], model.default_profile(game["away_team"]))
        result = sim.simulate_game(home, away, float(game["spread_line"]), float(game["total_line"]))

        spread_pick = pick_or_no_bet(game["home_team"], game["away_team"], result.spread_cover_prob)
        total_pick = total_pick_or_no_bet(result.over_prob)
        strength = max(result.spread_cover_prob, 1 - result.spread_cover_prob, result.over_prob, 1 - result.over_prob)

        rows.append(
            {
                "run_date_bj": now.strftime("%Y-%m-%d %H:%M"),
                "game_id": game["game_id"],
                "home_team": game["home_team"],
                "away_team": game["away_team"],
                "game_time_bj": game["game_time_bj"],
                "spread_line": game["spread_line"],
                "total_line": game["total_line"],
                "spread_pick": spread_pick,
                "total_pick": total_pick,
                "stars": to_stars(strength),
                "spread_prob": round(max(result.spread_cover_prob, 1 - result.spread_cover_prob) * 100, 2),
                "total_prob": round(max(result.over_prob, 1 - result.over_prob) * 100, 2),
                "home_proj": round(result.home_mean, 1),
                "away_proj": round(result.away_mean, 1),
            }
        )

    out_df = pd.DataFrame(rows)
    store.save_predictions(out_df)
    return out_df


def run_review_and_retrain_job() -> pd.DataFrame:
    now = datetime.now(BJ_TZ)
    fetcher = NBADataFetcher()
    store = CSVDatabase()
    model = TeamStrengthModel()

    results_df = fetcher.fetch_yesterday_results(now)
    if results_df.empty:
        LOGGER.info("昨日无完赛数据")
        return results_df

    results_df.insert(0, "sync_date_bj", now.strftime("%Y-%m-%d %H:%M"))
    store.save_results(results_df)

    all_results = store.load_results()
    profiles = model.fit(all_results)
    state_rows = [
        {
            "updated_at_bj": now.strftime("%Y-%m-%d %H:%M"),
            "team": p.team,
            "offense_rating": p.offense_rating,
            "defense_rating": p.defense_rating,
            "pace": p.pace,
        }
        for p in profiles.values()
    ]

    if state_rows:
        store.save_model_state(pd.DataFrame(state_rows))

    return results_df
