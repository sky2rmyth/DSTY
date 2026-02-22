# NBA自动预测系统

一个可长期运行的 NBA 赛前预测 Telegram Bot 项目，包含自动抓取、Monte Carlo 模拟预测、复盘再训练、CSV 持久化与 GitHub Actions 定时调度。

## 功能总览

- 每天 **北京时间 21:40** 自动执行预测流程：
  1. 拉取次日全部比赛
  2. 生成让分与大小分盘口（可替换为真实赔率源）
  3. 使用 Monte Carlo（10000次）模拟
  4. 产出每场预测并写入 CSV

- 每天 **北京时间 14:00** 自动执行复盘流程：
  1. 拉取昨日真实赛果
  2. 更新赛果数据库
  3. 重新校准球队强度参数
  4. 保存最新模型状态

- Telegram Bot（中文按钮交互）
  - 📊 今日预测
  - 📈 模型表现
  - 🧪 模型测试
  - 📅 今日赛程
  - ⚙️ 模型状态

## 项目结构

```text
/bot          Telegram机器人
/data         数据抓取
/model        模型校准
/simulation   Monte Carlo模拟
/database     CSV数据库
/actions      定时任务入口与管道
```

## 快速开始

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

配置 `.env`：

- `TELEGRAM_BOT_TOKEN`: 你的 Telegram Bot Token
- `TZ=Asia/Shanghai`

### 手动运行

```bash
python -m actions.run_prediction   # 生成次日预测
python -m actions.run_review       # 拉取赛果并重校准
python -m bot.telegram_bot         # 启动机器人
```

## 数据存储

CSV 文件位于 `database/storage/`：

- `predictions.csv`：所有历史预测
- `results.csv`：真实赛果
- `model_state.csv`：球队强度参数

## GitHub Actions

工作流文件：`.github/workflows/nba_automation.yml`

- `40 13 * * *`（UTC）=> 北京时间 21:40 预测任务
- `0 6 * * *`（UTC）=> 北京时间 14:00 复盘任务

支持 `workflow_dispatch` 手动触发。

## 说明

- 当前默认赛程/赛果来自 balldontlie 公共接口。
- 盘口由稳定规则生成，保证系统可持续运行；接入真实赔率时只需替换 `data/fetcher.py` 中盘口逻辑。
