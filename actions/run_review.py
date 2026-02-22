from __future__ import annotations

import logging

from actions.pipeline import run_review_and_retrain_job

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

if __name__ == "__main__":
    df = run_review_and_retrain_job()
    logging.info("复盘任务完成，记录: %s", len(df))
