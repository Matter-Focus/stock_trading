# A股量化回测系统

基于 Python 的 A 股量化回测系统，支持双均线交叉策略回测。

## 技术栈

- Python 3.14+
- akshare: 数据获取
- pandas: 数据处理
- matplotlib: 可视化
- pytest: 测试

## 项目结构

```
quant-backtest/
 src/
    data.py          # 数据获取
    strategy.py      # 策略逻辑
    backtest.py      # 回测引擎
    risk.py          # 风控管理
    report.py        # 绩效报告
 tests/
    test_backtest.py
    test_strategy.py
    test_data.py
 main.py              # 入口文件
 requirements.txt
 pytest.ini
```

## 快速开始

```bash
pip install -r requirements.txt
python main.py
```

## 策略说明

双均线交叉策略：
- MA5 上穿 MA20 时买入
- MA5 下穿 MA20 时卖出

## 回测参数

- 初始资金：10万元
- 佣金率：0.03%
- 滑点率：0.02%
- 印花税：0.1%
