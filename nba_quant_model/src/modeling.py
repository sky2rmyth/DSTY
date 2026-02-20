"""模型训练与加载模块。"""

from __future__ import annotations

from pathlib import Path
import joblib
import pandas as pd
from xgboost import XGBRegressor

from src.feature_engineering import feature_columns


MODELS_DIR = Path("models")
SPREAD_MODEL_FILE = MODELS_DIR / "spread_model.joblib"
TOTAL_MODEL_FILE = MODELS_DIR / "total_model.joblib"


def train_models(features_df: pd.DataFrame) -> tuple[XGBRegressor, XGBRegressor]:
    """训练让分与总分模型。"""
    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    cols = feature_columns()
    train_df = features_df.dropna(subset=["实际分差", "实际总分"]).copy()

    x_train = train_df[cols]
    y_spread = train_df["实际分差"]
    y_total = train_df["实际总分"]

    spread_model = XGBRegressor(
        n_estimators=300,
        max_depth=4,
        learning_rate=0.05,
        subsample=0.9,
        colsample_bytree=0.9,
        objective="reg:squarederror",
        random_state=42,
    )
    total_model = XGBRegressor(
        n_estimators=300,
        max_depth=4,
        learning_rate=0.05,
        subsample=0.9,
        colsample_bytree=0.9,
        objective="reg:squarederror",
        random_state=42,
    )

    spread_model.fit(x_train, y_spread)
    total_model.fit(x_train, y_total)

    joblib.dump(spread_model, SPREAD_MODEL_FILE)
    joblib.dump(total_model, TOTAL_MODEL_FILE)

    return spread_model, total_model


def load_models() -> tuple[XGBRegressor, XGBRegressor]:
    """加载模型。"""
    spread_model = joblib.load(SPREAD_MODEL_FILE)
    total_model = joblib.load(TOTAL_MODEL_FILE)
    return spread_model, total_model
