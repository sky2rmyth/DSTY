"""回测脚本：基于预测历史统计命中率与ROI。"""

from __future__ import annotations

import pandas as pd

HISTORY_FILE = "data/prediction_history.csv"


def _settle_hits(df: pd.DataFrame) -> pd.DataFrame:
    """根据实际赛果结算命中结果。"""
    settled = df.copy()

    settled["让分方向"] = (settled["模型预测让分"] - settled["市场让分"]).apply(lambda x: "主队" if x >= 0 else "客队")
    settled["大小分方向"] = (settled["模型预测总分"] - settled["市场总分"]).apply(lambda x: "大分" if x >= 0 else "小分")

    settled["是否命中让分"] = (
        ((settled["让分方向"] == "主队") & (settled["实际分差"] > settled["市场让分"]))
        | ((settled["让分方向"] == "客队") & (settled["实际分差"] < settled["市场让分"]))
    ).map({True: 1, False: 0})

    settled["是否命中大小分"] = (
        ((settled["大小分方向"] == "大分") & (settled["实际总分"] > settled["市场总分"]))
        | ((settled["大小分方向"] == "小分") & (settled["实际总分"] < settled["市场总分"]))
    ).map({True: 1, False: 0})

    return settled


def main() -> None:
    """执行回测统计。"""
    df = pd.read_csv(HISTORY_FILE)
    valid_df = df.dropna(subset=["实际分差", "实际总分"]).copy()
    valid_df = valid_df[(valid_df["实际总分"] > 0) | (valid_df["实际分差"] != 0)]

    if valid_df.empty:
        print("暂无可回测记录，请等待比赛结束后再运行。")
        return

    settled = _settle_hits(valid_df)

    total_games = len(settled)
    spread_hit = settled["是否命中让分"].mean()
    total_hit = settled["是否命中大小分"].mean()
    avg_edge = (settled["让分优势"].abs() + settled["大小分优势"].abs()).mean() / 2

    # 假设每场投注1单位：让分与大小分各下注1次
    pnl_spread = settled["是否命中让分"].sum() * 0.91 - (total_games - settled["是否命中让分"].sum())
    pnl_total = settled["是否命中大小分"].sum() * 0.91 - (total_games - settled["是否命中大小分"].sum())
    total_stake = total_games * 2
    roi = (pnl_spread + pnl_total) / total_stake

    print("NBA量化预测回测结果")
    print("=" * 30)
    print(f"总预测场数: {total_games}")
    print(f"让分命中率: {spread_hit:.2%}")
    print(f"大小分命中率: {total_hit:.2%}")
    print(f"平均优势: {avg_edge:.2f}")
    print(f"假设每场投注1单位ROI: {roi:.2%}")

    df.update(settled[["是否命中让分", "是否命中大小分"]])
    df.to_csv(HISTORY_FILE, index=False, encoding="utf-8-sig")


if __name__ == "__main__":
    main()
