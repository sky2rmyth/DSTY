# NBA职业量化预测系统（北京时间版）

本项目基于 `nba_api + XGBoost` 构建可持续运行的NBA量化预测系统，核心能力：

- 自动下载历史比赛数据
- 自动构建动态特征（ELO、状态、效率、节奏、体能）
- 双模型预测（让分 / 总分）
- 自动识别**北京时间今日比赛**并输出建议
- 自动记录预测历史
- 自动回测命中率与ROI

---

## 1. 项目结构

```text
nba_quant_model/
├── data/
├── models/
├── src/
│   ├── data_loader.py
│   ├── feature_engineering.py
│   ├── modeling.py
│   ├── predictor.py
│   └── time_utils.py
├── train.py
├── predict_today.py
├── backtest.py
└── README.md
```

---

## 2. 环境安装

建议 Python 3.10+。

```bash
pip install pandas numpy joblib xgboost nba_api
```

---

## 3. 训练模型

```bash
cd nba_quant_model
python train.py
```

训练后将生成：

- `data/games_raw.csv`
- `data/features.csv`
- `models/spread_model.joblib`
- `models/total_model.joblib`

---

## 4. 今日预测（北京时间）

```bash
python predict_today.py
```

输出字段：

- 比赛
- 北京时间
- 模型预测让分
- 市场让分
- 让分优势
- 模型预测总分
- 市场总分
- 大小分优势
- 是否建议下注

并自动追加到：

- `data/prediction_history.csv`

如需使用自定义盘口，可创建 `data/market_lines_today.csv`，字段如下：

- 比赛
- 市场让分
- 市场总分

---

## 5. 回测

```bash
python backtest.py
```

回测指标：

- 总预测场数
- 让分命中率
- 大小分命中率
- 平均优势
- 假设每场投注1单位ROI

---

## 6. 时间与时区说明（关键）

NBA数据默认采用美国东部时间。项目通过 `zoneinfo` 在 `src/time_utils.py` 中统一处理：

- 美国东部时间 -> UTC
- 美国东部时间 -> 北京时间（Asia/Shanghai）
- 全流程统一使用北京日期驱动“今日比赛识别、预测记录、回测匹配”

核心函数：

```python
convert_to_beijing_time(us_time_str)
```

返回：

- `bj_datetime`
- `bj_date`
- `bj_time_str`

---

## 7. 可持续优化建议

- 增加球员伤病、轮休、旅行距离等高级特征
- 增加盘口抓取接口，替换手工录入市场线
- 引入时间序列交叉验证与自动调参
- 增加模型监控（按月份追踪命中率/ROI）
