# A股技术分析选股策略系统

## 功能特点

✅ **插件化架构**：每个策略独立插件，新增策略不修改核心代码
✅ **多数据源冗余**：tushare + akshare，自动切换保障数据完整性
✅ **4套预设策略**：均线多头、超跌反弹、突破选股、底部吸筹
✅ **配置驱动**：YAML配置文件，灵活调整参数
✅ **完整技术指标**：MA、MACD、KDJ、RSI、BOLL、OBV等
✅ **真实交易适配**：复权处理、停牌过滤、数据质量保障

## 目录结构

```
stock_picker/
├── core/                    # 核心引擎
│   ├── data_provider.py     # 数据提供者
│   ├── indicator_calculator.py  # 技术指标计算
│   ├── strategy_manager.py  # 策略管理器
│   └── stock_picker.py      # 选股引擎
│
├── strategies/              # 策略插件
│   ├── base_strategy.py     # 策略基类
│   ├── ma_trend.py          # 均线多头策略
│   ├── oversold_rebound.py  # 超跌反弹策略
│   ├── breakout.py          # 突破策略
│   ├── bottom_accumulation.py  # 底部吸筹策略
│   └── custom_strategies/   # 自定义策略目录
│
├── configs/                 # 配置文件
│   ├── system_config.yaml   # 系统配置
│   └── strategies_config.yaml  # 策略配置
│
├── data/                    # 数据存储
├── output/                  # 输出结果
├── logs/                    # 日志文件
├── main.py                  # 主程序入口
├── requirements.txt         # 依赖包
└── README.md               # 说明文档
```

## 快速开始

### 1. 安装依赖

```bash
cd stock_picker
pip install -r requirements.txt
```

### 2. 配置数据源

编辑 `configs/system_config.yaml`，填写你的tushare token：

```yaml
data_sources:
  primary:
    name: "tushare"
    token: "your_token_here"  # 填写你的token
```

### 3. 测试配置

```bash
python main.py --test
```

### 4. 执行选股

```bash
# 使用默认配置选股
python main.py

# 指定日期选股
python main.py --date 2026-02-16

# 指定策略
python main.py --strategies ma_trend oversold_rebound
```

## 新增自定义策略

### 方法1：编写Python插件

在 `strategies/custom_strategies/` 目录创建新文件：

```python
# strategies/custom_strategies/my_strategy.py
from strategies.base_strategy import StrategyBase
import pandas as pd

class MyStrategy(StrategyBase):
    @staticmethod
    def get_name() -> str:
        return "我的策略"

    @staticmethod
    def get_description() -> str:
        return "策略描述"

    @staticmethod
    def get_required_indicators() -> list:
        return ['MA5', 'MA20', 'RSI']

    @staticmethod
    def get_params() -> dict:
        return {'threshold': 30}

    @staticmethod
    def check(stock_data: pd.DataFrame, params: dict) -> bool:
        latest = stock_data.iloc[-1]
        return latest['RSI'] < params['threshold']
```

然后在 `configs/strategies_config.yaml` 添加：

```yaml
my_strategy:
  enabled: true
  module: "strategies.custom_strategies.my_strategy"
  params:
    threshold: 20
  weight: 1.0
```

### 方法2：仅修改配置（简单策略）

直接在 `configs/strategies_config.yaml` 添加简单条件：

```yaml
simple_ma_cross:
  enabled: true
  type: simple
  conditions:
    - MA5 > MA20
    - RSI < 30
```

## 预设策略说明

### 1. 均线多头趋势 (ma_trend)
**逻辑**：短期均线上穿长期均线，形成多头排列
**条件**：
- MA5 > MA10 > MA20 > MA60
- 成交量放大（VOL > MA_VOL * 1.5）
- 收盘价在MA5之上

### 2. 超跌反弹 (oversold_rebound)
**逻辑**：股价超跌后出现止跌信号
**条件**：
- RSI < 20（超卖）
- KDJ的J值 < 10（低位）
- 股价接近布林线下轨
- 成交量开始放大

### 3. 突破选股 (breakout)
**逻辑**：股价突破关键压力位
**条件**：
- 突破60日新高
- 成交量显著放大（2倍以上）
- 布林带开口扩大

### 4. 底部吸筹 (bottom_accumulation)
**逻辑**：主力资金流入，股价横盘筑底
**条件**：
- OBV持续上升（资金流入）
- 股价波动率 < 5%（横盘）
- MACD红柱放大

## 输出说明

选股结果保存在 `output/picks/picks_YYYY-MM-DD.csv`，包含：

| 字段 | 说明 |
|------|------|
| ts_code | 股票代码 |
| name | 股票名称 |
| date | 选股日期 |
| close | 收盘价 |
| change_pct | 涨跌幅 |
| volume | 成交量 |
| matched_strategies | 匹配的策略 |
| strategy_count | 匹配策略数 |
| avg_score | 平均评分 |
| stop_loss | 止损价 |
| take_profit | 止盈价 |

## 风险提示

⚠️ **本系统仅供学习研究使用，不构成任何投资建议**
⚠️ **股市有风险，投资需谨慎**
⚠️ **历史数据不代表未来表现**

## 后续开发计划

- [ ] 完整的数据源实现（tushare + akshare）
- [ ] 回测系统
- [ ] Web界面
- [ ] 实时行情监控
- [ ] 微信/邮件告警
- [ ] 更多技术指标
- [ ] 参数自动优化

## License

MIT License
