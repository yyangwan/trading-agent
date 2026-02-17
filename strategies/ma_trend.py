"""
均线多头趋势策略
短期均线上穿长期均线，形成多头排列
"""
import pandas as pd
from .base_strategy import StrategyBase, StrategyResult


class MATrendStrategy(StrategyBase):
    """均线多头趋势策略"""

    @staticmethod
    def get_name() -> str:
        return "均线多头趋势"

    @staticmethod
    def get_description() -> str:
        return "短期均线上穿长期均线，形成多头排列"

    @staticmethod
    def get_required_indicators() -> list:
        return ['MA5', 'MA10', 'MA20', 'MA60', 'VOL', 'MA_VOL']

    @staticmethod
    def get_params() -> dict:
        return {
            'ma_short': 5,
            'ma_mid': 10,
            'ma_long': 20,
            'ma_vlong': 60,
            'volume_ratio': 1.5
        }

    @staticmethod
    def check(stock_data: pd.DataFrame, params: dict) -> bool:
        """
        检查是否符合均线多头趋势

        条件：
        1. MA5 > MA10 > MA20 > MA60（多头排列）
        2. 成交量放大（VOL > MA_VOL * volume_ratio）
        3. 最新收盘价在MA5之上
        """
        try:
            # 获取最新数据
            latest = stock_data.iloc[-1]

            # 提取参数
            ma_short = params.get('ma_short', 5)
            ma_mid = params.get('ma_mid', 10)
            ma_long = params.get('ma_long', 20)
            ma_vlong = params.get('ma_vlong', 60)
            volume_ratio = params.get('volume_ratio', 1.5)

            # 构建均线列名
            ma_short_col = f'MA{ma_short}'
            ma_mid_col = f'MA{ma_mid}'
            ma_long_col = f'MA{ma_long}'
            ma_vlong_col = f'MA{ma_vlong}'

            # 检查均线列是否存在
            required_cols = [ma_short_col, ma_mid_col, ma_long_col, ma_vlong_col, 'VOL', 'MA_VOL']
            if not all(col in stock_data.columns for col in required_cols):
                return False

            # 条件1：多头排列 MA5 > MA10 > MA20 > MA60
            ma_short_val = latest[ma_short_col]
            ma_mid_val = latest[ma_mid_col]
            ma_long_val = latest[ma_long_col]
            ma_vlong_val = latest[ma_vlong_col]

            condition1 = (ma_short_val > ma_mid_val > ma_long_val > ma_vlong_val)

            # 条件2：成交量放大
            condition2 = latest['VOL'] >= latest['MA_VOL'] * volume_ratio

            # 条件3：收盘价在MA5之上
            condition3 = latest['close'] > ma_short_val

            # 所有条件都满足
            return bool(condition1 and condition2 and condition3)

        except Exception as e:
            print(f"均线趋势策略检查错误: {e}")
            return False

    @staticmethod
    def get_score(stock_data: pd.DataFrame, params: dict) -> float:
        """
        评分函数
        根据均线排列的完美程度评分
        """
        try:
            latest = stock_data.iloc[-1]
            ma_short = params.get('ma_short', 5)
            ma_long = params.get('ma_long', 20)

            ma_short_col = f'MA{ma_short}'
            ma_long_col = f'MA{ma_long}'

            # 计算均线间距（越大越强）
            ma_gap = (latest[ma_short_col] - latest[ma_long_col]) / latest[ma_long_col]

            # 基础分60分，根据间距加分
            score = 60 + min(ma_gap * 500, 40)  # 最多加40分

            return round(score, 2)

        except Exception as e:
            print(f"均线趋势策略评分错误: {e}")
            return 50.0
