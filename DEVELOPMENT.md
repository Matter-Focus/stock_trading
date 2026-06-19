# AI 协作开发记录

## 开发阶段

### 第1阶段：项目骨架搭建

完成时间：2026-06-19
负责人：Trae AI

创建了完整的项目结构和模块框架：

- src/data.py: 数据获取模块
- src/strategy.py: 策略模块
- src/backtest.py: 回测引擎模块
- src/risk.py: 风控模块
- src/report.py: 报告模块
- tests/: 测试文件
- main.py: 入口文件

### 待完成阶段

- 第2阶段：核心逻辑实现（backtest.py 撮合逻辑）
- 第3阶段：策略和数据模块实现
- 第4阶段：测试和优化

## 技术决策

1. 使用 dataclass 定义数据结构（Trade, Position, BacktestConfig）
2. 使用 type hint 提高代码可读性和 IDE 支持
3. 采用 pytest 进行单元测试
4. 回测价格使用下一根K线开盘价 + 滑点

## 注意事项

- 涨跌停限制需要在撮合时判断
- 卖出时需要扣除印花税
- 成交量为100股的整数倍
