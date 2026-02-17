"""
超跌反弹策略
股价超跌后出现止跌信号
"""
import pandas as pd
from .base_strategy import StrategyBase, StrategyResult


class OversoldReboundStrategy(StrategyBase):
    """超跌反弹策略"""

    @staticmethod
    def get_name() -> str:
        return "超跌反弹"

    @staticmethod
    def get_description() -> str:
        return "股价超跌后出现止跌信号"

    @staticmethod
    def get_required_indicators() -> list:
        return ['RSI', 'KDJ_K', 'KDJ_D', 'KDJ_J', 'BOLL_UPPER', 'BOLL_MIDDLE', 'BOLL_LOWER', 'VOL', 'MA_VOL']

    @staticmethod
    def get_params() -> dict:
        return {
            'rsi_threshold': 20,
            'kdj_j_threshold': 10,
            'use_boll_lower': True,
            'volume_increase': True
        }

    @staticmethod
    def check(stock_data: pd.DataFrame, params: dict) -> bool:
        """
        检查是否符合超跌反弹条件

        条件：
        1. RSI < rsi_threshold（超卖）
        2. KDJ的J值 < kdj_j_threshold（低位）
        3. 股价接近或低于布林线下轨（可选）
        4. 成交量开始放大（可选）
        """
        try:
            latest = stock_data.iloc[-1]

            # 提取参数
            rsi_threshold = params.get('rsi_threshold', 20)
            kdj_j_threshold = params.get('kdj_j_threshold', 10)
            use_boll_lower = params.get('use_boll_lower', True)
            volume_increase = params.get('volume_increase', True)

            # 检查必需列
            required_cols = ['RSI', 'KDJ_J']
            if not all(col in stock_data.columns for col in required_cols):
                return False

            # 条件1：RSI超卖
            condition1 = latest['RSI'] < rsi_threshold

            # 条件2：KDJ的J值低位
            condition2 = latest['KDJ_J'] < kdj_j_threshold

            # 条件3：布林线下轨（可选）
            condition3 = True
            if use_boll_lower and 'BOLL_LOWER' in stock_data.columns:
                # 股价接近或低于布林线下轨
                condition3 = latest['close'] <= latest['BOLL_LOWER'] * 1.02

            # 条件4：成交量放大（可选）
            condition4 = True
            if volume_increase and 'VOL' in stock_data.columns and 'MA_VOL' in stock_data.columns:
                condition4 = latest['VOL'] >= latest['MA_VOL'] * 1.2

            # 至少满足条件1和2，其他条件根据配置
            return bool(condition1 and condition2 and condition3 and condition4)

        except Exception as e:
            print(f"超跌反弹策略检查错误: {e}")
            return False

    @staticmethod
    def get_score(stock_data: pd.DataFrame, params: dict) -> float:
        """
        评分函数
        RSI和KDJ越低，分数越高
        """
        try:
            latest = stock_data.iloc[-1]

            # RSI越低分数越高
            rsi_score = max(0, (30 - latest['RSI']) / 30 * 50)

            # KDJ_J越低分数越高
            kdj_score = max(0, (20 - latest['KDJ_J']) / 20 * 50)

            score = rsi_score * 0.6 + kdj_score * 0.4

            return round(score, 2)

        except Exception as e:
            print(f"超跌反弹策略评分错误: {e}")
            return 50.0
