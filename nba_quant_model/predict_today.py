"""北京时间今日比赛预测脚本。"""

from __future__ import annotations

import os
import pandas as pd

from src.feature_engineering import build_match_features
from src.data_loader import load_games_raw
from src.predictor import predict_today


def main() -> None:
    """执行今日预测。"""
    if not (os.path.exists("models/spread_model.joblib") and os.path.exists("models/total_model.joblib")):
        raise FileNotFoundError("未找到模型文件，请先运行 train.py")

    raw_df = load_games_raw()
    feat_df = build_match_features(raw_df)
    pred_df = predict_today(feat_df)

    if pred_df.empty:
        print("北京时间今日暂无可预测比赛。")
        return

    print("北京时间今日比赛预测如下：")
    print(pred_df.to_string(index=False))
    print("预测结果已自动写入 data/prediction_history.csv")


if __name__ == "__main__":
    pd.set_option("display.width", 200)
    main()
