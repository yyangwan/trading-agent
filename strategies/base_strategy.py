"""
策略基类
所有策略插件必须继承此类并实现相应方法
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Tuple, Optional
import pandas as pd


class StrategyBase(ABC):
    """策略基类"""

    @staticmethod
    @abstractmethod
    def get_name() -> str:
        """
        返回策略名称

        Returns:
            策略名称
        """
        pass

    @staticmethod
    @abstractmethod
    def get_description() -> str:
        """
        返回策略描述

        Returns:
            策略描述
        """
        pass

    @staticmethod
    @abstractmethod
    def get_required_indicators() -> List[str]:
        """
        返回需要的技术指标列表

        Returns:
            指标名称列表，如: ['MA5', 'MA10', 'MACD', 'RSI']
        """
        pass

    @staticmethod
    @abstractmethod
    def get_params() -> Dict[str, any]:
        """
        返回可调参数及默认值

        Returns:
            参数字典，如: {'ma_short': 5, 'ma_long': 20}
        """
        pass

    @staticmethod
    @abstractmethod
    def check(stock_data: pd.DataFrame, params: Dict[str, any]) -> bool:
        """
        选股逻辑核心函数

        Args:
            stock_data: 股票数据（DataFrame），包含OHLCV和技术指标
            params: 策略参数

        Returns:
            True/False（是否符合条件的股票）
        """
        pass

    @staticmethod
    def get_score(stock_data: pd.DataFrame, params: Dict[str, any]) -> float:
        """
        评分函数（可选实现）

        Args:
            stock_data: 股票数据
            params: 策略参数

        Returns:
            评分 0-100，越高表示符合度越高
        """
        # 默认实现：返回固定评分
        return 50.0

    @staticmethod
    def get_stop_loss(params: Dict[str, any]) -> float:
        """
        获取止损比例（可选实现）

        Args:
            params: 策略参数

        Returns:
            止损比例，如 0.05 表示5%
        """
        return 0.05

    @staticmethod
    def get_take_profit(params: Dict[str, any]) -> float:
        """
        获取止盈比例（可选实现）

        Args:
            params: 策略参数

        Returns:
            止盈比例，如 0.15 表示15%
        """
        return 0.15


class StrategyResult:
    """策略执行结果"""

    def __init__(
        self,
        strategy_name: str,
        passed: bool,
        score: float = 50.0,
        signals: Dict[str, any] = None,
        message: str = ""
    ):
        self.strategy_name = strategy_name
        self.passed = passed
        self.score = score
        self.signals = signals or {}
        self.message = message

    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'strategy_name': self.strategy_name,
            'passed': self.passed,
            'score': self.score,
            'signals': self.signals,
            'message': self.message
        }
