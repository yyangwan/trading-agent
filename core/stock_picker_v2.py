"""
选股核心引擎 - 改进版（支持本地数据）
"""
import pandas as pd
import logging
import os
from typing import List, Dict, Optional
from datetime import datetime

from core.data_provider_full import FullDataProvider
from core.indicator_calculator import IndicatorCalculator
from core.strategy_manager import StrategyManager

logger = logging.getLogger(__name__)


class StockPicker:
    """选股引擎（改进版）"""

    def __init__(self, config: dict):
        self.config = config
        self.indicator_calc = IndicatorCalculator()
        self.strategy_manager = StrategyManager(config.get('strategies', {}).get('config_path'))
        self.strategy_manager.load_strategies()
        self.data_dir = 'data/stock_data/csv'

    def pick_stocks(
        self,
        date: str = None,
        strategies: List[str] = None,
        stock_list: List[str] = None
    ) -> pd.DataFrame:
        """
        执行选股

        Args:
            date: 选股日期
            strategies: 策略列表
            stock_list: 股票列表（None则从本地读取）

        Returns:
            选股结果DataFrame
        """
        logger.info(f"开始选股: 日期={date}, 策略={strategies}")

        # 获取本地股票列表
        if stock_list is None:
            stock_list = self._get_local_stock_list()

        if not stock_list:
            logger.error("未找到股票数据")
            return pd.DataFrame()

        logger.info(f"本地数据: {len(stock_list)} 只股票")

        # 执行选股
        results = []
        for i, ts_code in enumerate(stock_list):
            if (i + 1) % 100 == 0:
                logger.info(f"进度: {i+1}/{len(stock_list)}")

            try:
                # 读取本地数据
                stock_data = self._load_local_stock_data(ts_code)

                if stock_data is None or stock_data.empty:
                    continue

                # 计算技术指标
                stock_data = self.indicator_calc.calculate_all(stock_data)

                # 执行策略
                strategy_results = self.strategy_manager.execute_all_strategies(
                    stock_data,
                    strategies
                )

                # 检查是否有策略通过
                passed_strategies = [r for r in strategy_results if r.passed]
                if passed_strategies:
                    latest = stock_data.iloc[-1]
                    result = {
                        'ts_code': ts_code,
                        'name': ts_code,  # 暂时使用代码
                        'date': date or datetime.now().strftime('%Y-%m-%d'),
                        'close': latest['close'],
                        'change_pct': self._calc_change_pct(stock_data),
                        'volume': latest.get('vol', 0),
                        'matched_strategies': ','.join([r.strategy_name for r in passed_strategies]),
                        'strategy_count': len(passed_strategies),
                        'avg_score': sum(r.score for r in passed_strategies) / len(passed_strategies),
                        'stop_loss': 0.05,
                        'take_profit': 0.15,
                    }
                    results.append(result)

            except Exception as e:
                logger.error(f"处理{ts_code}失败: {e}")
                continue

        # 转换为DataFrame
        results_df = pd.DataFrame(results)

        if not results_df.empty:
            results_df = results_df.sort_values(
                by=['strategy_count', 'avg_score'],
                ascending=[False, False]
            ).reset_index(drop=True)

            logger.info(f"选股完成: 找到{len(results_df)}只股票")

        return results_df

    def _get_local_stock_list(self) -> List[str]:
        """获取本地股票列表"""
        try:
            if os.path.exists(self.data_dir):
                files = [f for f in os.listdir(self.data_dir) if f.endswith('.csv')]
                logger.info(f"找到 {len(files)} 只本地股票数据")
                return [f.replace('.csv', '') for f in files]
        except Exception as e:
            logger.error(f"读取本地股票列表失败: {e}")

        return []

    def _load_local_stock_data(self, ts_code: str) -> Optional[pd.DataFrame]:
        """加载本地股票数据"""
        try:
            file_path = os.path.join(self.data_dir, f"{ts_code}.csv")

            if os.path.exists(file_path):
                df = pd.read_csv(file_path)

                # 确保有必要的列
                required_cols = ['open', 'high', 'low', 'close', 'vol']
                if all(col in df.columns for col in required_cols):
                    # 重命名volume为vol（如果需要）
                    if 'volume' in df.columns and 'vol' not in df.columns:
                        df = df.rename(columns={'volume': 'vol'})

                    return df
                else:
                    logger.warning(f"{ts_code} 缺少必要列，跳过")
                    return None

        except Exception as e:
            logger.error(f"读取{ts_code}数据失败: {e}")

        return None

    def _calc_change_pct(self, stock_data: pd.DataFrame) -> float:
        """计算涨跌幅"""
        if len(stock_data) < 2:
            return 0.0

        try:
            latest_close = stock_data.iloc[-1]['close']
            prev_close = stock_data.iloc[-2]['close']
            return round((latest_close - prev_close) / prev_close * 100, 2)
        except:
            return 0.0


# 测试代码
if __name__ == "__main__":
    import sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

    # 测试选股
    config = {}
    picker = StockPicker(config)

    results = picker.pick_stocks(date='2026-02-17')

    if not results.empty:
        print(f"✓ 找到 {len(results)} 只股票")
        print(results[['ts_code', 'close', 'change_pct', 'matched_strategies']].head(10))
    else:
        print("未找到符合条件的股票")
