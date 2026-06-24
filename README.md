# A股量化回测系统 (quant-backtest)

基于Python的轻量级A股回测引擎，支持数据获取、策略信号生成、撮合执行、风控管理和报告输出。

## 功能特性

- **数据获取**：基于akshare获取A股真实日线数据（新浪数据源），支持CSV本地缓存
- **策略信号**：双均线交叉策略（MA5/MA20），可自定义均线周期
- **撮合引擎**：支持涨跌停限制、佣金印花税计算、停牌处理、滑点模拟
- **风控管理**：支持止损止盈、仓位控制、交易频率限制
- **报告输出**：自动生成资金曲线图和交易明细报告

## 安装依赖

```bash
pip install -r requirements.txt
```

## 使用方法

```bash
# 默认参数运行（贵州茅台，2025-01-01 至 2026-06-01）
python main.py

# 指定参数运行
python main.py --stock sh600519 --start 2025-01-01 --end 2026-06-01

# 查看帮助
python main.py --help
```

## 项目结构

```
quant-backtest/
├── src/
│   ├── data.py          # 数据获取层 — akshare拉A股日线，CSV缓存
│   ├── strategy.py      # 策略层 — 双均线交叉生成买卖信号
│   ├── backtest.py      # 撮合引擎（核心）— 涨跌停/佣金/印花税/停牌/资金管理
│   ├── risk.py          # 风控层 — 止损止盈、仓位控制、交易频率限制
│   └── report.py        # 报告层 — 收益曲线图、交易明细、关键指标输出
├── tests/
│   ├── test_backtest.py # 回测撮合逻辑测试
│   ├── test_strategy.py # 策略信号生成测试
│   └── test_data.py     # 数据模块测试
├── reports/             # 报告输出目录
├── main.py              # 入口 — 串起来：拉数据→跑策略→回测→出报告
├── requirements.txt     # 依赖：akshare, pandas, matplotlib, pytest
├── pytest.ini           # pytest配置
├── .gitignore
├── README.md            # 项目说明
└── DEVELOPMENT.md       # 开发日志
```

## 技术栈

- Python 3.11+
- akshare（数据源）
- pandas（数据处理）
- matplotlib（收益曲线可视化）
- pytest（测试）

## 开发工具

- copilot
