from __future__ import annotations

import logging

from actions.pipeline import run_prediction_job

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

if __name__ == "__main__":
    df = run_prediction_job()
    logging.info("预测任务完成，场次: %s", len(df))
