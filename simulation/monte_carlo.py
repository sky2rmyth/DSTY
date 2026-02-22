from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from model.rating_model import TeamProfile


@dataclass
class SimulationResult:
    home_mean: float
    away_mean: float
    spread_cover_prob: float
    over_prob: float


class NBAMonteCarloSimulator:
    def __init__(self, n_runs: int = 10000, seed: int = 42) -> None:
        if n_runs < 10000:
            raise ValueError("Monte Carlo次数必须 >= 10000")
        self.n_runs = n_runs
        self.rng = np.random.default_rng(seed)

    def simulate_game(
        self,
        home: TeamProfile,
        away: TeamProfile,
        spread_line: float,
        total_line: float,
    ) -> SimulationResult:
        base_points = 111.5
        home_expect = base_points + home.offense_rating + away.defense_rating + 1.5
        away_expect = base_points + away.offense_rating + home.defense_rating

        tempo_factor = (home.pace + away.pace) / 200.0
        home_mu = home_expect * tempo_factor
        away_mu = away_expect * tempo_factor

        home_scores = self.rng.normal(loc=home_mu, scale=11.5, size=self.n_runs)
        away_scores = self.rng.normal(loc=away_mu, scale=11.5, size=self.n_runs)

        margins = home_scores - away_scores
        totals = home_scores + away_scores

        cover_prob = float(np.mean(margins > spread_line))
        over_prob = float(np.mean(totals > total_line))

        return SimulationResult(
            home_mean=float(np.mean(home_scores)),
            away_mean=float(np.mean(away_scores)),
            spread_cover_prob=cover_prob,
            over_prob=over_prob,
        )
