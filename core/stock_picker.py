"""
选股核心引擎
"""
import pandas as pd
import logging
from typing import List, Dict, Optional
from datetime import datetime

from core.data_provider import DataProvider
from core.indicator_calculator import IndicatorCalculator
from core.strategy_manager import StrategyManager
from strategies.base_strategy import StrategyResult

logger = logging.getLogger(__name__)


class StockPicker:
    """选股引擎"""

    def __init__(self, config: dict):
        self.config = config
        self.data_provider = DataProvider(config.get('data_sources', {}))
        self.indicator_calc = IndicatorCalculator()
        self.strategy_manager = StrategyManager(config.get('strategies', {}).get('config_path'))
        self.strategy_manager.load_strategies()

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
            stock_list: 股票列表（None表示全市场）

        Returns:
            选股结果DataFrame
        """
        logger.info(f"开始选股: 日期={date}, 策略={strategies}")

        # 获取股票列表
        if stock_list is None:
            stock_list_df = self.data_provider.get_stock_list()
            if stock_list_df.empty:
                logger.error("获取股票列表失败")
                return pd.DataFrame()
            stock_list = stock_list_df['ts_code'].tolist()

        logger.info(f"待扫描股票数量: {len(stock_list)}")

        # 执行选股
        results = []
        for i, ts_code in enumerate(stock_list):
            if (i + 1) % 100 == 0:
                logger.info(f"进度: {i+1}/{len(stock_list)}")

            try:
                # 获取股票数据
                stock_data = self._get_stock_data(ts_code, date)
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
                    # 获取最新行情
                    latest = stock_data.iloc[-1]
                    result = {
                        'ts_code': ts_code,
                        'name': self._get_stock_name(ts_code),
                        'date': date or datetime.now().strftime('%Y-%m-%d'),
                        'close': latest['close'],
                        'change_pct': self._calc_change_pct(stock_data),
                        'volume': latest.get('volume', 0),
                        'matched_strategies': ','.join([r.strategy_name for r in passed_strategies]),
                        'strategy_count': len(passed_strategies),
                        'avg_score': sum(r.score for r in passed_strategies) / len(passed_strategies),
                        'stop_loss': passed_strategies[0].signals.get('stop_loss', 0.05),
                        'take_profit': passed_strategies[0].signals.get('take_profit', 0.15),
                    }
                    results.append(result)

            except Exception as e:
                logger.error(f"处理{ts_code}失败: {e}")
                continue

        # 转换为DataFrame
        results_df = pd.DataFrame(results)

        if not results_df.empty:
            # 按匹配策略数和评分排序
            results_df = results_df.sort_values(
                by=['strategy_count', 'avg_score'],
                ascending=[False, False]
            ).reset_index(drop=True)

            logger.info(f"选股完成: 找到{len(results_df)}只股票")

        return results_df

    def _get_stock_data(self, ts_code: str, date: str = None) -> Optional[pd.DataFrame]:
        """获取股票数据"""
        # TODO: 实现数据获取逻辑
        # 这里先返回模拟数据
        return None

    def _get_stock_name(self, ts_code: str) -> str:
        """获取股票名称"""
        # TODO: 实现股票名称获取
        return ""

    def _calc_change_pct(self, stock_data: pd.DataFrame) -> float:
        """计算涨跌幅"""
        if len(stock_data) < 2:
            return 0.0
        latest_close = stock_data.iloc[-1]['close']
        prev_close = stock_data.iloc[-2]['close']
        return round((latest_close - prev_close) / prev_close * 100, 2)


# 测试代码
if __name__ == "__main__":
    # 测试策略管理器
    manager = StrategyManager("configs/strategies_config.yaml")
    manager.load_strategies()

    print(f"已加载策略: {manager.get_all_strategies()}")
    print(f"启用策略: {list(manager.get_enabled_strategies().keys())}")
