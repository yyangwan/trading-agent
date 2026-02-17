#!/usr/bin/env python3
"""
A股选股策略系统 - 主程序入口
"""
import sys
import yaml
import logging
import argparse
from pathlib import Path
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from core import StockPicker


def setup_logging(config: dict):
    """配置日志"""
    log_config = config.get('logging', {})

    logging.basicConfig(
        level=getattr(logging, log_config.get('level', 'INFO')),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler()
        ]
    )

    # 文件日志
    if log_config.get('file', True):
        log_file = log_config.get('file_path', 'logs/stock_picker.log')
        log_dir = Path(log_file).parent
        log_dir.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        logging.getLogger().addHandler(file_handler)


def load_config(config_file: str = "configs/system_config.yaml") -> dict:
    """加载系统配置"""
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        return config
    except Exception as e:
        print(f"加载配置失败: {e}")
        return {}


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='A股选股策略系统')
    parser.add_argument('--date', type=str, help='选股日期 (YYYY-MM-DD)')
    parser.add_argument('--strategies', type=str, nargs='+', help='指定策略')
    parser.add_argument('--config', type=str, default='configs/system_config.yaml', help='配置文件路径')
    parser.add_argument('--test', action='store_true', help='测试模式（仅验证配置）')

    args = parser.parse_args()

    # 加载配置
    config = load_config(args.config)

    # 配置日志
    setup_logging(config)

    logger = logging.getLogger(__name__)

    logger.info("=" * 50)
    logger.info("A股选股策略系统启动")
    logger.info("=" * 50)

    # 测试模式
    if args.test:
        logger.info("测试模式：验证配置")
        from core.strategy_manager import StrategyManager

        manager = StrategyManager("configs/strategies_config.yaml")
        manager.load_strategies()

        logger.info(f"✓ 配置文件: {args.config}")
        logger.info(f"✓ 已加载策略: {len(manager.get_all_strategies())}个")
        logger.info(f"✓ 启用策略: {list(manager.get_enabled_strategies().keys())}")
        logger.info("测试通过！")
        return

    # 创建选股引擎
    picker = StockPicker(config)

    # 执行选股
    date = args.date or datetime.now().strftime('%Y-%m-%d')

    logger.info(f"开始选股: {date}")

    results = picker.pick_stocks(
        date=date,
        strategies=args.strategies
    )

    # 输出结果
    if not results.empty:
        output_file = f"output/picks/picks_{date}.csv"
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)

        results.to_csv(output_file, index=False, encoding='utf-8-sig')

        logger.info(f"✓ 选股完成: {len(results)}只股票")
        logger.info(f"✓ 结果已保存: {output_file}")

        # 显示前10只
        print("\n前10只股票:")
        print(results.head(10).to_string(index=False))
    else:
        logger.warning("未找到符合条件的股票")

    logger.info("=" * 50)
    logger.info("选股结束")
    logger.info("=" * 50)


if __name__ == "__main__":
    main()
