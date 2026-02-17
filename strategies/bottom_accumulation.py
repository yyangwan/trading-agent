"""
底部吸筹策略
主力资金流入，股价横盘筑底
"""
import pandas as pd
import numpy as np
from .base_strategy import StrategyBase, StrategyResult


class BottomAccumulationStrategy(StrategyBase):
    """底部吸筹策略"""

    @staticmethod
    def get_name() -> str:
        return "底部吸筹"

    @staticmethod
    def get_description() -> str:
        return "主力资金流入，股价横盘筑底"

    @staticmethod
    def get_required_indicators() -> list:
        return ['OBV', 'CLOSE', 'MACD_DIF', 'MACD_DEA', 'MACD_BAR', 'VOL']

    @staticmethod
    def get_params() -> dict:
        return {
            'obv_trend': 'up',
            'volatility_threshold': 0.05,
            'macd_red_grow': True
        }

    @staticmethod
    def check(stock_data: pd.DataFrame, params: dict) -> bool:
        """
        检查是否符合底部吸筹条件

        条件：
        1. OBV持续上升（资金流入）
        2. 股价横盘（波动率低于阈值）
        3. MACD红柱放大（买入增强）
        """
        try:
            if len(stock_data) < 20:
                return False

            latest = stock_data.iloc[-1]

            # 提取参数
            obv_trend = params.get('obv_trend', 'up')
            volatility_threshold = params.get('volatility_threshold', 0.05)
            macd_red_grow = params.get('macd_red_grow', True)

            # 检查必需列
            if 'OBV' not in stock_data.columns:
                return False

            # 条件1：OBV持续上升
            if obv_trend == 'up':
                # 最近5天OBV趋势向上
                obv_recent = stock_data['OBV'].iloc[-5:]
                obv_trend_up = (obv_recent.iloc[-1] > obv_recent.iloc[0])
            else:
                obv_trend_up = True

            # 条件2：股价横盘（波动率低）
            # 计算最近20天的涨跌幅
            returns = stock_data['close'].iloc[-20:].pct_change()
            volatility = returns.std()
            condition2 = volatility < volatility_threshold

            # 条件3：MACD红柱放大（可选）
            condition3 = True
            if macd_red_grow and 'MACD_BAR' in stock_data.columns:
                # 最近3天MACD红柱递增
                macd_bars = stock_data['MACD_BAR'].iloc[-3:]
                condition3 = (macd_bars.iloc[-1] > macd_bars.iloc[-2] > macd_bars.iloc[-3]) and macd_bars.iloc[-1] > 0

            return bool(obv_trend_up and condition2 and condition3)

        except Exception as e:
            print(f"底部吸筹策略检查错误: {e}")
            return False

    @staticmethod
    def get_score(stock_data: pd.DataFrame, params: dict) -> float:
        """
        评分函数
        OBV上升越稳，分数越高
        """
        try:
            # OBV线性回归斜率
            obv_recent = stock_data['OBV'].iloc[-10:].values
            x = np.arange(len(obv_recent))
            slope = np.polyfit(x, obv_recent, 1)[0]

            # 斜率越大分数越高
            score = 60 + min(abs(slope) / 1000000 * 100, 40)

            return round(score, 2)

        except Exception as e:
            print(f"底部吸筹策略评分错误: {e}")
            return 50.0
