"""
技术指标计算器
支持主流技术指标的计算
"""
import pandas as pd
import numpy as np
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)


class IndicatorCalculator:
    """技术指标计算器"""

    def __init__(self):
        self.indicators = {}

    def calculate_all(self, stock_data: pd.DataFrame) -> pd.DataFrame:
        """
        计算所有常用技术指标

        Args:
            stock_data: 原始OHLCV数据

        Returns:
            添加了技术指标的DataFrame
        """
        df = stock_data.copy()

        # 移动平均线
        df = self.add_ma(df, periods=[5, 10, 20, 60])

        # 成交量均线
        if 'volume' in df.columns:
            df['MA_VOL'] = df['volume'].rolling(window=5).mean()

        # MACD
        df = self.add_macd(df)

        # KDJ
        df = self.add_kdj(df)

        # RSI
        df = self.add_rsi(df, period=14)

        # BOLL
        df = self.add_boll(df)

        # OBV
        if 'volume' in df.columns:
            df = self.add_obv(df)

        return df

    def add_ma(self, df: pd.DataFrame, periods: List[int]) -> pd.DataFrame:
        """添加移动平均线"""
        for period in periods:
            df[f'MA{period}'] = df['close'].rolling(window=period).mean()
        return df

    def add_macd(self, df: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
        """添加MACD指标"""
        try:
            # 计算EMA
            exp1 = df['close'].ewm(span=fast, adjust=False).mean()
            exp2 = df['close'].ewm(span=slow, adjust=False).mean()

            # DIF和DEA
            df['MACD_DIF'] = exp1 - exp2
            df['MACD_DEA'] = df['MACD_DIF'].ewm(span=signal, adjust=False).mean()
            df['MACD_BAR'] = (df['MACD_DIF'] - df['MACD_DEA']) * 2

            # 向后兼容
            df['MACD'] = df['MACD_DIF']

        except Exception as e:
            logger.error(f"MACD计算错误: {e}")
            df['MACD_DIF'] = 0
            df['MACD_DEA'] = 0
            df['MACD_BAR'] = 0
            df['MACD'] = 0

        return df

    def add_kdj(self, df: pd.DataFrame, period: int = 9, m1: int = 3, m2: int = 3) -> pd.DataFrame:
        """添加KDJ指标"""
        try:
            low_list = df['low'].rolling(window=period, min_periods=1).min()
            high_list = df['high'].rolling(window=period, min_periods=1).max()

            rsv = (df['close'] - low_list) / (high_list - low_list) * 100

            df['KDJ_K'] = rsv.ewm(com=m1, adjust=False).mean()
            df['KDJ_D'] = df['KDJ_K'].ewm(com=m2, adjust=False).mean()
            df['KDJ_J'] = 3 * df['KDJ_K'] - 2 * df['KDJ_D']

        except Exception as e:
            logger.error(f"KDJ计算错误: {e}")
            df['KDJ_K'] = 50
            df['KDJ_D'] = 50
            df['KDJ_J'] = 50

        return df

    def add_rsi(self, df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
        """添加RSI指标"""
        try:
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

            rs = gain / loss
            df['RSI'] = 100 - (100 / (1 + rs))

            # 填充NaN值
            df['RSI'] = df['RSI'].fillna(50)

        except Exception as e:
            logger.error(f"RSI计算错误: {e}")
            df['RSI'] = 50

        return df

    def add_boll(self, df: pd.DataFrame, period: int = 20, std_dev: int = 2) -> pd.DataFrame:
        """添加布林带指标"""
        try:
            ma = df['close'].rolling(window=period).mean()
            std = df['close'].rolling(window=period).std()

            df['BOLL_MIDDLE'] = ma
            df['BOLL_UPPER'] = ma + std * std_dev
            df['BOLL_LOWER'] = ma - std * std_dev

        except Exception as e:
            logger.error(f"BOLL计算错误: {e}")
            df['BOLL_MIDDLE'] = df['close']
            df['BOLL_UPPER'] = df['close']
            df['BOLL_LOWER'] = df['close']

        return df

    def add_obv(self, df: pd.DataFrame) -> pd.DataFrame:
        """添加OBV指标"""
        try:
            obv = (np.sign(df['close'].diff()) * df['volume']).fillna(0).cumsum()
            df['OBV'] = obv

        except Exception as e:
            logger.error(f"OBV计算错误: {e}")
            df['OBV'] = 0

        return df

    def calculate_custom(self, df: pd.DataFrame, indicator_name: str, **params) -> pd.Series:
        """
        计算自定义指标

        Args:
            df: 股票数据
            indicator_name: 指标名称
            **params: 指标参数

        Returns:
            指标值Series
        """
        # TODO: 实现自定义指标计算
        pass
