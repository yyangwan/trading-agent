"""
策略管理器 - 负责策略的加载、注册和执行
"""
import os
import importlib
import inspect
from typing import Dict, List, Optional
import yaml
import logging
from pathlib import Path

from strategies.base_strategy import StrategyBase, StrategyResult

logger = logging.getLogger(__name__)


class StrategyManager:
    """策略管理器"""

    def __init__(self, config_path: str = None):
        self.strategies: Dict[str, StrategyBase] = {}
        self.strategy_configs: Dict = {}
        self.config_path = config_path or "configs/strategies_config.yaml"
        self.load_configs()

    def load_configs(self):
        """加载策略配置"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                self.strategy_configs = config.get('strategies', {})
            logger.info(f"加载策略配置: {len(self.strategy_configs)}个策略")
        except Exception as e:
            logger.error(f"加载策略配置失败: {e}")
            self.strategy_configs = {}

    def load_strategies(self, strategies_dir: str = "strategies"):
        """
        动态加载所有策略

        Args:
            strategies_dir: 策略目录
        """
        strategies_path = Path(strategies_dir)

        # 遍历策略目录
        for py_file in strategies_path.glob("*.py"):
            if py_file.name.startswith("__"):
                continue

            module_name = py_file.stem
            try:
                # 动态导入模块
                module = importlib.import_module(f"strategies.{module_name}")

                # 查找策略类
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    if issubclass(obj, StrategyBase) and obj != StrategyBase:
                        # 注册策略
                        strategy_name = obj.get_name()
                        self.strategies[strategy_name] = obj
                        logger.info(f"加载策略: {strategy_name}")

            except Exception as e:
                logger.error(f"加载策略{module_name}失败: {e}")

    def get_strategy(self, strategy_name: str) -> Optional[StrategyBase]:
        """获取策略实例"""
        return self.strategies.get(strategy_name)

    def get_all_strategies(self) -> List[str]:
        """获取所有策略名称"""
        return list(self.strategies.keys())

    def get_enabled_strategies(self) -> Dict[str, StrategyBase]:
        """获取启用的策略"""
        enabled = {}
        for name, config in self.strategy_configs.items():
            if config.get('enabled', False):
                strategy = self.get_strategy_by_module(config.get('module', ''))
                if strategy:
                    enabled[name] = strategy
        return enabled

    def get_strategy_by_module(self, module_path: str) -> Optional[StrategyBase]:
        """根据模块路径获取策略类"""
        # 从模块路径提取类名
        # 例如: "strategies.ma_trend" -> "MATrendStrategy"
        try:
            module_name = module_path.split('.')[-1]
            module = importlib.import_module(module_path)

            for name, obj in inspect.getmembers(module, inspect.isclass):
                if issubclass(obj, StrategyBase) and obj != StrategyBase:
                    return obj

        except Exception as e:
            logger.error(f"获取策略{module_path}失败: {e}")

        return None

    def execute_strategy(
        self,
        strategy_name: str,
        stock_data,
        params: dict = None
    ) -> StrategyResult:
        """
        执行单个策略

        Args:
            strategy_name: 策略名称
            stock_data: 股票数据
            params: 策略参数

        Returns:
            策略执行结果
        """
        try:
            # 获取策略配置
            config = self.strategy_configs.get(strategy_name, {})
            final_params = params or config.get('params', {})

            # 获取策略类
            strategy_class = self.get_strategy_by_module(config.get('module', ''))
            if not strategy_class:
                return StrategyResult(
                    strategy_name=strategy_name,
                    passed=False,
                    message=f"策略{strategy_name}未找到"
                )

            # 执行策略检查
            passed = strategy_class.check(stock_data, final_params)

            # 计算评分
            score = strategy_class.get_score(stock_data, final_params) if passed else 0

            return StrategyResult(
                strategy_name=strategy_name,
                passed=passed,
                score=score,
                message=f"策略执行完成"
            )

        except Exception as e:
            logger.error(f"执行策略{strategy_name}失败: {e}")
            return StrategyResult(
                strategy_name=strategy_name,
                passed=False,
                message=f"执行错误: {str(e)}"
            )

    def execute_all_strategies(
        self,
        stock_data,
        strategy_names: List[str] = None
    ) -> List[StrategyResult]:
        """
        执行所有策略

        Args:
            stock_data: 股票数据
            strategy_names: 要执行的策略列表（默认执行所有启用的策略）

        Returns:
            策略执行结果列表
        """
        results = []

        # 确定要执行的策略
        if strategy_names is None:
            enabled = self.get_enabled_strategies()
            strategy_names = list(enabled.keys())

        for name in strategy_names:
            result = self.execute_strategy(name, stock_data)
            results.append(result)

        return results
