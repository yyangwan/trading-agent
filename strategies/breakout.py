"""
突破选股策略
股价突破关键压力位
"""
import pandas as pd
from .base_strategy import StrategyBase, StrategyResult


class BreakoutStrategy(StrategyBase):
    """突破选股策略"""

    @staticmethod
    def get_name() -> str:
        return "突破选股"

    @staticmethod
    def get_description() -> str:
        return "股价突破关键压力位"

    @staticmethod
    def get_required_indicators() -> list:
        return ['HIGH', 'LOW', 'CLOSE', 'VOL', 'MA_VOL', 'BOLL_UPPER', 'BOLL_LOWER']

    @staticmethod
    def get_params() -> dict:
        return {
            'days_high': 60,
            'volume_ratio': 2.0,
            'boll_expansion': True
        }

    @staticmethod
    def check(stock_data: pd.DataFrame, params: dict) -> bool:
        """
        检查是否符合突破条件

        条件：
        1. 股价突破N日新高
        2. 成交量显著放大
        3. 布林带开口扩大（可选）
        """
        try:
            latest = stock_data.iloc[-1]

            # 提取参数
            days_high = params.get('days_high', 60)
            volume_ratio = params.get('volume_ratio', 2.0)
            boll_expansion = params.get('boll_expansion', True)

            # 检查数据长度
            if len(stock_data) < days_high + 10:
                return False

            # 条件1：突破N日新高
            high_period = stock_data.iloc[-(days_high+1):-1]['high'].max()
            condition1 = latest['close'] > high_period

            # 条件2：成交量显著放大
            if 'VOL' in stock_data.columns and 'MA_VOL' in stock_data.columns:
                condition2 = latest['VOL'] >= latest['MA_VOL'] * volume_ratio
            else:
                condition2 = True

            # 条件3：布林带开口扩大（可选）
            condition3 = True
            if boll_expansion and 'BOLL_UPPER' in stock_data.columns and 'BOLL_LOWER' in stock_data.columns:
                # 计算布林带宽度
                latest_bw = latest['BOLL_UPPER'] - latest['BOLL_LOWER']
                avg_bw = (stock_data['BOLL_UPPER'] - stock_data['BOLL_LOWER']).iloc[-20:].mean()
                condition3 = latest_bw > avg_bw * 1.2

            return bool(condition1 and condition2 and condition3)

        except Exception as e:
            print(f"突破策略检查错误: {e}")
            return False

    @staticmethod
    def get_score(stock_data: pd.DataFrame, params: dict) -> float:
        """
        评分函数
        突破幅度越大，分数越高
        """
        try:
            latest = stock_data.iloc[-1]
            days_high = params.get('days_high', 60)

            # 计算突破幅度
            high_period = stock_data.iloc[-(days_high+1):-1]['high'].max()
            breakout_ratio = (latest['close'] - high_period) / high_period

            # 基础分60分，根据突破幅度加分
            score = 60 + min(breakout_ratio * 500, 40)

            return round(score, 2)

        except Exception as e:
            print(f"突破策略评分错误: {e}")
            return 50.0
