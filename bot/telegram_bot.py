from __future__ import annotations

import logging
import os

import pandas as pd
from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

from database.csv_store import CSVDatabase

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

BUTTONS = [["📊 今日预测", "📈 模型表现"], ["🧪 模型测试", "📅 今日赛程"], ["⚙️ 模型状态"]]
KEYBOARD = ReplyKeyboardMarkup(BUTTONS, resize_keyboard=True)


def _latest_predictions(store: CSVDatabase) -> pd.DataFrame:
    df = store.load_predictions()
    if df.empty:
        return df
    latest_run = df["run_date_bj"].max()
    return df[df["run_date_bj"] == latest_run].copy()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("欢迎使用NBA自动预测系统，请选择功能：", reply_markup=KEYBOARD)


async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = update.message.text
    store = CSVDatabase()

    if text == "📊 今日预测":
        await update.message.reply_text(render_predictions(_latest_predictions(store)))
    elif text == "📈 模型表现":
        await update.message.reply_text(render_performance(store))
    elif text == "🧪 模型测试":
        await update.message.reply_text("模型测试：Monte Carlo=10000次，阈值=53%，支持长期回测。")
    elif text == "📅 今日赛程":
        await update.message.reply_text(render_schedule(_latest_predictions(store)))
    elif text == "⚙️ 模型状态":
        await update.message.reply_text(render_status(store))
    else:
        await update.message.reply_text("请使用下方按钮进行操作。", reply_markup=KEYBOARD)


def render_predictions(df: pd.DataFrame) -> str:
    if df.empty:
        return "暂无预测数据。"

    lines = ["📊 今日预测"]
    for _, row in df.iterrows():
        lines.extend(
            [
                f"\n🏀 {row['away_team']} vs {row['home_team']}",
                f"⏰ 开赛时间(北京时间): {row['game_time_bj']}",
                f"让分预测: {row['spread_pick']} (命中概率 {row['spread_prob']:.2f}%)",
                f"大小分预测: {row['total_pick']} (命中概率 {row['total_prob']:.2f}%)",
                f"星级: {row['stars']}",
            ]
        )
    return "\n".join(lines)


def render_schedule(df: pd.DataFrame) -> str:
    if df.empty:
        return "暂无赛程数据。"
    lines = ["📅 今日赛程"]
    for _, row in df.iterrows():
        lines.append(f"- {row['game_time_bj']} | {row['away_team']} vs {row['home_team']}")
    return "\n".join(lines)


def render_performance(store: CSVDatabase) -> str:
    pred = store.load_predictions()
    results = store.load_results()
    if pred.empty or results.empty:
        return "模型表现：数据不足，尚未形成回测样本。"

    merged = pred.merge(results[["game_id", "home_score", "away_score", "total_score"]], on="game_id", how="inner")
    if merged.empty:
        return "模型表现：暂无可匹配样本。"

    spread_hit = 0
    total_hit = 0
    total_bet = 0
    for _, row in merged.iterrows():
        margin = row["home_score"] - row["away_score"]
        spread_pick = row["spread_pick"]
        if spread_pick != "No Bet":
            total_bet += 1
            if (spread_pick.endswith("让分") and margin > row["spread_line"]) or (
                spread_pick.endswith("受让") and margin < row["spread_line"]
            ):
                spread_hit += 1

        total_pick = row["total_pick"]
        if total_pick != "No Bet":
            total_bet += 1
            if (total_pick == "大分" and row["total_score"] > row["total_line"]) or (
                total_pick == "小分" and row["total_score"] < row["total_line"]
            ):
                total_hit += 1

    hit = spread_hit + total_hit
    hit_rate = 0 if total_bet == 0 else hit / total_bet * 100
    return f"📈 模型表现\n样本数: {len(merged)}\n总下注项: {total_bet}\n命中率: {hit_rate:.2f}%"


def render_status(store: CSVDatabase) -> str:
    state = store.load_model_state()
    pred = store.load_predictions()
    return (
        "⚙️ 模型状态\n"
        f"球队参数数量: {len(state)}\n"
        f"预测记录数: {len(pred)}\n"
        "Monte Carlo次数: 10000\n"
        "数据库: CSV"
    )


def main() -> None:
    token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    if not token:
        raise ValueError("请在环境变量 TELEGRAM_BOT_TOKEN 中配置机器人Token")

    app = ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_buttons))
    app.run_polling()


if __name__ == "__main__":
    main()
