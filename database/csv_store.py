from __future__ import annotations

from pathlib import Path

import pandas as pd


class CSVDatabase:
    def __init__(self, base_path: str = "database/storage") -> None:
        self.base = Path(base_path)
        self.base.mkdir(parents=True, exist_ok=True)

        self.predictions_file = self.base / "predictions.csv"
        self.results_file = self.base / "results.csv"
        self.model_state_file = self.base / "model_state.csv"

        self._ensure_file(self.predictions_file, [
            "run_date_bj", "game_id", "home_team", "away_team", "game_time_bj",
            "spread_line", "total_line", "spread_pick", "total_pick", "stars",
            "spread_prob", "total_prob", "home_proj", "away_proj"
        ])
        self._ensure_file(self.results_file, [
            "sync_date_bj", "game_id", "home_team", "away_team", "home_score", "away_score", "total_score"
        ])
        self._ensure_file(self.model_state_file, ["updated_at_bj", "team", "offense_rating", "defense_rating", "pace"])

    @staticmethod
    def _ensure_file(path: Path, headers: list[str]) -> None:
        if not path.exists():
            pd.DataFrame(columns=headers).to_csv(path, index=False)

    @staticmethod
    def append_rows(path: Path, df: pd.DataFrame) -> None:
        if df.empty:
            return
        existing = pd.read_csv(path)
        merged = pd.concat([existing, df], ignore_index=True)
        merged.drop_duplicates(inplace=True)
        merged.to_csv(path, index=False)

    def save_predictions(self, predictions_df: pd.DataFrame) -> None:
        self.append_rows(self.predictions_file, predictions_df)

    def save_results(self, results_df: pd.DataFrame) -> None:
        self.append_rows(self.results_file, results_df)

    def save_model_state(self, model_state_df: pd.DataFrame) -> None:
        model_state_df.to_csv(self.model_state_file, index=False)

    def load_results(self) -> pd.DataFrame:
        return pd.read_csv(self.results_file)

    def load_predictions(self) -> pd.DataFrame:
        return pd.read_csv(self.predictions_file)

    def load_model_state(self) -> pd.DataFrame:
        return pd.read_csv(self.model_state_file)
