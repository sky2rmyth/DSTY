"""训练入口脚本。"""

from __future__ import annotations

import pandas as pd

from src.data_loader import download_games_history
from src.feature_engineering import build_match_features
from src.modeling import train_models


def main() -> None:
    """执行训练流程。"""
    print("开始下载并整理历史比赛数据...")
    raw_df = download_games_history()

    print("开始生成特征...")
    feature_df = build_match_features(raw_df)
    feature_df.to_csv("data/features.csv", index=False, encoding="utf-8-sig")

    print("开始训练XGBoost模型...")
    train_models(feature_df)

    print(f"训练完成，共使用比赛样本: {len(feature_df)} 场")
    print("模型已保存至 models/spread_model.joblib 与 models/total_model.joblib")


if __name__ == "__main__":
    pd.set_option("display.width", 200)
    main()
